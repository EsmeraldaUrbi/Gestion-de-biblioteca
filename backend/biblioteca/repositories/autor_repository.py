from abc import ABC, abstractmethod
from typing import Dict, Iterable, Optional

from django.db import transaction
from django.db.models import Count, QuerySet

from biblioteca.models import Autor, LibroAutor


class IAutorRepository(ABC):
    """
    Contrato de acceso a datos para la gestión administrativa de autores.
    """

    @abstractmethod
    def listar(self, filtros: Optional[Dict] = None) -> QuerySet[Autor]:
        pass

    @abstractmethod
    def obtener_por_id(self, autor_id: int) -> Optional[Autor]:
        pass

    @abstractmethod
    def buscar_por_nombre_exacto(self, nombre: str) -> QuerySet[Autor]:
        pass

    @abstractmethod
    def crear(self, autor: Autor) -> Autor:
        pass

    @abstractmethod
    def actualizar(
        self,
        autor: Autor,
        campos: Optional[Iterable[str]] = None,
    ) -> Autor:
        pass

    @abstractmethod
    def tiene_libros_asociados(self, autor_id: int) -> bool:
        pass

    @abstractmethod
    def contar_libros_asociados(self, autor_id: int) -> int:
        pass


class DjangoAutorRepository(IAutorRepository):
    """
    Implementación concreta con Django ORM para la persistencia de autores.
    """

    def listar(self, filtros: Optional[Dict] = None) -> QuerySet[Autor]:
        queryset = (
            Autor.objects
            .annotate(cantidad_libros=Count('libroautor', distinct=True))
            .order_by('nombre', 'autor_id')
        )

        if not filtros:
            return queryset

        nombre = filtros.get('nombre')
        if nombre:
            queryset = queryset.filter(nombre__icontains=nombre.strip())

        nacionalidad = filtros.get('nacionalidad')
        if nacionalidad:
            queryset = queryset.filter(nacionalidad__icontains=nacionalidad.strip())

        return queryset

    def obtener_por_id(self, autor_id: int) -> Optional[Autor]:
        return (
            Autor.objects
            .annotate(cantidad_libros=Count('libroautor', distinct=True))
            .filter(autor_id=autor_id)
            .first()
        )

    def buscar_por_nombre_exacto(self, nombre: str) -> QuerySet[Autor]:
        return Autor.objects.filter(nombre__iexact=nombre.strip())

    def crear(self, autor: Autor) -> Autor:
        with transaction.atomic():
            autor.save(force_insert=True)
        return self.obtener_por_id(autor.autor_id) or autor

    def actualizar(
        self,
        autor: Autor,
        campos: Optional[Iterable[str]] = None,
    ) -> Autor:
        with transaction.atomic():
            if campos:
                autor.save(update_fields=list(campos))
            else:
                autor.save()
        return self.obtener_por_id(autor.autor_id) or autor

    def tiene_libros_asociados(self, autor_id: int) -> bool:
        return LibroAutor.objects.filter(autor_id=autor_id).exists()

    def contar_libros_asociados(self, autor_id: int) -> int:
        return LibroAutor.objects.filter(autor_id=autor_id).count()
