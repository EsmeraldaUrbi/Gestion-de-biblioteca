from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from biblioteca.models import Sancion
from biblioteca.repositories.sanciones_repository import (
    DjangoSancionesRepository,
)


class SancionNoEncontradaError(Exception):
    codigo = 'SANCION_NO_ENCONTRADA'


class PagoSancionNoPermitidoError(Exception):
    codigo = 'SANCION_PAGO_NO_PERMITIDO'


class PagoSancionDuplicadoError(Exception):
    codigo = 'SANCION_YA_PAGADA'


class SancionesService:
    def __init__(self, repository=None):
        self.repository = repository or DjangoSancionesRepository()

    def listar_administrativas(
        self,
        termino: str = '',
        tipo: str = 'todos',
        estado: str = 'todos',
    ):
        hoy = timezone.localdate()
        sanciones = self.repository.listar_administrativas(
            termino=termino,
            tipo=tipo,
            estado=estado,
            hoy=hoy,
        )
        return sanciones, self._resumen_administrativo(sanciones, hoy), hoy

    def obtener_administrativa(self, sancion_id: int) -> tuple[Sancion, date]:
        sancion = self.repository.obtener_administrativa(sancion_id)
        if sancion is None:
            raise SancionNoEncontradaError('La sanción solicitada no existe.')
        return sancion, timezone.localdate()

    @transaction.atomic
    def registrar_pago(self, sancion_id: int) -> tuple[Sancion, date]:
        sancion = self.repository.obtener_para_pago(sancion_id)
        if sancion is None:
            raise SancionNoEncontradaError('La sanción solicitada no existe.')

        if sancion.tipo != 'ECONOMICA' or sancion.monto is None:
            raise PagoSancionNoPermitidoError(
                'Solo las multas económicas pueden liquidarse en caja.'
            )

        if sancion.fecha_pago is not None:
            raise PagoSancionDuplicadoError(
                'La multa seleccionada ya tiene un pago registrado.'
            )

        fecha_pago = timezone.localdate()
        sancion.fecha_pago = fecha_pago
        self.repository.guardar(sancion)
        return sancion, fecha_pago

    def listar_personales(self, usuario_id: int):
        hoy = timezone.localdate()
        sanciones = self.repository.listar_personales(usuario_id)
        return sanciones, self._resumen_personal(sanciones, hoy), hoy

    def _resumen_administrativo(self, sanciones, hoy: date) -> dict:
        agregados = sanciones.aggregate(
            multas_pendientes=Count(
                'sancion_id',
                filter=Q(tipo='ECONOMICA', fecha_pago__isnull=True),
            ),
            monto_pendiente=Sum(
                'monto',
                filter=Q(tipo='ECONOMICA', fecha_pago__isnull=True),
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
            'multas_pendientes': agregados['multas_pendientes'],
            'monto_pendiente': agregados['monto_pendiente'] or Decimal('0.00'),
            'bloqueos_vigentes': agregados['bloqueos_vigentes'],
        }

    def _resumen_personal(self, sanciones, hoy: date) -> dict:
        agregados = sanciones.aggregate(
            monto_pendiente=Sum(
                'monto',
                filter=Q(tipo='ECONOMICA', fecha_pago__isnull=True),
            ),
            monto_pagado=Sum(
                'monto',
                filter=Q(tipo='ECONOMICA', fecha_pago__isnull=False),
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
            'monto_pendiente': agregados['monto_pendiente'] or Decimal('0.00'),
            'monto_pagado': agregados['monto_pagado'] or Decimal('0.00'),
            'bloqueos_vigentes': agregados['bloqueos_vigentes'],
        }
