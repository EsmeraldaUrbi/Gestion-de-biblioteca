from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Barrier
from unittest.mock import patch

from django.db import connections
from django.test import (
    TestCase,
    TransactionTestCase,
    skipUnlessDBFeature,
)

from biblioteca.models import (
    Ejemplar,
    Libro,
    Prestamo,
    Rol,
    Sancion,
    Usuario,
)
from biblioteca.repositories.prestamos_repository import (
    DjangoPrestamoRepository,
)
from biblioteca.services.prestamos_service import (
    AdeudoPendienteError,
    BloqueoVigenteError,
    EjemplarNoDisponibleError,
    EjemplarOcupadoError,
    EjemplarPrestamoNoEncontradoError,
    IdentificadorPrestamoInvalidoError,
    LimitePrestamosAlcanzadoError,
    PrestamoError,
    PrestamoService,
    RolNoHabilitadoError,
    UsuarioPrestamoNoEncontradoError,
)


class DatosPrestamosMixin:
    """
    Prepara usuarios, roles, libros y ejemplares
    reutilizables en las pruebas del módulo.
    """

    def setUp(self):
        super().setUp()

        self.estudiante_rol = Rol.objects.create(
            nombre='estudiante',
            limite_prestamos_activos=5
        )

        self.docente_rol = Rol.objects.create(
            nombre='docente',
            limite_prestamos_activos=5
        )

        self.bibliotecario_rol = Rol.objects.create(
            nombre='bibliotecario',
            limite_prestamos_activos=0
        )

        self.estudiante = Usuario.objects.create(
            rol=self.estudiante_rol,
            nombre='Estudiante',
            email='estudiante@test.local'
        )

        self.docente = Usuario.objects.create(
            rol=self.docente_rol,
            nombre='Docente',
            email='docente@test.local'
        )

        self.bibliotecario = Usuario.objects.create(
            rol=self.bibliotecario_rol,
            nombre='Bibliotecario',
            email='bibliotecario@test.local'
        )

        self.libro = Libro.objects.create(
            titulo='Pruebas de préstamos',
            isbn='9780000000002'
        )

        self.ejemplar = self.crear_ejemplar(
            'REG-001'
        )

        self.repository = DjangoPrestamoRepository()

        self.service = PrestamoService(
            repository=self.repository
        )

    def crear_ejemplar(
        self,
        codigo,
        estado='ACTIVO'
    ):
        return Ejemplar.objects.create(
            libro=self.libro,
            codigo_inventario=codigo,
            estado=estado
        )

    def crear_prestamo_previo(
        self,
        usuario,
        ejemplar,
        devuelto=False
    ):
        return Prestamo.objects.create(
            usuario=usuario,
            ejemplar=ejemplar,
            fecha_prestamo=date(2026, 10, 1),
            fecha_limite=date(2026, 10, 31),
            fecha_devolucion=(
                date(2026, 10, 10)
                if devuelto
                else None
            )
        )


