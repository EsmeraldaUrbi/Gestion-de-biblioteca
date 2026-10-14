from datetime import date
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from biblioteca.models import (
    Ejemplar,
    EstadoEjemplar,
    Libro,
    Prestamo,
    Rol,
    Usuario,
)


class EjemplaresApiTests(APITestCase):
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

        self.libro1 = Libro.objects.create(
            titulo='Don Quijote de la Mancha',
            isbn='9788424116286',
            fecha_publicacion=date(1605, 1, 16)
        )
        self.libro2 = Libro.objects.create(
            titulo='Cien Años de Soledad',
            isbn='9780307474728',
            fecha_publicacion=date(1967, 5, 30)
        )

        self.url_lista = reverse('ejemplares-list-create')

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

    def url_detalle(self, ejemplar_id):
        return reverse('ejemplares-detail', kwargs={'ejemplar_id': ejemplar_id})

    def crear_prestamo(self, ejemplar, devuelto=False):
        return Prestamo.objects.create(
            usuario=self.estudiante,
            ejemplar=ejemplar,
            fecha_prestamo=date(2025, 1, 1),
            fecha_limite=date(2025, 1, 31),
            fecha_devolucion=date(2025, 1, 15) if devuelto else None
        )

    # --- 1. Autenticación y Autorización por Rol ---

    def test_anonimo_es_rechazado_en_lista(self):
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
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'ANON-001'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_estudiante_es_rechazado_en_registro(self):
        self.autenticar(self.estudiante)
        respuesta = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'EST-001'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_estudiante_es_rechazado_en_detalle(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'DET-001'},
            format='json'
        )
        ej_id = res.data['ejemplar_id']

        self.autenticar(self.estudiante)
        respuesta = self.client.get(self.url_detalle(ej_id))
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    def test_estudiante_es_rechazado_en_modificacion_estado(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'MOD-001'},
            format='json'
        )
        ej_id = res.data['ejemplar_id']

        self.autenticar(self.estudiante)
        respuesta = self.client.patch(
            self.url_detalle(ej_id),
            {'estado': 'MANTENIMIENTO'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_403_FORBIDDEN)

    # --- 2. Registro Correcto y Código Duplicado (RN-02) ---

    def test_bibliotecario_registra_ejemplar_exitoso(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'libro_id': self.libro1.libro_id,
            'codigo_inventario': 'QUIJ-001'
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')

        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        data = respuesta.data
        self.assertIn('ejemplar_id', data)
        self.assertEqual(data['codigo_inventario'], 'QUIJ-001')
        self.assertEqual(data['estado'], 'ACTIVO')
        self.assertEqual(data['libro_id'], self.libro1.libro_id)
        self.assertEqual(data['libro']['titulo'], 'Don Quijote de la Mancha')

    def test_registro_rechaza_codigo_duplicado_rn02(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'libro_id': self.libro1.libro_id,
            'codigo_inventario': 'DUP-001'
        }
        res1 = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        res2 = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('codigo_inventario', res2.data)

    # --- 3. Libro Inexistente y Validación de Entradas ---

    def test_registro_rechaza_libro_inexistente(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'libro_id': 99999,
            'codigo_inventario': 'NOLIB-001'
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('libro_id', respuesta.data)

    def test_registro_rechaza_codigo_invalido(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'libro_id': self.libro1.libro_id,
            'codigo_inventario': '   '
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('codigo_inventario', respuesta.data)

    # --- 4. Estados Inválidos y Estado por Defecto (RN-03) ---

    def test_registro_asigna_activo_por_defecto_rn03(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'libro_id': self.libro1.libro_id,
            'codigo_inventario': 'DEF-001'
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['estado'], EstadoEjemplar.ACTIVO)

    def test_registro_con_estado_explicito_valido(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'libro_id': self.libro1.libro_id,
            'codigo_inventario': 'MNT-001',
            'estado': 'MANTENIMIENTO'
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(respuesta.data['estado'], EstadoEjemplar.MANTENIMIENTO)

    def test_registro_rechaza_estado_invalido_rn03(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'libro_id': self.libro1.libro_id,
            'codigo_inventario': 'BAD-001',
            'estado': 'EXTRAVIADO'
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('estado', respuesta.data)

    # --- 5. Listado, Filtros y Detalle ---

    def test_bibliotecario_lista_ejemplares_con_paginacion(self):
        self.autenticar(self.bibliotecario)
        for i in range(3):
            self.client.post(
                self.url_lista,
                {'libro_id': self.libro1.libro_id, 'codigo_inventario': f'PAG-00{i}'},
                format='json'
            )

        respuesta = self.client.get(self.url_lista)
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertIn('count', respuesta.data)
        self.assertIn('results', respuesta.data)
        self.assertEqual(respuesta.data['count'], 3)

    def test_listar_ejemplares_filtrado_por_libro(self):
        self.autenticar(self.bibliotecario)
        self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'FIL-L1'},
            format='json'
        )
        self.client.post(
            self.url_lista,
            {'libro_id': self.libro2.libro_id, 'codigo_inventario': 'FIL-L2'},
            format='json'
        )

        respuesta = self.client.get(f'{self.url_lista}?libro_id={self.libro1.libro_id}')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(respuesta.data['results'][0]['codigo_inventario'], 'FIL-L1')

    def test_listar_ejemplares_filtrado_por_estado(self):
        self.autenticar(self.bibliotecario)
        self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'F-ACT', 'estado': 'ACTIVO'},
            format='json'
        )
        self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'F-MNT', 'estado': 'MANTENIMIENTO'},
            format='json'
        )

        respuesta = self.client.get(f'{self.url_lista}?estado=MANTENIMIENTO')
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(respuesta.data['results'][0]['codigo_inventario'], 'F-MNT')

    def test_consultar_detalle_ejemplar_existente(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'DET-002'},
            format='json'
        )
        ej_id = res.data['ejemplar_id']

        respuesta = self.client.get(self.url_detalle(ej_id))
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['ejemplar_id'], ej_id)
        self.assertEqual(respuesta.data['codigo_inventario'], 'DET-002')
        self.assertEqual(respuesta.data['libro']['titulo'], self.libro1.titulo)

    def test_consultar_detalle_ejemplar_inexistente(self):
        self.autenticar(self.bibliotecario)
        respuesta = self.client.get(self.url_detalle(99999))
        self.assertEqual(respuesta.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(respuesta.data.get('detail'), 'Ejemplar no encontrado.')

    # --- 6. Cambios de Estado Válidos y Reactivación Provisional ---

    def test_patch_cambiar_estado_a_mantenimiento(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'CHG-001'},
            format='json'
        )
        ej_id = res.data['ejemplar_id']

        respuesta = self.client.patch(
            self.url_detalle(ej_id),
            {'estado': 'MANTENIMIENTO'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['estado'], 'MANTENIMIENTO')

    def test_patch_cambiar_estado_a_baja_sin_prestamo_activo(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'BAJA-001'},
            format='json'
        )
        ej_id = res.data['ejemplar_id']

        respuesta = self.client.patch(
            self.url_detalle(ej_id),
            {'estado': 'BAJA'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['estado'], 'BAJA')

    def test_patch_reactivacion_desde_baja_a_activo_permitida_provisionalmente(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'REAC-001', 'estado': 'BAJA'},
            format='json'
        )
        ej_id = res.data['ejemplar_id']

        respuesta = self.client.patch(
            self.url_detalle(ej_id),
            {'estado': 'ACTIVO'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['estado'], 'ACTIVO')

    # --- 7. Bloqueo de Mantenimiento y Baja ante Préstamos Activos (RN-04) ---

    def test_patch_mantenimiento_rechazado_con_prestamo_activo_rn04(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'ACT-MNT'},
            format='json'
        )
        ej_id = res.data['ejemplar_id']
        ejemplar = Ejemplar.objects.get(ejemplar_id=ej_id)
        self.crear_prestamo(ejemplar, devuelto=False)

        respuesta = self.client.patch(
            self.url_detalle(ej_id),
            {'estado': 'MANTENIMIENTO'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('estado', respuesta.data)

        ejemplar.refresh_from_db()
        self.assertEqual(ejemplar.estado, EstadoEjemplar.ACTIVO)

    def test_patch_baja_rechazada_con_prestamo_activo_rn04(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'ACT-BAJA'},
            format='json'
        )
        ej_id = res.data['ejemplar_id']
        ejemplar = Ejemplar.objects.get(ejemplar_id=ej_id)
        self.crear_prestamo(ejemplar, devuelto=False)

        respuesta = self.client.patch(
            self.url_detalle(ej_id),
            {'estado': 'BAJA'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('estado', respuesta.data)

        ejemplar.refresh_from_db()
        self.assertEqual(ejemplar.estado, EstadoEjemplar.ACTIVO)

    # --- 8. Baja Lógica con Historial Conservado (RN-20) ---

    def test_patch_baja_con_prestamo_devuelto_conserva_historial_rn20(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'DEV-001'},
            format='json'
        )
        ej_id = res.data['ejemplar_id']
        ejemplar = Ejemplar.objects.get(ejemplar_id=ej_id)
        prestamo = self.crear_prestamo(ejemplar, devuelto=True)

        respuesta = self.client.patch(
            self.url_detalle(ej_id),
            {'estado': 'BAJA'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_200_OK)
        self.assertEqual(respuesta.data['estado'], 'BAJA')

        # El historial de préstamo debe seguir existiendo intacto (RN-20)
        self.assertTrue(Prestamo.objects.filter(prestamo_id=prestamo.prestamo_id).exists())

    # --- 9. Rechazo de Campos Desconocidos y Modificaciones No Autorizadas ---

    def test_registro_rechaza_campos_desconocidos(self):
        self.autenticar(self.bibliotecario)
        payload = {
            'libro_id': self.libro1.libro_id,
            'codigo_inventario': 'UNK-001',
            'ubicacion': 'Pasillo 3'
        }
        respuesta = self.client.post(self.url_lista, payload, format='json')
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ubicacion', respuesta.data)

    def test_patch_rechaza_campos_desconocidos(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'UNK-002'},
            format='json'
        )
        ej_id = res.data['ejemplar_id']

        respuesta = self.client.patch(
            self.url_detalle(ej_id),
            {'estado': 'MANTENIMIENTO', 'observaciones': 'Dañado'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('observaciones', respuesta.data)

    def test_patch_rechaza_modificacion_no_autorizada_de_codigo(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'NO-MOD-1'},
            format='json'
        )
        ej_id = res.data['ejemplar_id']

        # El endpoint de cambio de estado no permite modificar codigo_inventario
        respuesta = self.client.patch(
            self.url_detalle(ej_id),
            {'codigo_inventario': 'ALTERADO'},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('codigo_inventario', respuesta.data)

    def test_patch_rechaza_modificacion_no_autorizada_de_libro(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'NO-MOD-2'},
            format='json'
        )
        ej_id = res.data['ejemplar_id']

        # El endpoint de cambio de estado no permite sustituir el libro asociado
        respuesta = self.client.patch(
            self.url_detalle(ej_id),
            {'libro_id': self.libro2.libro_id},
            format='json'
        )
        self.assertEqual(respuesta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('libro_id', respuesta.data)

    # --- 10. Rechazo de DELETE (HTTP 405) ---

    def test_delete_ejemplar_no_permitido_405(self):
        self.autenticar(self.bibliotecario)
        res = self.client.post(
            self.url_lista,
            {'libro_id': self.libro1.libro_id, 'codigo_inventario': 'NODEL-01'},
            format='json'
        )
        ej_id = res.data['ejemplar_id']

        # RN-04: las bajas se gestionan vía estado BAJA, no mediante DELETE físico
        respuesta = self.client.delete(self.url_detalle(ej_id))
        self.assertEqual(respuesta.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
