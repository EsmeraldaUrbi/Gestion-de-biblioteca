from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from biblioteca.models import (
    Ejemplar,
    Libro,
    Prestamo,
    Rol,
    Usuario,
)


class UsuariosApiTests(APITestCase):

    PASSWORD = 'Biblioteca123*'

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

        self.url_lista = reverse('usuarios-list-create')
        self.url_roles = reverse('roles-list')

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

    def datos_registro(self):
        return {
            'nombre': 'Ana Martínez',
            'email': 'ana@test.local',
            'direccion': 'Puebla',
            'telefono': '2221234567',
            'rol_id': self.roles['estudiante'].rol_id,
            'password': 'ClaveSegura123!'
        }

    def test_bibliotecario_registra_usuario(self):
        self.autenticar(self.bibliotecario)

        respuesta = self.client.post(
            self.url_lista,
            self.datos_registro(),
            format='json'
        )

        self.assertEqual(respuesta.status_code, 201)
        usuario = Usuario.objects.get(email='ana@test.local')
        self.assertTrue(usuario.check_password('ClaveSegura123!'))
        self.assertNotEqual(
            usuario.contrasena_hash,
            'ClaveSegura123!'
        )
        self.assertNotIn('password', respuesta.data)
        self.assertNotIn('contrasena_hash', respuesta.data)

    def test_listar_usuarios(self):
        self.autenticar(self.bibliotecario)

        respuesta = self.client.get(self.url_lista)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['count'], 3)
        self.assertEqual(len(respuesta.data['results']), 3)

    def test_consultar_usuario(self):
        self.autenticar(self.bibliotecario)

        respuesta = self.client.get(
            reverse(
                'usuarios-detail',
                kwargs={'usuario_id': self.estudiante.usuario_id}
            )
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(
            respuesta.data['email'],
            self.estudiante.email
        )

    def test_modificar_usuario(self):
        self.autenticar(self.bibliotecario)

        respuesta = self.client.patch(
            reverse(
                'usuarios-detail',
                kwargs={'usuario_id': self.estudiante.usuario_id}
            ),
            {'telefono': '2229876543'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 200)
        self.estudiante.refresh_from_db()
        self.assertEqual(
            self.estudiante.telefono,
            '2229876543'
        )

    def test_cambiar_rol_permitido(self):
        self.autenticar(self.bibliotecario)

        respuesta = self.client.patch(
            reverse(
                'usuarios-detail',
                kwargs={'usuario_id': self.estudiante.usuario_id}
            ),
            {'rol_id': self.roles['docente'].rol_id},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 200)
        self.estudiante.refresh_from_db()
        self.assertEqual(
            self.estudiante.rol_id,
            self.roles['docente'].rol_id
        )

    def test_correo_duplicado(self):
        self.autenticar(self.bibliotecario)
        datos = self.datos_registro()
        datos['email'] = self.estudiante.email

        respuesta = self.client.post(
            self.url_lista,
            datos,
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_correo_invalido(self):
        self.autenticar(self.bibliotecario)
        datos = self.datos_registro()
        datos['email'] = 'correo-invalido'

        respuesta = self.client.post(
            self.url_lista,
            datos,
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_rol_inexistente(self):
        self.autenticar(self.bibliotecario)
        datos = self.datos_registro()
        datos['rol_id'] = 99999

        respuesta = self.client.post(
            self.url_lista,
            datos,
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_contrasena_invalida(self):
        self.autenticar(self.bibliotecario)
        datos = self.datos_registro()
        datos['password'] = '123'

        respuesta = self.client.post(
            self.url_lista,
            datos,
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_no_permite_modificar_contrasena(self):
        self.autenticar(self.bibliotecario)

        respuesta = self.client.patch(
            reverse(
                'usuarios-detail',
                kwargs={'usuario_id': self.estudiante.usuario_id}
            ),
            {'password': 'OtraClave123!'},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

    def test_usuario_inexistente(self):
        self.autenticar(self.bibliotecario)

        respuesta = self.client.get(
            reverse(
                'usuarios-detail',
                kwargs={'usuario_id': 99999}
            )
        )

        self.assertEqual(respuesta.status_code, 404)

    def test_estudiante_no_administra_usuarios(self):
        self.autenticar(self.estudiante)

        respuesta = self.client.get(self.url_lista)

        self.assertEqual(respuesta.status_code, 403)

    def test_docente_no_administra_usuarios(self):
        self.autenticar(self.docente)

        respuesta = self.client.post(
            self.url_lista,
            self.datos_registro(),
            format='json'
        )

        self.assertEqual(respuesta.status_code, 403)

    def test_sin_autenticacion(self):
        respuesta = self.client.get(self.url_lista)

        self.assertEqual(respuesta.status_code, 401)

    def test_consultar_roles(self):
        self.autenticar(self.bibliotecario)

        respuesta = self.client.get(self.url_roles)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data), 3)

    def test_paginacion(self):
        self.autenticar(self.bibliotecario)

        respuesta = self.client.get(
            self.url_lista,
            {'page': 1, 'page_size': 2}
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['count'], 3)
        self.assertEqual(len(respuesta.data['results']), 2)

    def test_no_convertir_usuario_con_prestamo_activo(self):
        libro = Libro.objects.create(
            titulo='Libro de prueba',
            isbn='9781234567890'
        )
        ejemplar = Ejemplar.objects.create(
            libro=libro,
            codigo_inventario='TEST001',
            estado='ACTIVO'
        )
        Prestamo.objects.create(
            usuario=self.estudiante,
            ejemplar=ejemplar,
            fecha_prestamo='2026-10-01',
            fecha_limite='2026-10-31'
        )

        self.autenticar(self.bibliotecario)

        respuesta = self.client.patch(
            reverse(
                'usuarios-detail',
                kwargs={'usuario_id': self.estudiante.usuario_id}
            ),
            {'rol_id': self.roles['bibliotecario'].rol_id},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)
        self.estudiante.refresh_from_db()
        self.assertEqual(
            self.estudiante.rol_id,
            self.roles['estudiante'].rol_id
        )

    def test_listar_usuarios_con_token_real(self):
        login = self.client.post(
            reverse('auth-login'),
            {
                'email': self.bibliotecario.email,
                'password': self.PASSWORD,
            },
            format='json'
        )

        self.assertEqual(login.status_code, 200)
        self.assertIn('token', login.data)

        token = login.data['token']

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        respuesta = self.client.get(self.url_lista)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['count'], 3)

    def test_registro_rechaza_rol_no_permitido(self):
        self.autenticar(self.bibliotecario)

        otro_rol = Rol.objects.create(
            nombre='administrador',
            limite_prestamos_activos=0
        )

        datos = self.datos_registro()
        datos['rol_id'] = otro_rol.rol_id

        respuesta = self.client.post(
            self.url_lista,
            datos,
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

        self.assertFalse(
            Usuario.objects.filter(
                email='ana@test.local'
            ).exists()
        )

    def test_modificacion_rechaza_rol_no_permitido(self):
        self.autenticar(self.bibliotecario)

        otro_rol = Rol.objects.create(
            nombre='administrador',
            limite_prestamos_activos=0
        )

        respuesta = self.client.patch(
            reverse(
                'usuarios-detail',
                kwargs={
                    'usuario_id': self.estudiante.usuario_id
                }
            ),
            {'rol_id': otro_rol.rol_id},
            format='json'
        )

        self.assertEqual(respuesta.status_code, 400)

        self.estudiante.refresh_from_db()

        self.assertEqual(
            self.estudiante.rol_id,
            self.roles['estudiante'].rol_id
        )
    def test_listado_roles_excluye_roles_no_permitidos(self):
        self.autenticar(self.bibliotecario)

        Rol.objects.create(
            nombre='administrador',
            limite_prestamos_activos=0
        )

        respuesta = self.client.get(self.url_roles)

        self.assertEqual(respuesta.status_code, 200)

        nombres = {
            rol['nombre']
            for rol in respuesta.data
        }

        self.assertEqual(
            nombres,
            {'estudiante', 'docente', 'bibliotecario'}
        )
