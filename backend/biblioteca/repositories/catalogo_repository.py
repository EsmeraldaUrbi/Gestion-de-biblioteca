from abc import ABC, abstractmethod

from django.db.models import Count, Exists, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce

from biblioteca.models import Autor, Categoria, Ejemplar, Libro, Prestamo


class ICatalogoRepository(ABC):
    @abstractmethod
    def listar(self, filtros):
        pass

    @abstractmethod
    def obtener(self, libro_id):
        pass

    @abstractmethod
    def opciones(self):
        pass


class DjangoCatalogoRepository(ICatalogoRepository):
    def _libros(self):
        # EXISTS evita que el historial de préstamos multiplique las copias.
        activos = Prestamo.objects.filter(
            ejemplar_id=OuterRef('pk'), fecha_devolucion__isnull=True
        )
        ejemplares = Ejemplar.objects.filter(libro_id=OuterRef('pk'))
        total = ejemplares.exclude(estado='BAJA')
        disponibles = ejemplares.filter(estado='ACTIVO').filter(~Exists(activos))

        def cantidad(queryset):
            return Coalesce(Subquery(
                queryset.order_by().values('libro_id')
                .annotate(cantidad=Count('pk')).values('cantidad')
            ), 0)

        return Libro.objects.annotate(
            stock_total=cantidad(total),
            stock_disponible=cantidad(disponibles),
        ).prefetch_related('autores', 'categorias').order_by('titulo', 'libro_id')

    def listar(self, filtros):
        libros = self._libros()
        if filtros.get('titulo'):
            libros = libros.filter(titulo__icontains=filtros['titulo'])
        if 'autor' in filtros:
            libros = libros.filter(autores__autor_id=filtros['autor'])
        if 'categoria' in filtros:
            libros = libros.filter(categorias__categoria_id=filtros['categoria'])
        if 'disponible' in filtros:
            libros = libros.filter(
                Q(stock_disponible__gt=0) if filtros['disponible']
                else Q(stock_disponible=0)
            )
        return libros.distinct()

    def obtener(self, libro_id):
        return self._libros().filter(libro_id=libro_id).first()

    def opciones(self):
        return {
            'autores': Autor.objects.order_by('nombre', 'autor_id'),
            'categorias': Categoria.objects.order_by('nombre_categoria', 'categoria_id'),
        }
