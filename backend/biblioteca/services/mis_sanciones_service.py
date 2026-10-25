from datetime import date
from typing import Dict, Optional, Tuple

from django.db.models import QuerySet
from django.utils import timezone

from biblioteca.models import Sancion
from biblioteca.repositories.mis_sanciones_repository import (
    DjangoMisSancionesRepository,
    IMisSancionesRepository,
)


class MisSancionesService:
    """
    Servicio de consulta para sanciones y bloqueos personales.
    Aplica las reglas de clasificación y cálculo de estados vigentes/históricos.
    No realiza modificaciones, escrituras ni cobros.
    """

    TIPOS_PERMITIDOS = frozenset({'todas', 'economicas', 'bloqueos'})
    ESTADOS_MULTAS = frozenset({'pendientes', 'pagadas'})
    ESTADOS_BLOQUEOS = frozenset({'programados', 'vigentes', 'concluidos'})
    ESTADOS_PERMITIDOS = frozenset({'todos'} | ESTADOS_MULTAS | ESTADOS_BLOQUEOS)

    def __init__(
        self,
        repository: Optional[IMisSancionesRepository] = None,
    ):
        self.repository = (
            repository
            if repository is not None
            else DjangoMisSancionesRepository()
        )

    @classmethod
    def validar_filtros(cls, tipo: str, estado: str) -> None:
        tipo_normalizado = (tipo or 'todas').strip().lower()
        estado_normalizado = (estado or 'todos').strip().lower()

        if tipo_normalizado not in cls.TIPOS_PERMITIDOS:
            raise ValueError(
                f"El tipo de sanción '{tipo}' no es válido. Opciones: {sorted(cls.TIPOS_PERMITIDOS)}"
            )

        if estado_normalizado not in cls.ESTADOS_PERMITIDOS:
            raise ValueError(
                f"El estado '{estado}' no es válido. Opciones: {sorted(cls.ESTADOS_PERMITIDOS)}"
            )

        if tipo_normalizado == 'economicas' and estado_normalizado in cls.ESTADOS_BLOQUEOS:
            raise ValueError(
                "El estado solicitado no es aplicable a multas económicas."
            )

        if tipo_normalizado == 'bloqueos' and estado_normalizado in cls.ESTADOS_MULTAS:
            raise ValueError(
                "El estado solicitado no es aplicable a bloqueos temporales."
            )

    @staticmethod
    def determinar_estado(sancion: Sancion, hoy: date) -> str:
        """
        Determina el estado funcional de una sanción de acuerdo con sus fechas y tipo real.
        """
        if sancion.tipo == 'ECONOMICA':
            return 'PAGADA' if sancion.fecha_pago is not None else 'PENDIENTE'

        if sancion.tipo == 'BLOQUEO':
            if sancion.fecha_inicio_bloqueo and sancion.fecha_inicio_bloqueo > hoy:
                return 'PROGRAMADO'
            if (
                sancion.fecha_inicio_bloqueo
                and sancion.fecha_fin_bloqueo
                and sancion.fecha_inicio_bloqueo <= hoy <= sancion.fecha_fin_bloqueo
            ):
                return 'VIGENTE'
            return 'CONCLUIDO'

        return 'DESCONOCIDO'

    def consultar(
        self,
        usuario_id: int,
        tipo: str = 'todas',
        estado: str = 'todos',
        hoy: Optional[date] = None,
    ) -> Tuple[QuerySet[Sancion], Dict, date]:
        """
        Recupera las sanciones personales, el resumen general acumulado y la fecha de referencia.
        """
        self.validar_filtros(tipo, estado)

        fecha_referencia = (
            hoy
            if hoy is not None
            else timezone.localdate()
        )

        sanciones = self.repository.listar(
            usuario_id=usuario_id,
            tipo=tipo,
            estado=estado,
            hoy=fecha_referencia,
        )

        resumen = self.repository.obtener_resumen(
            usuario_id=usuario_id,
            hoy=fecha_referencia,
        )

        return sanciones, resumen, fecha_referencia
