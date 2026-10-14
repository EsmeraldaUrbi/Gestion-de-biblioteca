from datetime import date
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from biblioteca.models import (
    Autor,
    Categoria,
    Libro,
    Rol,
    Usuario,
)


class LibrosApiTests(APITestCase):
    PASSWORD = 'PasswordSeguro123*'

    def setUp(self):
        self.roles = {}
        for nombre, limite in [
            ('estudiante', 5),
            ('docente', 5),
            ('bibliotecario', 0),
        ]:
            self.roles[nombre] = Rol.objects.create(
                nombre=nombre,
                limite_prestamos_activos=limite
            )

        self.bibliotecario = self.crear_usuario(
            'Bibliotecario',
            'bibliotecario@test.local',
            'bibliotecario'
        )
        self.estudiante = self.crear_usuario(
            'Estudiante',
            'estudiante@test.local',
            'estudiante'
        )
        self.docente = self.crear_usuario(
            'Docente',
            'docente@test.local',
            'docente'
        )

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

        self.url_lista = reverse('libros-list-create')

    def crear_usuario(self, nombre, email, rol):
        usuario = Usuario(
            nombre=nombre,
            email=email,
            rol=self.roles[rol]
        )
        usuario.set_password(self.PASSWORD)
        usuario.save()
        return usuario

    def autenticar(self, usuario):
        self.client.force_authenticate(user=usuario)

    def url_detalle(self, libro_id):
        return reverse('libros-detail', kwargs={'libro_id': libro_id})

    # --- Permisos y Autenticación ---

    def test_anonimo_es_rechazado_en_lista(self):
        # DRF retorna 401 cuando no hay credenciales
        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_estudiante_es_rechazado_en_lista(self):
        self.autenticar(self.estudiante)
        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_docente_es_rechazado_en_lista(self):
        self.autenticar(self.docente)
        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonimo_es_rechazado_en_registro(self):
        respuesta = self.client.post(
            self.url_lista,
            {'titulo': 'Libro Anónimo', 'isbn': '9781111111111'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_estudiante_es_rechazado_en_registro(self):
        self.autenticar(self.estudiante)
        respuesta = self.client.post(
            self.url_lista,
            {'titulo': 'Libro No Autorizado', 'isbn': '9781111111111'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_estudiante_es_rechazado_en_detalle(self):
        self.autenticar(self.bibliotecario)
        res_crear = self.client.post(
            self.url_lista,
            {'titulo': 'Libro Test', 'isbn': '9781111111111'},
            format='json'
        )
        libro_id = res_crear.data['libro_id']

        self.autenticar(self.estudiante)
        respuesta = self.client.get(self.url_detalle(libro_id))
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    # --- Creación y Listado ---

    def test_bibliotecario_registra_libro_con_asociaciones(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'titulo': 'Cien Años de Soledad',
            'isbn': '9780307474728',
            'fecha_publicacion': '1967-05-30',
            'autor_ids': [self.autor1.autor_id, self.autor2.autor_id],
            'categoria_ids': [self.categoria1.categoria_id]
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        data = respuesta.data
        self.assertIn('libro_id', data)
        self.assertEqual(data['titulo'], 'Cien Años de Soledad')
        self.assertEqual(data['isbn'], '9780307474728')
        self.assertEqual(data['fecha_publicacion'], '1967-05-30')
        self.assertEqual(len(data['autores']), 2)
        self.assertEqual(len(data['categorias']), 1)
        autor_ids = [a['autor_id'] for a in data['autores']]
        self.assertIn(self.autor1.autor_id, autor_ids)
        self.assertIn(self.autor2.autor_id, autor_ids)

    def test_bibliotecario_registra_libro_sin_autores_ni_categorias(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'titulo': 'Libro Solitario',
            'isbn': '9780000000001'
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(respuesta.data['autores']), 0)
        self.assertEqual(len(respuesta.data['categorias']), 0)

    def test_registro_rechaza_campos_no_permitidos(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'titulo': 'Libro Inválido',
            'isbn': '9780000000002',
            'editorial': 'Editorial No Permitida'
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('editorial', respuesta.data)

    def test_registro_rechaza_isbn_duplicado(self):
        self.autenticar(self.bibliotecario)
        payload1 = {
            'titulo': 'Libro Original',
            'isbn': '9781234567890'
        }
        res1 = self.client.post(self.url_lista, payload1, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        payload2 = {
            'titulo': 'Libro Duplicado',
            'isbn': '9781234567890'
        }
        res2 = self.client.post(self.url_lista, payload2, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('isbn', res2.data)

    def test_registro_rechaza_autor_inexistente(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'titulo': 'Libro Autor Fantasma',
            'isbn': '9789999999999',
            'autor_ids': [99999]
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('autor_ids', respuesta.data)

    def test_registro_rechaza_categoria_inexistente(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'titulo': 'Libro Categoria Fantasma',
            'isbn': '9788888888888',
            'categoria_ids': [99999]
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('categoria_ids', respuesta.data)

    def test_bibliotecario_lista_libros_con_paginacion(self):
        self.autenticar(self.bibliotecario)
        for i in range(3):
            self.client.post(
                self.url_lista,
                {'titulo': f'Libro {i}', 'isbn': f'97800000000{i}'},
                format='json'
            )

        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('count', respuesta.data)
        self.assertIn('results', respuesta.data)
        self.assertEqual(respuesta.data['count'], 3)
        self.assertEqual(len(respuesta.data['results']), 3)

    # --- Consulta de Detalle ---

    def test_consultar_detalle_libro_existente(self):
        self.autenticar(self.bibliotecario)
        res_crear = self.client.post(
            self.url_lista,
            {
                'titulo': 'Libro Detalle',
                'isbn': '9783333333333',
                'autor_ids': [self.autor1.autor_id],
                'categoria_ids': [self.categoria1.categoria_id]
            },
            format='json'
        )
        libro_id = res_crear.data['libro_id']

        respuesta = self.client.get(self.url_detalle(libro_id))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['libro_id'], libro_id)
        self.assertEqual(respuesta.data['titulo'], 'Libro Detalle')
        self.assertEqual(len(respuesta.data['autores']), 1)
        self.assertEqual(respuesta.data['autores'][0]['autor_id'], self.autor1.autor_id)

    def test_consultar_detalle_libro_inexistente(self):
        self.autenticar(self.bibliotecario)
        respuesta = self.client.get(self.url_detalle(99999))
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(respuesta.data.get('detail'), 'Libro no encontrado.')

    # --- Modificaciones: PATCH y PUT ---

    def test_patch_modifica_titulo_conservando_asociaciones_omitidas(self):
        self.autenticar(self.bibliotecario)
        res_crear = self.client.post(
            self.url_lista,
            {
                'titulo': 'Título Original',
                'isbn': '9784444444444',
                'autor_ids': [self.autor1.autor_id],
                'categoria_ids': [self.categoria1.categoria_id]
            },
            format='json'
        )
        libro_id = res_crear.data['libro_id']

        # Enviar PATCH solo con titulo (omitiendo autor_ids y categoria_ids)
        respuesta = self.client.patch(
            self.url_detalle(libro_id),
            {'titulo': 'Título Modificado'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['titulo'], 'Título Modificado')
        self.assertEqual(respuesta.data['isbn'], '9784444444444')
        # Las asociaciones omitidas DEBEN conservarse
        self.assertEqual(len(respuesta.data['autores']), 1)
        self.assertEqual(respuesta.data['autores'][0]['autor_id'], self.autor1.autor_id)
        self.assertEqual(len(respuesta.data['categorias']), 1)
        self.assertEqual(respuesta.data['categorias'][0]['categoria_id'], self.categoria1.categoria_id)

    def test_patch_reemplaza_autores(self):
        self.autenticar(self.bibliotecario)
        res_crear = self.client.post(
            self.url_lista,
            {
                'titulo': 'Libro Cambio Autor',
                'isbn': '9785555555555',
                'autor_ids': [self.autor1.autor_id]
            },
            format='json'
        )
        libro_id = res_crear.data['libro_id']

        respuesta = self.client.patch(
            self.url_detalle(libro_id),
            {'autor_ids': [self.autor2.autor_id]},
            format='json'
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data['autores']), 1)
        self.assertEqual(respuesta.data['autores'][0]['autor_id'], self.autor2.autor_id)

    def test_patch_falla_con_isbn_duplicado(self):
        self.autenticar(self.bibliotecario)
        res_a = self.client.post(
            self.url_lista,
            {'titulo': 'Libro A', 'isbn': '9786666666661'},
            format='json'
        )
        res_b = self.client.post(
            self.url_lista,
            {'titulo': 'Libro B', 'isbn': '9786666666662'},
            format='json'
        )
        libro_b_id = res_b.data['libro_id']

        # Intentar cambiar el ISBN de B por el de A
        respuesta = self.client.patch(
            self.url_detalle(libro_b_id),
            {'isbn': '9786666666661'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('isbn', respuesta.data)

    def test_patch_falla_con_autor_inexistente(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'titulo': 'Libro C', 'isbn': '9787777777777'},
            format='json'
        )
        libro_id = res.data['libro_id']

        respuesta = self.client.patch(
            self.url_detalle(libro_id),
            {'autor_ids': [99999]},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('autor_ids', respuesta.data)

    def test_put_actualizacion_completa(self):
        self.autenticar(self.bibliotecario)
        res_crear = self.client.post(
            self.url_lista,
            {
                'titulo': 'Título Viejo',
                'isbn': '9788888888881',
                'autor_ids': [self.autor1.autor_id]
            },
            format='json'
        )
        libro_id = res_crear.data['libro_id']

        payload_put = {
            'titulo': 'Título Nuevo Total',
            'isbn': '9788888888882',
            'fecha_publicacion': '2020-01-01',
            'autor_ids': [self.autor2.autor_id],
            'categoria_ids': [self.categoria2.categoria_id]
        }
        respuesta = self.client.put(
            self.url_detalle(libro_id),
            payload_put,
            format='json'
        )

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['titulo'], 'Título Nuevo Total')
        self.assertEqual(respuesta.data['isbn'], '9788888888882')
        self.assertEqual(respuesta.data['fecha_publicacion'], '2020-01-01')
        self.assertEqual(len(respuesta.data['autores']), 1)
        self.assertEqual(respuesta.data['autores'][0]['autor_id'], self.autor2.autor_id)
        self.assertEqual(len(respuesta.data['categorias']), 1)
        self.assertEqual(respuesta.data['categorias'][0]['categoria_id'], self.categoria2.categoria_id)

    def test_delete_no_permitido(self):
        self.autenticar(self.bibliotecario)
        res_crear = self.client.post(
            self.url_lista,
            {'titulo': 'Libro No Borrable', 'isbn': '9789999999991'},
            format='json'
        )
        libro_id = res_crear.data['libro_id']

        # El endpoint DELETE no debe estar expuesto aún
        respuesta = self.client.delete(self.url_detalle(libro_id))
        self.assertEqual(respuesta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
