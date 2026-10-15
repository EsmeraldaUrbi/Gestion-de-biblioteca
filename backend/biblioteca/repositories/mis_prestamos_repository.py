from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from django.db.models import Count, Q

from biblioteca.models import Prestamo, Sancion


class IMisPrestamosRepository(ABC):
    """
    Contrato de lectura de los préstamos personales
    y de las restricciones registradas del lector.
    """

    @abstractmethod
    def listar(
        self,
        usuario_id: int,
        filtro: str,
        hoy: date
    ):
        pass

    @abstractmethod
    def obtener_resumen(
        self,
        usuario_id: int,
        hoy: date
    ):
        pass

    @abstractmethod
    def consultar_restricciones(
        self,
        usuario_id: int,
        hoy: date
    ) -> dict:
        pass


class DjangoMisPrestamosRepository(IMisPrestamosRepository):
    """
    Implementación de consultas mediante Django ORM.

    Todas las operaciones están restringidas al
    identificador del usuario autenticado.
    """

    def listar(
        self,
        usuario_id: int,
        filtro: str,
        hoy: date
    ):
        prestamos = (
            Prestamo.objects
            .filter(usuario_id=usuario_id)
            .select_related(
                'ejemplar',
                'ejemplar__libro'
            )
        )

        if filtro == 'activos':
            prestamos = prestamos.filter(
                fecha_devolucion__isnull=True
            )

        elif filtro == 'vencidos':
            prestamos = prestamos.filter(
                fecha_devolucion__isnull=True,
                fecha_limite__lt=hoy
            )

        elif filtro == 'devueltos':
            prestamos = prestamos.filter(
                fecha_devolucion__isnull=False
            )

        return prestamos.order_by(
            '-fecha_prestamo',
            '-prestamo_id'
        )

    def obtener_resumen(
        self,
        usuario_id: int,
        hoy: date
    ) -> dict:
        """
        Un préstamo vencido continúa activo mientras
        fecha_devolucion permanezca vacía.
        """

        return (
            Prestamo.objects
            .filter(usuario_id=usuario_id)
            .aggregate(
                total=Count('prestamo_id'),

                activos=Count(
                    'prestamo_id',
                    filter=Q(
                        fecha_devolucion__isnull=True
                    )
                ),

                vencidos=Count(
                    'prestamo_id',
                    filter=Q(
                        fecha_devolucion__isnull=True,
                        fecha_limite__lt=hoy
                    )
                ),

                devueltos=Count(
                    'prestamo_id',
                    filter=Q(
                        fecha_devolucion__isnull=False
                    )
                )
            )
        )

    def consultar_restricciones(
        self,
        usuario_id: int,
        hoy: date
    ) -> dict:
        """
        Consulta sanciones que ya se encuentran
        registradas en la base de datos.

        No calcula multas ni genera bloqueos:
        esas operaciones corresponden a otros
        módulos del sistema.
        """

        adeudos_pendientes = (
            Sancion.objects
            .filter(
                prestamo__usuario_id=usuario_id,
                monto__gt=Decimal('0.00'),
                fecha_pago__isnull=True
            )
            .exists()
        )

        bloqueo_vigente = (
            Sancion.objects
            .filter(
                prestamo__usuario_id=usuario_id,
                fecha_inicio_bloqueo__lte=hoy,
                fecha_fin_bloqueo__gte=hoy
            )
            .exists()
        )

        return {
            'adeudos_pendientes': adeudos_pendientes,
            'bloqueo_vigente': bloqueo_vigente,
        }