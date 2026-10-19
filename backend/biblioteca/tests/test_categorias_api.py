from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from biblioteca.models import (
    Categoria,
    Libro,
    Rol,
    Usuario,
)


class CategoriasApiTests(APITestCase):
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
                limite_prestamos_activos=limite,
            )

        self.bibliotecario = self.crear_usuario(
            'Bibliotecario Test',
            'bibliotecario@test.local',
            'bibliotecario',
        )
        self.estudiante = self.crear_usuario(
            'Estudiante Test',
            'estudiante@test.local',
            'estudiante',
        )
        self.docente = self.crear_usuario(
            'Docente Test',
            'docente@test.local',
            'docente',
        )

        self.url_lista = reverse('categorias-list-create')

    def crear_usuario(self, nombre, email, rol):
        usuario = Usuario(
            nombre=nombre,
            email=email,
            rol=self.roles[rol],
        )
        usuario.set_password(self.PASSWORD)
        usuario.save()
        return usuario

    def autenticar(self, usuario):
        self.client.force_authenticate(user=usuario)

    def url_detalle(self, categoria_id):
        return reverse('categorias-detail', kwargs={'categoria_id': categoria_id})

    # -------------------------------------------------------------------------
    # 1. Seguridad y Permisos
    # -------------------------------------------------------------------------

    def test_anonimo_es_rechazado_en_lista(self):
        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_invalido_es_rechazado(self):
        respuesta = self.client.get(
            self.url_lista,
            HTTP_AUTHORIZATION='Bearer token_invalido_categoria_456',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_estudiante_es_rechazado_en_lista(self):
        self.autenticar(self.estudiante)
        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_docente_es_rechazado_en_lista(self):
        self.autenticar(self.docente)
        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_estudiante_es_rechazado_en_registro(self):
        self.autenticar(self.estudiante)
        respuesta = self.client.post(
            self.url_lista,
            {'nombre_categoria': 'Categoría Ilegal'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_docente_es_rechazado_en_registro(self):
        self.autenticar(self.docente)
        respuesta = self.client.post(
            self.url_lista,
            {'nombre_categoria': 'Categoría Ilegal'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_estudiante_es_rechazado_en_detalle(self):
        cat = Categoria.objects.create(nombre_categoria='Base')
        self.autenticar(self.estudiante)
        respuesta = self.client.get(self.url_detalle(cat.categoria_id))
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_docente_es_rechazado_en_modificacion(self):
        cat = Categoria.objects.create(nombre_categoria='Base')
        self.autenticar(self.docente)
        respuesta = self.client.patch(
            self.url_detalle(cat.categoria_id),
            {'nombre_categoria': 'Nuevo Nombre'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_estudiante_es_rechazado_en_eliminacion(self):
        cat = Categoria.objects.create(nombre_categoria='Base')
        self.autenticar(self.estudiante)
        respuesta = self.client.delete(self.url_detalle(cat.categoria_id))
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    # -------------------------------------------------------------------------
    # 2. Listado y Consulta
    # -------------------------------------------------------------------------

    def test_bibliotecario_obtiene_listado_paginado(self):
        self.autenticar(self.bibliotecario)
        for i in range(12):
            Categoria.objects.create(nombre_categoria=f'Categoria {i:02d}')

        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 12)
        self.assertEqual(len(respuesta.data['results']), 10)

    def test_bibliotecario_filtra_por_nombre(self):
        self.autenticar(self.bibliotecario)
        Categoria.objects.create(nombre_categoria='Matemáticas Aplicadas')
        Categoria.objects.create(nombre_categoria='Historia del Arte')

        respuesta = self.client.get(self.url_lista, {'nombre': 'matemáticas'})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(respuesta.data['results'][0]['nombre_categoria'], 'Matemáticas Aplicadas')

    def test_consultar_detalle_categoria_existente(self):
        self.autenticar(self.bibliotecario)
        cat = Categoria.objects.create(nombre_categoria='Filosofía')

        respuesta = self.client.get(self.url_detalle(cat.categoria_id))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['categoria_id'], cat.categoria_id)
        self.assertEqual(respuesta.data['nombre_categoria'], 'Filosofía')
        self.assertEqual(respuesta.data['cantidad_libros'], 0)

    def test_consultar_detalle_categoria_inexistente_retorna_404(self):
        self.autenticar(self.bibliotecario)
        respuesta = self.client.get(self.url_detalle(99999))
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Categoría no encontrada', respuesta.data['detail'])

    # -------------------------------------------------------------------------
    # 3. Registro (POST)
    # -------------------------------------------------------------------------

    def test_registrar_categoria_valida(self):
        self.autenticar(self.bibliotecario)
        payload = {'nombre_categoria': 'Ciencia Ficción'}
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertIn('categoria_id', respuesta.data)
        self.assertEqual(respuesta.data['nombre_categoria'], 'Ciencia Ficción')
        self.assertEqual(respuesta.data['cantidad_libros'], 0)

    def test_registrar_categoria_normaliza_espacios(self):
        self.autenticar(self.bibliotecario)
        payload = {'nombre_categoria': '   Antropología   '}
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['nombre_categoria'], 'Antropología')

    def test_registrar_categoria_nombre_vacio_rechazado(self):
        self.autenticar(self.bibliotecario)
        respuesta = self.client.post(
            self.url_lista,
            {'nombre_categoria': '   '},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre_categoria', respuesta.data)

    def test_registrar_categoria_duplicada_exacta_rechazada(self):
        self.autenticar(self.bibliotecario)
        self.client.post(self.url_lista, {'nombre_categoria': 'Química'}, format='json')

        respuesta = self.client.post(self.url_lista, {'nombre_categoria': 'Química'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre_categoria', respuesta.data)

    def test_registrar_categoria_duplicada_case_insensitive_rechazada(self):
        self.autenticar(self.bibliotecario)
        self.client.post(self.url_lista, {'nombre_categoria': 'Biología'}, format='json')

        respuesta = self.client.post(self.url_lista, {'nombre_categoria': 'biología'}, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre_categoria', respuesta.data)

    def test_registrar_categoria_campos_desconocidos_rechazados(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'nombre_categoria': 'Música',
            'descripcion': 'No permitida',
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('descripcion', respuesta.data)

    def test_proteccion_campos_solo_lectura_en_post(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'nombre_categoria': 'Arte',
            'categoria_id': 9999,
            'cantidad_libros': 50,
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # 4. Modificación (PATCH y PUT)
    # -------------------------------------------------------------------------

    def test_patch_modifica_nombre_categoria(self):
        self.autenticar(self.bibliotecario)
        cat = Categoria.objects.create(nombre_categoria='Arq')

        respuesta = self.client.patch(
            self.url_detalle(cat.categoria_id),
            {'nombre_categoria': 'Arquitectura'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['nombre_categoria'], 'Arquitectura')

    def test_put_actualizacion_completa(self):
        self.autenticar(self.bibliotecario)
        cat = Categoria.objects.create(nombre_categoria='Med')

        respuesta = self.client.put(
            self.url_detalle(cat.categoria_id),
            {'nombre_categoria': 'Medicina General'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['nombre_categoria'], 'Medicina General')

    def test_put_sin_nombre_obligatorio_rechazado(self):
        self.autenticar(self.bibliotecario)
        cat = Categoria.objects.create(nombre_categoria='Sociología')

        respuesta = self.client.put(
            self.url_detalle(cat.categoria_id),
            {},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre_categoria', respuesta.data)

    def test_modificar_categoria_hacia_nombre_existente_en_otra_rechazado(self):
        self.autenticar(self.bibliotecario)
        c1 = Categoria.objects.create(nombre_categoria='Teatro')
        c2 = Categoria.objects.create(nombre_categoria='Danza')

        respuesta = self.client.patch(
            self.url_detalle(c2.categoria_id),
            {'nombre_categoria': 'teatro'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre_categoria', respuesta.data)

    def test_modificar_categoria_conservando_su_propio_nombre_exitoso(self):
        self.autenticar(self.bibliotecario)
        cat = Categoria.objects.create(nombre_categoria='Economía')

        respuesta = self.client.patch(
            self.url_detalle(cat.categoria_id),
            {'nombre_categoria': 'Economía'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['nombre_categoria'], 'Economía')

    def test_modificar_categoria_inexistente_retorna_404(self):
        self.autenticar(self.bibliotecario)
        respuesta = self.client.patch(
            self.url_detalle(99999),
            {'nombre_categoria': 'Fantasma'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------------------------------------------------------
    # 5. Eliminación (DELETE -> 405)
    # -------------------------------------------------------------------------

    def test_delete_categoria_responde_405_method_not_allowed(self):
        self.autenticar(self.bibliotecario)
        cat = Categoria.objects.create(nombre_categoria='Inmune')

        respuesta = self.client.delete(self.url_detalle(cat.categoria_id))
        self.assertEqual(respuesta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Categoria.objects.filter(categoria_id=cat.categoria_id).exists())

    # -------------------------------------------------------------------------
    # 6. Integración con Libros y Catálogo
    # -------------------------------------------------------------------------

    def test_categoria_nueva_aparece_en_filtros_catalogo(self):
        self.autenticar(self.bibliotecario)
        res_cat = self.client.post(
            self.url_lista,
            {'nombre_categoria': 'Inteligencia Artificial'},
            format='json',
        )
        cat_id = res_cat.data['categoria_id']

        # Consultar filtros del catálogo
        url_filtros = reverse('catalogo-filtros')
        res_filtros = self.client.get(url_filtros)
        self.assertEqual(res_filtros.status_code, status.HTTP_200_OK)

        categorias_catalogo = [c['categoria_id'] for c in res_filtros.data['categorias']]
        self.assertIn(cat_id, categorias_catalogo)

    def test_libro_se_asocia_a_categoria_nueva_y_se_recupera_correctamente(self):
        self.autenticar(self.bibliotecario)
        res_cat = self.client.post(
            self.url_lista,
            {'nombre_categoria': 'Robótica'},
            format='json',
        )
        cat_id = res_cat.data['categoria_id']

        # Registrar un libro con esta categoría
        url_libros = reverse('libros-list-create')
        res_libro = self.client.post(
            url_libros,
            {
                'titulo': 'Manual de Robótica',
                'isbn': '9780123456789',
                'categoria_ids': [cat_id],
            },
            format='json',
        )
        self.assertEqual(res_libro.status_code, status.HTTP_201_CREATED)
        libro_id = res_libro.data['libro_id']

        # Verificar detalle del libro
        url_libro_detalle = reverse('libros-detail', kwargs={'libro_id': libro_id})
        res_get_libro = self.client.get(url_libro_detalle)
        self.assertEqual(res_get_libro.status_code, status.HTTP_200_OK)
        categorias_libro = [c['categoria_id'] for c in res_get_libro.data['categorias']]
        self.assertIn(cat_id, categorias_libro)

        # Verificar que el conteo en el detalle de la categoría es 1
        res_get_cat = self.client.get(self.url_detalle(cat_id))
        self.assertEqual(res_get_cat.data['cantidad_libros'], 1)

    def test_modificar_categoria_no_rompe_relacion_con_libro(self):
        self.autenticar(self.bibliotecario)
        res_cat = self.client.post(
            self.url_lista,
            {'nombre_categoria': 'Cat Inicial'},
            format='json',
        )
        cat_id = res_cat.data['categoria_id']

        url_libros = reverse('libros-list-create')
        res_libro = self.client.post(
            url_libros,
            {'titulo': 'Libro Permanente Cat', 'isbn': '9780000000099', 'categoria_ids': [cat_id]},
            format='json',
        )
        libro_id = res_libro.data['libro_id']

        # Modificar categoría
        self.client.patch(
            self.url_detalle(cat_id),
            {'nombre_categoria': 'Cat Renombrada'},
            format='json',
        )

        # Consultar libro y verificar que conserva la categoría con el nuevo nombre
        url_libro_detalle = reverse('libros-detail', kwargs={'libro_id': libro_id})
        res_libro_get = self.client.get(url_libro_detalle)
        self.assertEqual(res_libro_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_libro_get.data['categorias'][0]['categoria_id'], cat_id)
        self.assertEqual(res_libro_get.data['categorias'][0]['nombre_categoria'], 'Cat Renombrada')
