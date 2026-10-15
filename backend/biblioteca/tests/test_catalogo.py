from datetime import date

from django.urls import reverse
from rest_framework.test import APITestCase

from biblioteca.models import (
    Autor, Categoria, Ejemplar, Libro,
    Prestamo, Rol, Usuario,
)


class CatalogoApiTests(APITestCase):
    def setUp(self):
        self.rol = Rol.objects.create(nombre='estudiante', limite_prestamos_activos=5)
        self.usuario = Usuario.objects.create(
            nombre='Lector', email='lector@test.local', rol=self.rol,
            contrasena_hash='no-utilizada',
        )
        self.client.force_authenticate(self.usuario)
        self.url = reverse('catalogo-list')
        self.libro = Libro.objects.create(titulo='Arquitectura de software', isbn='9780000000001')
        self.vacio = Libro.objects.create(titulo='Sin ejemplares', isbn='9780000000002')
        self.autores = [Autor.objects.create(nombre=n) for n in ['Ana', 'Luis']]
        self.categorias = [Categoria.objects.create(nombre_categoria=n) for n in ['Software', 'Diseño']]
        self.libro.autores.add(*self.autores)
        self.libro.categorias.add(*self.categorias)
        self.libre = self.ejemplar('LIBRE', 'ACTIVO')
        self.ocupado = self.ejemplar('PRESTADO', 'ACTIVO')
        self.ejemplar('TALLER', 'MANTENIMIENTO')
        self.ejemplar('BAJA', 'BAJA')
        # Vencido y no devuelto: continúa ocupando una copia.
        self.prestamo(self.ocupado)
        # Múltiples préstamos devueltos no multiplican el stock.
        self.prestamo(self.libre, date(2020, 2, 1))
        self.prestamo(self.libre, date(2020, 2, 2))

    def ejemplar(self, codigo, estado):
        return Ejemplar.objects.create(libro=self.libro, codigo_inventario=codigo, estado=estado)

    def prestamo(self, ejemplar, devolucion=None):
        return Prestamo.objects.create(
            usuario=self.usuario, ejemplar=ejemplar,
            fecha_prestamo=date(2020, 1, 1), fecha_limite=date(2020, 1, 31),
            fecha_devolucion=devolucion,
        )

    def test_stock_y_detalle_sin_multiplicar_relaciones(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data['count'], 2)
        libro, vacio = respuesta.data['results']
        self.assertEqual((libro['stock_total'], libro['stock_disponible']), (3, 1))
        self.assertEqual((vacio['stock_total'], vacio['stock_disponible']), (0, 0))
        detalle = self.client.get(reverse('catalogo-detail', args=[self.libro.pk]))
        self.assertEqual(detalle.data, libro)

    def test_filtros_individuales_y_combinados(self):
        filtros = {
            'titulo': 'ARQUITECTURA', 'autor': self.autores[0].pk,
            'categoria': self.categorias[0].pk, 'disponible': 'true',
        }
        for parametros in [{k: v} for k, v in filtros.items()] + [filtros]:
            with self.subTest(parametros=parametros):
                respuesta = self.client.get(self.url, parametros)
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.data['count'], 1)
                libro = respuesta.data['results'][0]
                self.assertEqual(libro['stock_total'], 3)
                self.assertEqual(libro['stock_disponible'], 1)
                self.assertEqual(len(libro['autores']), 2)
                self.assertEqual(len(libro['categorias']), 2)

    def test_filtros_combinados_con_varias_relaciones_no_duplican_libros_ni_stock(self):
        # El setUp ya vincula dos autores y dos categorías al libro.
        # Filtrar por autor[0] y categoría[0] produce un join N:M; distinct() y
        # las subconsultas del repositorio deben devolver exactamente un libro
        # con el stock correcto, sin duplicar filas ni existencias.
        respuesta = self.client.get(self.url, {
            'autor': self.autores[0].pk, 'categoria': self.categorias[0].pk,
        })
        self.assertEqual(respuesta.data['count'], 1)
        self.assertEqual(respuesta.data['results'][0]['stock_disponible'], 1)

    def test_sin_disponibilidad_y_sin_resultados(self):
        respuesta = self.client.get(self.url, {'disponible': 'false'})
        self.assertEqual([x['libro_id'] for x in respuesta.data['results']], [self.vacio.pk])
        for filtros in [{'titulo': 'inexistente'}, {'autor': 99999}, {'categoria': 99999}]:
            with self.subTest(filtros=filtros):
                respuesta = self.client.get(self.url, filtros)
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.data['results'], [])

    def test_devolucion_actualiza_disponibilidad(self):
        Prestamo.objects.filter(ejemplar=self.ocupado).update(fecha_devolucion=date.today())
        respuesta = self.client.get(reverse('catalogo-detail', args=[self.libro.pk]))
        self.assertEqual(respuesta.data['stock_disponible'], 2)

    def test_estados_ejemplar_y_prestamos_cobertura_disponibilidad(self):
        """
        RN-03, RN-05 y RN-06:
        - Mantenimiento: suma a stock_total, no a stock_disponible.
        - Baja: no suma a stock_total ni a stock_disponible.
        - Activo sin préstamo: suma a stock_total y stock_disponible.
        - Activo con préstamo activo (incluso vencido): suma a stock_total, no a stock_disponible.
        - Múltiples préstamos históricos devueltos no multiplican existencias.
        """
        libro_aislado = Libro.objects.create(titulo='Disponibilidad Integral', isbn='9789999999999')

        # 1. Ejemplar en mantenimiento
        e_taller = Ejemplar.objects.create(libro=libro_aislado, codigo_inventario='DISP-TAL', estado='MANTENIMIENTO')
        resp = self.client.get(reverse('catalogo-detail', args=[libro_aislado.pk]))
        self.assertEqual(resp.data['stock_total'], 1)
        self.assertEqual(resp.data['stock_disponible'], 0)

        # 2. Ejemplar dado de baja (no altera total ni disponible)
        Ejemplar.objects.create(libro=libro_aislado, codigo_inventario='DISP-BAJ', estado='BAJA')
        resp = self.client.get(reverse('catalogo-detail', args=[libro_aislado.pk]))
        self.assertEqual(resp.data['stock_total'], 1)
        self.assertEqual(resp.data['stock_disponible'], 0)

        # 3. Ejemplar activo libre
        e_activo = Ejemplar.objects.create(libro=libro_aislado, codigo_inventario='DISP-ACT', estado='ACTIVO')
        resp = self.client.get(reverse('catalogo-detail', args=[libro_aislado.pk]))
        self.assertEqual(resp.data['stock_total'], 2)
        self.assertEqual(resp.data['stock_disponible'], 1)

        # 4. Préstamo activo (sin devolución)
        p_activo = Prestamo.objects.create(
            usuario=self.usuario, ejemplar=e_activo,
            fecha_prestamo=date(2020, 1, 1), fecha_limite=date(2020, 1, 31),
            fecha_devolucion=None,
        )
        resp = self.client.get(reverse('catalogo-detail', args=[libro_aislado.pk]))
        self.assertEqual(resp.data['stock_total'], 2)
        self.assertEqual(resp.data['stock_disponible'], 0)

        # 5. Devolución restaura disponibilidad
        p_activo.fecha_devolucion = date(2020, 1, 20)
        p_activo.save()
        resp = self.client.get(reverse('catalogo-detail', args=[libro_aislado.pk]))
        self.assertEqual(resp.data['stock_total'], 2)
        self.assertEqual(resp.data['stock_disponible'], 1)

        # 6. Historial de múltiples préstamos devueltos no infla el stock
        for d in range(1, 4):
            Prestamo.objects.create(
                usuario=self.usuario, ejemplar=e_activo,
                fecha_prestamo=date(2020, 2, d), fecha_limite=date(2020, 2, 28),
                fecha_devolucion=date(2020, 2, d + 1),
            )
        resp = self.client.get(reverse('catalogo-detail', args=[libro_aislado.pk]))
        self.assertEqual(resp.data['stock_total'], 2)
        self.assertEqual(resp.data['stock_disponible'], 1)

    def test_paginacion_y_validacion(self):
        respuesta = self.client.get(self.url, {'page_size': 1})
        self.assertEqual(respuesta.data['count'], 2)
        self.assertEqual(len(respuesta.data['results']), 1)
        self.assertIsNotNone(respuesta.data['next'])
        for filtros in [{'autor': 'abc'}, {'categoria': 0}, {'disponible': 'quizas'},
                        {'page': 0}, {'page_size': 101}, {'page_size': 'abc'}]:
            with self.subTest(filtros=filtros):
                self.assertEqual(self.client.get(self.url, filtros).status_code, 400)
        self.assertEqual(self.client.get(self.url, {'page': 999}).status_code, 404)

    def test_opciones_y_no_encontrado(self):
        respuesta = self.client.get(reverse('catalogo-filtros'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(len(respuesta.data['autores']), 2)
        self.assertEqual(len(respuesta.data['categorias']), 2)
        self.assertEqual(self.client.get(reverse('catalogo-detail', args=[99999])).status_code, 404)

    def test_permisos_y_solo_lectura(self):
        urls = [self.url, reverse('catalogo-filtros'), reverse('catalogo-detail', args=[self.libro.pk])]
        for nombre in ['estudiante', 'docente', 'bibliotecario']:
            self.rol.nombre = nombre
            self.rol.save()
            for url in urls:
                self.assertEqual(self.client.get(url).status_code, 200)
                self.assertEqual(self.client.post(url, {}).status_code, 405)
        self.rol.nombre = 'desconocido'
        self.rol.save()
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_authenticate(user=None)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 401)

    def test_acceso_con_token_real(self):
        self.usuario.set_password('Catalogo123*')
        self.usuario.save()
        self.client.force_authenticate(user=None)
        login = self.client.post(reverse('auth-login'), {
            'email': self.usuario.email, 'password': 'Catalogo123*',
        }, format='json')
        self.assertEqual(login.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['token']}")
        self.assertEqual(self.client.get(self.url).status_code, 200)
