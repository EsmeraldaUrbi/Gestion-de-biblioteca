from abc import ABC, abstractmethod
from datetime import date

from django.db.models import Count, Q

from biblioteca.models import Prestamo


class IMisPrestamosRepository(ABC):
    """
    Contrato de lectura de préstamos personales.
    """

    @abstractmethod
    def listar(self, usuario_id, filtro, hoy):
        pass

    @abstractmethod
    def obtener_resumen(self, usuario_id, hoy):
        pass


class DjangoMisPrestamosRepository(IMisPrestamosRepository):
    """
    Consultas de préstamos mediante Django ORM.

    Todas las consultas se restringen al usuario
    autenticado recibido desde el servicio.
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
    ):
        """
        Activos incluye todos los préstamos sin
        devolución, incluso los vencidos.

        Vencidos es un subconjunto de activos.
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