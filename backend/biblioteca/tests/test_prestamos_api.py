from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from biblioteca.models import (
    Ejemplar,
    Libro,
    Prestamo,
    Rol,
    Sancion,
    Usuario,
)


class PrestamosApiTests(APITestCase):
    """
    Pruebas de los endpoints REST del ticket 3.5.

    Verifica autenticación, autorización, validaciones,
    elegibilidad, registro y conflictos de negocio.
    """

    PASSWORD = 'Biblioteca123*'

    def setUp(self):
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
            'estudiante@test.local',
            self.rol_estudiante
        )

        self.docente = self.crear_usuario(
            'Docente Demo',
            'docente@test.local',
            self.rol_docente
        )

        self.bibliotecario = self.crear_usuario(
            'Bibliotecario Demo',
            'bibliotecario@test.local',
            self.rol_bibliotecario
        )

        self.libro = Libro.objects.create(
            titulo='Ingeniería de software',
            isbn='9780000000003'
        )

        self.ejemplar = self.crear_ejemplar(
            'API-001'
        )

        self.url_registro = reverse(
            'prestamos-registro'
        )

        self.url_elegibilidad = reverse(
            'prestamos-elegibilidad'
        )

        self.url_busqueda = reverse(
            'prestamos-buscar-lectores'
        )

        self._contador_ejemplares = 1

    def crear_usuario(
        self,
        nombre,
        email,
        rol
    ):
        usuario = Usuario(
            nombre=nombre,
            email=email,
            rol=rol
        )

        usuario.set_password(
            self.PASSWORD
        )

        usuario.save()

        return usuario

    def crear_ejemplar(
        self,
        codigo,
        estado='ACTIVO'
    ):
        return Ejemplar.objects.create(
            libro=self.libro,
            codigo_inventario=codigo,
            estado=estado
        )

    def crear_prestamo_anterior(
        self,
        usuario,
        devuelto=True
    ):
        self._contador_ejemplares += 1

        ejemplar = self.crear_ejemplar(
            f'HIST-{self._contador_ejemplares:03d}'
        )

        return Prestamo.objects.create(
            usuario=usuario,
            ejemplar=ejemplar,
            fecha_prestamo=date(2026, 9, 1),
            fecha_limite=date(2026, 10, 1),
            fecha_devolucion=(
                date(2026, 9, 20)
                if devuelto
                else None
            )
        )

    def autenticar_bibliotecario(self):
        self.client.force_authenticate(
            user=self.bibliotecario
        )

    def datos_validos(self):
        return {
            'usuario_id': self.estudiante.usuario_id,
            'ejemplar_id': self.ejemplar.ejemplar_id,
        }

    # -----------------------------------------
    # Búsqueda de lectores
    # -----------------------------------------

    def test_buscar_lectores_por_nombre(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.get(
            self.url_busqueda,
            {'q': 'Estudiante'}
        )

        self.assertEqual(
            respuesta.status_code,
            200
        )

        self.assertEqual(
            respuesta.data['count'],
            1
        )

        usuario = respuesta.data['results'][0]

        self.assertEqual(
            usuario['usuario_id'],
            self.estudiante.usuario_id
        )

        self.assertEqual(
            usuario['rol']['nombre'],
            'estudiante'
        )

    def test_busqueda_excluye_bibliotecarios(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.get(
            self.url_busqueda,
            {'q': 'Bibliotecario'}
        )

        self.assertEqual(
            respuesta.status_code,
            200
        )

        self.assertEqual(
            respuesta.data['results'],
            []
        )

    def test_busqueda_rechaza_termino_vacio(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.get(
            self.url_busqueda,
            {'q': ''}
        )

        self.assertEqual(
            respuesta.status_code,
            400
        )

        self.assertIn(
            'q',
            respuesta.data
        )

    def test_busqueda_rechaza_limite_invalido(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.get(
            self.url_busqueda,
            {
                'q': 'Demo',
                'limite': 21,
            }
        )

        self.assertEqual(
            respuesta.status_code,
            400
        )

    # -----------------------------------------
    # Autenticación y permisos
    # -----------------------------------------

    def test_anonimo_no_accede_a_las_operaciones(self):
        operaciones = [
            (
                'get',
                self.url_busqueda,
                {'q': 'Demo'}
            ),
            (
                'get',
                self.url_elegibilidad,
                self.datos_validos()
            ),
            (
                'post',
                self.url_registro,
                self.datos_validos()
            ),
        ]

        for metodo, url, datos in operaciones:
            with self.subTest(
                metodo=metodo,
                url=url
            ):
                if metodo == 'get':
                    respuesta = self.client.get(
                        url,
                        datos
                    )
                else:
                    respuesta = self.client.post(
                        url,
                        datos,
                        format='json'
                    )

                self.assertEqual(
                    respuesta.status_code,
                    401
                )

        self.assertFalse(
            Prestamo.objects.exists()
        )

    def test_estudiante_no_administra_prestamos(self):
        self.client.force_authenticate(
            user=self.estudiante
        )

        operaciones = [
            (
                'get',
                self.url_busqueda,
                {'q': 'Demo'}
            ),
            (
                'get',
                self.url_elegibilidad,
                self.datos_validos()
            ),
            (
                'post',
                self.url_registro,
                self.datos_validos()
            ),
        ]

        for metodo, url, datos in operaciones:
            with self.subTest(
                metodo=metodo,
                url=url
            ):
                if metodo == 'get':
                    respuesta = self.client.get(
                        url,
                        datos
                    )
                else:
                    respuesta = self.client.post(
                        url,
                        datos,
                        format='json'
                    )

                self.assertEqual(
                    respuesta.status_code,
                    403
                )

        self.assertFalse(
            Prestamo.objects.exists()
        )

    def test_docente_no_puede_registrar_prestamos(self):
        self.client.force_authenticate(
            user=self.docente
        )

        respuesta = self.client.post(
            self.url_registro,
            self.datos_validos(),
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            403
        )

    # -----------------------------------------
    # Consulta de elegibilidad
    # -----------------------------------------

    def test_elegibilidad_correcta(self):
        self.autenticar_bibliotecario()

        with patch(
            'biblioteca.services.prestamos_service.timezone.localdate',
            return_value=date(2026, 10, 14)
        ):
            respuesta = self.client.get(
                self.url_elegibilidad,
                self.datos_validos()
            )

        self.assertEqual(
            respuesta.status_code,
            200
        )

        self.assertTrue(
            respuesta.data['elegible']
        )

        self.assertEqual(
            respuesta.data['motivos'],
            []
        )

        self.assertEqual(
            respuesta.data['prestamos_activos'],
            0
        )

        self.assertEqual(
            respuesta.data['limite_prestamos_activos'],
            5
        )

        self.assertEqual(
            respuesta.data['fecha_limite'],
            '2026-11-13'
        )

        self.assertEqual(
            respuesta.data['usuario']['usuario_id'],
            self.estudiante.usuario_id
        )

        self.assertEqual(
            respuesta.data['ejemplar']['ejemplar_id'],
            self.ejemplar.ejemplar_id
        )

    def test_elegibilidad_no_registra_prestamo(self):
        self.autenticar_bibliotecario()

        for _ in range(3):
            respuesta = self.client.get(
                self.url_elegibilidad,
                self.datos_validos()
            )

            self.assertEqual(
                respuesta.status_code,
                200
            )

        self.assertEqual(
            Prestamo.objects.count(),
            0
        )

    def test_elegibilidad_rechazada_por_ocupacion(self):
        self.autenticar_bibliotecario()

        Prestamo.objects.create(
            usuario=self.docente,
            ejemplar=self.ejemplar,
            fecha_prestamo=date(2026, 10, 1),
            fecha_limite=date(2026, 10, 31)
        )

        respuesta = self.client.get(
            self.url_elegibilidad,
            self.datos_validos()
        )

        self.assertEqual(
            respuesta.status_code,
            200
        )

        self.assertFalse(
            respuesta.data['elegible']
        )

        self.assertEqual(
            respuesta.data['motivos'][0]['codigo'],
            'EJEMPLAR_OCUPADO'
        )

    def test_elegibilidad_rechazada_por_rol(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.get(
            self.url_elegibilidad,
            {
                'usuario_id': self.bibliotecario.usuario_id,
                'ejemplar_id': self.ejemplar.ejemplar_id,
            }
        )

        self.assertEqual(
            respuesta.status_code,
            200
        )

        self.assertFalse(
            respuesta.data['elegible']
        )

        self.assertEqual(
            respuesta.data['motivos'][0]['codigo'],
            'ROL_NO_HABILITADO'
        )

    def test_elegibilidad_rechazada_por_mantenimiento(self):
        self.autenticar_bibliotecario()

        self.ejemplar.estado = 'MANTENIMIENTO'
        self.ejemplar.save(
            update_fields=['estado']
        )

        respuesta = self.client.get(
            self.url_elegibilidad,
            self.datos_validos()
        )

        self.assertEqual(
            respuesta.status_code,
            200
        )

        self.assertFalse(
            respuesta.data['elegible']
        )

        self.assertEqual(
            respuesta.data['motivos'][0]['codigo'],
            'EJEMPLAR_NO_DISPONIBLE'
        )

    def test_elegibilidad_valida_parametros(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.get(
            self.url_elegibilidad,
            {
                'usuario_id': 'abc',
                'ejemplar_id': self.ejemplar.ejemplar_id,
            }
        )

        self.assertEqual(
            respuesta.status_code,
            400
        )

        self.assertIn(
            'usuario_id',
            respuesta.data
        )

    def test_elegibilidad_usuario_inexistente(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.get(
            self.url_elegibilidad,
            {
                'usuario_id': 999999,
                'ejemplar_id': self.ejemplar.ejemplar_id,
            }
        )

        self.assertEqual(
            respuesta.status_code,
            404
        )

        self.assertEqual(
            respuesta.data['codigo'],
            'USUARIO_NO_ENCONTRADO'
        )

    # -----------------------------------------
    # Registro del préstamo
    # -----------------------------------------

    def test_registro_exitoso_de_estudiante(self):
        self.autenticar_bibliotecario()

        with patch(
            'biblioteca.services.prestamos_service.timezone.localdate',
            return_value=date(2026, 10, 14)
        ):
            respuesta = self.client.post(
                self.url_registro,
                self.datos_validos(),
                format='json'
            )

        self.assertEqual(
            respuesta.status_code,
            201
        )

        self.assertIn(
            'prestamo_id',
            respuesta.data
        )

        self.assertEqual(
            respuesta.data['fecha_prestamo'],
            '2026-10-14'
        )

        self.assertEqual(
            respuesta.data['fecha_limite'],
            '2026-11-13'
        )

        self.assertIsNone(
            respuesta.data['fecha_devolucion']
        )

        self.assertEqual(
            respuesta.data['usuario']['email'],
            self.estudiante.email
        )

        self.assertEqual(
            respuesta.data['ejemplar']['codigo_inventario'],
            'API-001'
        )

        self.assertEqual(
            Prestamo.objects.count(),
            1
        )

    def test_registro_exitoso_de_docente(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.post(
            self.url_registro,
            {
                'usuario_id': self.docente.usuario_id,
                'ejemplar_id': self.ejemplar.ejemplar_id,
            },
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            201
        )

        self.assertEqual(
            respuesta.data['usuario_id'],
            self.docente.usuario_id
        )

    def test_repetir_registro_devuelve_conflicto(self):
        self.autenticar_bibliotecario()

        primera = self.client.post(
            self.url_registro,
            self.datos_validos(),
            format='json'
        )

        segunda = self.client.post(
            self.url_registro,
            self.datos_validos(),
            format='json'
        )

        self.assertEqual(
            primera.status_code,
            201
        )

        self.assertEqual(
            segunda.status_code,
            409
        )

        self.assertEqual(
            segunda.data['codigo'],
            'EJEMPLAR_OCUPADO'
        )

        self.assertEqual(
            Prestamo.objects.count(),
            1
        )

    def test_rechaza_prestamo_a_bibliotecario(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.post(
            self.url_registro,
            {
                'usuario_id': self.bibliotecario.usuario_id,
                'ejemplar_id': self.ejemplar.ejemplar_id,
            },
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            409
        )

        self.assertEqual(
            respuesta.data['codigo'],
            'ROL_NO_HABILITADO'
        )

    def test_rechaza_usuario_con_limite_alcanzado(self):
        self.autenticar_bibliotecario()

        for _ in range(5):
            self.crear_prestamo_anterior(
                self.estudiante,
                devuelto=False
            )

        respuesta = self.client.post(
            self.url_registro,
            self.datos_validos(),
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            409
        )

        self.assertEqual(
            respuesta.data['codigo'],
            'LIMITE_PRESTAMOS'
        )

        self.assertEqual(
            Prestamo.objects.count(),
            5
        )

    def test_rechaza_usuario_con_adeudo(self):
        self.autenticar_bibliotecario()

        anterior = self.crear_prestamo_anterior(
            self.estudiante
        )

        Sancion.objects.create(
            prestamo=anterior,
            tipo='MULTA',
            monto=Decimal('25.00'),
            fecha_pago=None
        )

        respuesta = self.client.post(
            self.url_registro,
            self.datos_validos(),
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            409
        )

        self.assertEqual(
            respuesta.data['codigo'],
            'ADEUDO_PENDIENTE'
        )

    def test_rechaza_usuario_con_bloqueo(self):
        self.autenticar_bibliotecario()

        anterior = self.crear_prestamo_anterior(
            self.estudiante
        )

        Sancion.objects.create(
            prestamo=anterior,
            tipo='BLOQUEO',
            monto=Decimal('0.00'),
            fecha_inicio_bloqueo=date(2020, 1, 1),
            fecha_fin_bloqueo=date(2099, 1, 1)
        )

        respuesta = self.client.post(
            self.url_registro,
            self.datos_validos(),
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            409
        )

        self.assertEqual(
            respuesta.data['codigo'],
            'BLOQUEO_VIGENTE'
        )

    # -----------------------------------------
    # Validaciones de entrada y 404
    # -----------------------------------------

    def test_rechaza_datos_incompletos(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.post(
            self.url_registro,
            {
                'usuario_id': self.estudiante.usuario_id
            },
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            400
        )

        self.assertIn(
            'ejemplar_id',
            respuesta.data
        )

    def test_rechaza_campos_no_autorizados(self):
        self.autenticar_bibliotecario()

        datos = self.datos_validos()

        datos['fecha_limite'] = '2040-01-01'

        respuesta = self.client.post(
            self.url_registro,
            datos,
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            400
        )

        self.assertIn(
            'fecha_limite',
            respuesta.data
        )

        self.assertFalse(
            Prestamo.objects.exists()
        )

    def test_rechaza_identificadores_invalidos(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.post(
            self.url_registro,
            {
                'usuario_id': -1,
                'ejemplar_id': self.ejemplar.ejemplar_id,
            },
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            400
        )

    def test_usuario_inexistente_devuelve_404(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.post(
            self.url_registro,
            {
                'usuario_id': 999999,
                'ejemplar_id': self.ejemplar.ejemplar_id,
            },
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            404
        )

        self.assertEqual(
            respuesta.data['codigo'],
            'USUARIO_NO_ENCONTRADO'
        )

    def test_ejemplar_inexistente_devuelve_404(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.post(
            self.url_registro,
            {
                'usuario_id': self.estudiante.usuario_id,
                'ejemplar_id': 999999,
            },
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            404
        )

        self.assertEqual(
            respuesta.data['codigo'],
            'EJEMPLAR_NO_ENCONTRADO'
        )

    # -----------------------------------------
    # Integración con autenticación real
    # -----------------------------------------

    def test_registro_con_token_bearer_real(self):
        login = self.client.post(
            reverse('auth-login'),
            {
                'email': self.bibliotecario.email,
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

        respuesta = self.client.post(
            self.url_registro,
            self.datos_validos(),
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            201
        )

        self.assertEqual(
            Prestamo.objects.count(),
            1
        )

    def test_metodos_no_disponibles(self):
        self.autenticar_bibliotecario()

        respuesta = self.client.get(
            self.url_registro
        )

        self.assertEqual(
            respuesta.status_code,
            405
        )

        respuesta = self.client.post(
            self.url_elegibilidad,
            self.datos_validos(),
            format='json'
        )

        self.assertEqual(
            respuesta.status_code,
            405
        )