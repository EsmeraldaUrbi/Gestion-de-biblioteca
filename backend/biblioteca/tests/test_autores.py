from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from biblioteca.models import Autor, Libro, LibroAutor
from biblioteca.repositories.autor_repository import DjangoAutorRepository
from biblioteca.services.autor_service import (
    AutorDatosInvalidosError,
    AutorNoEncontradoError,
    AutorOperacionNoPermitidaError,
    AutorService,
)


class AutorServiceAndRepositoryTests(TestCase):
    """
    Pruebas unitarias y de integración para el repositorio y servicio de autores.
    Verifica validaciones, consultas, homónimos, conteos y protección de historial.
    """

    def setUp(self):
        self.repository = DjangoAutorRepository()
        self.service = AutorService(autor_repository=self.repository)

    # -------------------------------------------------------------------------
    # 1. Registro y validaciones de campos
    # -------------------------------------------------------------------------

    def test_registrar_autor_datos_completos(self):
        datos = {
            'nombre': 'Gabriel García Márquez',
            'nacionalidad': 'Colombiana',
            'fecha_nacimiento': date(1927, 3, 6),
        }
        autor = self.service.registrar_autor(datos)

        self.assertIsNotNone(autor.autor_id)
        self.assertEqual(autor.nombre, 'Gabriel García Márquez')
        self.assertEqual(autor.nacionalidad, 'Colombiana')
        self.assertEqual(autor.fecha_nacimiento, date(1927, 3, 6))
        self.assertEqual(autor.cantidad_libros, 0)

    def test_registrar_autor_solo_campos_obligatorios(self):
        datos = {
            'nombre': 'Julio Cortázar',
        }
        autor = self.service.registrar_autor(datos)

        self.assertIsNotNone(autor.autor_id)
        self.assertEqual(autor.nombre, 'Julio Cortázar')
        self.assertIsNone(autor.nacionalidad)
        self.assertIsNone(autor.fecha_nacimiento)

    def test_registrar_autor_normaliza_espacios(self):
        datos = {
            'nombre': '   Jorge Luis Borges   ',
            'nacionalidad': '   Argentina   ',
        }
        autor = self.service.registrar_autor(datos)

        self.assertEqual(autor.nombre, 'Jorge Luis Borges')
        self.assertEqual(autor.nacionalidad, 'Argentina')

    def test_registrar_autor_nombre_vacio_o_espacios_falla(self):
        nombres_invalidos = ['', '    ', None, 12345]
        for nombre in nombres_invalidos:
            with self.subTest(nombre=nombre):
                with self.assertRaises(AutorDatosInvalidosError):
                    self.service.registrar_autor({'nombre': nombre})

    def test_registrar_autor_nombre_longitud_excedida_falla(self):
        nombre_largo = 'A' * 101
        with self.assertRaises(AutorDatosInvalidosError) as ctx:
            self.service.registrar_autor({'nombre': nombre_largo})
        self.assertIn('100 caracteres', str(ctx.exception))

    def test_registrar_autor_nacionalidad_longitud_excedida_falla(self):
        nac_larga = 'N' * 51
        with self.assertRaises(AutorDatosInvalidosError) as ctx:
            self.service.registrar_autor({
                'nombre': 'Autor Prueba',
                'nacionalidad': nac_larga,
            })
        self.assertIn('50 caracteres', str(ctx.exception))

    def test_registrar_autor_nacionalidad_vacia_se_guarda_como_none(self):
        autor = self.service.registrar_autor({
            'nombre': 'Autor Sin Nacionalidad',
            'nacionalidad': '   ',
        })
        self.assertIsNone(autor.nacionalidad)

    def test_registrar_autor_fecha_nacimiento_formato_str(self):
        autor = self.service.registrar_autor({
            'nombre': 'Mario Vargas Llosa',
            'fecha_nacimiento': '1936-03-28',
        })
        self.assertEqual(autor.fecha_nacimiento, date(1936, 3, 28))

    def test_registrar_autor_fecha_nacimiento_formato_invalido_falla(self):
        formatos_malos = ['28/03/1936', '1936.03.28', 'fecha-invalida']
        for formato in formatos_malos:
            with self.subTest(formato=formato):
                with self.assertRaises(AutorDatosInvalidosError):
                    self.service.registrar_autor({
                        'nombre': 'Autor Fecha Mala',
                        'fecha_nacimiento': formato,
                    })

    def test_registrar_autor_fecha_nacimiento_futura_falla(self):
        manana = timezone.localdate() + timedelta(days=1)
        with self.assertRaises(AutorDatosInvalidosError) as ctx:
            self.service.registrar_autor({
                'nombre': 'Autor del Futuro',
                'fecha_nacimiento': manana,
            })
        self.assertIn('futura', str(ctx.exception).lower())

    # -------------------------------------------------------------------------
    # 2. Consultas y listados
    # -------------------------------------------------------------------------

    def test_obtener_autor_existente(self):
        creado = self.service.registrar_autor({'nombre': 'Octavio Paz'})
        recuperado = self.service.obtener_autor(creado.autor_id)

        self.assertEqual(recuperado.autor_id, creado.autor_id)
        self.assertEqual(recuperado.nombre, 'Octavio Paz')
        self.assertEqual(recuperado.cantidad_libros, 0)

    def test_obtener_autor_inexistente_falla(self):
        with self.assertRaises(AutorNoEncontradoError):
            self.service.obtener_autor(99999)

    def test_listar_autores_sin_filtros(self):
        self.service.registrar_autor({'nombre': 'Carlos Fuentes'})
        self.service.registrar_autor({'nombre': 'Alfonso Reyes'})

        autores = self.service.listar_autores()
        self.assertGreaterEqual(autores.count(), 2)
        nombres = list(autores.values_list('nombre', flat=True))
        self.assertIn('Alfonso Reyes', nombres)
        self.assertIn('Carlos Fuentes', nombres)

    def test_listar_autores_con_filtro_nombre(self):
        a1 = self.service.registrar_autor({'nombre': 'Isabel Allende'})
        self.service.registrar_autor({'nombre': 'Pablo Neruda'})

        resultado = self.service.listar_autores({'nombre': 'allende'})
        self.assertEqual(resultado.count(), 1)
        self.assertEqual(resultado.first().autor_id, a1.autor_id)

    def test_listar_autores_con_filtro_nacionalidad(self):
        a1 = self.service.registrar_autor({
            'nombre': 'Gabriela Mistral',
            'nacionalidad': 'Chilena',
        })
        self.service.registrar_autor({
            'nombre': 'Juan Rulfo',
            'nacionalidad': 'Mexicana',
        })

        resultado = self.service.listar_autores({'nacionalidad': 'chilena'})
        self.assertEqual(resultado.count(), 1)
        self.assertEqual(resultado.first().autor_id, a1.autor_id)

    # -------------------------------------------------------------------------
    # 3. Modificaciones y conservación de campos omitidos
    # -------------------------------------------------------------------------

    def test_modificar_autor_parcial_nombre(self):
        autor = self.service.registrar_autor({
            'nombre': 'Nombre Inicial',
            'nacionalidad': 'Mexicana',
            'fecha_nacimiento': date(1950, 1, 1),
        })

        actualizado = self.service.modificar_autor(autor.autor_id, {
            'nombre': 'Nombre Corregido',
        })

        self.assertEqual(actualizado.nombre, 'Nombre Corregido')
        # Campos omitidos permanecen intactos
        self.assertEqual(actualizado.nacionalidad, 'Mexicana')
        self.assertEqual(actualizado.fecha_nacimiento, date(1950, 1, 1))

    def test_modificar_autor_parcial_nacionalidad(self):
        autor = self.service.registrar_autor({
            'nombre': 'Laura Esquivel',
            'nacionalidad': 'Mexicana',
        })

        actualizado = self.service.modificar_autor(autor.autor_id, {
            'nacionalidad': 'Mexicana-Española',
        })

        self.assertEqual(actualizado.nacionalidad, 'Mexicana-Española')
        self.assertEqual(actualizado.nombre, 'Laura Esquivel')

    def test_modificar_autor_parcial_fecha_nacimiento(self):
        autor = self.service.registrar_autor({
            'nombre': 'Autor Con Fecha',
        })

        actualizado = self.service.modificar_autor(autor.autor_id, {
            'fecha_nacimiento': '1970-12-15',
        })

        self.assertEqual(actualizado.fecha_nacimiento, date(1970, 12, 15))

    def test_modificar_autor_con_nombre_invalido_falla(self):
        autor = self.service.registrar_autor({'nombre': 'Autor Original'})

        with self.assertRaises(AutorDatosInvalidosError):
            self.service.modificar_autor(autor.autor_id, {'nombre': '   '})

    def test_modificar_autor_inexistente_falla(self):
        with self.assertRaises(AutorNoEncontradoError):
            self.service.modificar_autor(99999, {'nombre': 'Fantasma'})

    # -------------------------------------------------------------------------
    # 4. Homónimos y búsqueda informativa
    # -------------------------------------------------------------------------

    def test_permite_registro_de_autores_homonimos(self):
        a1 = self.service.registrar_autor({
            'nombre': 'Alejandro Dumas',
            'nacionalidad': 'Francesa',
            'fecha_nacimiento': date(1802, 7, 24),
        })
        # Dumas hijo: mismo nombre en el acervo tradicional
        a2 = self.service.registrar_autor({
            'nombre': 'Alejandro Dumas',
            'nacionalidad': 'Francesa',
            'fecha_nacimiento': date(1824, 7, 27),
        })

        self.assertNotEqual(a1.autor_id, a2.autor_id)
        self.assertEqual(a1.nombre, a2.nombre)
        self.assertEqual(Autor.objects.filter(nombre='Alejandro Dumas').count(), 2)

    def test_buscar_homonimos_informativo(self):
        self.service.registrar_autor({'nombre': 'José Emilio Pacheco'})
        self.service.registrar_autor({'nombre': 'José Emilio Pacheco'})

        coincidencias = self.service.buscar_homonimos('  josé emilio pacheco  ')
        self.assertEqual(coincidencias.count(), 2)

    # -------------------------------------------------------------------------
    # 5. Relaciones con libros y conteos
    # -------------------------------------------------------------------------

    def test_conteo_libros_asociados_cero(self):
        autor = self.service.registrar_autor({'nombre': 'Autor Solitario'})

        self.assertFalse(self.service.tiene_libros_asociados(autor.autor_id))
        self.assertEqual(self.service.contar_libros_asociados(autor.autor_id), 0)

    def test_conteo_libros_asociados_con_libros(self):
        autor = self.service.registrar_autor({'nombre': 'Autor Prolífico'})

        l1 = Libro.objects.create(titulo='Libro A', isbn='9789999999901')
        l2 = Libro.objects.create(titulo='Libro B', isbn='9789999999902')

        LibroAutor.objects.create(autor=autor, libro=l1)
        LibroAutor.objects.create(autor=autor, libro=l2)

        self.assertTrue(self.service.tiene_libros_asociados(autor.autor_id))
        self.assertEqual(self.service.contar_libros_asociados(autor.autor_id), 2)

        recuperado = self.service.obtener_autor(autor.autor_id)
        self.assertEqual(recuperado.cantidad_libros, 2)

    # -------------------------------------------------------------------------
    # 6. Bloqueo de eliminaciones físicas
    # -------------------------------------------------------------------------

    def test_bloqueo_eliminacion_fisica_sin_libros(self):
        autor = self.service.registrar_autor({'nombre': 'Autor No Eliminable'})

        with self.assertRaises(AutorOperacionNoPermitidaError):
            self.service.eliminar_autor(autor.autor_id)

        # El autor debe seguir existiendo intacto
        self.assertTrue(Autor.objects.filter(autor_id=autor.autor_id).exists())

    def test_bloqueo_eliminacion_fisica_con_libros(self):
        autor = self.service.registrar_autor({'nombre': 'Autor Con Libros'})
        libro = Libro.objects.create(titulo='Libro Protegido', isbn='9789999999903')
        LibroAutor.objects.create(autor=autor, libro=libro)

        with self.assertRaises(AutorOperacionNoPermitidaError) as ctx:
            self.service.eliminar_autor(autor.autor_id)

        self.assertIn('RN-20', str(ctx.exception))
        self.assertTrue(Autor.objects.filter(autor_id=autor.autor_id).exists())
