from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Dict, Optional

from django.db.models import Count, DecimalField, Q, QuerySet, Sum
from django.db.models.functions import Coalesce

from biblioteca.models import Sancion


class IMisSancionesRepository(ABC):
    """
    Contrato de acceso a datos de solo lectura para las sanciones
    (multas económicas y bloqueos) personales de un usuario lector.
    """

    @abstractmethod
    def listar(
        self,
        usuario_id: int,
        tipo: Optional[str] = None,
        estado: Optional[str] = None,
        hoy: Optional[date] = None,
    ) -> QuerySet[Sancion]:
        pass

    @abstractmethod
    def obtener_resumen(
        self,
        usuario_id: int,
        hoy: date,
    ) -> Dict:
        pass


class DjangoMisSancionesRepository(IMisSancionesRepository):
    """
    Implementación concreta con Django ORM.

    Todas las consultas están restringidas estrictamente al usuario_id
    obtenido de la identidad autenticada. No admite escritura.
    """

    def listar(
        self,
        usuario_id: int,
        tipo: Optional[str] = None,
        estado: Optional[str] = None,
        hoy: Optional[date] = None,
    ) -> QuerySet[Sancion]:
        queryset = (
            Sancion.objects
            .filter(prestamo__usuario_id=usuario_id)
            .select_related(
                'prestamo',
                'prestamo__ejemplar',
                'prestamo__ejemplar__libro',
            )
            .order_by('-sancion_id')
        )

        tipo_normalizado = tipo.strip().lower() if tipo else 'todas'
        estado_normalizado = estado.strip().lower() if estado else 'todos'

        # Filtro de tipo
        if tipo_normalizado in ('economicas', 'economica'):
            queryset = queryset.filter(tipo='ECONOMICA')
            if estado_normalizado in ('pendientes', 'pendiente'):
                queryset = queryset.filter(fecha_pago__isnull=True)
            elif estado_normalizado in ('pagadas', 'pagada'):
                queryset = queryset.filter(fecha_pago__isnull=False)

        elif tipo_normalizado in ('bloqueos', 'bloqueo'):
            queryset = queryset.filter(tipo='BLOQUEO')
            if hoy is not None:
                if estado_normalizado in ('programados', 'programado'):
                    queryset = queryset.filter(fecha_inicio_bloqueo__gt=hoy)
                elif estado_normalizado in ('vigentes', 'vigente'):
                    queryset = queryset.filter(
                        fecha_inicio_bloqueo__lte=hoy,
                        fecha_fin_bloqueo__gte=hoy,
                    )
                elif estado_normalizado in ('concluidos', 'concluido'):
                    queryset = queryset.filter(fecha_fin_bloqueo__lt=hoy)

        elif tipo_normalizado in ('todas', 'todos'):
            # Si se solicita 'todas', pero con un estado específico
            if estado_normalizado in ('pendientes', 'pendiente'):
                queryset = queryset.filter(tipo='ECONOMICA', fecha_pago__isnull=True)
            elif estado_normalizado in ('pagadas', 'pagada'):
                queryset = queryset.filter(tipo='ECONOMICA', fecha_pago__isnull=False)
            elif hoy is not None:
                if estado_normalizado in ('programados', 'programado'):
                    queryset = queryset.filter(tipo='BLOQUEO', fecha_inicio_bloqueo__gt=hoy)
                elif estado_normalizado in ('vigentes', 'vigente'):
                    queryset = queryset.filter(
                        tipo='BLOQUEO',
                        fecha_inicio_bloqueo__lte=hoy,
                        fecha_fin_bloqueo__gte=hoy,
                    )
                elif estado_normalizado in ('concluidos', 'concluido'):
                    queryset = queryset.filter(tipo='BLOQUEO', fecha_fin_bloqueo__lt=hoy)

        return queryset

    def obtener_resumen(
        self,
        usuario_id: int,
        hoy: date,
    ) -> Dict:
        """
        Calcula las métricas de resumen sobre el total de sanciones del usuario,
        independientemente de los filtros o paginación de la consulta.
        """
        queryset = Sancion.objects.filter(prestamo__usuario_id=usuario_id)

        agregados = queryset.aggregate(
            total_sanciones=Count('sancion_id'),
            multas_pendientes=Count(
                'sancion_id',
                filter=Q(tipo='ECONOMICA', fecha_pago__isnull=True),
            ),
            monto_total_adeudado=Coalesce(
                Sum(
                    'monto',
                    filter=Q(tipo='ECONOMICA', fecha_pago__isnull=True),
                ),
                Decimal('0.00'),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
            bloqueos_vigentes=Count(
                'sancion_id',
                filter=Q(
                    tipo='BLOQUEO',
                    fecha_inicio_bloqueo__lte=hoy,
                    fecha_fin_bloqueo__gte=hoy,
                ),
            ),
        )

        return {
            'total_sanciones': agregados['total_sanciones'] or 0,
            'multas_pendientes': agregados['multas_pendientes'] or 0,
            'monto_total_adeudado': agregados['monto_total_adeudado'] or Decimal('0.00'),
            'bloqueos_vigentes': agregados['bloqueos_vigentes'] or 0,
        }
