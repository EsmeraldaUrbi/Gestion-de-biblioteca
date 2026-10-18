from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.db import IntegrityError, transaction
from django.test import TestCase

from biblioteca.models import (
    Ejemplar,
    Libro,
    Prestamo,
    Rol,
    Sancion,
    Usuario,
)

from biblioteca.services.bloqueos_service import BloqueosService
from biblioteca.services.prestamos_service import (
    BloqueoVigenteError,
    PrestamoService,
)


class BloqueosServiceTests(TestCase):
    """
    Pruebas de bloqueos automaticos del ticket 3.7.2.

    Se ejecutan sobre la base de datos de pruebas.
    """

    def setUp(self):
        self.hoy = date(2026, 10, 15)
        self.service = BloqueosService()

        self.rol = Rol.objects.create(
            nombre='estudiante',
            limite_prestamos_activos=5
        )

        self.usuario = Usuario(
            rol=self.rol,
            nombre='Usuario de prueba',
            email='bloqueos@test.local'
        )
        self.usuario.set_password('Biblioteca123*')
        self.usuario.save()

        self.libro = Libro.objects.create(
            titulo='Libro para pruebas de bloqueos',
            isbn='9780000000002'
        )

        self.contador_ejemplares = 0

    def crear_ejemplar(self):
        self.contador_ejemplares += 1

        return Ejemplar.objects.create(
            libro=self.libro,
            codigo_inventario=(
                f'BLOQ-{self.contador_ejemplares:03d}'
            ),
            estado='ACTIVO'
        )

    def crear_prestamo(
        self,
        fecha_limite,
        fecha_devolucion=None
    ):
        ejemplar = self.crear_ejemplar()

        return Prestamo.objects.create(
            usuario=self.usuario,
            ejemplar=ejemplar,
            fecha_prestamo=(
                fecha_limite - timedelta(days=30)
            ),
            fecha_limite=fecha_limite,
            fecha_devolucion=fecha_devolucion
        )

    # -------------------------------------
    # 1. Calculo de fechas
    # -------------------------------------

    def test_calcula_un_mes_calendario(self):
        casos = [
            (
                date(2026, 9, 15),
                date(2026, 10, 15)
            ),
            (
                date(2026, 1, 31),
                date(2026, 2, 28)
            ),
            (
                date(2028, 1, 31),
                date(2028, 2, 29)
            ),
            (
                date(2026, 12, 31),
                date(2027, 1, 31)
            ),
        ]

        for limite, esperado in casos:
            with self.subTest(fecha_limite=limite):
                self.assertEqual(
                    self.service.calcular_inicio_bloqueo(
                        limite
                    ),
                    esperado
                )

    def test_bloqueo_dura_treinta_dias(self):
        inicio = date(2026, 10, 15)

        fin = self.service.calcular_fin_bloqueo(
            inicio
        )

        self.assertEqual(
            fin,
            date(2026, 11, 13)
        )

        self.assertEqual(
            (fin - inicio).days + 1,
            30
        )

    # -------------------------------------
    # 2. Deteccion de prestamos vencidos
    # -------------------------------------

    def test_no_bloquea_prestamo_en_plazo(self):
        self.crear_prestamo(
            fecha_limite=date(2026, 10, 20)
        )

        resultado = self.service.aplicar_bloqueos(
            self.hoy
        )

        self.assertEqual(
            resultado['bloqueos_creados'],
            0
        )
        self.assertFalse(
            Sancion.objects.exists()
        )

    def test_no_bloquea_antes_del_umbral(self):
        self.crear_prestamo(
            fecha_limite=date(2026, 9, 16)
        )

        resultado = self.service.aplicar_bloqueos(
            self.hoy
        )

        self.assertEqual(
            resultado['prestamos_revisados'],
            1
        )
        self.assertEqual(
            resultado['bloqueos_creados'],
            0
        )
        self.assertFalse(
            Sancion.objects.exists()
        )

    def test_bloquea_exactamente_en_el_umbral(self):
        prestamo = self.crear_prestamo(
            fecha_limite=date(2026, 9, 15)
        )

        resultado = self.service.aplicar_bloqueos(
            self.hoy
        )

        self.assertEqual(
            resultado['bloqueos_creados'],
            1
        )

        sancion = Sancion.objects.get(
            prestamo=prestamo
        )

        self.assertEqual(
            sancion.tipo,
            'BLOQUEO'
        )
        self.assertIsNone(
            sancion.monto
        )
        self.assertIsNone(
            sancion.fecha_pago
        )
        self.assertEqual(
            sancion.fecha_inicio_bloqueo,
            date(2026, 10, 15)
        )
        self.assertEqual(
            sancion.fecha_fin_bloqueo,
            date(2026, 11, 13)
        )

        prestamo.refresh_from_db()
        self.assertIsNone(
            prestamo.fecha_devolucion
        )

    def test_no_bloquea_prestamo_devuelto(self):
        self.crear_prestamo(
            fecha_limite=date(2026, 9, 15),
            fecha_devolucion=date(2026, 10, 10)
        )

        resultado = self.service.aplicar_bloqueos(
            self.hoy
        )

        self.assertEqual(
            resultado['bloqueos_creados'],
            0
        )
        self.assertFalse(
            Sancion.objects.exists()
        )

    # -------------------------------------
    # 3. Idempotencia e historial
    # -------------------------------------

    def test_ejecutar_dos_veces_no_duplica(self):
        prestamo = self.crear_prestamo(
            fecha_limite=date(2026, 9, 15)
        )

        primera = self.service.aplicar_bloqueos(
            self.hoy
        )

        segunda = self.service.aplicar_bloqueos(
            self.hoy
        )

        self.assertEqual(
            primera['bloqueos_creados'],
            1
        )
        self.assertEqual(
            segunda['bloqueos_creados'],
            0
        )
        self.assertEqual(
            Sancion.objects.filter(
                prestamo=prestamo,
                tipo='BLOQUEO'
            ).count(),
            1
        )

    def test_repetir_dias_despues_no_extiende(self):
        prestamo = self.crear_prestamo(
            fecha_limite=date(2026, 9, 15)
        )

        self.service.aplicar_bloqueos(
            date(2026, 10, 15)
        )

        sancion = Sancion.objects.get(
            prestamo=prestamo,
            tipo='BLOQUEO'
        )

        id_original = sancion.sancion_id
        inicio_original = sancion.fecha_inicio_bloqueo
        fin_original = sancion.fecha_fin_bloqueo

        resultado = self.service.aplicar_bloqueos(
            date(2026, 10, 20)
        )

        sancion.refresh_from_db()

        self.assertEqual(
            resultado['bloqueos_creados'],
            0
        )
        self.assertEqual(
            sancion.sancion_id,
            id_original
        )
        self.assertEqual(
            sancion.fecha_inicio_bloqueo,
            inicio_original
        )
        self.assertEqual(
            sancion.fecha_fin_bloqueo,
            fin_original
        )

    def test_bloqueo_expirado_no_se_reinicia(self):
        prestamo = self.crear_prestamo(
            fecha_limite=date(2026, 9, 15)
        )

        self.service.aplicar_bloqueos(
            date(2026, 10, 15)
        )

        resultado = self.service.aplicar_bloqueos(
            date(2026, 11, 14)
        )

        self.assertEqual(
            resultado['bloqueos_creados'],
            0
        )
        self.assertEqual(
            Sancion.objects.filter(
                prestamo=prestamo,
                tipo='BLOQUEO'
            ).count(),
            1
        )

    def test_procesa_dos_prestamos_del_usuario(self):
        self.crear_prestamo(
            fecha_limite=date(2026, 9, 15)
        )

        self.crear_prestamo(
            fecha_limite=date(2026, 9, 10)
        )

        resultado = self.service.aplicar_bloqueos(
            self.hoy
        )

        self.assertEqual(
            resultado['bloqueos_creados'],
            2
        )
        self.assertEqual(
            Sancion.objects.filter(
                tipo='BLOQUEO'
            ).count(),
            2
        )

    # -------------------------------------
    # 4. Integracion con registro de prestamos
    # -------------------------------------

    def test_bloqueo_impide_nuevo_prestamo(self):
        self.crear_prestamo(
            fecha_limite=date(2026, 9, 15)
        )

        self.service.aplicar_bloqueos(
            self.hoy
        )

        ejemplar_libre = self.crear_ejemplar()
        prestamos_service = PrestamoService()

        with patch(
            'biblioteca.services.prestamos_service.timezone.localdate',
            return_value=self.hoy
        ):
            with self.assertRaises(
                BloqueoVigenteError
            ):
                prestamos_service.registrar_prestamo(
                    usuario_id=self.usuario.usuario_id,
                    ejemplar_id=ejemplar_libre.ejemplar_id
                )

        self.assertFalse(
            Prestamo.objects.filter(
                ejemplar=ejemplar_libre
            ).exists()
        )

    def test_prestamo_permitido_tras_bloqueo(self):
        self.crear_prestamo(
            fecha_limite=date(2026, 9, 15)
        )

        self.service.aplicar_bloqueos(
            self.hoy
        )

        ejemplar_libre = self.crear_ejemplar()
        fecha_posterior = date(2026, 11, 14)

        with patch(
            'biblioteca.services.prestamos_service.timezone.localdate',
            return_value=fecha_posterior
        ):
            prestamo_nuevo = PrestamoService().registrar_prestamo(
                usuario_id=self.usuario.usuario_id,
                ejemplar_id=ejemplar_libre.ejemplar_id
            )

        self.assertEqual(
            prestamo_nuevo.usuario_id,
            self.usuario.usuario_id
        )
        self.assertEqual(
            prestamo_nuevo.fecha_prestamo,
            fecha_posterior
        )

    # -------------------------------------
    # 5. Restricciones de integridad de MySQL
    # -------------------------------------

    def test_bd_rechaza_bloqueo_con_monto(self):
        prestamo = self.crear_prestamo(
            fecha_limite=date(2026, 9, 15)
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Sancion.objects.create(
                    prestamo=prestamo,
                    tipo='BLOQUEO',
                    monto=Decimal('0.00'),
                    fecha_pago=None,
                    fecha_inicio_bloqueo=date(2026, 10, 15),
                    fecha_fin_bloqueo=date(2026, 11, 13)
                )

        self.assertFalse(
            Sancion.objects.exists()
        )

    def test_bd_rechaza_multa_sin_importe(self):
        prestamo = self.crear_prestamo(
            fecha_limite=date(2026, 9, 15)
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Sancion.objects.create(
                    prestamo=prestamo,
                    tipo='ECONOMICA',
                    monto=None,
                    fecha_pago=None
                )

        self.assertFalse(
            Sancion.objects.exists()
        )
    # -------------------------------------
    # 6. Bloqueos al intentar prestar
    # -------------------------------------

    def test_elegibilidad_detecta_bloqueo_no_registrado(self):
        self.crear_prestamo(
            fecha_limite=date(2026, 9, 15)
        )

        ejemplar_libre = self.crear_ejemplar()

        with patch(
            'biblioteca.services.prestamos_service.timezone.localdate',
            return_value=self.hoy
        ):
            resultado = PrestamoService().evaluar_elegibilidad(
                usuario_id=self.usuario.usuario_id,
                ejemplar_id=ejemplar_libre.ejemplar_id
            )

        self.assertFalse(resultado['elegible'])
        self.assertEqual(
            resultado['motivos'][0]['codigo'],
            'BLOQUEO_VIGENTE'
        )

        # GET de elegibilidad no debe escribir sanciones.
        self.assertEqual(Sancion.objects.count(), 0)

    def test_registrar_prestamo_aplica_bloqueo_pendiente(self):
        prestamo_vencido = self.crear_prestamo(
            fecha_limite=date(2026, 9, 15)
        )

        ejemplar_libre = self.crear_ejemplar()

        with patch(
            'biblioteca.services.prestamos_service.timezone.localdate',
            return_value=self.hoy
        ):
            with self.assertRaises(BloqueoVigenteError):
                PrestamoService().registrar_prestamo(
                    usuario_id=self.usuario.usuario_id,
                    ejemplar_id=ejemplar_libre.ejemplar_id
                )

        sancion = Sancion.objects.get(
            prestamo=prestamo_vencido,
            tipo='BLOQUEO'
        )

        self.assertIsNone(sancion.monto)
        self.assertIsNone(sancion.fecha_pago)
        self.assertEqual(
            sancion.fecha_inicio_bloqueo,
            date(2026, 10, 15)
        )
        self.assertEqual(
            sancion.fecha_fin_bloqueo,
            date(2026, 11, 13)
        )

        # El prestamo rechazado no debe existir.
        self.assertFalse(
            Prestamo.objects.filter(
                ejemplar=ejemplar_libre
            ).exists()
        )

    def test_reintentar_prestamo_no_duplica_bloqueo(self):
        prestamo_vencido = self.crear_prestamo(
            fecha_limite=date(2026, 9, 15)
        )

        ejemplar_libre = self.crear_ejemplar()

        with patch(
            'biblioteca.services.prestamos_service.timezone.localdate',
            return_value=self.hoy
        ):
            for _ in range(2):
                with self.assertRaises(BloqueoVigenteError):
                    PrestamoService().registrar_prestamo(
                        usuario_id=self.usuario.usuario_id,
                        ejemplar_id=ejemplar_libre.ejemplar_id
                    )

        self.assertEqual(
            Sancion.objects.filter(
                prestamo=prestamo_vencido,
                tipo='BLOQUEO'
            ).count(),
            1
        )