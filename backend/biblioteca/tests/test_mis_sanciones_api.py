from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from biblioteca.models import (
    Ejemplar,
    Libro,
    Prestamo,
    Rol,
    Sancion,
    TokenAcceso,
    Usuario,
)


class MisSancionesApiTests(APITestCase):
    """
    Pruebas automatizadas de la API para la consulta personal de sanciones
    (multas económicas y bloqueos) - Ticket 3.9 / Subtickets 3.9.2 y 3.9.3.
    """

    PASSWORD = 'PasswordSeguro123*'

    def setUp(self):
        self.hoy = date(2026, 10, 25)

        self.roles = {}
        for nombre, limite in [
            ('estudiante', 5),
            ('docente', 10),
            ('bibliotecario', 0),
        ]:
            self.roles[nombre] = Rol.objects.create(
                nombre=nombre,
                limite_prestamos_activos=limite,
            )

        self.estudiante_1 = self.crear_usuario(
            'Estudiante Uno',
            'estudiante1@test.local',
            'estudiante',
        )
        self.estudiante_2 = self.crear_usuario(
            'Estudiante Dos',
            'estudiante2@test.local',
            'estudiante',
        )
        self.docente = self.crear_usuario(
            'Docente Uno',
            'docente@test.local',
            'docente',
        )
        self.bibliotecario = self.crear_usuario(
            'Bibliotecario Test',
            'bibliotecario@test.local',
            'bibliotecario',
        )

        self.libro_1 = Libro.objects.create(
            titulo='Estructuras de Datos en Python',
            isbn='9780000000010',
        )
        self.libro_2 = Libro.objects.create(
            titulo='Ingeniería de Software Moderna',
            isbn='9780000000020',
        )

        self.ejemplar_1 = Ejemplar.objects.create(
            libro=self.libro_1,
            codigo_inventario='EDP-01',
            estado='ACTIVO',
        )
        self.ejemplar_2 = Ejemplar.objects.create(
            libro=self.libro_2,
            codigo_inventario='ISM-01',
            estado='ACTIVO',
        )

        self.url = reverse('sanciones-mias')

    def crear_usuario(self, nombre: str, email: str, rol: str) -> Usuario:
        usuario = Usuario(
            nombre=nombre,
            email=email,
            rol=self.roles[rol],
        )
        usuario.set_password(self.PASSWORD)
        usuario.save()
        return usuario

    def crear_prestamo(self, usuario: Usuario, ejemplar: Ejemplar, fecha_limite: date) -> Prestamo:
        return Prestamo.objects.create(
            usuario=usuario,
            ejemplar=ejemplar,
            fecha_prestamo=fecha_limite - timedelta(days=14),
            fecha_limite=fecha_limite,
        )

    def crear_multa(
        self,
        prestamo: Prestamo,
        monto: Decimal = Decimal('25.00'),
        fecha_pago: date | None = None,
    ) -> Sancion:
        return Sancion.objects.create(
            prestamo=prestamo,
            tipo='ECONOMICA',
            monto=monto,
            fecha_pago=fecha_pago,
        )

    def crear_bloqueo(
        self,
        prestamo: Prestamo,
        fecha_inicio: date,
        fecha_fin: date,
    ) -> Sancion:
        return Sancion.objects.create(
            prestamo=prestamo,
            tipo='BLOQUEO',
            fecha_inicio_bloqueo=fecha_inicio,
            fecha_fin_bloqueo=fecha_fin,
        )

    def obtener_token_bearer(self, email: str) -> str:
        resp = self.client.post(
            reverse('auth-login'),
            {'email': email, 'password': self.PASSWORD},
            format='json',
        )
        return resp.data['token']

    # -------------------------------------------------------------------------
    # 1. Estudiante con multas propias
    # -------------------------------------------------------------------------
    def test_estudiante_consulta_sus_propias_multas(self):
        self.client.force_authenticate(user=self.estudiante_1)
        prestamo = self.crear_prestamo(self.estudiante_1, self.ejemplar_1, self.hoy - timedelta(days=5))
        sancion = self.crear_multa(prestamo, Decimal('35.50'))

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 1)
        resultado = respuesta.data['results'][0]
        self.assertEqual(resultado['sancion_id'], sancion.sancion_id)
        self.assertEqual(resultado['prestamo_id'], prestamo.prestamo_id)
        self.assertEqual(resultado['tipo'], 'ECONOMICA')
        self.assertEqual(resultado['estado'], 'PENDIENTE')
        self.assertEqual(resultado['monto'], '35.50')
        self.assertEqual(resultado['libro']['titulo'], 'Estructuras de Datos en Python')
        self.assertEqual(resultado['ejemplar']['codigo_inventario'], 'EDP-01')

    # -------------------------------------------------------------------------
    # 2. Docente con bloqueos propios
    # -------------------------------------------------------------------------
    def test_docente_consulta_sus_propios_bloqueos(self):
        self.client.force_authenticate(user=self.docente)
        prestamo = self.crear_prestamo(self.docente, self.ejemplar_2, self.hoy - timedelta(days=40))
        bloqueo = self.crear_bloqueo(
            prestamo,
            fecha_inicio=self.hoy - timedelta(days=5),
            fecha_fin=self.hoy + timedelta(days=24),
        )

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 1)
        resultado = respuesta.data['results'][0]
        self.assertEqual(resultado['sancion_id'], bloqueo.sancion_id)
        self.assertEqual(resultado['tipo'], 'BLOQUEO')
        self.assertEqual(resultado['estado'], 'VIGENTE')
        self.assertIsNone(resultado['monto'])
        self.assertEqual(resultado['fecha_inicio_bloqueo'], (self.hoy - timedelta(days=5)).isoformat())
        self.assertEqual(resultado['fecha_fin_bloqueo'], (self.hoy + timedelta(days=24)).isoformat())

    # -------------------------------------------------------------------------
    # 3. Usuario sin sanciones
    # -------------------------------------------------------------------------
    def test_usuario_sin_sanciones_devuelve_lista_vacia_y_resumen_en_cero(self):
        self.client.force_authenticate(user=self.estudiante_1)

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 0)
        self.assertEqual(respuesta.data['results'], [])
        resumen = respuesta.data['resumen']
        self.assertEqual(resumen['total_sanciones'], 0)
        self.assertEqual(resumen['multas_pendientes'], 0)
        self.assertEqual(resumen['monto_total_adeudado'], '0.00')
        self.assertEqual(resumen['bloqueos_vigentes'], 0)

    # -------------------------------------------------------------------------
    # 4. Multas pendientes y pagadas
    # -------------------------------------------------------------------------
    def test_distincion_entre_multa_pendiente_y_pagada(self):
        self.client.force_authenticate(user=self.estudiante_1)
        p1 = self.crear_prestamo(self.estudiante_1, self.ejemplar_1, self.hoy - timedelta(days=10))
        p2 = self.crear_prestamo(self.estudiante_1, self.ejemplar_2, self.hoy - timedelta(days=20))

        s_pendiente = self.crear_multa(p1, Decimal('15.00'), fecha_pago=None)
        s_pagada = self.crear_multa(p2, Decimal('20.00'), fecha_pago=self.hoy - timedelta(days=2))

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 2)

        resultados = {r['sancion_id']: r for r in respuesta.data['results']}
        self.assertEqual(resultados[s_pendiente.sancion_id]['estado'], 'PENDIENTE')
        self.assertIsNone(resultados[s_pendiente.sancion_id]['fecha_pago'])

        self.assertEqual(resultados[s_pagada.sancion_id]['estado'], 'PAGADA')
        self.assertEqual(
            resultados[s_pagada.sancion_id]['fecha_pago'],
            (self.hoy - timedelta(days=2)).isoformat(),
        )

        resumen = respuesta.data['resumen']
        self.assertEqual(resumen['total_sanciones'], 2)
        self.assertEqual(resumen['multas_pendientes'], 1)
        self.assertEqual(resumen['monto_total_adeudado'], '15.00')

    # -------------------------------------------------------------------------
    # 5. Bloqueos programados, vigentes y concluidos (casos de borde temporal)
    # -------------------------------------------------------------------------
    def test_estados_y_limites_temporales_exactos_de_bloqueos(self):
        self.client.force_authenticate(user=self.docente)
        p = self.crear_prestamo(self.docente, self.ejemplar_1, self.hoy)

        # 1. Programado: fecha_inicio posterior a hoy
        b_programado = self.crear_bloqueo(p, self.hoy + timedelta(days=1), self.hoy + timedelta(days=30))
        # 2. Vigente en inicio exacto (inicio == hoy)
        b_vigente_inicio = self.crear_bloqueo(p, self.hoy, self.hoy + timedelta(days=10))
        # 3. Vigente en fin exacto (fin == hoy)
        b_vigente_fin = self.crear_bloqueo(p, self.hoy - timedelta(days=10), self.hoy)
        # 4. Vigente de un solo día (inicio == fin == hoy)
        b_vigente_mismo_dia = self.crear_bloqueo(p, self.hoy, self.hoy)
        # 5. Concluido exacto (fin anterior a hoy)
        b_concluido = self.crear_bloqueo(p, self.hoy - timedelta(days=20), self.hoy - timedelta(days=1))

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        resultados = {r['sancion_id']: r for r in respuesta.data['results']}
        self.assertEqual(resultados[b_programado.sancion_id]['estado'], 'PROGRAMADO')
        self.assertEqual(resultados[b_vigente_inicio.sancion_id]['estado'], 'VIGENTE')
        self.assertEqual(resultados[b_vigente_fin.sancion_id]['estado'], 'VIGENTE')
        self.assertEqual(resultados[b_vigente_mismo_dia.sancion_id]['estado'], 'VIGENTE')
        self.assertEqual(resultados[b_concluido.sancion_id]['estado'], 'CONCLUIDO')

        self.assertEqual(respuesta.data['resumen']['bloqueos_vigentes'], 3)

    # -------------------------------------------------------------------------
    # 6. Cálculo correcto de importes decimales
    # -------------------------------------------------------------------------
    def test_calculo_correcto_de_importes_decimales(self):
        self.client.force_authenticate(user=self.estudiante_1)
        p1 = self.crear_prestamo(self.estudiante_1, self.ejemplar_1, self.hoy)
        p2 = self.crear_prestamo(self.estudiante_1, self.ejemplar_2, self.hoy)

        self.crear_multa(p1, Decimal('12.75'))
        self.crear_multa(p2, Decimal('3.25'))

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['resumen']['monto_total_adeudado'], '16.00')

    # -------------------------------------------------------------------------
    # 7. Filtrado por tipo y estado
    # -------------------------------------------------------------------------
    def test_filtrado_por_tipo_economicas(self):
        self.client.force_authenticate(user=self.estudiante_1)
        p = self.crear_prestamo(self.estudiante_1, self.ejemplar_1, self.hoy)
        self.crear_multa(p, Decimal('10.00'))
        self.crear_bloqueo(p, self.hoy - timedelta(days=2), self.hoy + timedelta(days=27))

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            respuesta = self.client.get(f"{self.url}?tipo=economicas")

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(respuesta.data['results'][0]['tipo'], 'ECONOMICA')

    def test_filtrado_por_tipo_bloqueos(self):
        self.client.force_authenticate(user=self.estudiante_1)
        p = self.crear_prestamo(self.estudiante_1, self.ejemplar_1, self.hoy)
        self.crear_multa(p, Decimal('10.00'))
        self.crear_bloqueo(p, self.hoy - timedelta(days=2), self.hoy + timedelta(days=27))

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            respuesta = self.client.get(f"{self.url}?tipo=bloqueos")

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(respuesta.data['results'][0]['tipo'], 'BLOQUEO')

    def test_filtrado_por_estado_multas(self):
        self.client.force_authenticate(user=self.estudiante_1)
        p = self.crear_prestamo(self.estudiante_1, self.ejemplar_1, self.hoy)
        self.crear_multa(p, Decimal('10.00'), fecha_pago=None)
        self.crear_multa(p, Decimal('15.00'), fecha_pago=self.hoy)

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            resp_pend = self.client.get(f"{self.url}?tipo=economicas&estado=pendientes")
            resp_pag = self.client.get(f"{self.url}?tipo=economicas&estado=pagadas")

        self.assertEqual(resp_pend.data['count'], 1)
        self.assertEqual(resp_pend.data['results'][0]['estado'], 'PENDIENTE')

        self.assertEqual(resp_pag.data['count'], 1)
        self.assertEqual(resp_pag.data['results'][0]['estado'], 'PAGADA')

    # -------------------------------------------------------------------------
    # 8. Rechazo de combinaciones contradictorias
    # -------------------------------------------------------------------------
    def test_rechaza_combinacion_contradictoria_multa_con_estado_vigente(self):
        self.client.force_authenticate(user=self.estudiante_1)
        respuesta = self.client.get(f"{self.url}?tipo=economicas&estado=vigentes")
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('estado', respuesta.data)

    def test_rechaza_combinacion_contradictoria_bloqueo_con_estado_pendiente(self):
        self.client.force_authenticate(user=self.estudiante_1)
        respuesta = self.client.get(f"{self.url}?tipo=bloqueos&estado=pendientes")
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('estado', respuesta.data)

    # -------------------------------------------------------------------------
    # 9. Paginación y límites
    # -------------------------------------------------------------------------
    def test_paginacion_de_sanciones(self):
        self.client.force_authenticate(user=self.estudiante_1)
        p = self.crear_prestamo(self.estudiante_1, self.ejemplar_1, self.hoy)
        for i in range(12):
            self.crear_multa(p, Decimal('5.00'))

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            resp_p1 = self.client.get(f"{self.url}?page=1&page_size=5")
            resp_p2 = self.client.get(f"{self.url}?page=2&page_size=5")

        self.assertEqual(resp_p1.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_p1.data['count'], 12)
        self.assertEqual(len(resp_p1.data['results']), 5)
        self.assertIsNotNone(resp_p1.data['next'])

        self.assertEqual(resp_p2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_p2.data['results']), 5)

        ids_p1 = [r['sancion_id'] for r in resp_p1.data['results']]
        ids_p2 = [r['sancion_id'] for r in resp_p2.data['results']]
        self.assertEqual(len(set(ids_p1) & set(ids_p2)), 0)

    def test_paginacion_con_parametros_invalidos(self):
        self.client.force_authenticate(user=self.estudiante_1)

        # page=0 o negativo
        r_page_0 = self.client.get(f"{self.url}?page=0")
        self.assertEqual(r_page_0.status_code, status.HTTP_400_BAD_REQUEST)

        # page_size=0 o negativo
        r_size_0 = self.client.get(f"{self.url}?page_size=0")
        self.assertEqual(r_size_0.status_code, status.HTTP_400_BAD_REQUEST)

        # page_size superior al límite máximo (50)
        r_size_max = self.client.get(f"{self.url}?page_size=51")
        self.assertEqual(r_size_max.status_code, status.HTTP_400_BAD_REQUEST)

        # page inexistente devuelve 404
        r_page_404 = self.client.get(f"{self.url}?page=999")
        self.assertEqual(r_page_404.status_code, status.HTTP_404_NOT_FOUND)

    # -------------------------------------------------------------------------
    # 10. Resumen independiente de filtros y paginación
    # -------------------------------------------------------------------------
    def test_resumen_es_global_e_independiente_de_filtros_y_paginacion(self):
        self.client.force_authenticate(user=self.estudiante_1)
        p = self.crear_prestamo(self.estudiante_1, self.ejemplar_1, self.hoy)
        self.crear_multa(p, Decimal('50.00'), fecha_pago=None)
        self.crear_bloqueo(p, self.hoy - timedelta(days=2), self.hoy + timedelta(days=27))

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            respuesta = self.client.get(f"{self.url}?tipo=bloqueos")

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(len(respuesta.data['results']), 1)
        self.assertEqual(respuesta.data['results'][0]['tipo'], 'BLOQUEO')

        resumen = respuesta.data['resumen']
        self.assertEqual(resumen['total_sanciones'], 2)
        self.assertEqual(resumen['multas_pendientes'], 1)
        self.assertEqual(resumen['monto_total_adeudado'], '50.00')
        self.assertEqual(resumen['bloqueos_vigentes'], 1)

    # -------------------------------------------------------------------------
    # 11. Seguridad: Anónimo, token inválido, expirado, revocado y bibliotecario
    # -------------------------------------------------------------------------
    def test_usuario_anonimo_recibe_401(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_invalido_recibe_401(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token_invalido_xyz')
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_expirado_recibe_401(self):
        token_str = self.obtener_token_bearer(self.estudiante_1.email)
        token_obj = TokenAcceso.objects.get(usuario=self.estudiante_1)
        token_obj.expira_en = timezone.now() - timedelta(hours=1)
        token_obj.save()

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_str}')
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_revocado_recibe_401(self):
        token_str = self.obtener_token_bearer(self.estudiante_1.email)
        token_obj = TokenAcceso.objects.get(usuario=self.estudiante_1)
        token_obj.revocado_en = timezone.now()
        token_obj.save()

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_str}')
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_bibliotecario_recibe_403_en_endpoint_personal(self):
        self.client.force_authenticate(user=self.bibliotecario)
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    # -------------------------------------------------------------------------
    # 12. Manipulación de usuario_id y parámetros no autorizados rechazada
    # -------------------------------------------------------------------------
    def test_intento_de_inyeccion_de_usuario_id_es_rechazado_por_campos_permitidos(self):
        self.client.force_authenticate(user=self.estudiante_1)
        respuesta = self.client.get(f"{self.url}?usuario_id={self.estudiante_2.usuario_id}")
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)

    def test_parametros_desconocidos_son_rechazados(self):
        self.client.force_authenticate(user=self.estudiante_1)
        r1 = self.client.get(f"{self.url}?prestamo_id=10")
        self.assertEqual(r1.status_code, status.HTTP_400_BAD_REQUEST)

        r2 = self.client.get(f"{self.url}?prestamo__usuario_id=10")
        self.assertEqual(r2.status_code, status.HTTP_400_BAD_REQUEST)

        r3 = self.client.get(f"{self.url}?filtro_arbitrario=hack")
        self.assertEqual(r3.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------------------
    # 13. Aislamiento estricto: Estudiante frente a Estudiante y Estudiante frente a Docente
    # -------------------------------------------------------------------------
    def test_aislamiento_estricto_entre_estudiantes(self):
        p1 = self.crear_prestamo(self.estudiante_1, self.ejemplar_1, self.hoy)
        s1 = self.crear_multa(p1, Decimal('100.00'))

        p2 = self.crear_prestamo(self.estudiante_2, self.ejemplar_2, self.hoy)
        s2 = self.crear_multa(p2, Decimal('200.00'))

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            self.client.force_authenticate(user=self.estudiante_1)
            resp1 = self.client.get(self.url)

            self.client.force_authenticate(user=self.estudiante_2)
            resp2 = self.client.get(self.url)

        self.assertEqual(resp1.data['count'], 1)
        self.assertEqual(resp1.data['results'][0]['sancion_id'], s1.sancion_id)
        self.assertEqual(resp1.data['resumen']['monto_total_adeudado'], '100.00')

        self.assertEqual(resp2.data['count'], 1)
        self.assertEqual(resp2.data['results'][0]['sancion_id'], s2.sancion_id)
        self.assertEqual(resp2.data['resumen']['monto_total_adeudado'], '200.00')

    def test_aislamiento_estricto_entre_estudiante_y_docente(self):
        # Estudiante 1 tiene multa económica
        p_est = self.crear_prestamo(self.estudiante_1, self.ejemplar_1, self.hoy)
        s_est = self.crear_multa(p_est, Decimal('75.00'))

        # Docente tiene bloqueo vigente
        p_doc = self.crear_prestamo(self.docente, self.ejemplar_2, self.hoy)
        s_doc = self.crear_bloqueo(p_doc, self.hoy - timedelta(days=2), self.hoy + timedelta(days=28))

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            # Consulta Estudiante
            self.client.force_authenticate(user=self.estudiante_1)
            resp_est = self.client.get(self.url)

            # Consulta Docente
            self.client.force_authenticate(user=self.docente)
            resp_doc = self.client.get(self.url)

        # Estudiante solo ve su multa
        self.assertEqual(resp_est.data['count'], 1)
        self.assertEqual(resp_est.data['results'][0]['sancion_id'], s_est.sancion_id)
        self.assertEqual(resp_est.data['results'][0]['tipo'], 'ECONOMICA')
        self.assertEqual(resp_est.data['resumen']['monto_total_adeudado'], '75.00')
        self.assertEqual(resp_est.data['resumen']['bloqueos_vigentes'], 0)

        # Docente solo ve su bloqueo
        self.assertEqual(resp_doc.data['count'], 1)
        self.assertEqual(resp_doc.data['results'][0]['sancion_id'], s_doc.sancion_id)
        self.assertEqual(resp_doc.data['results'][0]['tipo'], 'BLOQUEO')
        self.assertEqual(resp_doc.data['resumen']['monto_total_adeudado'], '0.00')
        self.assertEqual(resp_doc.data['resumen']['bloqueos_vigentes'], 1)

    # -------------------------------------------------------------------------
    # 14. Confirmación de que GET no realiza escrituras ni cambios de estado
    # -------------------------------------------------------------------------
    def test_consulta_get_no_modifica_la_base_de_datos(self):
        self.client.force_authenticate(user=self.estudiante_1)
        p = self.crear_prestamo(self.estudiante_1, self.ejemplar_1, self.hoy)
        self.crear_multa(p, Decimal('30.00'))

        conteo_antes = Sancion.objects.count()
        sancion_antes = Sancion.objects.first()

        with patch('biblioteca.services.mis_sanciones_service.timezone.localdate', return_value=self.hoy):
            respuesta = self.client.get(self.url)

        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(Sancion.objects.count(), conteo_antes)

        sancion_despues = Sancion.objects.first()
        self.assertEqual(sancion_antes.fecha_pago, sancion_despues.fecha_pago)
        self.assertEqual(sancion_antes.monto, sancion_despues.monto)

    # -------------------------------------------------------------------------
    # 15. Métodos HTTP no permitidos
    # -------------------------------------------------------------------------
    def test_metodos_modificatorios_no_permitidos(self):
        self.client.force_authenticate(user=self.estudiante_1)

        resp_post = self.client.post(self.url, {})
        resp_put = self.client.put(self.url, {})
        resp_patch = self.client.patch(self.url, {})
        resp_del = self.client.delete(self.url)

        self.assertEqual(resp_post.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(resp_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(resp_patch.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(resp_del.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    # -------------------------------------------------------------------------
    # 16. Regresión de resolución de ruta: aislamiento de vistas de 3.9 y 3.8
    # -------------------------------------------------------------------------
    def test_resolucion_de_ruta_apunta_a_mis_sanciones_view_especializada(self):
        """Garantiza que /api/sanciones/mias/ resuelva a mis_sanciones_views y no a sanciones_views."""
        from django.urls import resolve
        match = resolve('/api/sanciones/mias/')
        self.assertEqual(match.url_name, 'sanciones-mias')
        self.assertEqual(
            match.func.view_class.__module__,
            'biblioteca.presentation.mis_sanciones_views',
        )

    def test_ausencia_de_rutas_duplicadas_para_sanciones_mias(self):
        """Verifica que el patrón sanciones/mias/ esté registrado exactamente una vez en urlpatterns."""
        from django.urls import get_resolver
        resolver = get_resolver()

        def buscar_patrones(patterns, prefix=''):
            coincidencias = []
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    coincidencias.extend(buscar_patrones(pattern.url_patterns, prefix + str(pattern.pattern)))
                else:
                    ruta_completa = prefix + str(pattern.pattern)
                    if 'sanciones/mias/' in ruta_completa:
                        coincidencias.append(pattern)
            return coincidencias

        rutas_sanciones_mias = buscar_patrones(resolver.url_patterns)
        self.assertEqual(
            len(rutas_sanciones_mias),
            1,
            f'Se esperaba 1 registro de sanciones/mias/, pero se encontraron {len(rutas_sanciones_mias)}',
        )
