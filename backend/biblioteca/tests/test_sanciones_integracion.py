from datetime import timedelta
from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from biblioteca.models import Ejemplar, Libro, Prestamo, Rol, Sancion, Usuario


class SancionesIntegracionTests(APITestCase):
    """Flujos 3.8: pago puntual y preservación de restricciones restantes."""

    def setUp(self):
        self.hoy = timezone.localdate()
        rol_lector = Rol.objects.create(
            nombre='estudiante', limite_prestamos_activos=5,
        )
        rol_bibliotecario = Rol.objects.create(
            nombre='bibliotecario', limite_prestamos_activos=0,
        )
        self.lector = Usuario.objects.create(
            nombre='Lector Integración',
            email='lector.integracion@sanciones.test',
            rol=rol_lector,
            contrasena_hash='no-usada',
        )
        self.bibliotecario = Usuario.objects.create(
            nombre='Bibliotecario Integración',
            email='bibliotecario.integracion@sanciones.test',
            rol=rol_bibliotecario,
            contrasena_hash='no-usada',
        )
        libro = Libro.objects.create(
            titulo='Integración de sanciones', isbn='9780000000088',
        )
        self.ejemplar = Ejemplar.objects.create(
            libro=libro, codigo_inventario='SAN-INT-001', estado='ACTIVO',
        )

    def crear_sancion(self, tipo, monto=None):
        prestamo = Prestamo.objects.create(
            usuario=self.lector,
            ejemplar=self.ejemplar,
            fecha_prestamo=self.hoy - timedelta(days=20),
            fecha_limite=self.hoy - timedelta(days=8),
            fecha_devolucion=self.hoy - timedelta(days=2),
        )
        if tipo == 'ECONOMICA':
            return Sancion.objects.create(
                prestamo=prestamo,
                tipo=tipo,
                monto=Decimal(monto),
                fecha_pago=None,
            )
        return Sancion.objects.create(
            prestamo=prestamo,
            tipo=tipo,
            monto=None,
            fecha_inicio_bloqueo=self.hoy - timedelta(days=1),
            fecha_fin_bloqueo=self.hoy + timedelta(days=5),
        )

    def test_pago_individual_no_salda_otros_adeudos_ni_bloqueos(self):
        multa_pagada = self.crear_sancion('ECONOMICA', '15.00')
        multa_pendiente = self.crear_sancion('ECONOMICA', '20.00')
        bloqueo = self.crear_sancion('BLOQUEO')

        self.client.force_authenticate(user=self.bibliotecario)
        pago = self.client.post(
            reverse('sanciones-pago', kwargs={'sancion_id': multa_pagada.sancion_id}),
            {}, format='json',
        )
        self.assertEqual(pago.status_code, 200)
        self.assertEqual(pago.data['estado'], 'PAGADA')

        # La elegibilidad continúa restringida por la multa distinta.
        elegibilidad = self.client.get(
            reverse('prestamos-elegibilidad'),
            {
                'usuario_id': self.lector.usuario_id,
                'ejemplar_id': self.ejemplar.ejemplar_id,
            },
        )
        self.assertEqual(elegibilidad.status_code, 200)
        self.assertFalse(elegibilidad.data['elegible'])
        self.assertEqual(
            elegibilidad.data['motivos'][0]['codigo'],
            'ADEUDO_PENDIENTE',
        )

        multa_pagada.refresh_from_db()
        multa_pendiente.refresh_from_db()
        bloqueo.refresh_from_db()
        self.assertEqual(multa_pagada.fecha_pago, self.hoy)
        self.assertIsNone(multa_pendiente.fecha_pago)
        self.assertIsNone(bloqueo.fecha_pago)
        self.assertGreaterEqual(bloqueo.fecha_fin_bloqueo, self.hoy)

        # El lector ve el cambio sin poder consultar datos ajenos.
        self.client.force_authenticate(user=self.lector)
        consulta_personal = self.client.get(reverse('sanciones-mias'))
        self.assertEqual(consulta_personal.status_code, 200)
        estados = {
            item['sancion_id']: item['estado']
            for item in consulta_personal.data['results']
        }
        self.assertEqual(estados[multa_pagada.sancion_id], 'PAGADA')
        self.assertEqual(estados[multa_pendiente.sancion_id], 'PENDIENTE')
        self.assertEqual(estados[bloqueo.sancion_id], 'VIGENTE')

    def test_reintento_de_pago_no_altera_el_registro_original(self):
        multa = self.crear_sancion('ECONOMICA', '30.00')
        self.client.force_authenticate(user=self.bibliotecario)
        url = reverse('sanciones-pago', kwargs={'sancion_id': multa.sancion_id})

        primera = self.client.post(url, {}, format='json')
        segunda = self.client.post(url, {}, format='json')

        self.assertEqual(primera.status_code, 200)
        self.assertEqual(segunda.status_code, 400)
        self.assertEqual(segunda.data['codigo'], 'SANCION_YA_PAGADA')
        multa.refresh_from_db()
        self.assertEqual(multa.fecha_pago, self.hoy)
