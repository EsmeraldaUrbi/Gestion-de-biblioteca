from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APITestCase

from biblioteca.models import (
    Ejemplar,
    Libro,
    Prestamo,
    Rol,
    Usuario,
)


class MisPrestamosApiTests(APITestCase):
    PASSWORD = 'Biblioteca123*'

    def setUp(self):
        self.hoy = timezone.localdate()

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
            'Estudiante Demo',
            'estudiante-mios@test.local',
            self.rol_estudiante
        )

        self.docente = self.crear_usuario(
            'Docente Demo',
            'docente-mios@test.local',
            self.rol_docente
        )

        self.bibliotecario = self.crear_usuario(
            'Bibliotecario Demo',
            'bibliotecario-mios@test.local',
            self.rol_bibliotecario
        )

        self.libro = Libro.objects.create(
            titulo='Sistemas de información',
            isbn='9780000000123'
        )

        self.ejemplar1 = self.crear_ejemplar('MIO-001')
        self.ejemplar2 = self.crear_ejemplar('MIO-002')
        self.ejemplar3 = self.crear_ejemplar('MIO-003')
        self.ejemplar4 = self.crear_ejemplar('MIO-004')

        self.activo = self.crear_prestamo(
            self.estudiante,
            self.ejemplar1,
            self.hoy - timedelta(days=5),
            self.hoy + timedelta(days=25)
        )

        self.vencido = self.crear_prestamo(
            self.estudiante,
            self.ejemplar2,
            self.hoy - timedelta(days=40),
            self.hoy - timedelta(days=10)
        )

        self.devuelto = self.crear_prestamo(
            self.estudiante,
            self.ejemplar3,
            self.hoy - timedelta(days=60),
            self.hoy - timedelta(days=30),
            self.hoy - timedelta(days=35)
        )

        self.prestamo_docente = self.crear_prestamo(
            self.docente,
            self.ejemplar4,
            self.hoy - timedelta(days=2),
            self.hoy + timedelta(days=28)
        )

        self.url = reverse('prestamos-mios')

    def crear_usuario(self, nombre, email, rol):
        usuario = Usuario(
            nombre=nombre,
            email=email,
            rol=rol
        )

        usuario.set_password(self.PASSWORD)
        usuario.save()

        return usuario

    def crear_ejemplar(self, codigo):
        return Ejemplar.objects.create(
            libro=self.libro,
            codigo_inventario=codigo,
            estado='ACTIVO'
        )

    def crear_prestamo(
        self,
        usuario,
        ejemplar,
        fecha_prestamo,
        fecha_limite,
        fecha_devolucion=None
    ):
        return Prestamo.objects.create(
            usuario=usuario,
            ejemplar=ejemplar,
            fecha_prestamo=fecha_prestamo,
            fecha_limite=fecha_limite,
            fecha_devolucion=fecha_devolucion
        )

    def autenticar(self, usuario):
        self.client.force_authenticate(user=usuario)

    def test_anonimo_no_accede(self):
        respuesta = self.client.get(self.url)

        self.assertEqual(
            respuesta.status_code,
            401
        )

    def test_bibliotecario_no_accede(self):
        self.autenticar(self.bibliotecario)

        respuesta = self.client.get(self.url)

        self.assertEqual(
            respuesta.status_code,
            403
        )

    def test_estudiante_ve_solo_sus_prestamos(self):
        self.autenticar(self.estudiante)

        respuesta = self.client.get(self.url)

        self.assertEqual(
            respuesta.status_code,
            200
        )

        self.assertEqual(
            respuesta.data['count'],
            3
        )

        identificadores = {
            item['prestamo_id']
            for item in respuesta.data['results']
        }

        self.assertEqual(
            identificadores,
            {
                self.activo.prestamo_id,
                self.vencido.prestamo_id,
                self.devuelto.prestamo_id,
            }
        )

        self.assertNotIn(
            self.prestamo_docente.prestamo_id,
            identificadores
        )

    def test_docente_ve_solo_sus_prestamos(self):
        self.autenticar(self.docente)

        respuesta = self.client.get(self.url)

        self.assertEqual(
            respuesta.status_code,
            200
        )

        self.assertEqual(
            respuesta.data['count'],
            1
        )

        self.assertEqual(
            respuesta.data['results'][0]['prestamo_id'],
            self.prestamo_docente.prestamo_id
        )

    def test_estados_calculados_correctamente(self):
        self.autenticar(self.estudiante)

        respuesta = self.client.get(
            self.url,
            {'page_size': 10}
        )

        estados = {
            item['prestamo_id']: item['estado']
            for item in respuesta.data['results']
        }

        self.assertEqual(
            estados[self.activo.prestamo_id],
            'EN_PRESTAMO'
        )

        self.assertEqual(
            estados[self.vencido.prestamo_id],
            'VENCIDO'
        )

        self.assertEqual(
            estados[self.devuelto.prestamo_id],
            'DEVUELTO'
        )

    def test_resumen_de_prestamos(self):
        self.autenticar(self.estudiante)

        respuesta = self.client.get(self.url)

        self.assertEqual(
            respuesta.data['resumen'],
            {
                'total': 3,
                'activos': 2,
                'vencidos': 1,
                'devueltos': 1,
            }
        )

    def test_filtro_activos_incluye_vencidos(self):
        self.autenticar(self.estudiante)

        respuesta = self.client.get(
            self.url,
            {'filtro': 'activos'}
        )

        self.assertEqual(
            respuesta.data['count'],
            2
        )

        identificadores = {
            item['prestamo_id']
            for item in respuesta.data['results']
        }

        self.assertEqual(
            identificadores,
            {
                self.activo.prestamo_id,
                self.vencido.prestamo_id,
            }
        )

    def test_filtro_vencidos(self):
        self.autenticar(self.estudiante)

        respuesta = self.client.get(
            self.url,
            {'filtro': 'vencidos'}
        )

        self.assertEqual(
            respuesta.data['count'],
            1
        )

        self.assertEqual(
            respuesta.data['results'][0]['prestamo_id'],
            self.vencido.prestamo_id
        )

    def test_filtro_devueltos(self):
        self.autenticar(self.estudiante)

        respuesta = self.client.get(
            self.url,
            {'filtro': 'devueltos'}
        )

        self.assertEqual(
            respuesta.data['count'],
            1
        )

        self.assertEqual(
            respuesta.data['results'][0]['prestamo_id'],
            self.devuelto.prestamo_id
        )

    def test_dias_restantes(self):
        self.autenticar(self.estudiante)

        respuesta = self.client.get(self.url)

        resultados = {
            item['prestamo_id']: item
            for item in respuesta.data['results']
        }

        self.assertEqual(
            resultados[self.activo.prestamo_id]['dias_restantes'],
            25
        )

        self.assertEqual(
            resultados[self.vencido.prestamo_id]['dias_restantes'],
            0
        )

        self.assertIsNone(
            resultados[self.devuelto.prestamo_id]['dias_restantes']
        )

    def test_usuario_sin_prestamos(self):
        nuevo = self.crear_usuario(
            'Estudiante sin préstamos',
            'sin-prestamos@test.local',
            self.rol_estudiante
        )

        self.autenticar(nuevo)

        respuesta = self.client.get(self.url)

        self.assertEqual(
            respuesta.status_code,
            200
        )

        self.assertEqual(
            respuesta.data['count'],
            0
        )

        self.assertEqual(
            respuesta.data['results'],
            []
        )

        self.assertEqual(
            respuesta.data['resumen']['total'],
            0
        )

    def test_parametros_no_permiten_elegir_otro_usuario(self):
        self.autenticar(self.estudiante)

        respuesta = self.client.get(
            self.url,
            {
                'usuario_id': self.docente.usuario_id
            }
        )

        self.assertEqual(
            respuesta.status_code,
            400
        )

        respuesta_normal = self.client.get(self.url)

        self.assertEqual(
            respuesta_normal.data['count'],
            3
        )

    def test_filtro_invalido(self):
        self.autenticar(self.estudiante)

        respuesta = self.client.get(
            self.url,
            {'filtro': 'otro'}
        )

        self.assertEqual(
            respuesta.status_code,
            400
        )

    def test_paginacion(self):
        self.autenticar(self.estudiante)

        primera = self.client.get(
            self.url,
            {
                'page': 1,
                'page_size': 1
            }
        )

        segunda = self.client.get(
            self.url,
            {
                'page': 2,
                'page_size': 1
            }
        )

        self.assertEqual(primera.status_code, 200)
        self.assertEqual(segunda.status_code, 200)

        self.assertEqual(
            len(primera.data['results']),
            1
        )

        self.assertEqual(
            len(segunda.data['results']),
            1
        )

        self.assertNotEqual(
            primera.data['results'][0]['prestamo_id'],
            segunda.data['results'][0]['prestamo_id']
        )

    def test_consulta_no_modifica_registros(self):
        self.autenticar(self.estudiante)

        total_antes = Prestamo.objects.count()

        for filtro in [
            'todos',
            'activos',
            'vencidos',
            'devueltos',
        ]:
            respuesta = self.client.get(
                self.url,
                {'filtro': filtro}
            )

            self.assertEqual(
                respuesta.status_code,
                200
            )

        self.assertEqual(
            Prestamo.objects.count(),
            total_antes
        )

    def test_post_no_permitido(self):
        self.autenticar(self.estudiante)

        respuesta = self.client.post(
            self.url,
            {},
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            405
        )

    def test_token_bearer_real(self):
        login = self.client.post(
            reverse('auth-login'),
            {
                'email': self.estudiante.email,
                'password': self.PASSWORD,
            },
            format='json'
        )

        self.assertEqual(
            login.status_code,
            200
        )

        token = login.data['token']

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {token}'
        )

        respuesta = self.client.get(self.url)

        self.assertEqual(
            respuesta.status_code,
            200
        )

        self.assertEqual(
            respuesta.data['count'],
            3
        )