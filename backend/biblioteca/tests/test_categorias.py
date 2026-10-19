import threading
from unittest.mock import MagicMock

from django.db import IntegrityError, connection
from django.test import TestCase, TransactionTestCase

from biblioteca.models import Categoria, CategoriaLibro, Libro
from biblioteca.repositories.categoria_repository import DjangoCategoriaRepository
from biblioteca.services.categoria_service import (
    CategoriaDatosInvalidosError,
    CategoriaDuplicadaError,
    CategoriaNoEncontradaError,
    CategoriaOperacionNoPermitidaError,
    CategoriaService,
)


class CategoriaServiceAndRepositoryTests(TestCase):
    """
    Pruebas unitarias y de integración para el repositorio y servicio de categorías.
    Verifica validaciones, unicidad, consultas, conteos y bloqueo de eliminaciones.
    """

    def setUp(self):
        self.repository = DjangoCategoriaRepository()
        self.service = CategoriaService(categoria_repository=self.repository)

    # -------------------------------------------------------------------------
    # 1. Registro y validaciones
    # -------------------------------------------------------------------------

    def test_registrar_categoria_exitoso(self):
        cat = self.service.registrar_categoria({'nombre_categoria': 'Ciencia Ficción'})

        self.assertIsNotNone(cat.categoria_id)
        self.assertEqual(cat.nombre_categoria, 'Ciencia Ficción')
        self.assertEqual(cat.cantidad_libros, 0)

    def test_registrar_categoria_con_alias_nombre(self):
        cat = self.service.registrar_categoria({'nombre': 'Filosofía'})

        self.assertIsNotNone(cat.categoria_id)
        self.assertEqual(cat.nombre_categoria, 'Filosofía')

    def test_registrar_categoria_normaliza_espacios(self):
        cat = self.service.registrar_categoria({
            'nombre_categoria': '   Historia Universal   ',
        })

        self.assertEqual(cat.nombre_categoria, 'Historia Universal')

    def test_registrar_categoria_nombre_vacio_falla(self):
        nombres_invalidos = ['', '    ', None, 9876]
        for nombre in nombres_invalidos:
            with self.subTest(nombre=nombre):
                with self.assertRaises(CategoriaDatosInvalidosError):
                    self.service.registrar_categoria({'nombre_categoria': nombre})

    def test_registrar_categoria_longitud_excedida_falla(self):
        nombre_largo = 'C' * 51
        with self.assertRaises(CategoriaDatosInvalidosError) as ctx:
            self.service.registrar_categoria({'nombre_categoria': nombre_largo})
        self.assertIn('50 caracteres', str(ctx.exception))

    # -------------------------------------------------------------------------
    # 2. Detección de duplicados
    # -------------------------------------------------------------------------

    def test_registrar_categoria_duplicada_exacta_falla(self):
        self.service.registrar_categoria({'nombre_categoria': 'Matemáticas'})

        with self.assertRaises(CategoriaDuplicadaError) as ctx:
            self.service.registrar_categoria({'nombre_categoria': 'Matemáticas'})
        self.assertIn('ya se encuentra registrada', str(ctx.exception))

    def test_registrar_categoria_duplicada_case_insensitive_falla(self):
        self.service.registrar_categoria({'nombre_categoria': 'Literatura'})

        variantes = ['literatura', 'LITERATURA', '  LiTeRaTuRa  ']
        for var in variantes:
            with self.subTest(variante=var):
                with self.assertRaises(CategoriaDuplicadaError):
                    self.service.registrar_categoria({'nombre_categoria': var})

    # -------------------------------------------------------------------------
    # 3. Modificaciones
    # -------------------------------------------------------------------------

    def test_modificar_categoria_exitoso(self):
        cat = self.service.registrar_categoria({'nombre_categoria': 'Bio'})

        modificada = self.service.modificar_categoria(cat.categoria_id, {
            'nombre_categoria': 'Biología',
        })

        self.assertEqual(modificada.nombre_categoria, 'Biología')

    def test_modificar_categoria_conserva_su_propio_nombre_sin_falla(self):
        cat = self.service.registrar_categoria({'nombre_categoria': 'Química'})

        # Modificar con el mismo nombre (mismo ID) no debe considerarse duplicado
        modificada = self.service.modificar_categoria(cat.categoria_id, {
            'nombre_categoria': 'Química',
        })
        self.assertEqual(modificada.nombre_categoria, 'Química')

    def test_modificar_categoria_hacia_nombre_existente_en_otra_falla(self):
        c1 = self.service.registrar_categoria({'nombre_categoria': 'Arte'})
        c2 = self.service.registrar_categoria({'nombre_categoria': 'Música'})

        with self.assertRaises(CategoriaDuplicadaError):
            self.service.modificar_categoria(c2.categoria_id, {
                'nombre_categoria': 'arte',
            })

    def test_modificar_categoria_con_nombre_vacio_falla(self):
        cat = self.service.registrar_categoria({'nombre_categoria': 'Economía'})

        with self.assertRaises(CategoriaDatosInvalidosError):
            self.service.modificar_categoria(cat.categoria_id, {
                'nombre_categoria': '   ',
            })

    def test_modificar_categoria_inexistente_falla(self):
        with self.assertRaises(CategoriaNoEncontradaError):
            self.service.modificar_categoria(99999, {'nombre_categoria': 'Fantasma'})

    # -------------------------------------------------------------------------
    # 4. Consultas y listados
    # -------------------------------------------------------------------------

    def test_obtener_categoria_existente(self):
        creada = self.service.registrar_categoria({'nombre_categoria': 'Psicología'})
        recuperada = self.service.obtener_categoria(creada.categoria_id)

        self.assertEqual(recuperada.categoria_id, creada.categoria_id)
        self.assertEqual(recuperada.nombre_categoria, 'Psicología')
        self.assertEqual(recuperada.cantidad_libros, 0)

    def test_obtener_categoria_inexistente_falla(self):
        with self.assertRaises(CategoriaNoEncontradaError):
            self.service.obtener_categoria(99999)

    def test_listar_categorias_sin_filtros(self):
        self.service.registrar_categoria({'nombre_categoria': 'Derecho'})
        self.service.registrar_categoria({'nombre_categoria': 'Medicina'})

        todas = self.service.listar_categorias()
        self.assertGreaterEqual(todas.count(), 2)

    def test_listar_categorias_con_filtro_nombre(self):
        c1 = self.service.registrar_categoria({'nombre_categoria': 'Ingeniería de Software'})
        self.service.registrar_categoria({'nombre_categoria': 'Sociología'})

        resultado = self.service.listar_categorias({'nombre': 'software'})
        self.assertEqual(resultado.count(), 1)
        self.assertEqual(resultado.first().categoria_id, c1.categoria_id)

    # -------------------------------------------------------------------------
    # 5. Relaciones con libros y conteos
    # -------------------------------------------------------------------------

    def test_conteo_libros_asociados_cero(self):
        cat = self.service.registrar_categoria({'nombre_categoria': 'Arqueología'})

        self.assertFalse(self.service.tiene_libros_asociados(cat.categoria_id))
        self.assertEqual(self.service.contar_libros_asociados(cat.categoria_id), 0)

    def test_conteo_libros_asociados_con_libros(self):
        cat = self.service.registrar_categoria({'nombre_categoria': 'Tecnología'})

        l1 = Libro.objects.create(titulo='Libro Tech 1', isbn='9789999999801')
        l2 = Libro.objects.create(titulo='Libro Tech 2', isbn='9789999999802')

        CategoriaLibro.objects.create(categoria=cat, libro=l1)
        CategoriaLibro.objects.create(categoria=cat, libro=l2)

        self.assertTrue(self.service.tiene_libros_asociados(cat.categoria_id))
        self.assertEqual(self.service.contar_libros_asociados(cat.categoria_id), 2)

        recuperada = self.service.obtener_categoria(cat.categoria_id)
        self.assertEqual(recuperada.cantidad_libros, 2)

    # -------------------------------------------------------------------------
    # 6. Bloqueo de eliminaciones físicas
    # -------------------------------------------------------------------------

    def test_bloqueo_eliminacion_fisica_sin_libros(self):
        cat = self.service.registrar_categoria({'nombre_categoria': 'Astronomía'})

        with self.assertRaises(CategoriaOperacionNoPermitidaError):
            self.service.eliminar_categoria(cat.categoria_id)

        self.assertTrue(Categoria.objects.filter(categoria_id=cat.categoria_id).exists())

    def test_bloqueo_eliminacion_fisica_con_libros(self):
        cat = self.service.registrar_categoria({'nombre_categoria': 'Física'})
        libro = Libro.objects.create(titulo='Libro Física I', isbn='9789999999803')
        CategoriaLibro.objects.create(categoria=cat, libro=libro)

        with self.assertRaises(CategoriaOperacionNoPermitidaError) as ctx:
            self.service.eliminar_categoria(cat.categoria_id)

        self.assertIn('RN-20', str(ctx.exception))
        self.assertTrue(Categoria.objects.filter(categoria_id=cat.categoria_id).exists())

    # -------------------------------------------------------------------------
    # 7. Unicidad en BD, acentos y manejo de errores de integridad
    # -------------------------------------------------------------------------

    def test_proteccion_unicidad_directa_orm(self):
        Categoria.objects.create(nombre_categoria='Poesía')
        with self.assertRaises(IntegrityError):
            Categoria.objects.create(nombre_categoria='poesía')

    def test_unicidad_acentos_bajo_colacion_actual(self):
        self.service.registrar_categoria({'nombre_categoria': 'Música'})
        with self.assertRaises(CategoriaDuplicadaError):
            self.service.registrar_categoria({'nombre_categoria': 'Musica'})

    def test_manejo_integrity_error_no_relacionado_re_lanza(self):
        mock_repo = MagicMock()
        mock_repo.obtener_por_nombre.return_value = None
        mock_repo.crear.side_effect = IntegrityError('Error ajeno a unicidad de categoría')
        service = CategoriaService(categoria_repository=mock_repo)

        with self.assertRaises(IntegrityError) as ctx:
            service.registrar_categoria({'nombre_categoria': 'Informatica'})
        self.assertIn('Error ajeno a unicidad de categoría', str(ctx.exception))

    def test_modificacion_conserva_relaciones_libros(self):
        cat = self.service.registrar_categoria({'nombre_categoria': 'Antropología'})
        libro = Libro.objects.create(titulo='Libro Antropo', isbn='9789999999804')
        CategoriaLibro.objects.create(categoria=cat, libro=libro)

        modificada = self.service.modificar_categoria(
            cat.categoria_id,
            {'nombre_categoria': 'Antropología Cultural'}
        )
        self.assertEqual(modificada.nombre_categoria, 'Antropología Cultural')
        self.assertEqual(self.service.contar_libros_asociados(cat.categoria_id), 1)
        self.assertTrue(
            CategoriaLibro.objects.filter(
                categoria_id=cat.categoria_id,
                libro_id=libro.libro_id
            ).exists()
        )


