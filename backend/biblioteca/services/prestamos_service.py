from datetime import date, timedelta
from typing import Optional

from django.db import transaction
from django.utils import timezone

from biblioteca.models import (
    Ejemplar,
    EstadoEjemplar,
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


class IdentificadorPrestamoInvalidoError(PrestamoError):
    pass


class RolNoHabilitadoError(PrestamoError):
    pass


class LimitePrestamosAlcanzadoError(PrestamoError):
    pass


class EjemplarNoDisponibleError(PrestamoError):
    pass


class EjemplarOcupadoError(PrestamoError):
    pass


class AdeudoPendienteError(PrestamoError):
    pass


class BloqueoVigenteError(PrestamoError):
    pass


class PrestamoService:
    """
    Servicio de negocio para el registro de préstamos.

    Gestiona las consultas y el registro de préstamos físicos
    respetando las reglas establecidas por el proyecto.

    La persistencia se delega al repositorio correspondiente.
    """

    DIAS_PRESTAMO = 30

    ROLES_LECTORES = frozenset({
        'estudiante',
        'docente',
    })

    def __init__(
        self,
        repository: Optional[IPrestamoRepository] = None
    ):
        self.repository = (
            repository
            if repository is not None
            else DjangoPrestamoRepository()
        )

    # -----------------------------------------
    # Consultas del servicio
    # -----------------------------------------

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
        Busca estudiantes y docentes por nombre o correo.
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

    # -----------------------------------------
    # Validaciones del registro
    # -----------------------------------------

    @staticmethod
    def _validar_id(
        valor: int,
        nombre: str
    ) -> None:
        """
        Rechaza identificadores vacíos, negativos,
        booleanos y valores que no sean enteros.
        """
        if (
            not isinstance(valor, int)
            or isinstance(valor, bool)
            or valor <= 0
        ):
            raise IdentificadorPrestamoInvalidoError(
                f'{nombre} debe ser un entero positivo.'
            )

    # -----------------------------------------
    # Registro definitivo del préstamo
    # -----------------------------------------

    def registrar_prestamo(
        self,
        usuario_id: int,
        ejemplar_id: int
    ) -> Prestamo:
        """
        Registra un préstamo físico cuando cumple las
        condiciones del usuario y del ejemplar.

        Orden de bloqueo:
        1. Usuario.
        2. Ejemplar.

        La transacción impide que solicitudes simultáneas
        presten dos veces la misma copia o superen el límite
        del mismo usuario.
        """

        self._validar_id(
            usuario_id,
            'usuario_id'
        )

        self._validar_id(
            ejemplar_id,
            'ejemplar_id'
        )

        with transaction.atomic():

            # -------------------------------------
            # 1. Obtener y bloquear al usuario
            # -------------------------------------

            usuario = self.repository.obtener_usuario(
                usuario_id,
                con_bloqueo=True
            )

            if usuario is None:
                raise UsuarioPrestamoNoEncontradoError(
                    f'No existe un usuario con ID {usuario_id}.'
                )

            # -------------------------------------
            # 2. Validar el rol del lector
            # -------------------------------------

            rol = usuario.rol

            nombre_rol = (
                rol.nombre
                .strip()
                .casefold()
            )

            if nombre_rol not in self.ROLES_LECTORES:
                raise RolNoHabilitadoError(
                    'Solo estudiantes y docentes pueden '
                    'recibir préstamos.'
                )

            # -------------------------------------
            # 3. Obtener y bloquear el ejemplar
            # -------------------------------------

            ejemplar = self.repository.obtener_ejemplar(
                ejemplar_id,
                con_bloqueo=True
            )

            if ejemplar is None:
                raise EjemplarPrestamoNoEncontradoError(
                    f'No existe un ejemplar con ID {ejemplar_id}.'
                )

            # -------------------------------------
            # 4. Comprobar estado operativo
            # -------------------------------------

            if ejemplar.estado != EstadoEjemplar.ACTIVO:
                raise EjemplarNoDisponibleError(
                    'El ejemplar no está ACTIVO y '
                    'no puede prestarse.'
                )

            # -------------------------------------
            # 5. Comprobar ocupación del ejemplar
            # -------------------------------------

            ejemplar_ocupado = (
                self.repository.tiene_prestamo_activo(
                    ejemplar_id,
                    con_bloqueo=True
                )
            )

            if ejemplar_ocupado:
                raise EjemplarOcupadoError(
                    'El ejemplar ya tiene un préstamo activo.'
                )

            # -------------------------------------
            # 6. Comprobar límite de préstamos
            # -------------------------------------

            prestamos_activos = (
                self.repository.contar_prestamos_activos(
                    usuario_id,
                    con_bloqueo=True
                )
            )

            limite_permitido = (
                rol.limite_prestamos_activos
            )

            if (
                limite_permitido <= 0
                or prestamos_activos >= limite_permitido
            ):
                raise LimitePrestamosAlcanzadoError(
                    'El usuario alcanzó su límite de '
                    'préstamos activos.'
                )

            # -------------------------------------
            # 7. Comprobar adeudos económicos
            # -------------------------------------

            tiene_adeudos = (
                self.repository.tiene_adeudos_pendientes(
                    usuario_id
                )
            )

            if tiene_adeudos:
                raise AdeudoPendienteError(
                    'El usuario tiene multas '
                    'pendientes de pago.'
                )

            # -------------------------------------
            # 8. Comprobar bloqueos vigentes
            # -------------------------------------

            fecha_actual = timezone.localdate()

            tiene_bloqueo = (
                self.repository.tiene_bloqueo_vigente(
                    usuario_id,
                    fecha_actual
                )
            )

            if tiene_bloqueo:
                raise BloqueoVigenteError(
                    'El usuario tiene un bloqueo '
                    'temporal vigente.'
                )

            # -------------------------------------
            # 9. Calcular la fecha límite
            # -------------------------------------

            fecha_limite = (
                fecha_actual
                + timedelta(days=self.DIAS_PRESTAMO)
            )

            # -------------------------------------
            # 10. Registrar el préstamo
            # -------------------------------------

            prestamo = self.repository.crear_prestamo(
                usuario_id=usuario_id,
                ejemplar_id=ejemplar_id,
                fecha_prestamo=fecha_actual,
                fecha_limite=fecha_limite
            )

            return prestamo