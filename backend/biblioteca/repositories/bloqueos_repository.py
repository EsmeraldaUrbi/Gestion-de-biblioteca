from abc import ABC, abstractmethod
from datetime import date
from typing import Iterator, Optional

from biblioteca.models import Prestamo, Sancion, Usuario


class IBloqueosRepository(ABC):
    """
    Contrato de acceso a datos para bloqueos automaticos.
    """

    @abstractmethod
    def listar_prestamos_candidatos(
        self,
        fecha_actual: date
    ) -> Iterator[int]:
        pass

    @abstractmethod
    def listar_prestamos_candidatos_usuario(
        self,
        usuario_id: int,
        fecha_actual: date
    ) -> list[Prestamo]:
        pass
    
    @abstractmethod
    def obtener_usuario_id(
        self,
        prestamo_id: int
    ) -> Optional[int]:
        pass

    @abstractmethod
    def bloquear_usuario(
        self,
        usuario_id: int
    ) -> Optional[Usuario]:
        pass

    @abstractmethod
    def bloquear_prestamo(
        self,
        prestamo_id: int
    ) -> Optional[Prestamo]:
        pass

    @abstractmethod
    def existe_bloqueo(
        self,
        prestamo_id: int
    ) -> bool:
        pass

    @abstractmethod
    def crear_bloqueo(
        self,
        prestamo_id: int,
        fecha_inicio: date,
        fecha_fin: date
    ) -> Sancion:
        pass


class DjangoBloqueosRepository(IBloqueosRepository):
    """
    Persistencia de bloqueos mediante Django ORM.
    """

    def listar_prestamos_candidatos(
        self,
        fecha_actual: date
    ) -> Iterator[int]:
        """
        Preselecciona prestamos vencidos sin devolucion.

        El servicio comprobara el mes calendario exacto
        antes de generar una sancion.
        """
        consulta = (
            Prestamo.objects
            .filter(
                fecha_devolucion__isnull=True,
                fecha_limite__lt=fecha_actual
            )
            .order_by('prestamo_id')
            .values_list('prestamo_id', flat=True)
        )

        return consulta.iterator(chunk_size=200)
    
    def listar_prestamos_candidatos_usuario(
        self,
        usuario_id: int,
        fecha_actual: date
    ) -> list[Prestamo]:
        """
        Consulta prestamos vencidos sin devolver
        pertenecientes a un usuario concreto.
        """
        return list(
            Prestamo.objects
            .filter(
                usuario_id=usuario_id,
                fecha_devolucion__isnull=True,
                fecha_limite__lt=fecha_actual
            )
            .order_by('prestamo_id')
        )

    def obtener_usuario_id(
        self,
        prestamo_id: int
    ) -> Optional[int]:
        return (
            Prestamo.objects
            .filter(prestamo_id=prestamo_id)
            .values_list('usuario_id', flat=True)
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

    def existe_bloqueo(
        self,
        prestamo_id: int
    ) -> bool:
        return (
            Sancion.objects
            .select_for_update()
            .filter(
                prestamo_id=prestamo_id,
                tipo='BLOQUEO'
            )
            .exists()
        )

    def crear_bloqueo(
        self,
        prestamo_id: int,
        fecha_inicio: date,
        fecha_fin: date
    ) -> Sancion:
        return Sancion.objects.create(
            prestamo_id=prestamo_id,
            tipo='BLOQUEO',
            monto=None,
            fecha_pago=None,
            fecha_inicio_bloqueo=fecha_inicio,
            fecha_fin_bloqueo=fecha_fin
        )
