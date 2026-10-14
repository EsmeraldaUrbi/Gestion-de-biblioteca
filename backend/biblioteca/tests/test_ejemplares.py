from datetime import date
from unittest.mock import MagicMock, patch

from django.db import IntegrityError
from django.test import TestCase

from biblioteca.models import (
    Ejemplar,
    EstadoEjemplar,
    Libro,
    Prestamo,
    Rol,
    Usuario,
)
from biblioteca.repositories.ejemplar_repository import (
    DjangoEjemplarRepository,
    IEjemplarRepository,
)
from biblioteca.services.ejemplar_service import (
    CodigoInventarioDuplicadoError,
    CodigoInventarioInvalidoError,
    EjemplarConHistorialPrestamosError,
    EjemplarConPrestamoActivoError,
    EjemplarNoEncontradoError,
    EjemplarService,
    EstadoEjemplarInvalidoError,
)
from biblioteca.services.libro_service import LibroNoEncontradoError


class EjemplarServiceTests(TestCase):

    def setUp(self):
        self.service = EjemplarService()

        self.libro = Libro.objects.create(
            titulo='Don Quijote de la Mancha',
            isbn='9788424116286',
            fecha_publicacion=date(1605, 1, 16)
        )
        self.libro2 = Libro.objects.create(
            titulo='Cien Años de Soledad',
            isbn='9780307474728',
            fecha_publicacion=date(1967, 5, 30)
        )

        self.rol = Rol.objects.create(
            nombre='estudiante',
            limite_prestamos_activos=5
        )
        self.usuario = Usuario.objects.create(
            nombre='Carlos Lector',
            email='carlos@biblioteca.test',
            rol=self.rol
        )

    def crear_prestamo(self, ejemplar, devuelto=False):
        return Prestamo.objects.create(
            usuario=self.usuario,
            ejemplar=ejemplar,
            fecha_prestamo=date(2025, 1, 1),
            fecha_limite=date(2025, 1, 15),
            fecha_devolucion=date(2025, 1, 10) if devuelto else None
        )

    # --- 1. Registro y Estados Predeterminados ---

    def test_registrar_ejemplar_exitoso_estado_por_defecto_activo(self):
        datos = {
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'QUIJ-001'
        }
        ejemplar = self.service.registrar_ejemplar(datos)

        self.assertIsNotNone(ejemplar.ejemplar_id)
        self.assertEqual(ejemplar.libro_id, self.libro.libro_id)
        self.assertEqual(ejemplar.codigo_inventario, 'QUIJ-001')
        self.assertEqual(ejemplar.estado, EstadoEjemplar.ACTIVO)

    def test_registrar_ejemplar_con_estado_explicito(self):
        datos = {
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'QUIJ-002',
            'estado': 'MANTENIMIENTO'
        }
        ejemplar = self.service.registrar_ejemplar(datos)
        self.assertEqual(ejemplar.estado, EstadoEjemplar.MANTENIMIENTO)

    # --- 2. Unicidad del Código de Inventario (RN-02) ---

    def test_registrar_ejemplar_codigo_duplicado_falla_rn02(self):
        self.service.registrar_ejemplar({
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'DUP-001'
        })

        with self.assertRaises(CodigoInventarioDuplicadoError):
            self.service.registrar_ejemplar({
                'libro_id': self.libro.libro_id,
                'codigo_inventario': 'DUP-001'
            })

    def test_registrar_ejemplar_codigo_duplicado_captura_integrity_error(self):
        repo_mock = MagicMock(spec=IEjemplarRepository)
        repo_mock.existe_libro.return_value = True
        repo_mock.obtener_por_codigo.return_value = None
        repo_mock.crear.side_effect = IntegrityError("Duplicate entry 'DUP-002' for key 'codigo_inventario'")

        servicio = EjemplarService(ejemplar_repository=repo_mock)

        with self.assertRaises(CodigoInventarioDuplicadoError):
            servicio.registrar_ejemplar({
                'libro_id': 1,
                'codigo_inventario': 'DUP-002'
            })

    # --- 3. Validación de Códigos y Estados (RN-03) ---

    def test_registrar_ejemplar_codigo_invalido_o_vacio(self):
        casos = ['', '   ', None, 'A' * 16]
        for codigo in casos:
            with self.subTest(codigo=codigo):
                with self.assertRaises(CodigoInventarioInvalidoError):
                    self.service.registrar_ejemplar({
                        'libro_id': self.libro.libro_id,
                        'codigo_inventario': codigo
                    })

    def test_registrar_ejemplar_estado_invalido_falla_rn03(self):
        with self.assertRaises(EstadoEjemplarInvalidoError):
            self.service.registrar_ejemplar({
                'libro_id': self.libro.libro_id,
                'codigo_inventario': 'INV-001',
                'estado': 'EXTRAVIADO'
            })

    def test_registrar_ejemplar_libro_inexistente_falla(self):
        with self.assertRaises(LibroNoEncontradoError):
            self.service.registrar_ejemplar({
                'libro_id': 99999,
                'codigo_inventario': 'LIB-999'
            })

    # --- 4. Consultas por ID, Libro y Filtros ---

    def test_obtener_ejemplar_existente(self):
        ej = self.service.registrar_ejemplar({
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'OBT-001'
        })
        recuperado = self.service.obtener_ejemplar(ej.ejemplar_id)
        self.assertEqual(recuperado.codigo_inventario, 'OBT-001')
        self.assertEqual(recuperado.libro.titulo, self.libro.titulo)

    def test_obtener_ejemplar_inexistente_falla(self):
        with self.assertRaises(EjemplarNoEncontradoError):
            self.service.obtener_ejemplar(99999)

    def test_listar_ejemplares_por_libro(self):
        self.service.registrar_ejemplar({'libro_id': self.libro.libro_id, 'codigo_inventario': 'L1-01'})
        self.service.registrar_ejemplar({'libro_id': self.libro.libro_id, 'codigo_inventario': 'L1-02'})
        self.service.registrar_ejemplar({'libro_id': self.libro2.libro_id, 'codigo_inventario': 'L2-01'})

        ejemplares_l1 = self.service.listar_ejemplares_por_libro(self.libro.libro_id)
        self.assertEqual(ejemplares_l1.count(), 2)
        codigos = [e.codigo_inventario for e in ejemplares_l1]
        self.assertIn('L1-01', codigos)
        self.assertIn('L1-02', codigos)
        self.assertNotIn('L2-01', codigos)

    def test_listar_ejemplares_por_libro_inexistente_falla(self):
        with self.assertRaises(LibroNoEncontradoError):
            self.service.listar_ejemplares_por_libro(99999)

    def test_listar_ejemplares_con_filtros(self):
        self.service.registrar_ejemplar({'libro_id': self.libro.libro_id, 'codigo_inventario': 'F-ACT', 'estado': 'ACTIVO'})
        self.service.registrar_ejemplar({'libro_id': self.libro.libro_id, 'codigo_inventario': 'F-MNT', 'estado': 'MANTENIMIENTO'})

        activos = self.service.listar_ejemplares({'estado': EstadoEjemplar.ACTIVO})
        self.assertTrue(activos.filter(codigo_inventario='F-ACT').exists())
        self.assertFalse(activos.filter(codigo_inventario='F-MNT').exists())

    # --- 5. Cambios de Estado y Préstamos Activos (RN-04) ---

    def test_cambiar_estado_a_mantenimiento_sin_prestamo_activo(self):
        ej = self.service.registrar_ejemplar({
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'MNT-001'
        })
        actualizado = self.service.cambiar_estado(ej.ejemplar_id, EstadoEjemplar.MANTENIMIENTO)
        self.assertEqual(actualizado.estado, EstadoEjemplar.MANTENIMIENTO)

    def test_cambiar_estado_a_mantenimiento_con_prestamo_activo_falla_rn04(self):
        ej = self.service.registrar_ejemplar({
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'PREST-001'
        })
        self.crear_prestamo(ej, devuelto=False)

        with self.assertRaises(EjemplarConPrestamoActivoError):
            self.service.cambiar_estado(ej.ejemplar_id, EstadoEjemplar.MANTENIMIENTO)

        ej.refresh_from_db()
        self.assertEqual(ej.estado, EstadoEjemplar.ACTIVO)

    def test_cambiar_estado_a_baja_con_prestamo_activo_falla_rn04(self):
        ej = self.service.registrar_ejemplar({
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'PREST-002'
        })
        self.crear_prestamo(ej, devuelto=False)

        with self.assertRaises(EjemplarConPrestamoActivoError):
            self.service.dar_de_baja(ej.ejemplar_id)

        ej.refresh_from_db()
        self.assertEqual(ej.estado, EstadoEjemplar.ACTIVO)

    def test_dar_de_baja_con_prestamos_historicos_devueltos_exitoso(self):
        ej = self.service.registrar_ejemplar({
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'HIST-001'
        })
        self.crear_prestamo(ej, devuelto=True)

        actualizado = self.service.dar_de_baja(ej.ejemplar_id)
        self.assertEqual(actualizado.estado, EstadoEjemplar.BAJA)

    def test_cambiar_estado_con_estado_invalido_falla(self):
        ej = self.service.registrar_ejemplar({
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'EST-001'
        })
        with self.assertRaises(EstadoEjemplarInvalidoError):
            self.service.cambiar_estado(ej.ejemplar_id, 'DESCONOCIDO')

    def test_cambiar_estado_ejemplar_inexistente_falla(self):
        with self.assertRaises(EjemplarNoEncontradoError):
            self.service.cambiar_estado(99999, EstadoEjemplar.ACTIVO)

    # --- 6. Conservación del Historial y Eliminación Física (RN-20) ---

    def test_eliminar_ejemplar_con_historial_prestamos_falla_rn20(self):
        ej = self.service.registrar_ejemplar({
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'HIST-002'
        })
        self.crear_prestamo(ej, devuelto=True)

        with self.assertRaises(EjemplarConHistorialPrestamosError):
            self.service.eliminar_ejemplar(ej.ejemplar_id)

        # El ejemplar y el préstamo deben seguir existiendo en la base de datos
        self.assertTrue(Ejemplar.objects.filter(ejemplar_id=ej.ejemplar_id).exists())
        self.assertTrue(Prestamo.objects.filter(ejemplar_id=ej.ejemplar_id).exists())

    def test_eliminar_ejemplar_sin_prestamos_exitoso(self):
        ej = self.service.registrar_ejemplar({
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'DEL-001'
        })
        self.service.eliminar_ejemplar(ej.ejemplar_id)
        self.assertFalse(Ejemplar.objects.filter(ejemplar_id=ej.ejemplar_id).exists())

    @patch.object(DjangoEjemplarRepository, 'obtener_por_id', wraps=DjangoEjemplarRepository().obtener_por_id)
    def test_cambio_de_estado_solicita_bloqueo_select_for_update(self, mock_obtener):
        ej = self.service.registrar_ejemplar({
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'LOCK-001'
        })
        self.service.cambiar_estado(ej.ejemplar_id, EstadoEjemplar.MANTENIMIENTO)
        mock_obtener.assert_called_with(ej.ejemplar_id, con_bloqueo=True)

    # --- 8. Verificaciones Adicionales de Integridad y Robustez ---

    def test_registrar_ejemplar_integrity_error_ajeno_no_se_enmascara(self):
        repo_mock = MagicMock(spec=IEjemplarRepository)
        repo_mock.existe_libro.return_value = True
        repo_mock.obtener_por_codigo.return_value = None
        repo_mock.crear.side_effect = IntegrityError(
            "Cannot add or update a child row: a foreign key constraint fails"
        )

        servicio = EjemplarService(ejemplar_repository=repo_mock)

        with self.assertRaises(IntegrityError):
            servicio.registrar_ejemplar({
                'libro_id': 1,
                'codigo_inventario': 'FK-FAIL-001'
            })

    def test_reactivacion_desde_baja_permitida_segun_reglas_actuales(self):
        # La documentación no declara irreversible el estado BAJA
        ej = self.service.registrar_ejemplar({
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'REAC-001',
            'estado': EstadoEjemplar.BAJA
        })
        actualizado = self.service.cambiar_estado(ej.ejemplar_id, EstadoEjemplar.ACTIVO)
        self.assertEqual(actualizado.estado, EstadoEjemplar.ACTIVO)

    def test_cambio_fallido_de_estado_conserva_estado_anterior_en_bd(self):
        ej = self.service.registrar_ejemplar({
            'libro_id': self.libro.libro_id,
            'codigo_inventario': 'ROLL-001',
            'estado': EstadoEjemplar.ACTIVO
        })
        self.crear_prestamo(ej, devuelto=False)

        # Intento hacia MANTENIMIENTO
        with self.assertRaises(EjemplarConPrestamoActivoError):
            self.service.cambiar_estado(ej.ejemplar_id, EstadoEjemplar.MANTENIMIENTO)

        ej.refresh_from_db()
        self.assertEqual(ej.estado, EstadoEjemplar.ACTIVO)

        # Intento hacia BAJA
        with self.assertRaises(EjemplarConPrestamoActivoError):
            self.service.dar_de_baja(ej.ejemplar_id)

        ej.refresh_from_db()
        self.assertEqual(ej.estado, EstadoEjemplar.ACTIVO)
