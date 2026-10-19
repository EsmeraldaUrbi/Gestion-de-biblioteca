from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Optional

from biblioteca.models import Ejemplar, Prestamo, Sancion, Usuario


class IDevolucionesRepository(ABC):
    """Contrato de acceso a datos para devoluciones."""

    @abstractmethod
    def obtener_prestamo(
        self,
        prestamo_id: int
    ) -> Optional[Prestamo]:
        pass

    @abstractmethod
    def bloquear_usuario(
        self,
        usuario_id: int
    ) -> Optional[Usuario]:
        pass

    @abstractmethod
    def bloquear_ejemplar(
        self,
        ejemplar_id: int
    ) -> Optional[Ejemplar]:
        pass

    @abstractmethod
    def bloquear_prestamo(
        self,
        prestamo_id: int
    ) -> Optional[Prestamo]:
        pass

    @abstractmethod
    def registrar_fecha_devolucion(
        self,
        prestamo: Prestamo,
        fecha_devolucion: date
    ) -> None:
        pass

    @abstractmethod
    def crear_multa(
        self,
        prestamo_id: int,
        monto: Decimal
    ) -> Sancion:
        pass


class DjangoDevolucionesRepository(IDevolucionesRepository):
    """Persistencia de devoluciones mediante Django ORM."""

    def obtener_prestamo(
        self,
        prestamo_id: int
    ) -> Optional[Prestamo]:
        return (
            Prestamo.objects
            .filter(prestamo_id=prestamo_id)
            .first()
        )

    def bloquear_usuario(
        self,
        usuario_id: int
    ) -> Optional[Usuario]:
        return (
            Usuario.objects
            .select_for_update()
            .filter(usuario_id=usuario_id)
            .first()
        )

    def bloquear_ejemplar(
        self,
        ejemplar_id: int
    ) -> Optional[Ejemplar]:
        return (
            Ejemplar.objects
            .select_for_update()
            .filter(ejemplar_id=ejemplar_id)
            .first()
        )

    def bloquear_prestamo(
        self,
        prestamo_id: int
    ) -> Optional[Prestamo]:
        return (
            Prestamo.objects
            .select_for_update()
            .filter(prestamo_id=prestamo_id)
            .first()
        )

    def registrar_fecha_devolucion(
        self,
        prestamo: Prestamo,
        fecha_devolucion: date
    ) -> None:
        prestamo.fecha_devolucion = fecha_devolucion
        prestamo.save(update_fields=['fecha_devolucion'])

    def crear_multa(
        self,
        prestamo_id: int,
        monto: Decimal
    ) -> Sancion:
        return Sancion.objects.create(
            prestamo_id=prestamo_id,
            tipo='ECONOMICA',
            monto=monto,
            fecha_pago=None,
            fecha_inicio_bloqueo=None,
            fecha_fin_bloqueo=None
        )