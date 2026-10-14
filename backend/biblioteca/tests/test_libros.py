from datetime import date
from unittest.mock import MagicMock, patch

from django.db import IntegrityError
from django.test import TestCase

from biblioteca.models import Autor, Categoria, Ejemplar, Libro, LibroAutor, CategoriaLibro
from biblioteca.repositories.libro_repository import ILibroRepository
from biblioteca.services.libro_service import (
    AutoresNoEncontradosError,
    CategoriasNoEncontradasError,
    IsbnDuplicadoError,
    LibroConEjemplaresError,
    LibroNoEncontradoError,
    LibroService,
)


class LibroServiceTests(TestCase):

    def setUp(self):
        self.service = LibroService()

        self.autor1 = Autor.objects.create(
            nombre='Gabriel García Márquez',
            nacionalidad='Colombiana',
            fecha_nacimiento=date(1927, 3, 6)
        )
        self.autor2 = Autor.objects.create(
            nombre='Mario Vargas Llosa',
            nacionalidad='Peruana',
            fecha_nacimiento=date(1936, 3, 28)
        )
        self.categoria1 = Categoria.objects.create(
            nombre_categoria='Realismo Mágico'
        )
        self.categoria2 = Categoria.objects.create(
            nombre_categoria='Novela Latinoamericana'
        )

    def test_registrar_libro_exitoso_con_asociaciones(self):
        datos = {
            'titulo': 'Cien Años de Soledad',
            'isbn': '9780307474728',
            'fecha_publicacion': date(1967, 5, 30),
            'autor_ids': [self.autor1.autor_id, self.autor2.autor_id],
            'categoria_ids': [self.categoria1.categoria_id]
        }

        libro = self.service.registrar_libro(datos)

        self.assertIsNotNone(libro.libro_id)
        self.assertEqual(libro.titulo, 'Cien Años de Soledad')
        self.assertEqual(libro.isbn, '9780307474728')
        self.assertEqual(libro.autores.count(), 2)
        self.assertEqual(libro.categorias.count(), 1)
        self.assertTrue(libro.autores.filter(autor_id=self.autor1.autor_id).exists())
        self.assertTrue(libro.categorias.filter(categoria_id=self.categoria1.categoria_id).exists())

    def test_registrar_libro_sin_autores_ni_categorias(self):
        datos = {
            'titulo': 'Libro Sin Autores',
            'isbn': '9780000000001',
        }

        libro = self.service.registrar_libro(datos)

        self.assertIsNotNone(libro.libro_id)
        self.assertEqual(libro.autores.count(), 0)
        self.assertEqual(libro.categorias.count(), 0)

    def test_registrar_libro_isbn_duplicado_falla(self):
        datos1 = {
            'titulo': 'Edición Original',
            'isbn': '9781111111111'
        }
        self.service.registrar_libro(datos1)

        datos2 = {
            'titulo': 'Edición Pirata',
            'isbn': '9781111111111'
        }
        with self.assertRaises(IsbnDuplicadoError):
            self.service.registrar_libro(datos2)

    def test_registrar_libro_deduplica_asociaciones_rn19(self):
        datos = {
            'titulo': 'Libro con IDs duplicados en request',
            'isbn': '9782222222222',
            'autor_ids': [self.autor1.autor_id, self.autor1.autor_id],
            'categoria_ids': [self.categoria1.categoria_id, self.categoria1.categoria_id]
        }

        libro = self.service.registrar_libro(datos)

        self.assertEqual(libro.autores.count(), 1)
        self.assertEqual(libro.categorias.count(), 1)
        self.assertEqual(
            LibroAutor.objects.filter(libro=libro, autor=self.autor1).count(),
            1
        )
        self.assertEqual(
            CategoriaLibro.objects.filter(libro=libro, categoria=self.categoria1).count(),
            1
        )

    def test_registrar_libro_autor_inexistente_falla(self):
        datos = {
            'titulo': 'Libro Fantasma',
            'isbn': '9783333333333',
            'autor_ids': [9999]
        }

        with self.assertRaises(AutoresNoEncontradosError) as ctx:
            self.service.registrar_libro(datos)

        self.assertIn(9999, ctx.exception.ids_inexistentes)
        self.assertFalse(Libro.objects.filter(isbn='9783333333333').exists())

    def test_registrar_libro_categoria_inexistente_falla(self):
        datos = {
            'titulo': 'Libro Fantasma 2',
            'isbn': '9784444444444',
            'categoria_ids': [8888]
        }

        with self.assertRaises(CategoriasNoEncontradasError) as ctx:
            self.service.registrar_libro(datos)

        self.assertIn(8888, ctx.exception.ids_inexistentes)
        self.assertFalse(Libro.objects.filter(isbn='9784444444444').exists())

    def test_obtener_libro_existente_e_inexistente(self):
        libro_creado = self.service.registrar_libro({
            'titulo': 'La Ciudad y los Perros',
            'isbn': '9785555555555',
            'autor_ids': [self.autor2.autor_id]
        })

        libro_recuperado = self.service.obtener_libro(libro_creado.libro_id)
        self.assertEqual(libro_recuperado.titulo, 'La Ciudad y los Perros')
        self.assertEqual(libro_recuperado.autores.first().nombre, 'Mario Vargas Llosa')

        with self.assertRaises(LibroNoEncontradoError):
            self.service.obtener_libro(99999)

    def test_modificar_libro_metadatos_basicos(self):
        libro = self.service.registrar_libro({
            'titulo': 'Título Inicial',
            'isbn': '9786666666666'
        })

        modificado = self.service.modificar_libro(libro.libro_id, {
            'titulo': 'Título Actualizado',
            'fecha_publicacion': date(2020, 1, 1)
        })

        self.assertEqual(modificado.titulo, 'Título Actualizado')
        self.assertEqual(modificado.fecha_publicacion, date(2020, 1, 1))
        self.assertEqual(modificado.isbn, '9786666666666')

    def test_modificar_libro_con_mismo_isbn_no_falla(self):
        libro = self.service.registrar_libro({
            'titulo': 'Libro Con Mismo ISBN',
            'isbn': '9787777777777'
        })

        modificado = self.service.modificar_libro(libro.libro_id, {
            'isbn': '9787777777777',
            'titulo': 'Mismo ISBN Título Nuevo'
        })

        self.assertEqual(modificado.titulo, 'Mismo ISBN Título Nuevo')

    def test_modificar_libro_con_isbn_ocupado_por_otro_falla(self):
        self.service.registrar_libro({
            'titulo': 'Primer Libro',
            'isbn': '9788888888881'
        })
        libro2 = self.service.registrar_libro({
            'titulo': 'Segundo Libro',
            'isbn': '9788888888882'
        })

        with self.assertRaises(IsbnDuplicadoError):
            self.service.modificar_libro(libro2.libro_id, {
                'isbn': '9788888888881'
            })

    def test_modificar_libro_reemplaza_asociaciones(self):
        libro = self.service.registrar_libro({
            'titulo': 'Libro Inicial',
            'isbn': '9789999999999',
            'autor_ids': [self.autor1.autor_id],
            'categoria_ids': [self.categoria1.categoria_id]
        })

        modificado = self.service.modificar_libro(libro.libro_id, {
            'autor_ids': [self.autor2.autor_id],
            'categoria_ids': [self.categoria2.categoria_id]
        })

        self.assertEqual(modificado.autores.count(), 1)
        self.assertEqual(modificado.autores.first().autor_id, self.autor2.autor_id)
        self.assertEqual(modificado.categorias.count(), 1)
        self.assertEqual(modificado.categorias.first().categoria_id, self.categoria2.categoria_id)

    def test_eliminar_libro_sin_ejemplares_exitoso(self):
        libro = self.service.registrar_libro({
            'titulo': 'Libro Para Eliminar',
            'isbn': '9781212121212'
        })
        libro_id = libro.libro_id

        self.service.eliminar_libro(libro_id)

        self.assertFalse(Libro.objects.filter(libro_id=libro_id).exists())

    def test_eliminar_libro_con_ejemplares_rechazado_rn20(self):
        libro = self.service.registrar_libro({
            'titulo': 'Libro Con Copias',
            'isbn': '9781313131313'
        })
        Ejemplar.objects.create(
            libro=libro,
            codigo_inventario='INV-LIBRO-01',
            estado='ACTIVO'
        )

        with self.assertRaises(LibroConEjemplaresError):
            self.service.eliminar_libro(libro.libro_id)

        self.assertTrue(Libro.objects.filter(libro_id=libro.libro_id).exists())

    def test_listar_libros_con_filtros(self):
        l1 = self.service.registrar_libro({
            'titulo': 'Algoritmos en Python',
            'isbn': '9781414141414',
            'autor_ids': [self.autor1.autor_id],
            'categoria_ids': [self.categoria1.categoria_id]
        })
        l2 = self.service.registrar_libro({
            'titulo': 'Estructuras de Datos',
            'isbn': '9781515151515',
            'autor_ids': [self.autor2.autor_id],
            'categoria_ids': [self.categoria2.categoria_id]
        })

        todos = self.service.listar_libros()
        self.assertGreaterEqual(todos.count(), 2)

        filtrados_titulo = self.service.listar_libros({'titulo': 'Python'})
        self.assertEqual(filtrados_titulo.count(), 1)
        self.assertEqual(filtrados_titulo.first().libro_id, l1.libro_id)

        filtrados_isbn = self.service.listar_libros({'isbn': '9781515151515'})
        self.assertEqual(filtrados_isbn.count(), 1)
        self.assertEqual(filtrados_isbn.first().libro_id, l2.libro_id)

        filtrados_autor = self.service.listar_libros({'autor_id': self.autor1.autor_id})
        self.assertEqual(filtrados_autor.count(), 1)
        self.assertEqual(filtrados_autor.first().libro_id, l1.libro_id)

        filtrados_categoria = self.service.listar_libros({'categoria_id': self.categoria2.categoria_id})
        self.assertEqual(filtrados_categoria.count(), 1)
        self.assertEqual(filtrados_categoria.first().libro_id, l2.libro_id)

    def test_modificar_libro_parcial_conserva_relaciones_existentes(self):
        """
        Una actualización parcial que omite autor_ids y categoria_ids
        no debe alterar las asociaciones preexistentes (punto 3 del contrato).
        """
        libro = self.service.registrar_libro({
            'titulo': 'Libro con Relaciones',
            'isbn': '9781616161616',
            'autor_ids': [self.autor1.autor_id],
            'categoria_ids': [self.categoria1.categoria_id],
        })

        # Actualización que SOLO cambia el título; no pasa autor_ids ni categoria_ids
        modificado = self.service.modificar_libro(libro.libro_id, {
            'titulo': 'Título Modificado Parcialmente',
        })

        # Las relaciones deben permanecer intactas
        self.assertEqual(modificado.titulo, 'Título Modificado Parcialmente')
        self.assertEqual(modificado.autores.count(), 1)
        self.assertEqual(modificado.autores.first().autor_id, self.autor1.autor_id)
        self.assertEqual(modificado.categorias.count(), 1)
        self.assertEqual(modificado.categorias.first().categoria_id, self.categoria1.categoria_id)

    def test_integrity_error_no_isbn_no_se_enmascara(self):
        """
        Si el repositorio lanza una IntegrityError cuyo mensaje no contiene 'isbn'
        (e.g., violación de FK desconocida), el servicio debe relanzarla tal cual
        en lugar de convertirla en IsbnDuplicadoError (punto 5 del contrato).
        """
        # Repositorio falso que devuelve valores válidos para validaciones
        # pero lanza IntegrityError ajena al ISBN al intentar crear.
        repo_mock = MagicMock(spec=ILibroRepository)
        repo_mock.obtener_por_isbn.return_value = None
        repo_mock.verificar_autores_existentes.return_value = set()
        repo_mock.verificar_categorias_existentes.return_value = set()
        repo_mock.crear.side_effect = IntegrityError(
            1452,
            "Cannot add or update a child row: a foreign key constraint fails"
        )

        service = LibroService(libro_repository=repo_mock)

        with self.assertRaises(IntegrityError):
            service.registrar_libro({
                'titulo': 'Libro FK Error',
                'isbn': '9781717171717',
            })
