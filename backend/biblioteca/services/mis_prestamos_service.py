from django.utils import timezone

from biblioteca.repositories.mis_prestamos_repository import (
    DjangoMisPrestamosRepository,
    IMisPrestamosRepository,
)


class MisPrestamosService:
    """
    Servicio de consulta de préstamos personales.

    No registra ni modifica préstamos, devoluciones,
    multas, bloqueos ni pagos.
    """

    FILTROS_PERMITIDOS = frozenset({
        'todos',
        'activos',
        'vencidos',
        'devueltos',
    })

    def __init__(
        self,
        repository: IMisPrestamosRepository | None = None
    ):
        self.repository = (
            repository
            if repository is not None
            else DjangoMisPrestamosRepository()
        )

    def consultar(
        self,
        usuario_id: int,
        filtro: str = 'todos'
    ):
        """
        Recupera los préstamos, estadísticas y fecha
        utilizada en el cálculo de estados.
        """

        if filtro not in self.FILTROS_PERMITIDOS:
            raise ValueError(
                'El filtro de préstamos no es válido.'
            )

        hoy = timezone.localdate()

        prestamos = self.repository.listar(
            usuario_id=usuario_id,
            filtro=filtro,
            hoy=hoy
        )

        resumen = self.repository.obtener_resumen(
            usuario_id=usuario_id,
            hoy=hoy
        )

        return prestamos, resumen, hoy

    def obtener_estado_cuenta(
        self,
        usuario_id: int,
        limite_prestamos: int,
        resumen: dict,
        hoy
    ) -> dict:
        """
        Determina si el lector cumple las condiciones
        personales conocidas para obtener un préstamo.

        No comprueba un ejemplar específico; esa
        validación corresponde a registrar_prestamo().
        """

        prestamos_activos = resumen['activos']

        restricciones = (
            self.repository.consultar_restricciones(
                usuario_id=usuario_id,
                hoy=hoy
            )
        )

        cupos_disponibles = max(
            limite_prestamos - prestamos_activos,
            0
        )

        motivos = []

        if prestamos_activos >= limite_prestamos:
            motivos.append({
                'codigo': 'LIMITE_PRESTAMOS',
                'mensaje': (
                    'Has alcanzado el límite de préstamos '
                    'activos permitido para tu rol.'
                )
            })

        if restricciones['adeudos_pendientes']:
            motivos.append({
                'codigo': 'ADEUDO_PENDIENTE',
                'mensaje': (
                    'Tienes un adeudo económico '
                    'pendiente de pago registrado.'
                )
            })

        if restricciones['bloqueo_vigente']:
            motivos.append({
                'codigo': 'BLOQUEO_VIGENTE',
                'mensaje': (
                    'Tienes un bloqueo temporal vigente '
                    'registrado en el sistema.'
                )
            })

        return {
            'limite_prestamos_activos': limite_prestamos,
            'prestamos_activos': prestamos_activos,
            'cupos_disponibles': cupos_disponibles,
            'adeudos_pendientes': (
                restricciones['adeudos_pendientes']
            ),
            'bloqueo_vigente': (
                restricciones['bloqueo_vigente']
            ),
            'puede_solicitar': len(motivos) == 0,
            'motivos': motivos,
        }