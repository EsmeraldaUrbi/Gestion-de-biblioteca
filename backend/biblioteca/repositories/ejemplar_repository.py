from abc import ABC, abstractmethod
from typing import Dict, Iterable, Optional

from django.db import transaction
from django.db.models import QuerySet

from biblioteca.models import Ejemplar, Libro, Prestamo


class IEjemplarRepository(ABC):
    """
    Contrato de acceso a datos para la gestión de ejemplares físicos.
    """

    @abstractmethod
    def listar(self, filtros: Optional[Dict] = None) -> QuerySet[Ejemplar]:
        pass

    @abstractmethod
    def listar_por_libro(self, libro_id: int) -> QuerySet[Ejemplar]:
        pass

    @abstractmethod
    def obtener_por_id(self, ejemplar_id: int, con_bloqueo: bool = False) -> Optional[Ejemplar]:
        pass

    @abstractmethod
    def obtener_por_codigo(self, codigo_inventario: str) -> Optional[Ejemplar]:
        pass

    @abstractmethod
    def existe_libro(self, libro_id: int) -> bool:
        pass

    @abstractmethod
    def crear(self, ejemplar: Ejemplar) -> Ejemplar:
        pass

    @abstractmethod
    def actualizar(self, ejemplar: Ejemplar, campos: Optional[Iterable[str]] = None) -> Ejemplar:
        pass

    @abstractmethod
    def tiene_prestamos_activos(self, ejemplar_id: int) -> bool:
        pass

    @abstractmethod
    def tiene_prestamos_historicos(self, ejemplar_id: int) -> bool:
        pass

    @abstractmethod
    def eliminar_fisico(self, ejemplar: Ejemplar) -> None:
        pass


class DjangoEjemplarRepository(IEjemplarRepository):
    """
    Implementación concreta con Django ORM para la persistencia de ejemplares físicos.
    """

    def listar(self, filtros: Optional[Dict] = None) -> QuerySet[Ejemplar]:
        queryset = (
            Ejemplar.objects
            .select_related('libro')
            .order_by('ejemplar_id')
        )

        if not filtros:
            return queryset

        if filtros.get('libro_id'):
            queryset = queryset.filter(libro_id=filtros['libro_id'])

        if filtros.get('estado'):
            queryset = queryset.filter(estado=filtros['estado'])

        if filtros.get('codigo_inventario'):
            queryset = queryset.filter(
                codigo_inventario__icontains=filtros['codigo_inventario'].strip()
            )

        return queryset

    def listar_por_libro(self, libro_id: int) -> QuerySet[Ejemplar]:
        return (
            Ejemplar.objects
            .select_related('libro')
            .filter(libro_id=libro_id)
            .order_by('ejemplar_id')
        )

    def obtener_por_id(self, ejemplar_id: int, con_bloqueo: bool = False) -> Optional[Ejemplar]:
        queryset = Ejemplar.objects.select_related('libro')
        if con_bloqueo:
            queryset = queryset.select_for_update()
        return queryset.filter(ejemplar_id=ejemplar_id).first()

    def obtener_por_codigo(self, codigo_inventario: str) -> Optional[Ejemplar]:
        return (
            Ejemplar.objects
            .select_related('libro')
            .filter(codigo_inventario__iexact=codigo_inventario.strip())
            .first()
        )

    def existe_libro(self, libro_id: int) -> bool:
        return Libro.objects.filter(libro_id=libro_id).exists()

    def crear(self, ejemplar: Ejemplar) -> Ejemplar:
        with transaction.atomic():
            ejemplar.save(force_insert=True)
        return ejemplar

    def actualizar(self, ejemplar: Ejemplar, campos: Optional[Iterable[str]] = None) -> Ejemplar:
        with transaction.atomic():
            if campos:
                ejemplar.save(update_fields=list(campos))
            else:
                ejemplar.save()
        return ejemplar

    def tiene_prestamos_activos(self, ejemplar_id: int) -> bool:
        return (
            Prestamo.objects
            .filter(
                ejemplar_id=ejemplar_id,
                fecha_devolucion__isnull=True
            )
            .exists()
        )

    def tiene_prestamos_historicos(self, ejemplar_id: int) -> bool:
        return Prestamo.objects.filter(ejemplar_id=ejemplar_id).exists()

    def eliminar_fisico(self, ejemplar: Ejemplar) -> None:
        with transaction.atomic():
            ejemplar.delete()
