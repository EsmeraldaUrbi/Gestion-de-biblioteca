"""Datos ficticios y repetibles para verificar el catálogo local."""
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from biblioteca.models import (
    Autor, Categoria, CategoriaLibro, Ejemplar, Libro, LibroAutor,
    Prestamo, Rol, Usuario,
)


class Command(BaseCommand):
    help = 'Agrega 15 libros ficticios; conserva los registros existentes.'

    @transaction.atomic
    def handle(self, *args, **options):
        titulos = [
            'Arquitectura de software: fundamentos', 'Bases de datos relacionales',
            'Redes de computadoras', 'Programación con Python', 'Algoritmos y estructuras',
            'Ingeniería de software aplicada', 'Matemáticas discretas',
            'Introducción a la física', 'Historia de la ciencia', 'Literatura contemporánea',
            'Diseño de interfaces', 'Seguridad informática', 'Inteligencia artificial',
            'Estadística para ingeniería', 'Sistemas operativos',
        ]
        categorias = ['Computación', 'Ingeniería', 'Ciencias', 'Literatura', 'Diseño']
        autores = ['Ana Rivera (demo)', 'Luis Torres (demo)', 'María Luna (demo)',
                   'Carlos Vega (demo)', 'Sofía Montes (demo)']
        # Completar solo datos demo faltantes, sin sobrescribir valores existentes.
        for indice, nombre in enumerate(autores):
            autor = Autor.objects.filter(nombre=nombre).first()
            if autor is None:
                autor = Autor(nombre=nombre)
            if autor.fecha_nacimiento is None:
                autor.fecha_nacimiento = date(1970 + indice * 4, indice + 1, 15)
            if not autor.nacionalidad:
                autor.nacionalidad = 'Mexicana'
            autor.save()
        lector = Usuario.objects.filter(email='catalogo-demo@test.local').first()
        if lector is not None:
            if not lector.direccion:
                lector.direccion = 'Calle de Pruebas 100, Ciudad Demo'
            if not lector.telefono:
                lector.telefono = '0000000000'
            lector.save()
        hoy = timezone.localdate()
        creados = 0
        for i, titulo in enumerate(titulos, 1):
            # ISBN sintético de 13 dígitos con dígito de control.
            base = f'97800000{i:04d}'
            control = (-sum(int(n) * (1 if j % 2 == 0 else 3)
                            for j, n in enumerate(base))) % 10
            libro, nuevo = Libro.objects.get_or_create(
                isbn=base + str(control), defaults={
                    'titulo': titulo,
                    'fecha_publicacion': date(2010 + i, (i - 1) % 12 + 1, 10),
                },
            )
            if libro.titulo == titulo and libro.fecha_publicacion is None:
                libro.fecha_publicacion = date(2010 + i, (i - 1) % 12 + 1, 10)
                libro.save(update_fields=['fecha_publicacion'])
            if not nuevo:
                self.stdout.write(f'Conservado: {libro.titulo}')
                continue
            creados += 1
            for indice in {(i - 1) % 5, i % 5}:
                autor = Autor.objects.filter(nombre=autores[indice]).first()
                if autor is None:
                    autor = Autor.objects.create(nombre=autores[indice])
                LibroAutor.objects.create(libro=libro, autor=autor)
                categoria = Categoria.objects.filter(nombre_categoria=categorias[indice]).first()
                if categoria is None:
                    categoria = Categoria.objects.create(nombre_categoria=categorias[indice])
                CategoriaLibro.objects.create(libro=libro, categoria=categoria)
            # Tres libros por escenario: mixto, libres, mantenimiento, baja, sin copias.
            perfil = (i - 1) % 5
            estados = {
                0: ['ACTIVO', 'ACTIVO', 'MANTENIMIENTO', 'BAJA'],
                1: ['ACTIVO', 'ACTIVO'], 2: ['MANTENIMIENTO'],
                3: ['BAJA'], 4: [],
            }[perfil]
            for j, estado in enumerate(estados, 1):
                ejemplar = Ejemplar.objects.create(
                    libro=libro, codigo_inventario=f'CATDEMO{i:02d}-{j}', estado=estado,
                )
                if perfil == 0 and j <= 2:
                    usuario = Usuario.objects.filter(email='catalogo-demo@test.local').first()
                    if usuario is None:
                        rol = Rol.objects.filter(nombre__iexact='estudiante').first()
                        if rol is None:
                            rol = Rol.objects.create(nombre='estudiante', limite_prestamos_activos=5)
                        usuario = Usuario(nombre='Lector de pruebas del catálogo',
                                          email='catalogo-demo@test.local', rol=rol,
                                          direccion='Calle de Pruebas 100, Ciudad Demo',
                                          telefono='0000000000')
                        usuario.set_password(None)
                        usuario.save()
                    Prestamo.objects.create(
                        usuario=usuario, ejemplar=ejemplar,
                        fecha_prestamo=hoy - timedelta(days=40),
                        fecha_limite=hoy - timedelta(days=10),
                        fecha_devolucion=hoy - timedelta(days=15) if j == 1 else None,
                    )
            self.stdout.write(f'Creado: {titulo}')
        self.stdout.write(self.style.SUCCESS(f'Libros nuevos: {creados}. Datos anteriores conservados.'))
