from datetime import date
from decimal import Decimal
from typing import Optional

from django.db import transaction
from django.utils import timezone

from biblioteca.repositories.devoluciones_repository import (
    DjangoDevolucionesRepository,
    IDevolucionesRepository,
)
from biblioteca.services.bloqueos_service import BloqueosService


class DevolucionError(Exception):
    """Excepción base del módulo de devoluciones."""

    codigo = 'ERROR_DEVOLUCION'


class PrestamoDevolucionNoEncontradoError(DevolucionError):
    codigo = 'PRESTAMO_NO_ENCONTRADO'


class PrestamoYaDevueltoError(DevolucionError):
    codigo = 'PRESTAMO_YA_DEVUELTO'


class DatosDevolucionInvalidosError(DevolucionError):
    codigo = 'DATOS_DEVOLUCION_INVALIDOS'


class DevolucionService:
    """Registra devoluciones y calcula multas por retraso."""

    TARIFA_DIARIA = Decimal('5.00')

    def __init__(
        self,
        repository: Optional[IDevolucionesRepository] = None
    ):
        self.repository = (
            repository
            if repository is not None
            else DjangoDevolucionesRepository()
        )

    def registrar_devolucion(
        self,
        prestamo_id: int,
        fecha_devolucion: Optional[date] = None
    ) -> dict:
        """
        Registra la devolución y su multa en una transacción.

        La fecha opcional permite probar el servicio con fechas
        controladas. La API utilizará la fecha del servidor.
        """
        if (
            not isinstance(prestamo_id, int)
            or isinstance(prestamo_id, bool)
            or prestamo_id <= 0
        ):
            raise DatosDevolucionInvalidosError(
                'prestamo_id debe ser un entero positivo.'
            )

        if (
            fecha_devolucion is not None
            and type(fecha_devolucion) is not date
        ):
            raise DatosDevolucionInvalidosError(
                'La fecha de devolución debe ser una fecha válida.'
            )

        # Lectura inicial para identificar qué filas bloquear.
        referencia = self.repository.obtener_prestamo(
            prestamo_id
        )

        if referencia is None:
            raise PrestamoDevolucionNoEncontradoError(
                f'No existe un préstamo con ID {prestamo_id}.'
            )

        with transaction.atomic():
            # Mantener el orden utilizado por préstamos.
            usuario = self.repository.bloquear_usuario(
                referencia.usuario_id
            )

            ejemplar = self.repository.bloquear_ejemplar(
                referencia.ejemplar_id
            )

            prestamo = self.repository.bloquear_prestamo(
                prestamo_id
            )

            if (
                usuario is None
                or ejemplar is None
                or prestamo is None
            ):
                raise PrestamoDevolucionNoEncontradoError(
                    'El préstamo o sus registros asociados '
                    'ya no existen.'
                )

            # Revalidar las referencias tras adquirir los bloqueos.
            if (
                prestamo.usuario_id != usuario.usuario_id
                or prestamo.ejemplar_id != ejemplar.ejemplar_id
            ):
                raise DatosDevolucionInvalidosError(
                    'Los datos del préstamo cambiaron. '
                    'Vuelve a intentar la operación.'
                )

            if prestamo.fecha_devolucion is not None:
                raise PrestamoYaDevueltoError(
                    'El préstamo ya tiene una devolución registrada.'
                )

            hoy = timezone.localdate()

            fecha_real = (
                fecha_devolucion
                if fecha_devolucion is not None
                else hoy
            )

            if fecha_real < prestamo.fecha_prestamo:
                raise DatosDevolucionInvalidosError(
                    'La devolución no puede ser anterior '
                    'a la fecha del préstamo.'
                )

            if fecha_real > hoy:
                raise DatosDevolucionInvalidosError(
                    'La devolución no puede tener una fecha futura.'
                )

            dias_retraso = max(
                (fecha_real - prestamo.fecha_limite).days,
                0
            )

            monto_multa = (
                self.TARIFA_DIARIA * dias_retraso
            ).quantize(Decimal('0.01'))

            # Registrar bloqueos que ya correspondían antes de
            # cerrar el préstamo, aunque el worker no haya pasado.
            # No cancela ni reinicia bloqueos existentes.
            BloqueosService().aplicar_bloqueos_usuario(
                usuario_id=prestamo.usuario_id,
                fecha_actual=fecha_real
            )

            self.repository.registrar_fecha_devolucion(
                prestamo=prestamo,
                fecha_devolucion=fecha_real
            )

            sancion = None

            if dias_retraso > 0:
                sancion = self.repository.crear_multa(
                    prestamo_id=prestamo.prestamo_id,
                    monto=monto_multa
                )

            resultado = {
                'mensaje': (
                    'Devolución registrada con retraso. '
                    'Multa generada.'
                    if sancion is not None
                    else 'Devolución registrada correctamente.'
                ),
                'prestamo_id': prestamo.prestamo_id,
                'fecha_devolucion': fecha_real,
                'dias_retraso': dias_retraso,
                'monto_multa': format(monto_multa, '.2f'),
                'sancion_generada': sancion is not None,
                'ejemplar_estado': ejemplar.estado,
            }

            if sancion is not None:
                resultado['sancion_id'] = sancion.sancion_id

            return resultado