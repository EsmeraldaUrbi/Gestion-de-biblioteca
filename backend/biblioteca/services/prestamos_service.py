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
    Excepción base del módulo de préstamos.

    El código permite identificar los errores de negocio
    desde las respuestas de la API.
    """
    codigo = 'ERROR_PRESTAMO'


class UsuarioPrestamoNoEncontradoError(PrestamoError):
    codigo = 'USUARIO_NO_ENCONTRADO'


class EjemplarPrestamoNoEncontradoError(PrestamoError):
    codigo = 'EJEMPLAR_NO_ENCONTRADO'


class IdentificadorPrestamoInvalidoError(PrestamoError):
    codigo = 'IDENTIFICADOR_INVALIDO'


class RolNoHabilitadoError(PrestamoError):
    codigo = 'ROL_NO_HABILITADO'


class LimitePrestamosAlcanzadoError(PrestamoError):
    codigo = 'LIMITE_PRESTAMOS'


class EjemplarNoDisponibleError(PrestamoError):
    codigo = 'EJEMPLAR_NO_DISPONIBLE'


class EjemplarOcupadoError(PrestamoError):
    codigo = 'EJEMPLAR_OCUPADO'


class AdeudoPendienteError(PrestamoError):
    codigo = 'ADEUDO_PENDIENTE'


class BloqueoVigenteError(PrestamoError):
    codigo = 'BLOQUEO_VIGENTE'


class PrestamoService:
    """
    Servicio de negocio para el registro de préstamos.

    Centraliza las reglas de elegibilidad y delega las
    consultas y operaciones de escritura al repositorio.

    La evaluación previa es informativa y de solo lectura.
    El registro definitivo utiliza una transacción y
    bloqueos sobre el usuario y el ejemplar.
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
    # Consultas
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
    # Validaciones compartidas
    # -----------------------------------------

    @staticmethod
    def _validar_id(
        valor: int,
        nombre: str
    ) -> None:
        if (
            not isinstance(valor, int)
            or isinstance(valor, bool)
            or valor <= 0
        ):
            raise IdentificadorPrestamoInvalidoError(
                f'{nombre} debe ser un entero positivo.'
            )

    def _validar_condiciones(
        self,
        usuario: Usuario,
        ejemplar: Ejemplar,
        fecha_actual: date,
        con_bloqueo: bool = False
    ) -> None:
        """
        Comprueba las condiciones del préstamo.

        En la evaluación previa se ejecutan lecturas normales.
        Durante el registro se utilizan lecturas bloqueantes
        después de bloquear usuario y ejemplar.
        """

        # 1. Rol autorizado para recibir préstamos.
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

        # 2. Estado operativo del ejemplar.
        if ejemplar.estado != EstadoEjemplar.ACTIVO:
            raise EjemplarNoDisponibleError(
                'El ejemplar no está ACTIVO y '
                'no puede prestarse.'
            )

        # 3. El ejemplar no debe estar prestado.
        ejemplar_ocupado = (
            self.repository.tiene_prestamo_activo(
                ejemplar.ejemplar_id,
                con_bloqueo=con_bloqueo
            )
        )

        if ejemplar_ocupado:
            raise EjemplarOcupadoError(
                'El ejemplar ya tiene un préstamo activo.'
            )

        # 4. Límite de préstamos del usuario.
        prestamos_activos = (
            self.repository.contar_prestamos_activos(
                usuario.usuario_id,
                con_bloqueo=con_bloqueo
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

        # 5. Adeudos económicos pendientes.
        if self.repository.tiene_adeudos_pendientes(
            usuario.usuario_id
        ):
            raise AdeudoPendienteError(
                'El usuario tiene multas pendientes de pago.'
            )

        # 6. Bloqueos temporales vigentes.
        if self.repository.tiene_bloqueo_vigente(
            usuario.usuario_id,
            fecha_actual
        ):
            raise BloqueoVigenteError(
                'El usuario tiene un bloqueo temporal vigente.'
            )

    # -----------------------------------------
    # Evaluación previa del préstamo
    # -----------------------------------------

    def evaluar_elegibilidad(
        self,
        usuario_id: int,
        ejemplar_id: int
    ) -> dict:
        """
        Evalúa si un préstamo podría registrarse.

        No modifica la base de datos ni bloquea registros.
        Retorna la primera condición incumplida, si existe.

        El resultado puede cambiar antes del registro,
        por lo que el POST debe repetir todas las reglas.
        """

        self._validar_id(
            usuario_id,
            'usuario_id'
        )

        self._validar_id(
            ejemplar_id,
            'ejemplar_id'
        )

        usuario = self.obtener_usuario(
            usuario_id
        )

        ejemplar = self.obtener_ejemplar(
            ejemplar_id
        )

        fecha_actual = timezone.localdate()

        fecha_limite = (
            fecha_actual
            + timedelta(days=self.DIAS_PRESTAMO)
        )

        resultado = {
            'elegible': True,
            'motivos': [],
            'usuario': usuario,
            'ejemplar': ejemplar,
            'prestamos_activos': (
                self.repository.contar_prestamos_activos(
                    usuario_id
                )
            ),
            'limite_prestamos_activos': (
                usuario.rol.limite_prestamos_activos
            ),
            'fecha_prestamo': fecha_actual,
            'fecha_limite': fecha_limite,
        }

        try:
            self._validar_condiciones(
                usuario=usuario,
                ejemplar=ejemplar,
                fecha_actual=fecha_actual,
                con_bloqueo=False
            )

        except PrestamoError as error:
            resultado['elegible'] = False

            resultado['motivos'] = [
                {
                    'codigo': error.codigo,
                    'mensaje': str(error),
                }
            ]

        return resultado

    # -----------------------------------------
    # Registro definitivo del préstamo
    # -----------------------------------------

    def registrar_prestamo(
        self,
        usuario_id: int,
        ejemplar_id: int
    ) -> Prestamo:
        """
        Registra un préstamo aplicando las reglas
        de negocio y el control transaccional.

        Orden de bloqueo:
        1. Usuario.
        2. Ejemplar.

        Revalida las condiciones dentro de la
        transacción antes de guardar el préstamo.
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

            # 1. Bloquear la fila del usuario.
            usuario = self.repository.obtener_usuario(
                usuario_id,
                con_bloqueo=True
            )

            if usuario is None:
                raise UsuarioPrestamoNoEncontradoError(
                    f'No existe un usuario con ID {usuario_id}.'
                )

            # 2. Bloquear la fila del ejemplar.
            ejemplar = self.repository.obtener_ejemplar(
                ejemplar_id,
                con_bloqueo=True
            )

            if ejemplar is None:
                raise EjemplarPrestamoNoEncontradoError(
                    f'No existe un ejemplar con ID {ejemplar_id}.'
                )

            fecha_actual = timezone.localdate()

            # 3. Validar nuevamente todas las condiciones.
            self._validar_condiciones(
                usuario=usuario,
                ejemplar=ejemplar,
                fecha_actual=fecha_actual,
                con_bloqueo=True
            )

            # 4. Calcular fecha límite.
            fecha_limite = (
                fecha_actual
                + timedelta(days=self.DIAS_PRESTAMO)
            )

            # 5. Registrar el préstamo.
            prestamo = self.repository.crear_prestamo(
                usuario_id=usuario_id,
                ejemplar_id=ejemplar_id,
                fecha_prestamo=fecha_actual,
                fecha_limite=fecha_limite
            )

            return prestamo