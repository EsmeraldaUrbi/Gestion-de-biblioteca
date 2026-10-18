
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

from django.db import transaction
from django.test import TestCase

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
    IPrestamoRepository,
)
from biblioteca.services.prestamos_service import (
    EjemplarPrestamoNoEncontradoError,
    PrestamoService,
    UsuarioPrestamoNoEncontradoError,
)


class PrestamosBaseTests(TestCase):
    """
    Pruebas de la capa de datos y del servicio base.

    Estas pruebas no validan todavía el registro
    definitivo ni su comportamiento concurrente.
    """

    def setUp(self):
        self.repository = DjangoPrestamoRepository()
        self.service = PrestamoService(
            repository=self.repository
        )

        self.rol_estudiante = Rol.objects.create(
            nombre='estudiante',
            limite_prestamos_activos=5
        )

        self.rol_docente = Rol.objects.create(
            nombre='docente',
            limite_prestamos_activos=5
        )

        self.rol_bibliotecario = Rol.objects.create(
            nombre='bibliotecario',
            limite_prestamos_activos=0
        )

        self.estudiante = self.crear_usuario(
            nombre='Esmeralda Urbina Cinto',
            email='esme@bibliotech.com',
            rol=self.rol_estudiante
        )

        self.docente = self.crear_usuario(
            nombre='Josué Saúl Torres Zamora',
            email='saul@bibliotech.com',
            rol=self.rol_docente
        )

        self.bibliotecario = self.crear_usuario(
            nombre='Kaltum Abdala Viveros Gómez',
            email='kalt@bibliotech.com',
            rol=self.rol_bibliotecario
        )

        self.libro = Libro.objects.create(
            titulo='Arquitectura de software',
            isbn='9780000000001'
        )

        self.ejemplar_activo = Ejemplar.objects.create(
            libro=self.libro,
            codigo_inventario='BASE-001',
            estado='ACTIVO'
        )

        self.ejemplar_devuelto = Ejemplar.objects.create(
            libro=self.libro,
            codigo_inventario='BASE-002',
            estado='ACTIVO'
        )

        self.ejemplar_libre = Ejemplar.objects.create(
            libro=self.libro,
            codigo_inventario='BASE-003',
            estado='ACTIVO'
        )

        self.prestamo_activo = Prestamo.objects.create(
            usuario=self.estudiante,
            ejemplar=self.ejemplar_activo,
            fecha_prestamo=date(2026, 10, 1),
            fecha_limite=date(2026, 10, 31),
            fecha_devolucion=None
        )

        self.prestamo_devuelto = Prestamo.objects.create(
            usuario=self.estudiante,
            ejemplar=self.ejemplar_devuelto,
            fecha_prestamo=date(2026, 9, 1),
            fecha_limite=date(2026, 10, 1),
            fecha_devolucion=date(2026, 9, 20)
        )

    def crear_usuario(
        self,
        nombre,
        email,
        rol
    ):
        usuario = Usuario(
            nombre=nombre,
            email=email,
            rol=rol
        )

        usuario.set_password('Biblioteca123*')
        usuario.save()

        return usuario

    # ----------------------------------------
    # Búsqueda de lectores y consulta de roles
    # ----------------------------------------

    def test_buscar_lectores_por_nombre(self):
        resultados = self.service.buscar_lectores(
            'Esmeralda'
        )

        self.assertEqual(len(resultados), 1)

        self.assertEqual(
            resultados[0].usuario_id,
            self.estudiante.usuario_id
        )

    def test_buscar_lectores_por_correo(self):
        resultados = self.service.buscar_lectores(
            'saul@bibliotech.com'
        )

        self.assertEqual(len(resultados), 1)

        self.assertEqual(
            resultados[0].usuario_id,
            self.docente.usuario_id
        )

    def test_busqueda_excluye_bibliotecarios(self):
        resultados = self.service.buscar_lectores(
            'kalt'
        )

        self.assertEqual(resultados, [])

    def test_busqueda_vacia_devuelve_lista_vacia(self):
        resultados = self.service.buscar_lectores(
            '   '
        )

        self.assertEqual(resultados, [])

    def test_busqueda_limita_resultados(self):
        resultados = self.service.buscar_lectores(
            '@bibliotech.com',
            limite=1
        )

        self.assertEqual(len(resultados), 1)

    def test_busqueda_valida_parametros(self):
        with self.assertRaises(ValueError):
            self.service.buscar_lectores(
                None
            )

        with self.assertRaises(ValueError):
            self.service.buscar_lectores(
                'Esmeralda',
                limite=0
            )

        with self.assertRaises(ValueError):
            self.service.buscar_lectores(
                'Esmeralda',
                limite=21
            )

    def test_listar_roles_lectores(self):
        roles = self.service.listar_roles_lectores()

        nombres = {
            rol.nombre
            for rol in roles
        }

        self.assertEqual(
            nombres,
            {'estudiante', 'docente'}
        )

    # ----------------------------------------
    # Consulta de usuarios y ejemplares
    # ----------------------------------------

    def test_obtener_usuario_con_rol(self):
        usuario = self.service.obtener_usuario(
            self.estudiante.usuario_id
        )

        self.assertEqual(
            usuario.email,
            'esme@bibliotech.com'
        )

        self.assertEqual(
            usuario.rol.nombre,
            'estudiante'
        )

        self.assertEqual(
            usuario.rol.limite_prestamos_activos,
            5
        )

    def test_obtener_usuario_inexistente(self):
        with self.assertRaises(
            UsuarioPrestamoNoEncontradoError
        ):
            self.service.obtener_usuario(99999)

    def test_obtener_ejemplar_con_libro(self):
        ejemplar = self.service.obtener_ejemplar(
            self.ejemplar_activo.ejemplar_id
        )

        self.assertEqual(
            ejemplar.codigo_inventario,
            'BASE-001'
        )

        self.assertEqual(
            ejemplar.libro.titulo,
            'Arquitectura de software'
        )

    def test_obtener_ejemplar_inexistente(self):
        with self.assertRaises(
            EjemplarPrestamoNoEncontradoError
        ):
            self.service.obtener_ejemplar(99999)

    # ----------------------------------------
    # Préstamos activos e históricos
    # ----------------------------------------

    def test_contar_solo_prestamos_activos(self):
        total = self.service.contar_prestamos_activos(
            self.estudiante.usuario_id
        )

        self.assertEqual(total, 1)

    def test_listar_solo_prestamos_activos(self):
        prestamos = self.service.listar_prestamos_activos(
            self.estudiante.usuario_id
        )

        self.assertEqual(len(prestamos), 1)

        self.assertEqual(
            prestamos[0].prestamo_id,
            self.prestamo_activo.prestamo_id
        )

    def test_ejemplar_con_prestamo_activo(self):
        ocupado = self.service.tiene_prestamo_activo(
            self.ejemplar_activo.ejemplar_id
        )

        self.assertTrue(ocupado)

    def test_ejemplar_devuelto_ya_no_ocupado(self):
        ocupado = self.service.tiene_prestamo_activo(
            self.ejemplar_devuelto.ejemplar_id
        )

        self.assertFalse(ocupado)

    def test_ejemplar_sin_prestamos(self):
        ocupado = self.service.tiene_prestamo_activo(
            self.ejemplar_libre.ejemplar_id
        )

        self.assertFalse(ocupado)

    # ----------------------------------------
    # Sanciones y adeudos
    # ----------------------------------------

    def test_listar_sanciones_de_un_usuario(self):
        sancion = Sancion.objects.create(
            prestamo=self.prestamo_activo,
            tipo='ECONOMICA',
            monto=Decimal('25.00')
        )

        sanciones = self.service.listar_sanciones(
            self.estudiante.usuario_id
        )

        self.assertEqual(len(sanciones), 1)

        self.assertEqual(
            sanciones[0].sancion_id,
            sancion.sancion_id
        )

        sanciones_docente = self.service.listar_sanciones(
            self.docente.usuario_id
        )

        self.assertEqual(sanciones_docente, [])

    def test_detectar_adeudo_pendiente(self):
        Sancion.objects.create(
            prestamo=self.prestamo_activo,
            tipo='ECONOMICA',
            monto=Decimal('25.00'),
            fecha_pago=None
        )

        self.assertTrue(
            self.service.tiene_adeudos_pendientes(
                self.estudiante.usuario_id
            )
        )

        self.assertFalse(
            self.service.tiene_adeudos_pendientes(
                self.docente.usuario_id
            )
        )

    def test_multa_pagada_no_es_adeudo(self):
        Sancion.objects.create(
            prestamo=self.prestamo_activo,
            tipo='ECONOMICA',
            monto=Decimal('25.00'),
            fecha_pago=date(2026, 10, 10)
        )

        self.assertFalse(
            self.service.tiene_adeudos_pendientes(
                self.estudiante.usuario_id
            )
        )

    def test_sancion_sin_monto_no_es_adeudo(self):
        Sancion.objects.create(
            prestamo=self.prestamo_activo,
            tipo='BLOQUEO',
            monto=None,
            fecha_pago=None,
            fecha_inicio_bloqueo=date(2026, 10, 10),
            fecha_fin_bloqueo=date(2026, 11, 8)
        )

        self.assertFalse(
            self.service.tiene_adeudos_pendientes(
                self.estudiante.usuario_id
            )
        )

    # ----------------------------------------
    # Bloqueos registrados
    # ----------------------------------------

    def test_detectar_bloqueo_vigente(self):
        Sancion.objects.create(
            prestamo=self.prestamo_activo,
            tipo='BLOQUEO',
            monto=None,
            fecha_inicio_bloqueo=date(2026, 10, 10),
            fecha_fin_bloqueo=date(2026, 10, 20)
        )

        self.assertTrue(
            self.service.tiene_bloqueo_vigente(
                self.estudiante.usuario_id,
                date(2026, 10, 14)
            )
        )

        self.assertFalse(
            self.service.tiene_bloqueo_vigente(
                self.docente.usuario_id,
                date(2026, 10, 14)
            )
        )

    def test_limites_del_bloqueo_inclusivos(self):
        Sancion.objects.create(
            prestamo=self.prestamo_activo,
            tipo='BLOQUEO',
            monto=None,
            fecha_inicio_bloqueo=date(2026, 10, 10),
            fecha_fin_bloqueo=date(2026, 10, 20)
        )

        self.assertTrue(
            self.service.tiene_bloqueo_vigente(
                self.estudiante.usuario_id,
                date(2026, 10, 10)
            )
        )

        self.assertTrue(
            self.service.tiene_bloqueo_vigente(
                self.estudiante.usuario_id,
                date(2026, 10, 20)
            )
        )

    def test_bloqueo_vencido_no_es_vigente(self):
        Sancion.objects.create(
            prestamo=self.prestamo_activo,
            tipo='BLOQUEO',
            monto=None,
            fecha_inicio_bloqueo=date(2026, 9, 1),
            fecha_fin_bloqueo=date(2026, 9, 30)
        )

        self.assertFalse(
            self.service.tiene_bloqueo_vigente(
                self.estudiante.usuario_id,
                date(2026, 10, 14)
            )
        )

    # ----------------------------------------
    # Persistencia del repositorio
    # ----------------------------------------

    def test_repositorio_crea_prestamo(self):
        prestamo = self.repository.crear_prestamo(
            usuario_id=self.docente.usuario_id,
            ejemplar_id=self.ejemplar_libre.ejemplar_id,
            fecha_prestamo=date(2026, 10, 14),
            fecha_limite=date(2026, 11, 13)
        )

        self.assertIsNotNone(prestamo.prestamo_id)

        almacenado = Prestamo.objects.get(
            prestamo_id=prestamo.prestamo_id
        )

        self.assertEqual(
            almacenado.usuario_id,
            self.docente.usuario_id
        )

        self.assertEqual(
            almacenado.ejemplar_id,
            self.ejemplar_libre.ejemplar_id
        )

        self.assertEqual(
            almacenado.fecha_limite,
            date(2026, 11, 13)
        )

        self.assertIsNone(
            almacenado.fecha_devolucion
        )

    # ----------------------------------------
    # Preparación de bloqueos transaccionales
    # ----------------------------------------

    def test_consultas_admiten_bloqueo_transaccional(self):
        with transaction.atomic():
            usuario = self.repository.obtener_usuario(
                self.estudiante.usuario_id,
                con_bloqueo=True
            )

            ejemplar = self.repository.obtener_ejemplar(
                self.ejemplar_libre.ejemplar_id,
                con_bloqueo=True
            )

            self.assertEqual(
                usuario.usuario_id,
                self.estudiante.usuario_id
            )

            self.assertEqual(
                ejemplar.ejemplar_id,
                self.ejemplar_libre.ejemplar_id
            )

    # ----------------------------------------
    # Inyección de dependencias
    # ----------------------------------------

    def test_servicio_admite_repositorio_inyectado(self):
        repository_mock = MagicMock(
            spec=IPrestamoRepository
        )

        repository_mock.buscar_lectores.return_value = [
            self.estudiante
        ]

        service = PrestamoService(
            repository=repository_mock
        )

        resultados = service.buscar_lectores(
            ' Esmeralda ',
            limite=3
        )

        self.assertEqual(
            resultados,
            [self.estudiante]
        )

        repository_mock.buscar_lectores.assert_called_once_with(
            termino='Esmeralda',
            limite=3
        )
