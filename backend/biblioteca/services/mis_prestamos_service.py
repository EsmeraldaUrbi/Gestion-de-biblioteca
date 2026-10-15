from django.utils import timezone

from biblioteca.repositories.mis_prestamos_repository import (
    DjangoMisPrestamosRepository,
    IMisPrestamosRepository,
)


class MisPrestamosService:
    """
    Servicio de consulta del historial personal.

    No registra, modifica ni elimina préstamos.
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