class PrestamoReglasTests(
    DatosPrestamosMixin,
    TestCase
):
    """
    Verifica las reglas de negocio del registro
    de préstamos mediante Django ORM.
    """

    # -----------------------------------------
    # Registro correcto y fechas
    # -----------------------------------------

    def test_registra_prestamo_estudiante_y_calcula_treinta_dias(
        self
    ):
        with patch(
            'biblioteca.services.prestamos_service.timezone.localdate',
            return_value=date(2026, 10, 14)
        ):
            prestamo = self.service.registrar_prestamo(
                self.estudiante.usuario_id,
                self.ejemplar.ejemplar_id
            )

        self.assertEqual(
            prestamo.fecha_prestamo,
            date(2026, 10, 14)
        )

        self.assertEqual(
            prestamo.fecha_limite,
            date(2026, 11, 13)
        )

        self.assertIsNone(
            prestamo.fecha_devolucion
        )

        self.assertEqual(
            prestamo.usuario_id,
            self.estudiante.usuario_id
        )

        self.assertEqual(
            prestamo.ejemplar_id,
            self.ejemplar.ejemplar_id
        )

        self.assertEqual(
            Prestamo.objects.count(),
            1
        )

    def test_registra_prestamo_docente(self):
        prestamo = self.service.registrar_prestamo(
            self.docente.usuario_id,
            self.ejemplar.ejemplar_id
        )

        self.assertEqual(
            prestamo.usuario_id,
            self.docente.usuario_id
        )

    # -----------------------------------------
    # Validación de roles
    # -----------------------------------------

    def test_rechaza_prestamo_a_bibliotecario(self):
        with self.assertRaises(
            RolNoHabilitadoError
        ):
            self.service.registrar_prestamo(
                self.bibliotecario.usuario_id,
                self.ejemplar.ejemplar_id
            )

        self.assertFalse(
            Prestamo.objects.exists()
        )

    def test_rechaza_usuario_con_rol_desconocido(self):
        rol = Rol.objects.create(
            nombre='administrador',
            limite_prestamos_activos=5
        )

        usuario = Usuario.objects.create(
            rol=rol,
            nombre='Administrador',
            email='admin@test.local'
        )

        with self.assertRaises(
            RolNoHabilitadoError
        ):
            self.service.registrar_prestamo(
                usuario.usuario_id,
                self.ejemplar.ejemplar_id
            )

    # -----------------------------------------
    # Límite de préstamos activos
    # -----------------------------------------

    def test_permite_quinto_prestamo_y_rechaza_sexto(self):
        for indice in range(4):
            ejemplar = self.crear_ejemplar(
                f'LIM-{indice:03d}'
            )

            self.crear_prestamo_previo(
                self.estudiante,
                ejemplar
            )

        quinto = self.service.registrar_prestamo(
            self.estudiante.usuario_id,
            self.ejemplar.ejemplar_id
        )

        self.assertIsNotNone(
            quinto.prestamo_id
        )

        sexto_ejemplar = self.crear_ejemplar(
            'LIM-006'
        )

        with self.assertRaises(
            LimitePrestamosAlcanzadoError
        ):
            self.service.registrar_prestamo(
                self.estudiante.usuario_id,
                sexto_ejemplar.ejemplar_id
            )

        total = self.service.contar_prestamos_activos(
            self.estudiante.usuario_id
        )

        self.assertEqual(total, 5)

    def test_usa_limite_configurado_en_rol_y_no_cifra_fija(
        self
    ):
        self.estudiante_rol.limite_prestamos_activos = 1

        self.estudiante_rol.save(
            update_fields=[
                'limite_prestamos_activos'
            ]
        )

        ejemplar_previo = self.crear_ejemplar(
            'LIM-UNICO'
        )

        self.crear_prestamo_previo(
            self.estudiante,
            ejemplar_previo
        )

        with self.assertRaises(
            LimitePrestamosAlcanzadoError
        ):
            self.service.registrar_prestamo(
                self.estudiante.usuario_id,
                self.ejemplar.ejemplar_id
            )

    def test_rechaza_limite_no_positivo(self):
        self.estudiante_rol.limite_prestamos_activos = 0

        self.estudiante_rol.save(
            update_fields=[
                'limite_prestamos_activos'
            ]
        )

        with self.assertRaises(
            LimitePrestamosAlcanzadoError
        ):
            self.service.registrar_prestamo(
                self.estudiante.usuario_id,
                self.ejemplar.ejemplar_id
            )

    def test_no_cuenta_prestamos_ya_devueltos(self):
        for indice in range(5):
            ejemplar = self.crear_ejemplar(
                f'DEV-{indice:03d}'
            )

            self.crear_prestamo_previo(
                self.estudiante,
                ejemplar,
                devuelto=True
            )

        self.service.registrar_prestamo(
            self.estudiante.usuario_id,
            self.ejemplar.ejemplar_id
        )

        total = self.service.contar_prestamos_activos(
            self.estudiante.usuario_id
        )

        self.assertEqual(total, 1)

    # -----------------------------------------
    # Disponibilidad del ejemplar
    # -----------------------------------------

    def test_rechaza_ejemplar_prestado_a_otro_usuario(
        self
    ):
        self.crear_prestamo_previo(
            self.docente,
            self.ejemplar
        )

        with self.assertRaises(
            EjemplarOcupadoError
        ):
            self.service.registrar_prestamo(
                self.estudiante.usuario_id,
                self.ejemplar.ejemplar_id
            )

        self.assertEqual(
            Prestamo.objects.count(),
            1
        )

    def test_rechaza_ejemplar_en_mantenimiento_o_baja(
        self
    ):
        casos = [
            ('NO-01', 'MANTENIMIENTO'),
            ('NO-02', 'BAJA'),
        ]

        for codigo, estado in casos:
            with self.subTest(estado=estado):
                ejemplar = self.crear_ejemplar(
                    codigo,
                    estado
                )

                with self.assertRaises(
                    EjemplarNoDisponibleError
                ):
                    self.service.registrar_prestamo(
                        self.estudiante.usuario_id,
                        ejemplar.ejemplar_id
                    )

        self.assertFalse(
            Prestamo.objects.exists()
        )

    def test_acepta_ejemplar_con_prestamo_historico_devuelto(
        self
    ):
        self.crear_prestamo_previo(
            self.docente,
            self.ejemplar,
            devuelto=True
        )

        prestamo = self.service.registrar_prestamo(
            self.estudiante.usuario_id,
            self.ejemplar.ejemplar_id
        )

        self.assertIsNone(
            prestamo.fecha_devolucion
        )

        self.assertEqual(
            Prestamo.objects.count(),
            2
        )

    # -----------------------------------------
    # Adeudos económicos
    # -----------------------------------------

    def test_rechaza_multa_pendiente(self):
        ejemplar_previo = self.crear_ejemplar(
            'MUL-001'
        )

        prestamo_previo = self.crear_prestamo_previo(
            self.estudiante,
            ejemplar_previo,
            devuelto=True
        )

        Sancion.objects.create(
            prestamo=prestamo_previo,
            tipo='ECONOMICA',
            monto=Decimal('25.00'),
            fecha_pago=None
        )

        with self.assertRaises(
            AdeudoPendienteError
        ):
            self.service.registrar_prestamo(
                self.estudiante.usuario_id,
                self.ejemplar.ejemplar_id
            )

        self.assertEqual(
            Prestamo.objects.count(),
            1
        )

    def test_multa_pagada_no_impide_prestamo(self):
        ejemplar_previo = self.crear_ejemplar(
            'MUL-002'
        )

        prestamo_previo = self.crear_prestamo_previo(
            self.estudiante,
            ejemplar_previo,
            devuelto=True
        )

        Sancion.objects.create(
            prestamo=prestamo_previo,
            tipo='ECONOMICA',
            monto=Decimal('25.00'),
            fecha_pago=date(2026, 10, 12)
        )

        prestamo = self.service.registrar_prestamo(
            self.estudiante.usuario_id,
            self.ejemplar.ejemplar_id
        )

        self.assertIsNotNone(
            prestamo.prestamo_id
        )

    # -----------------------------------------
    # Bloqueos por sanciones
    # -----------------------------------------

    def test_rechaza_bloqueo_vigente(self):
        ejemplar_previo = self.crear_ejemplar(
            'BLO-001'
        )

        prestamo_previo = self.crear_prestamo_previo(
            self.estudiante,
            ejemplar_previo,
            devuelto=True
        )

        Sancion.objects.create(
            prestamo=prestamo_previo,
            tipo='BLOQUEO',
            monto=None,
            fecha_inicio_bloqueo=date(2020, 1, 1),
            fecha_fin_bloqueo=date(2099, 1, 1)
        )

        with self.assertRaises(
            BloqueoVigenteError
        ):
            self.service.registrar_prestamo(
                self.estudiante.usuario_id,
                self.ejemplar.ejemplar_id
            )

    def test_bloqueo_terminado_no_impide_prestamo(self):
        ejemplar_previo = self.crear_ejemplar(
            'BLO-002'
        )

        prestamo_previo = self.crear_prestamo_previo(
            self.estudiante,
            ejemplar_previo,
            devuelto=True
        )

        Sancion.objects.create(
            prestamo=prestamo_previo,
            tipo='BLOQUEO',
            monto=None,
            fecha_inicio_bloqueo=date(2020, 1, 1),
            fecha_fin_bloqueo=date(2020, 1, 15)
        )

        prestamo = self.service.registrar_prestamo(
            self.estudiante.usuario_id,
            self.ejemplar.ejemplar_id
        )

        self.assertIsNotNone(
            prestamo.prestamo_id
        )

    # -----------------------------------------
    # Registros inexistentes y parámetros
    # -----------------------------------------

    def test_rechaza_usuario_o_ejemplar_inexistente(
        self
    ):
        with self.assertRaises(
            UsuarioPrestamoNoEncontradoError
        ):
            self.service.registrar_prestamo(
                999999,
                self.ejemplar.ejemplar_id
            )

        with self.assertRaises(
            EjemplarPrestamoNoEncontradoError
        ):
            self.service.registrar_prestamo(
                self.estudiante.usuario_id,
                999999
            )

        self.assertFalse(
            Prestamo.objects.exists()
        )

    def test_rechaza_identificadores_invalidos(self):
        valores_invalidos = [
            0,
            -1,
            True,
            '1',
            None,
        ]

        for valor in valores_invalidos:
            with self.subTest(valor=valor):
                with self.assertRaises(
                    IdentificadorPrestamoInvalidoError
                ):
                    self.service.registrar_prestamo(
                        valor,
                        self.ejemplar.ejemplar_id
                    )

        self.assertFalse(
            Prestamo.objects.exists()
        )

    # -----------------------------------------
    # Transacciones
    # -----------------------------------------

    def test_transaccion_revierte_si_falla_persistencia(
        self
    ):
        crear_original = self.repository.crear_prestamo

        def crear_y_fallar(**datos):
            crear_original(**datos)

            raise RuntimeError(
                'Fallo simulado después del INSERT'
            )

        with patch.object(
            self.repository,
            'crear_prestamo',
            side_effect=crear_y_fallar
        ):
            with self.assertRaises(RuntimeError):
                self.service.registrar_prestamo(
                    self.estudiante.usuario_id,
                    self.ejemplar.ejemplar_id
                )

        self.assertFalse(
            Prestamo.objects.exists()
        )

    def test_solicita_bloqueos_y_lecturas_actuales(self):
        with (
            patch.object(
                self.repository,
                'obtener_usuario',
                wraps=self.repository.obtener_usuario
            ) as usuario_mock,

            patch.object(
                self.repository,
                'obtener_ejemplar',
                wraps=self.repository.obtener_ejemplar
            ) as ejemplar_mock,

            patch.object(
                self.repository,
                'contar_prestamos_activos',
                wraps=self.repository.contar_prestamos_activos
            ) as conteo_mock,

            patch.object(
                self.repository,
                'tiene_prestamo_activo',
                wraps=self.repository.tiene_prestamo_activo
            ) as ocupado_mock
        ):
            self.service.registrar_prestamo(
                self.estudiante.usuario_id,
                self.ejemplar.ejemplar_id
            )

        usuario_mock.assert_called_once_with(
            self.estudiante.usuario_id,
            con_bloqueo=True
        )

        ejemplar_mock.assert_called_once_with(
            self.ejemplar.ejemplar_id,
            con_bloqueo=True
        )

        conteo_mock.assert_called_once_with(
            self.estudiante.usuario_id,
            con_bloqueo=True
        )

        ocupado_mock.assert_called_once_with(
            self.ejemplar.ejemplar_id,
            con_bloqueo=True
        )


