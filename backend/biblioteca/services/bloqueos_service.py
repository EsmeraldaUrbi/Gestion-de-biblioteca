import calendar
from datetime import date, timedelta
from typing import Optional

from django.db import transaction
from django.utils import timezone

from biblioteca.repositories.bloqueos_repository import (
    DjangoBloqueosRepository,
    IBloqueosRepository,
)


class BloqueosService:
    """
    Aplica bloqueos automaticos conforme a P-04 y RN-18.

    El bloqueo comienza un mes calendario despues de
    la fecha limite y dura 30 dias naturales inclusivos.
    """

    DIAS_BLOQUEO = 30

    def __init__(
        self,
        repository: Optional[IBloqueosRepository] = None
    ):
        self.repository = (
            repository
            if repository is not None
            else DjangoBloqueosRepository()
        )

    @staticmethod
    def calcular_inicio_bloqueo(
        fecha_limite: date
    ) -> date:
        """
        Suma un mes calendario a la fecha limite.

        Cuando el mes siguiente tiene menos dias,
        utiliza su ultimo dia.
        """
        if fecha_limite.month == 12:
            anio = fecha_limite.year + 1
            mes = 1
        else:
            anio = fecha_limite.year
            mes = fecha_limite.month + 1

        ultimo_dia = calendar.monthrange(
            anio,
            mes
        )[1]

        dia = min(
            fecha_limite.day,
            ultimo_dia
        )

        return date(anio, mes, dia)

    def calcular_fin_bloqueo(
        self,
        fecha_inicio: date
    ) -> date:
        """
        Calcula el ultimo dia del intervalo inclusivo.
        """
        return (
            fecha_inicio
            + timedelta(days=self.DIAS_BLOQUEO - 1)
        )

    def aplicar_bloqueos(
        self,
        fecha_actual: Optional[date] = None
    ) -> dict:
        """
        Revisa prestamos candidatos y crea bloqueos
        cuando corresponde.

        Cada prestamo se procesa en su propia transaccion.
        Repetir la ejecucion no debe duplicar sanciones.
        """
        hoy = (
            fecha_actual
            if fecha_actual is not None
            else timezone.localdate()
        )

        revisados = 0
        creados = 0

        candidatos = self.repository.listar_prestamos_candidatos(
            hoy
        )

        for prestamo_id in candidatos:
            revisados += 1

            if self._aplicar_bloqueo_prestamo(
                prestamo_id,
                hoy
            ):
                creados += 1

        return {
            'fecha_revision': hoy,
            'prestamos_revisados': revisados,
            'bloqueos_creados': creados,
        }
    
    def aplicar_bloqueos_usuario(
        self,
        usuario_id: int,
        fecha_actual: Optional[date] = None
    ) -> int:
        """
        Registra bloqueos pendientes de un solo usuario.

        Debe ejecutarse antes de iniciar la transaccion
        de registro de un nuevo prestamo.

        Devuelve el numero de bloqueos creados.
        """
        hoy = (
            fecha_actual
            if fecha_actual is not None
            else timezone.localdate()
        )

        candidatos = (
            self.repository.listar_prestamos_candidatos_usuario(
                usuario_id,
                hoy
            )
        )

        creados = 0

        for prestamo in candidatos:
            if self._aplicar_bloqueo_prestamo(
                prestamo.prestamo_id,
                hoy
            ):
                creados += 1

        return creados

    def tiene_bloqueo_por_atraso_vigente(
        self,
        usuario_id: int,
        fecha_actual: date
    ) -> bool:
        """
        Comprueba si algun prestamo sin devolver
        deberia producir un bloqueo vigente.

        Es una consulta de solo lectura. Permite
        informar el rechazo incluso antes de que
        el worker haya creado la sancion.
        """
        candidatos = (
            self.repository.listar_prestamos_candidatos_usuario(
                usuario_id,
                fecha_actual
            )
        )

        for prestamo in candidatos:
            inicio = self.calcular_inicio_bloqueo(
                prestamo.fecha_limite
            )

            fin = self.calcular_fin_bloqueo(
                inicio
            )

            if inicio <= fecha_actual <= fin:
                return True

        return False

    def _aplicar_bloqueo_prestamo(
        self,
        prestamo_id: int,
        fecha_actual: date
    ) -> bool:
        """
        Devuelve True solamente si crea un bloqueo.
        """
        usuario_id = self.repository.obtener_usuario_id(
            prestamo_id
        )

        if usuario_id is None:
            return False

        with transaction.atomic():
            # Mantener el orden de bloqueo del modulo
            # de prestamos: primero el usuario.
            usuario = self.repository.bloquear_usuario(
                usuario_id
            )

            if usuario is None:
                return False

            prestamo = self.repository.bloquear_prestamo(
                prestamo_id
            )

            if prestamo is None:
                return False

            # Revalidar dentro de la transaccion.
            if prestamo.usuario_id != usuario_id:
                return False

            if prestamo.fecha_devolucion is not None:
                return False

            fecha_inicio = self.calcular_inicio_bloqueo(
                prestamo.fecha_limite
            )

            if fecha_actual < fecha_inicio:
                return False

            # No repetir ni reiniciar una sancion existente.
            if self.repository.existe_bloqueo(prestamo_id):
                return False

            fecha_fin = self.calcular_fin_bloqueo(
                fecha_inicio
            )

            self.repository.crear_bloqueo(
                prestamo_id=prestamo_id,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )

            return True
