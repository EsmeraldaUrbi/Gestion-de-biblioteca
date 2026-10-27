from django.utils import timezone

from biblioteca.repositories.prestamos_admin_repository import (
    DjangoPrestamosAdminRepository,
)


class PrestamosAdminService:
    """
    Servicio de consulta administrativa de préstamos.

    Mantiene separada esta lectura del servicio
    transaccional de registro de préstamos.
    """

    ESTADOS_PERMITIDOS = frozenset({
        'todos',
        'en_prestamo',
        'vencidos',
        'devueltos',
    })

    def __init__(self, repository=None):
        self.repository = (
            repository
            if repository is not None
            else DjangoPrestamosAdminRepository()
        )

    def consultar(
        self,
        estado: str = 'todos',
        termino: str = '',
    ):
        if estado not in self.ESTADOS_PERMITIDOS:
            raise ValueError(
                'El estado de préstamo no es válido.'
            )

        termino = termino.strip()
        hoy = timezone.localdate()

        prestamos = self.repository.listar(
            estado=estado,
            termino=termino,
            hoy=hoy,
        )

        resumen = self.repository.obtener_resumen(
            hoy=hoy,
        )

        return prestamos, resumen, hoy