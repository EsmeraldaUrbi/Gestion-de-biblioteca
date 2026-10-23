from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from biblioteca.models import Ejemplar, Libro, Prestamo, Rol, Sancion, Usuario


class SancionesApiTests(APITestCase):
    def setUp(self):
        self.hoy = timezone.localdate()
        self.rol_estudiante = Rol.objects.create(
            nombre='estudiante', limite_prestamos_activos=5,
        )
        self.rol_bibliotecario = Rol.objects.create(
            nombre='bibliotecario', limite_prestamos_activos=0,
        )
        self.lector = self.crear_usuario(
            'Lector Uno', 'lector.uno@sanciones.test', self.rol_estudiante,
        )
        self.otro_lector = self.crear_usuario(
            'Lector Dos', 'lector.dos@sanciones.test', self.rol_estudiante,
        )
        self.bibliotecario = self.crear_usuario(
            'Bibliotecario', 'bibliotecario@sanciones.test', self.rol_bibliotecario,
        )
        libro = Libro.objects.create(
            titulo='Sanciones de prueba', isbn='9780000000099',
        )
        self.ejemplar = Ejemplar.objects.create(
            libro=libro, codigo_inventario='SAN-001', estado='ACTIVO',
        )

    def crear_usuario(self, nombre, email, rol):
        usuario = Usuario(nombre=nombre, email=email, rol=rol)
        usuario.set_password('ClaveSegura123*')
        usuario.save()
        return usuario

    def crear_prestamo(self, usuario=None):
        return Prestamo.objects.create(
            usuario=usuario or self.lector,
            ejemplar=self.ejemplar,
            fecha_prestamo=self.hoy - timedelta(days=10),
            fecha_limite=self.hoy - timedelta(days=3),
            fecha_devolucion=self.hoy,
        )

    def crear_multa(self, usuario=None, monto='15.00', pagada=False):
        return Sancion.objects.create(
            prestamo=self.crear_prestamo(usuario),
            tipo='ECONOMICA',
            monto=Decimal(monto),
            fecha_pago=self.hoy if pagada else None,
        )

    def crear_bloqueo(self, usuario=None):
        return Sancion.objects.create(
            prestamo=self.crear_prestamo(usuario),
            tipo='BLOQUEO',
            monto=None,
            fecha_inicio_bloqueo=self.hoy - timedelta(days=1),
            fecha_fin_bloqueo=self.hoy + timedelta(days=4),
        )

    def autenticar_bibliotecario(self):
        self.client.force_authenticate(user=self.bibliotecario)

    def test_bibliotecario_registra_pago_total_de_multa_pendiente(self):
        multa = self.crear_multa()
        otra_multa = self.crear_multa(monto='20.00')
        bloqueo = self.crear_bloqueo()
        self.autenticar_bibliotecario()

        respuesta = self.client.post(
            reverse('sanciones-pago', kwargs={'sancion_id': multa.sancion_id}),
            {}, format='json',
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['estado'], 'PAGADA')
        multa.refresh_from_db()
        otra_multa.refresh_from_db()
        bloqueo.refresh_from_db()
        self.assertEqual(multa.fecha_pago, self.hoy)
        self.assertIsNone(otra_multa.fecha_pago)
        self.assertIsNone(bloqueo.fecha_pago)

    def test_pago_duplicado_es_rechazado(self):
        multa = self.crear_multa(pagada=True)
        self.autenticar_bibliotecario()

        respuesta = self.client.post(
            reverse('sanciones-pago', kwargs={'sancion_id': multa.sancion_id}),
            {}, format='json',
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.data['codigo'], 'SANCION_YA_PAGADA')

    def test_un_bloqueo_no_puede_pagarse(self):
        bloqueo = self.crear_bloqueo()
        self.autenticar_bibliotecario()

        respuesta = self.client.post(
            reverse('sanciones-pago', kwargs={'sancion_id': bloqueo.sancion_id}),
            {}, format='json',
        )

        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.data['codigo'], 'SANCION_PAGO_NO_PERMITIDO')

    def test_listado_administrativo_filtra_y_resume_sanciones(self):
        self.crear_multa()
        self.crear_multa(pagada=True)
        self.crear_bloqueo()
        self.autenticar_bibliotecario()

        respuesta = self.client.get(reverse('sanciones-list'), {'estado': 'pendiente'})

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(respuesta.data['results'][0]['estado'], 'PENDIENTE')
        self.assertEqual(respuesta.data['resumen']['multas_pendientes'], 1)
        self.assertEqual(Decimal(respuesta.data['resumen']['monto_pendiente']), Decimal('15.00'))

    def test_lector_solo_consulta_sus_propias_sanciones(self):
        propia = self.crear_multa()
        ajena = self.crear_multa(usuario=self.otro_lector)
        self.client.force_authenticate(user=self.lector)

        respuesta = self.client.get(reverse('sanciones-mias'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(respuesta.data['results'][0]['sancion_id'], propia.sancion_id)
        self.assertNotEqual(respuesta.data['results'][0]['sancion_id'], ajena.sancion_id)

    def test_lector_no_puede_consultar_ni_pagar_administrativamente(self):
        multa = self.crear_multa()
        self.client.force_authenticate(user=self.lector)

        listado = self.client.get(reverse('sanciones-list'))
        pago = self.client.post(
            reverse('sanciones-pago', kwargs={'sancion_id': multa.sancion_id}),
            {}, format='json',
        )

        self.assertEqual(listado.status_code, 403)
        self.assertEqual(pago.status_code, 403)
