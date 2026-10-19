from abc import ABC, abstractmethod
from typing import Dict, Iterable, Optional

from django.db import transaction
from django.db.models import Count, QuerySet

from biblioteca.models import Categoria, CategoriaLibro


class ICategoriaRepository(ABC):
    """
    Contrato de acceso a datos para la gestión administrativa de categorías.
    """

    @abstractmethod
    def listar(self, filtros: Optional[Dict] = None) -> QuerySet[Categoria]:
        pass

    @abstractmethod
    def obtener_por_id(self, categoria_id: int) -> Optional[Categoria]:
        pass

    @abstractmethod
    def obtener_por_nombre(self, nombre_categoria: str) -> Optional[Categoria]:
        pass

    @abstractmethod
    def crear(self, categoria: Categoria) -> Categoria:
        pass

    @abstractmethod
    def actualizar(
        self,
        categoria: Categoria,
        campos: Optional[Iterable[str]] = None,
    ) -> Categoria:
        pass

    @abstractmethod
    def tiene_libros_asociados(self, categoria_id: int) -> bool:
        pass

    @abstractmethod
    def contar_libros_asociados(self, categoria_id: int) -> int:
        pass


class DjangoCategoriaRepository(ICategoriaRepository):
    """
    Implementación concreta con Django ORM para la persistencia de categorías.
    """

    def listar(self, filtros: Optional[Dict] = None) -> QuerySet[Categoria]:
        queryset = (
            Categoria.objects
            .annotate(cantidad_libros=Count('categorialibro', distinct=True))
            .order_by('nombre_categoria', 'categoria_id')
        )

        if not filtros:
            return queryset

        nombre = filtros.get('nombre')
        if nombre:
            queryset = queryset.filter(nombre_categoria__icontains=nombre.strip())

        return queryset

    def obtener_por_id(self, categoria_id: int) -> Optional[Categoria]:
        return (
            Categoria.objects
            .annotate(cantidad_libros=Count('categorialibro', distinct=True))
            .filter(categoria_id=categoria_id)
            .first()
        )

    def obtener_por_nombre(self, nombre_categoria: str) -> Optional[Categoria]:
        return (
            Categoria.objects
            .filter(nombre_categoria__iexact=nombre_categoria.strip())
            .first()
        )

    def crear(self, categoria: Categoria) -> Categoria:
        with transaction.atomic():
            categoria.save(force_insert=True)
        return self.obtener_por_id(categoria.categoria_id) or categoria

    def actualizar(
        self,
        categoria: Categoria,
        campos: Optional[Iterable[str]] = None,
    ) -> Categoria:
        with transaction.atomic():
            if campos:
                categoria.save(update_fields=list(campos))
            else:
                categoria.save()
        return self.obtener_por_id(categoria.categoria_id) or categoria

    def tiene_libros_asociados(self, categoria_id: int) -> bool:
        return CategoriaLibro.objects.filter(categoria_id=categoria_id).exists()

    def contar_libros_asociados(self, categoria_id: int) -> int:
        return CategoriaLibro.objects.filter(categoria_id=categoria_id).count()
