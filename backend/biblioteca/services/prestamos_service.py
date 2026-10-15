
from datetime import date
from typing import Optional

from biblioteca.models import (
    Ejemplar,
    Prestamo,
    Rol,
    Sancion,
    Usuario,
)
from biblioteca.repositories.prestamos_repository import (
    DjangoPrestamoRepository,
    IPrestamoRepository,
)


class PrestamoError(Exception):
    """
    Excepción base para errores del módulo de préstamos.
    """
    pass


class UsuarioPrestamoNoEncontradoError(PrestamoError):
    pass


class EjemplarPrestamoNoEncontradoError(PrestamoError):
    pass


class PrestamoService:
    """
    Servicio de negocio para el módulo de préstamos.

    En esta primera etapa ofrece las operaciones de
    consulta requeridas para preparar el registro.

    La validación integral y el registro transaccional
    serán incorporados en el siguiente commit.
    """

    def __init__(
        self,
        repository: Optional[IPrestamoRepository] = None
    ):
        self.repository = (
            repository
            if repository is not None
            else DjangoPrestamoRepository()
        )

    def listar_roles_lectores(self) -> list[Rol]:
        return list(
            self.repository.listar_roles_lectores()
        )

    def buscar_lectores(
        self,
        termino: str,
        limite: int = 10
    ) -> list[Usuario]:
        """
        Prepara la búsqueda de estudiantes y docentes
        para la pantalla de registro de préstamos.
        """
        if not isinstance(termino, str):
            raise ValueError(
                'El término de búsqueda debe ser texto.'
            )

        if (
            not isinstance(limite, int)
            or isinstance(limite, bool)
            or limite < 1
            or limite > 20
        ):
            raise ValueError(
                'El límite debe estar entre 1 y 20.'
            )

        termino_limpio = termino.strip()

        if not termino_limpio:
            return []

        return self.repository.buscar_lectores(
            termino=termino_limpio,
            limite=limite
        )

    def obtener_usuario(
        self,
        usuario_id: int
    ) -> Usuario:
        usuario = self.repository.obtener_usuario(
            usuario_id
        )

        if usuario is None:
            raise UsuarioPrestamoNoEncontradoError(
                f'No existe un usuario con ID {usuario_id}.'
            )

        return usuario

    def obtener_ejemplar(
        self,
        ejemplar_id: int
    ) -> Ejemplar:
        ejemplar = self.repository.obtener_ejemplar(
            ejemplar_id
        )

        if ejemplar is None:
            raise EjemplarPrestamoNoEncontradoError(
                f'No existe un ejemplar con ID {ejemplar_id}.'
            )

        return ejemplar

    def listar_prestamos_activos(
        self,
        usuario_id: int
    ) -> list[Prestamo]:
        self.obtener_usuario(usuario_id)

        return list(
            self.repository.listar_prestamos_activos(
                usuario_id
            )
        )

    def contar_prestamos_activos(
        self,
        usuario_id: int
    ) -> int:
        self.obtener_usuario(usuario_id)

        return self.repository.contar_prestamos_activos(
            usuario_id
        )

    def tiene_prestamo_activo(
        self,
        ejemplar_id: int
    ) -> bool:
        self.obtener_ejemplar(ejemplar_id)

        return self.repository.tiene_prestamo_activo(
            ejemplar_id
        )

    def listar_sanciones(
        self,
        usuario_id: int
    ) -> list[Sancion]:
        self.obtener_usuario(usuario_id)

        return list(
            self.repository.listar_sanciones(
                usuario_id
            )
        )

    def tiene_adeudos_pendientes(
        self,
        usuario_id: int
    ) -> bool:
        self.obtener_usuario(usuario_id)

        return self.repository.tiene_adeudos_pendientes(
            usuario_id
        )

    def tiene_bloqueo_vigente(
        self,
        usuario_id: int,
        fecha: date
    ) -> bool:
        self.obtener_usuario(usuario_id)

        return self.repository.tiene_bloqueo_vigente(
            usuario_id,
            fecha
        )