class CategoriaConcurrencyTests(TransactionTestCase):
    """
    Pruebas de concurrencia real entre hilos para verificar la exclusión mutua
    y la protección física del UNIQUE constraint en MySQL sin falsear resultados.
    """

    def test_concurrencia_registro_simultaneo_misma_categoria(self):
        nombre_objetivo = 'Bioética Concurrente'
        exitos = []
        duplicados = []
        errores_inesperados = []

        def registrar_en_hilo():
            connection.close()  # Abre nueva conexión independiente de base de datos para este hilo
            try:
                service = CategoriaService()
                cat = service.registrar_categoria({'nombre_categoria': nombre_objetivo})
                exitos.append(cat.categoria_id)
            except CategoriaDuplicadaError:
                duplicados.append(True)
            except Exception as exc:
                errores_inesperados.append(exc)
            finally:
                connection.close()

        hilos = [threading.Thread(target=registrar_en_hilo) for _ in range(5)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()

        self.assertEqual(len(errores_inesperados), 0, f"Errores inesperados: {errores_inesperados}")
        self.assertEqual(len(exitos), 1, "Exactamente una solicitud concurrente debió tener éxito")
        self.assertEqual(len(duplicados), 4, "Las demás solicitudes debieron ser rechazadas como duplicadas")
        self.assertEqual(
            Categoria.objects.filter(nombre_categoria=nombre_objetivo).count(),
            1,
            "Solo debe existir una única fila en la base de datos MySQL"
        )
