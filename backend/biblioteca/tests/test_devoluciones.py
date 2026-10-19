from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from biblioteca.models import (
    Ejemplar,
    EstadoEjemplar,
    Libro,
    Prestamo,
    Rol,
    Sancion,
    Usuario,
)
from biblioteca.repositories.devoluciones_repository import (
    DjangoDevolucionesRepository,
)
from biblioteca.services.devoluciones_service import (
    DevolucionService,
)


class DevolucionesTests(TestCase):
    def setUp(self):
        self.hoy = timezone.localdate()

        rol_lector = Rol.objects.create(
            nombre='estudiante',
            limite_prestamos_activos=5
        )
        rol_bibliotecario = Rol.objects.create(
            nombre='bibliotecario',
            limite_prestamos_activos=0
        )

        self.lector = Usuario.objects.create(
            rol=rol_lector,
            nombre='Lector de prueba',
            email='lector.devoluciones@example.com',
            contrasena_hash='no-utilizada'
        )
        self.bibliotecario = Usuario.objects.create(
            rol=rol_bibliotecario,
            nombre='Bibliotecario de prueba',
            email='bibliotecario.devoluciones@example.com',
            contrasena_hash='no-utilizada'
        )

        libro = Libro.objects.create(
            titulo='Libro de prueba',
            isbn='9780000000001'
        )
        self.ejemplar = Ejemplar.objects.create(
            libro=libro,
            codigo_inventario='DEV-001',
            estado=EstadoEjemplar.ACTIVO
        )

        self.client = APIClient()
        self.client.force_authenticate(
            user=self.bibliotecario
        )

    def crear_prestamo(self, dias_retraso=0):
        return Prestamo.objects.create(
            usuario=self.lector,
            ejemplar=self.ejemplar,
            fecha_prestamo=self.hoy - timedelta(days=60),
            fecha_limite=(
                self.hoy - timedelta(days=dias_retraso)
            ),
            fecha_devolucion=None
        )

    def devolver(self, prestamo):
        return self.client.post(
            reverse(
                'prestamos-devolucion',
                kwargs={'prestamo_id': prestamo.prestamo_id}
            ),
            {},
            format='json'
        )

    def test_devolucion_en_fecha_limite_no_genera_multa(self):
        prestamo = self.crear_prestamo()

        respuesta = self.devolver(prestamo)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['dias_retraso'], 0)
        self.assertEqual(respuesta.data['monto_multa'], '0.00')
        self.assertFalse(respuesta.data['sancion_generada'])
        self.assertFalse(
            Sancion.objects.filter(prestamo=prestamo).exists()
        )

        prestamo.refresh_from_db()
        self.assertEqual(
            prestamo.fecha_devolucion,
            self.hoy
        )

    def test_cinco_dias_generan_multa_de_25_pesos(self):
        prestamo = self.crear_prestamo(dias_retraso=5)

        respuesta = self.devolver(prestamo)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['dias_retraso'], 5)
        self.assertEqual(respuesta.data['monto_multa'], '25.00')
        self.assertTrue(respuesta.data['sancion_generada'])

        sancion = Sancion.objects.get(prestamo=prestamo)
        self.assertEqual(sancion.tipo, 'ECONOMICA')
        self.assertEqual(sancion.monto, Decimal('25.00'))
        self.assertIsNone(sancion.fecha_pago)
        self.assertIsNone(sancion.fecha_inicio_bloqueo)
        self.assertIsNone(sancion.fecha_fin_bloqueo)

    def test_repetir_devolucion_no_cambia_fecha_ni_duplica_multa(self):
        prestamo = self.crear_prestamo(dias_retraso=5)

        primera = self.devolver(prestamo)
        self.assertEqual(primera.status_code, 200)

        prestamo.refresh_from_db()
        fecha_original = prestamo.fecha_devolucion

        segunda = self.devolver(prestamo)

        self.assertEqual(segunda.status_code, 400)
        self.assertEqual(
            segunda.data['codigo'],
            'PRESTAMO_YA_DEVUELTO'
        )

        prestamo.refresh_from_db()
        self.assertEqual(
            prestamo.fecha_devolucion,
            fecha_original
        )
        self.assertEqual(
            Sancion.objects.filter(
                prestamo=prestamo,
                tipo='ECONOMICA'
            ).count(),
            1
        )

    def test_prestamo_inexistente_devuelve_404(self):
        respuesta = self.client.post(
            reverse(
                'prestamos-devolucion',
                kwargs={'prestamo_id': 999999}
            ),
            {},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 404)

    def test_estudiante_no_puede_registrar_devolucion(self):
        prestamo = self.crear_prestamo()
        self.client.force_authenticate(user=self.lector)

        respuesta = self.devolver(prestamo)

        self.assertEqual(respuesta.status_code, 403)
        prestamo.refresh_from_db()
        self.assertIsNone(prestamo.fecha_devolucion)

    def test_no_permite_enviar_fecha_desde_la_api(self):
        prestamo = self.crear_prestamo()

        respuesta = self.client.post(
            reverse(
                'prestamos-devolucion',
                kwargs={'prestamo_id': prestamo.prestamo_id}
            ),
            {'fecha_devolucion': self.hoy.isoformat()},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)
        prestamo.refresh_from_db()
        self.assertIsNone(prestamo.fecha_devolucion)

    def test_fallo_al_crear_multa_revierte_devolucion(self):
        prestamo = self.crear_prestamo(dias_retraso=5)
        repository = DjangoDevolucionesRepository()
        service = DevolucionService(repository=repository)

        with patch.object(
            repository,
            'crear_multa',
            side_effect=RuntimeError('Fallo simulado')
        ):
            with self.assertRaises(RuntimeError):
                service.registrar_devolucion(
                    prestamo.prestamo_id
                )

        prestamo.refresh_from_db()
        self.assertIsNone(prestamo.fecha_devolucion)
        self.assertFalse(
            Sancion.objects.filter(prestamo=prestamo).exists()
        )

    def test_bloqueo_vigente_permite_devolver_y_se_conserva(self):
        prestamo = self.crear_prestamo(dias_retraso=35)

        inicio = self.hoy - timedelta(days=2)
        fin = self.hoy + timedelta(days=27)

        bloqueo = Sancion.objects.create(
            prestamo=prestamo,
            tipo='BLOQUEO',
            monto=None,
            fecha_pago=None,
            fecha_inicio_bloqueo=inicio,
            fecha_fin_bloqueo=fin
        )

        respuesta = self.devolver(prestamo)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['monto_multa'], '175.00')

        prestamo.refresh_from_db()
        self.assertEqual(prestamo.fecha_devolucion, self.hoy)

        bloqueo.refresh_from_db()
        self.assertEqual(bloqueo.fecha_inicio_bloqueo, inicio)
        self.assertEqual(bloqueo.fecha_fin_bloqueo, fin)
        self.assertIsNone(bloqueo.monto)
        self.assertIsNone(bloqueo.fecha_pago)

        self.assertEqual(
            Sancion.objects.filter(
                prestamo=prestamo,
                tipo='BLOQUEO'
            ).count(),
            1
        )
        self.assertEqual(
            Sancion.objects.filter(
                prestamo=prestamo,
                tipo='ECONOMICA'
            ).count(),
            1
        )

    def test_devolucion_registra_bloqueo_pendiente_del_worker(self):
        prestamo = self.crear_prestamo(dias_retraso=35)

        respuesta = self.devolver(prestamo)

        self.assertEqual(respuesta.status_code, 200)

        bloqueo = Sancion.objects.get(
            prestamo=prestamo,
            tipo='BLOQUEO'
        )

        self.assertLessEqual(
            bloqueo.fecha_inicio_bloqueo,
            self.hoy
        )
        self.assertEqual(
            bloqueo.fecha_fin_bloqueo,
            bloqueo.fecha_inicio_bloqueo + timedelta(days=29)
        )
        self.assertIsNone(bloqueo.monto)
        self.assertIsNone(bloqueo.fecha_pago)

        self.assertEqual(
            Sancion.objects.filter(
                prestamo=prestamo,
                tipo='ECONOMICA'
            ).count(),
            1
        )

        segunda = self.devolver(prestamo)

        self.assertEqual(segunda.status_code, 400)
        self.assertEqual(
            Sancion.objects.filter(prestamo=prestamo).count(),
            2
        )

    def test_busqueda_encuentra_prestamo_activo_y_estima_multa(self):
        prestamo = self.crear_prestamo(dias_retraso=5)

        respuesta = self.client.get(
            reverse('devoluciones-prestamos-activos'),
            {'q': self.ejemplar.codigo_inventario}
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['count'], 1)

        resultado = respuesta.data['results'][0]

        self.assertEqual(
            resultado['prestamo']['prestamo_id'],
            prestamo.prestamo_id
        )
        self.assertEqual(resultado['dias_retraso'], 5)
        self.assertEqual(resultado['monto_multa'], '25.00')

        # Consultar no debe registrar la devolución ni sanciones.
        prestamo.refresh_from_db()
        self.assertIsNone(prestamo.fecha_devolucion)
        self.assertFalse(
            Sancion.objects.filter(prestamo=prestamo).exists()
        )

    def test_busqueda_excluye_prestamos_devueltos(self):
        prestamo = self.crear_prestamo()
        prestamo.fecha_devolucion = self.hoy
        prestamo.save(update_fields=['fecha_devolucion'])

        respuesta = self.client.get(
            reverse('devoluciones-prestamos-activos'),
            {'q': self.ejemplar.codigo_inventario}
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['count'], 0)
        self.assertEqual(respuesta.data['results'], [])

    def test_busqueda_por_nombre_correo_e_id(self):
        prestamo = self.crear_prestamo()

        for termino in [
            self.lector.nombre,
            self.lector.email,
            str(prestamo.prestamo_id),
        ]:
            with self.subTest(termino=termino):
                respuesta = self.client.get(
                    reverse('devoluciones-prestamos-activos'),
                    {'q': termino}
                )

                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.data['count'], 1)
                self.assertEqual(
                    respuesta.data['results'][0]
                    ['prestamo']['prestamo_id'],
                    prestamo.prestamo_id
                )

    def test_busqueda_rechaza_termino_vacio(self):
        respuesta = self.client.get(
            reverse('devoluciones-prestamos-activos'),
            {'q': '   '}
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_estudiante_no_puede_buscar_devoluciones(self):
        self.client.force_authenticate(user=self.lector)

        respuesta = self.client.get(
            reverse('devoluciones-prestamos-activos'),
            {'q': 'DEV'}
        )

        self.assertEqual(respuesta.status_code, 403)