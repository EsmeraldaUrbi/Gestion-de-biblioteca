from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from biblioteca.models import (
    Autor,
    Categoria,
    Ejemplar,
    Libro,
)
from biblioteca.services.ejemplar_service import EjemplarService
from biblioteca.services.libro_service import LibroService


class Command(BaseCommand):
    help = (
        'Crea libros y ejemplares de demostración '
        'para el módulo de préstamos 3.5.'
    )

    LIBROS = [
        {
            'titulo': 'Fundamentos de redes modernas',
            'anio': 2021,
            'autor': 'Mariana Montes (demo)',
            'categoria': 'Computación',
            'ejemplares': ['ACTIVO', 'ACTIVO', 'ACTIVO'],
        },
        {
            'titulo': 'Diseño de bases de datos',
            'anio': 2020,
            'autor': 'Luis Paredes (demo)',
            'categoria': 'Computación',
            'ejemplares': ['ACTIVO', 'ACTIVO'],
        },
        {
            'titulo': 'Programación orientada a objetos',
            'anio': 2022,
            'autor': 'Elena Vargas (demo)',
            'categoria': 'Computación',
            'ejemplares': ['ACTIVO', 'ACTIVO'],
        },
        {
            'titulo': 'Sistemas operativos y procesos',
            'anio': 2019,
            'autor': 'Roberto Castillo (demo)',
            'categoria': 'Ingeniería',
            'ejemplares': ['ACTIVO', 'ACTIVO', 'MANTENIMIENTO'],
        },
        {
            'titulo': 'Diseño de interfaces web',
            'anio': 2023,
            'autor': 'Claudia Romero (demo)',
            'categoria': 'Diseño',
            'ejemplares': ['ACTIVO', 'ACTIVO'],
        },
        {
            'titulo': 'Pruebas y calidad de software',
            'anio': 2021,
            'autor': 'Mariana Montes (demo)',
            'categoria': 'Ingeniería',
            'ejemplares': ['ACTIVO', 'ACTIVO'],
        },
        {
            'titulo': 'Arquitectura de aplicaciones',
            'anio': 2024,
            'autor': 'Luis Paredes (demo)',
            'categoria': 'Ingeniería',
            'ejemplares': ['ACTIVO', 'ACTIVO', 'ACTIVO'],
        },
        {
            'titulo': 'Inteligencia artificial aplicada',
            'anio': 2023,
            'autor': 'Elena Vargas (demo)',
            'categoria': 'Computación',
            'ejemplares': ['ACTIVO', 'MANTENIMIENTO'],
        },
        {
            'titulo': 'Matemáticas para computación',
            'anio': 2018,
            'autor': 'Roberto Castillo (demo)',
            'categoria': 'Matemáticas',
            'ejemplares': ['BAJA'],
        },
        {
            'titulo': 'Ingeniería de software y equipos',
            'anio': 2022,
            'autor': 'Claudia Romero (demo)',
            'categoria': 'Ingeniería',
            'ejemplares': [],
        },
    ]

    @staticmethod
    def generar_isbn(indice):
        """
        Genera ISBN-13 sintéticos con dígito de control válido.
        El prefijo utilizado evita colisiones con la seed
        existente del catálogo.
        """
        base = f'97860000{indice:04d}'

        suma = sum(
            int(digito) * (1 if posicion % 2 == 0 else 3)
            for posicion, digito in enumerate(base)
        )

        verificador = (-suma) % 10

        return f'{base}{verificador}'

    def obtener_autor(self, nombre):
        autor = Autor.objects.filter(
            nombre=nombre
        ).first()

        if autor is None:
            autor = Autor.objects.create(
                nombre=nombre,
                fecha_nacimiento=date(1980, 5, 12),
                nacionalidad='Mexicana'
            )

        return autor

    def obtener_categoria(self, nombre):
        categoria = Categoria.objects.filter(
            nombre_categoria=nombre
        ).first()

        if categoria is None:
            categoria = Categoria.objects.create(
                nombre_categoria=nombre
            )

        return categoria

    @transaction.atomic
    def handle(self, *args, **options):
        libro_service = LibroService()
        ejemplar_service = EjemplarService()

        libros_nuevos = 0
        ejemplares_nuevos = 0

        self.stdout.write(
            'Preparando libros de demostración para préstamos...'
        )

        for indice, datos in enumerate(self.LIBROS, start=1):
            isbn = self.generar_isbn(indice)

            autor = self.obtener_autor(
                datos['autor']
            )

            categoria = self.obtener_categoria(
                datos['categoria']
            )

            libro = Libro.objects.filter(
                isbn=isbn
            ).first()

            if libro is None:
                libro = libro_service.registrar_libro({
                    'titulo': datos['titulo'],
                    'isbn': isbn,
                    'fecha_publicacion': date(
                        datos['anio'], 1, 15
                    ),
                    'autor_ids': [
                        autor.autor_id
                    ],
                    'categoria_ids': [
                        categoria.categoria_id
                    ],
                })

                libros_nuevos += 1

            for numero, estado in enumerate(
                datos['ejemplares'],
                start=1
            ):
                codigo = f'PDEM{indice:02d}-{numero:02d}'

                existente = Ejemplar.objects.filter(
                    codigo_inventario=codigo
                ).first()

                if existente is not None:
                    if existente.libro_id != libro.libro_id:
                        self.stdout.write(
                            self.style.WARNING(
                                f'Código {codigo} ocupado por otro libro.'
                            )
                        )

                    # Conservamos cualquier cambio de estado
                    # realizado anteriormente por el equipo.
                    continue

                ejemplar_service.registrar_ejemplar({
                    'libro_id': libro.libro_id,
                    'codigo_inventario': codigo,
                    'estado': estado,
                })

                ejemplares_nuevos += 1

            self.stdout.write(
                f'Libro #{libro.libro_id}: '
                f'{libro.titulo} | ISBN {isbn}'
            )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Libros nuevos: {libros_nuevos}'
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Ejemplares nuevos: {ejemplares_nuevos}'
            )
        )

        self.stdout.write(
            'Los registros existentes fueron conservados.'
        )