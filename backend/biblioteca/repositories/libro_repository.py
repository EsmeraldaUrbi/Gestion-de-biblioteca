from abc import ABC, abstractmethod
from typing import Dict, Iterable, Optional, Set

from django.db import transaction
from django.db.models import QuerySet

from biblioteca.models import Autor, Categoria, CategoriaLibro, Ejemplar, Libro, LibroAutor


class ILibroRepository(ABC):
    """
    Contrato de acceso a datos para la gestión bibliográfica de libros.
    """

    @abstractmethod
    def listar(self, filtros: Optional[Dict] = None) -> QuerySet[Libro]:
        pass

    @abstractmethod
    def obtener_por_id(self, libro_id: int) -> Optional[Libro]:
        pass

    @abstractmethod
    def obtener_por_isbn(self, isbn: str) -> Optional[Libro]:
        pass

    @abstractmethod
    def verificar_autores_existentes(self, autor_ids: Iterable[int]) -> Set[int]:
        pass

    @abstractmethod
    def verificar_categorias_existentes(self, categoria_ids: Iterable[int]) -> Set[int]:
        pass

    @abstractmethod
    def crear(
        self,
        libro: Libro,
        autor_ids: Optional[Iterable[int]] = None,
        categoria_ids: Optional[Iterable[int]] = None
    ) -> Libro:
        pass

    @abstractmethod
    def actualizar(
        self,
        libro: Libro,
        campos: Optional[Iterable[str]] = None,
        autor_ids: Optional[Iterable[int]] = None,
        categoria_ids: Optional[Iterable[int]] = None
    ) -> Libro:
        pass

    @abstractmethod
    def eliminar(self, libro: Libro) -> None:
        pass

    @abstractmethod
    def tiene_ejemplares(self, libro_id: int) -> bool:
        pass


class DjangoLibroRepository(ILibroRepository):
    """
    Implementación concreta con Django ORM para la persistencia de libros.
    """

    def listar(self, filtros: Optional[Dict] = None) -> QuerySet[Libro]:
        queryset = (
            Libro.objects
            .prefetch_related('autores', 'categorias')
            .order_by('-libro_id')
        )

        if not filtros:
            return queryset

        if filtros.get('titulo'):
            queryset = queryset.filter(titulo__icontains=filtros['titulo'])

        if filtros.get('isbn'):
            queryset = queryset.filter(isbn__icontains=filtros['isbn'])

        if filtros.get('autor_id'):
            queryset = queryset.filter(autores__autor_id=filtros['autor_id'])

        if filtros.get('categoria_id'):
            queryset = queryset.filter(categorias__categoria_id=filtros['categoria_id'])

        return queryset.distinct()

    def obtener_por_id(self, libro_id: int) -> Optional[Libro]:
        return (
            Libro.objects
            .prefetch_related('autores', 'categorias')
            .filter(libro_id=libro_id)
            .first()
        )

    def obtener_por_isbn(self, isbn: str) -> Optional[Libro]:
        return (
            Libro.objects
            .filter(isbn__iexact=isbn.strip())
            .first()
        )

    def verificar_autores_existentes(self, autor_ids: Iterable[int]) -> Set[int]:
        ids = set(autor_ids)
        if not ids:
            return set()
        return set(
            Autor.objects
            .filter(autor_id__in=ids)
            .values_list('autor_id', flat=True)
        )

    def verificar_categorias_existentes(self, categoria_ids: Iterable[int]) -> Set[int]:
        ids = set(categoria_ids)
        if not ids:
            return set()
        return set(
            Categoria.objects
            .filter(categoria_id__in=ids)
            .values_list('categoria_id', flat=True)
        )

    def crear(
        self,
        libro: Libro,
        autor_ids: Optional[Iterable[int]] = None,
        categoria_ids: Optional[Iterable[int]] = None
    ) -> Libro:
        with transaction.atomic():
            libro.save(force_insert=True)

            if autor_ids:
                autores_unicos = set(autor_ids)
                asociaciones_autores = [
                    LibroAutor(libro=libro, autor_id=aid)
                    for aid in autores_unicos
                ]
                LibroAutor.objects.bulk_create(asociaciones_autores)

            if categoria_ids:
                categorias_unicas = set(categoria_ids)
                asociaciones_categorias = [
                    CategoriaLibro(libro=libro, categoria_id=cid)
                    for cid in categorias_unicas
                ]
                CategoriaLibro.objects.bulk_create(asociaciones_categorias)

        return self.obtener_por_id(libro.libro_id) or libro

    def actualizar(
        self,
        libro: Libro,
        campos: Optional[Iterable[str]] = None,
        autor_ids: Optional[Iterable[int]] = None,
        categoria_ids: Optional[Iterable[int]] = None
    ) -> Libro:
        with transaction.atomic():
            if campos:
                libro.save(update_fields=list(campos))
            else:
                libro.save()

            if autor_ids is not None:
                autores_unicos = set(autor_ids)
                LibroAutor.objects.filter(libro=libro).delete()
                asociaciones_autores = [
                    LibroAutor(libro=libro, autor_id=aid)
                    for aid in autores_unicos
                ]
                if asociaciones_autores:
                    LibroAutor.objects.bulk_create(asociaciones_autores)

            if categoria_ids is not None:
                categorias_unicas = set(categoria_ids)
                CategoriaLibro.objects.filter(libro=libro).delete()
                asociaciones_categorias = [
                    CategoriaLibro(libro=libro, categoria_id=cid)
                    for cid in categorias_unicas
                ]
                if asociaciones_categorias:
                    CategoriaLibro.objects.bulk_create(asociaciones_categorias)

        return self.obtener_por_id(libro.libro_id) or libro

    def eliminar(self, libro: Libro) -> None:
        libro.delete()

    def tiene_ejemplares(self, libro_id: int) -> bool:
        return Ejemplar.objects.filter(libro_id=libro_id).exists()
