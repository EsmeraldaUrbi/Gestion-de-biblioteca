from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from biblioteca.models import Rol, Usuario


class AuthApiTests(APITestCase):

    PASSWORD = 'Biblioteca123*'

    def setUp(self):
        self.rol_estudiante = (
            Rol.objects.create(
                nombre='estudiante',
                limite_prestamos_activos=5
            )
        )

        self.rol_docente = (
            Rol.objects.create(
                nombre='docente',
                limite_prestamos_activos=5
            )
        )

        self.rol_bibliotecario = (
            Rol.objects.create(
                nombre='bibliotecario',
                limite_prestamos_activos=0
            )
        )

        self.estudiante = (
            self._crear_usuario(
                nombre='Estudiante Test',
                email='estudiante@test.local',
                rol=self.rol_estudiante
            )
        )

        self.docente = (
            self._crear_usuario(
                nombre='Docente Test',
                email='docente@test.local',
                rol=self.rol_docente
            )
        )

        self.bibliotecario = (
            self._crear_usuario(
                nombre='Bibliotecario Test',
                email='bibliotecario@test.local',
                rol=self.rol_bibliotecario
            )
        )

    def _crear_usuario(
        self,
        nombre,
        email,
        rol
    ):
        usuario = Usuario(
            nombre=nombre,
            email=email,
            rol=rol,
            contrasena_hash=''
        )

        usuario.set_password(
            self.PASSWORD
        )

        usuario.save()

        return usuario

    def _login(
        self,
        email,
        password=None
    ):
        return self.client.post(
            reverse('auth-login'),
            {
                'email': email,
                'password': (
                    password
                    or self.PASSWORD
                ),
            },
            format='json'
        )

    def _autenticar(
        self,
        email
    ):
        response = self._login(email)

        token = response.data['token']

        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f'Bearer {token}'
            )
        )

        return token

    def test_login_correcto(self):
        response = self._login(
            'estudiante@test.local'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertIn(
            'token',
            response.data
        )

        self.assertEqual(
            response.data['tipo_token'],
            'Bearer'
        )

        self.assertEqual(
            response.data[
                'usuario'
            ]['rol']['nombre'],
            'estudiante'
        )

        self.assertNotIn(
            'contrasena_hash',
            response.data['usuario']
        )

    def test_login_con_password_incorrecto(self):
        response = self._login(
            'estudiante@test.local',
            password='Incorrecta123*'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_login_usuario_inexistente(self):
        response = self._login(
            'noexiste@test.local'
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_me_requiere_autenticacion(self):
        response = self.client.get(
            reverse('auth-me')
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_estudiante_puede_consultar_me(self):
        self._autenticar(
            'estudiante@test.local'
        )

        response = self.client.get(
            reverse('auth-me')
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data['email'],
            'estudiante@test.local'
        )

    def test_estudiante_no_puede_acceder_como_bibliotecario(
        self
    ):
        self._autenticar(
            'estudiante@test.local'
        )

        response = self.client.get(
            reverse(
                'auth-access-bibliotecario'
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_bibliotecario_puede_acceder_a_recurso_bibliotecario(
        self
    ):
        self._autenticar(
            'bibliotecario@test.local'
        )

        response = self.client.get(
            reverse(
                'auth-access-bibliotecario'
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_docente_puede_acceder_a_recurso_lector(
        self
    ):
        self._autenticar(
            'docente@test.local'
        )

        response = self.client.get(
            reverse(
                'auth-access-lector'
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_bibliotecario_no_puede_acceder_como_lector(
        self
    ):
        self._autenticar(
            'bibliotecario@test.local'
        )

        response = self.client.get(
            reverse(
                'auth-access-lector'
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_logout_invalida_el_token(self):
        self._autenticar(
            'estudiante@test.local'
        )

        logout_response = (
            self.client.post(
                reverse('auth-logout')
            )
        )

        self.assertEqual(
            logout_response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        me_response = self.client.get(
            reverse('auth-me')
        )

        self.assertEqual(
            me_response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )