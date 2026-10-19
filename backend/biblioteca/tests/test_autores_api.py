from datetime import date, timedelta
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from biblioteca.models import (
    Autor,
    Categoria,
    Libro,
    Rol,
    Usuario,
)


class AutoresApiTests(APITestCase):
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

        self.url_lista = reverse('autores-list-create')

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

    def url_detalle(self, autor_id):
        return reverse('autores-detail', kwargs={'autor_id': autor_id})

    # -------------------------------------------------------------------------
    # 1. Seguridad y Permisos
    # -------------------------------------------------------------------------

    def test_anonimo_es_rechazado_en_lista(self):
        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_invalido_es_rechazado(self):
        respuesta = self.client.get(
            self.url_lista,
            HTTP_AUTHORIZATION='Bearer token_completamente_invalido_123',
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
            {'nombre': 'Autor Ilegal'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_docente_es_rechazado_en_registro(self):
        self.autenticar(self.docente)
        respuesta = self.client.post(
            self.url_lista,
            {'nombre': 'Autor Ilegal'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_estudiante_es_rechazado_en_detalle(self):
        autor = Autor.objects.create(nombre='Autor Base')
        self.autenticar(self.estudiante)
        respuesta = self.client.get(self.url_detalle(autor.autor_id))
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_docente_es_rechazado_en_modificacion(self):
        autor = Autor.objects.create(nombre='Autor Base')
        self.autenticar(self.docente)
        respuesta = self.client.patch(
            self.url_detalle(autor.autor_id),
            {'nombre': 'Nuevo Nombre'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_estudiante_es_rechazado_en_eliminacion(self):
        autor = Autor.objects.create(nombre='Autor Base')
        self.autenticar(self.estudiante)
        respuesta = self.client.delete(self.url_detalle(autor.autor_id))
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    # -------------------------------------------------------------------------
    # 2. Consulta y Listado Paginado
    # -------------------------------------------------------------------------

    def test_bibliotecario_obtiene_listado_paginado(self):
        self.autenticar(self.bibliotecario)
        for i in range(15):
            Autor.objects.create(nombre=f'Autor {i:02d}')

        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 15)
        self.assertEqual(len(respuesta.data['results']), 10)
        self.assertIsNotNone(respuesta.data['next'])

    def test_bibliotecario_filtra_por_nombre(self):
        self.autenticar(self.bibliotecario)
        Autor.objects.create(nombre='Gabriel García Márquez')
        Autor.objects.create(nombre='Mario Vargas Llosa')

        respuesta = self.client.get(self.url_lista, {'nombre': 'garcía'})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(respuesta.data['results'][0]['nombre'], 'Gabriel García Márquez')

    def test_bibliotecario_filtra_por_nacionalidad(self):
        self.autenticar(self.bibliotecario)
        Autor.objects.create(nombre='Juan Rulfo', nacionalidad='Mexicana')
        Autor.objects.create(nombre='Julio Cortázar', nacionalidad='Argentina')

        respuesta = self.client.get(self.url_lista, {'nacionalidad': 'mexicana'})
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(respuesta.data['results'][0]['nombre'], 'Juan Rulfo')

    def test_consultar_detalle_autor_existente(self):
        self.autenticar(self.bibliotecario)
        autor = Autor.objects.create(
            nombre='Jorge Luis Borges',
            nacionalidad='Argentina',
            fecha_nacimiento=date(1899, 8, 24),
        )

        respuesta = self.client.get(self.url_detalle(autor.autor_id))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['autor_id'], autor.autor_id)
        self.assertEqual(respuesta.data['nombre'], 'Jorge Luis Borges')
        self.assertEqual(respuesta.data['nacionalidad'], 'Argentina')
        self.assertEqual(respuesta.data['fecha_nacimiento'], '1899-08-24')
        self.assertEqual(respuesta.data['cantidad_libros'], 0)

    def test_consultar_detalle_autor_inexistente_retorna_404(self):
        self.autenticar(self.bibliotecario)
        respuesta = self.client.get(self.url_detalle(99999))
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Autor no encontrado', respuesta.data['detail'])

    # -------------------------------------------------------------------------
    # 3. Registro (POST)
    # -------------------------------------------------------------------------

    def test_registrar_autor_completo(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'nombre': 'Octavio Paz',
            'nacionalidad': 'Mexicana',
            'fecha_nacimiento': '1914-03-31',
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertIn('autor_id', respuesta.data)
        self.assertEqual(respuesta.data['nombre'], 'Octavio Paz')
        self.assertEqual(respuesta.data['nacionalidad'], 'Mexicana')
        self.assertEqual(respuesta.data['fecha_nacimiento'], '1914-03-31')
        self.assertEqual(respuesta.data['cantidad_libros'], 0)

    def test_registrar_autor_solo_nombre(self):
        self.autenticar(self.bibliotecario)
        respuesta = self.client.post(
            self.url_lista,
            {'nombre': 'Carlos Fuentes'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(respuesta.data['nacionalidad'])
        self.assertIsNone(respuesta.data['fecha_nacimiento'])

    def test_registrar_autor_normaliza_espacios(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'nombre': '   Alfonso Reyes   ',
            'nacionalidad': '   Mexicana   ',
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['nombre'], 'Alfonso Reyes')
        self.assertEqual(respuesta.data['nacionalidad'], 'Mexicana')

    def test_registrar_autor_homonimo_permitido(self):
        self.autenticar(self.bibliotecario)
        p1 = {'nombre': 'Alejandro Dumas', 'nacionalidad': 'Francesa'}
        p2 = {'nombre': 'Alejandro Dumas', 'nacionalidad': 'Francesa'}

        res1 = self.client.post(self.url_lista, p1, format='json')
        res2 = self.client.post(self.url_lista, p2, format='json')

        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(res1.data['autor_id'], res2.data['autor_id'])

    def test_registrar_autor_nombre_vacio_rechazado(self):
        self.autenticar(self.bibliotecario)
        respuesta = self.client.post(
            self.url_lista,
            {'nombre': '   '},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre', respuesta.data)

    def test_registrar_autor_fecha_futura_rechazada(self):
        self.autenticar(self.bibliotecario)
        manana = timezone.localdate() + timedelta(days=2)
        payload = {
            'nombre': 'Autor Futuro',
            'fecha_nacimiento': manana.isoformat(),
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('fecha_nacimiento', respuesta.data)

    def test_registrar_autor_campos_desconocidos_rechazados(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'nombre': 'Autor Test',
            'campo_desconocido': 'valor_ilegal',
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('campo_desconocido', respuesta.data)

    def test_proteccion_campos_solo_lectura_en_post(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'nombre': 'Autor Inyección',
            'autor_id': 9999,
            'cantidad_libros': 50,
        }
        # CamposPermitidosSerializer debe rechazar autor_id y cantidad_libros
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # 4. Modificación (PATCH y PUT)
    # -------------------------------------------------------------------------

    def test_patch_modifica_solo_nombre_conservando_otros_campos(self):
        self.autenticar(self.bibliotecario)
        autor = Autor.objects.create(
            nombre='Nombre Original',
            nacionalidad='Chilena',
            fecha_nacimiento=date(1904, 7, 12),
        )

        respuesta = self.client.patch(
            self.url_detalle(autor.autor_id),
            {'nombre': 'Pablo Neruda'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['nombre'], 'Pablo Neruda')
        self.assertEqual(respuesta.data['nacionalidad'], 'Chilena')
        self.assertEqual(respuesta.data['fecha_nacimiento'], '1904-07-12')

    def test_patch_modifica_solo_nacionalidad(self):
        self.autenticar(self.bibliotecario)
        autor = Autor.objects.create(nombre='Gabriela Mistral')

        respuesta = self.client.patch(
            self.url_detalle(autor.autor_id),
            {'nacionalidad': 'Chilena'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['nacionalidad'], 'Chilena')
        self.assertEqual(respuesta.data['nombre'], 'Gabriela Mistral')

    def test_put_actualizacion_completa(self):
        self.autenticar(self.bibliotecario)
        autor = Autor.objects.create(nombre='Inicial')

        payload = {
            'nombre': 'César Vallejo',
            'nacionalidad': 'Peruana',
            'fecha_nacimiento': '1892-03-16',
        }
        respuesta = self.client.put(
            self.url_detalle(autor.autor_id),
            payload,
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['nombre'], 'César Vallejo')
        self.assertEqual(respuesta.data['nacionalidad'], 'Peruana')
        self.assertEqual(respuesta.data['fecha_nacimiento'], '1892-03-16')

    def test_put_con_campos_opcionales_omitidos_los_establece_en_null(self):
        self.autenticar(self.bibliotecario)
        autor = Autor.objects.create(
            nombre='Autor Previo',
            nacionalidad='Española',
            fecha_nacimiento=date(1920, 5, 1),
        )

        # En PUT la omisión de campos opcionales restablece a null (representación completa)
        respuesta = self.client.put(
            self.url_detalle(autor.autor_id),
            {'nombre': 'Autor Previo Modificado'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['nombre'], 'Autor Previo Modificado')
        self.assertIsNone(respuesta.data['nacionalidad'])
        self.assertIsNone(respuesta.data['fecha_nacimiento'])

    def test_put_sin_nombre_obligatorio_rechazado(self):
        self.autenticar(self.bibliotecario)
        autor = Autor.objects.create(nombre='Autor Válido')

        respuesta = self.client.put(
            self.url_detalle(autor.autor_id),
            {'nacionalidad': 'Argentina'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nombre', respuesta.data)

    def test_modificar_autor_inexistente_retorna_404(self):
        self.autenticar(self.bibliotecario)
        respuesta = self.client.patch(
            self.url_detalle(99999),
            {'nombre': 'Fantasma'},
            format='json',
        )
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------------------------------------------------------
    # 5. Eliminación (DELETE -> 405)
    # -------------------------------------------------------------------------

    def test_delete_autor_responde_405_method_not_allowed(self):
        self.autenticar(self.bibliotecario)
        autor = Autor.objects.create(nombre='Autor Inmune')

        respuesta = self.client.delete(self.url_detalle(autor.autor_id))
        self.assertEqual(respuesta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Autor.objects.filter(autor_id=autor.autor_id).exists())

    # -------------------------------------------------------------------------
    # 6. Integración con Libros y Catálogo
    # -------------------------------------------------------------------------

    def test_autor_nuevo_aparece_en_filtros_catalogo(self):
        self.autenticar(self.bibliotecario)
        res_autor = self.client.post(
            self.url_lista,
            {'nombre': 'Autor Para Catálogo'},
            format='json',
        )
        autor_id = res_autor.data['autor_id']

        # Consultar filtros del catálogo (GET /api/catalogo/filtros/)
        url_filtros = reverse('catalogo-filtros')
        res_filtros = self.client.get(url_filtros)
        self.assertEqual(res_filtros.status_code, status.HTTP_200_OK)

        autores_catalogo = [a['autor_id'] for a in res_filtros.data['autores']]
        self.assertIn(autor_id, autores_catalogo)

    def test_libro_se_asocia_a_autor_nuevo_y_se_recupera_correctamente(self):
        self.autenticar(self.bibliotecario)
        res_autor = self.client.post(
            self.url_lista,
            {'nombre': 'Clarice Lispector'},
            format='json',
        )
        autor_id = res_autor.data['autor_id']

        # Registrar un libro asociando al autor recién creado
        url_libros = reverse('libros-list-create')
        res_libro = self.client.post(
            url_libros,
            {
                'titulo': 'La Hora de la Estrella',
                'isbn': '9788417430153',
                'autor_ids': [autor_id],
            },
            format='json',
        )
        self.assertEqual(res_libro.status_code, status.HTTP_201_CREATED)
        libro_id = res_libro.data['libro_id']

        # Verificar detalle del libro
        url_libro_detalle = reverse('libros-detail', kwargs={'libro_id': libro_id})
        res_get_libro = self.client.get(url_libro_detalle)
        self.assertEqual(res_get_libro.status_code, status.HTTP_200_OK)
        autores_libro = [a['autor_id'] for a in res_get_libro.data['autores']]
        self.assertIn(autor_id, autores_libro)

        # Verificar que el conteo en el detalle del autor se incrementó a 1
        res_get_autor = self.client.get(self.url_detalle(autor_id))
        self.assertEqual(res_get_autor.data['cantidad_libros'], 1)

    def test_modificar_autor_no_rompe_relacion_con_libro(self):
        self.autenticar(self.bibliotecario)
        res_autor = self.client.post(
            self.url_lista,
            {'nombre': 'Autor Original'},
            format='json',
        )
        autor_id = res_autor.data['autor_id']

        url_libros = reverse('libros-list-create')
        res_libro = self.client.post(
            url_libros,
            {'titulo': 'Libro Permanente', 'isbn': '9780000000088', 'autor_ids': [autor_id]},
            format='json',
        )
        libro_id = res_libro.data['libro_id']

        # Modificar autor
        self.client.patch(
            self.url_detalle(autor_id),
            {'nombre': 'Autor Nombre Actualizado'},
            format='json',
        )

        # Consultar el libro y verificar que sigue vinculado con el nuevo nombre
        url_libro_detalle = reverse('libros-detail', kwargs={'libro_id': libro_id})
        res_libro_get = self.client.get(url_libro_detalle)
        self.assertEqual(res_libro_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_libro_get.data['autores'][0]['autor_id'], autor_id)
        self.assertEqual(res_libro_get.data['autores'][0]['nombre'], 'Autor Nombre Actualizado')