@skipUnlessDBFeature('has_select_for_update')
class PrestamosConcurrenciaTests(
    DatosPrestamosMixin,
    TransactionTestCase
):
    """
    Verifica el registro simultáneo de préstamos.

    Utiliza TransactionTestCase porque las pruebas normales
    de TestCase mantienen una transacción envolvente.

    Cada hilo ejecuta el servicio mediante una conexión
    independiente de Django.
    """

    def ejecutar_en_paralelo(
        self,
        solicitudes
    ):
        inicio = Barrier(
            len(solicitudes) + 1
        )

        def operacion(
            usuario_id,
            ejemplar_id
        ):
            connections.close_all()

            try:
                inicio.wait(timeout=20)

                try:
                    prestamo = (
                        PrestamoService()
                        .registrar_prestamo(
                            usuario_id,
                            ejemplar_id
                        )
                    )

                    return (
                        'creado',
                        prestamo.prestamo_id
                    )

                except PrestamoError as error:
                    return (
                        'rechazado',
                        type(error)
                    )

            finally:
                connections.close_all()

        with ThreadPoolExecutor(
            max_workers=len(solicitudes)
        ) as executor:

            futuros = [
                executor.submit(
                    operacion,
                    usuario_id,
                    ejemplar_id
                )
                for usuario_id, ejemplar_id in solicitudes
            ]

            inicio.wait(timeout=20)

            resultados = [
                futuro.result(timeout=35)
                for futuro in futuros
            ]

        return resultados

    def test_dos_usuarios_no_reciben_el_mismo_ejemplar(
        self
    ):
        solicitudes = [
            (
                self.estudiante.usuario_id,
                self.ejemplar.ejemplar_id
            ),
            (
                self.docente.usuario_id,
                self.ejemplar.ejemplar_id
            ),
        ]

        resultados = self.ejecutar_en_paralelo(
            solicitudes
        )

        creados = sum(
            estado == 'creado'
            for estado, _ in resultados
        )

        rechazados = [
            error
            for estado, error in resultados
            if estado == 'rechazado'
        ]

        self.assertEqual(creados, 1)

        self.assertEqual(
            rechazados,
            [EjemplarOcupadoError]
        )

        total = Prestamo.objects.filter(
            ejemplar=self.ejemplar,
            fecha_devolucion__isnull=True
        ).count()

        self.assertEqual(total, 1)

    def test_dos_solicitudes_no_exceden_limite_del_usuario(
        self
    ):
        for indice in range(4):
            ejemplar = self.crear_ejemplar(
                f'PAR-{indice:03d}'
            )

            self.crear_prestamo_previo(
                self.estudiante,
                ejemplar
            )

        otro_ejemplar = self.crear_ejemplar(
            'PAR-006'
        )

        solicitudes = [
            (
                self.estudiante.usuario_id,
                self.ejemplar.ejemplar_id
            ),
            (
                self.estudiante.usuario_id,
                otro_ejemplar.ejemplar_id
            ),
        ]

        resultados = self.ejecutar_en_paralelo(
            solicitudes
        )

        creados = sum(
            estado == 'creado'
            for estado, _ in resultados
        )

        rechazados = [
            error
            for estado, error in resultados
            if estado == 'rechazado'
        ]

        self.assertEqual(creados, 1)

        self.assertEqual(
            rechazados,
            [LimitePrestamosAlcanzadoError]
        )

        total = Prestamo.objects.filter(
            usuario=self.estudiante,
            fecha_devolucion__isnull=True
        ).count()

        self.assertEqual(total, 5)