from django.db import IntegrityError

from biblioteca.models import Usuario
from biblioteca.repositories.usuarios_repository import (
    DjangoRolRepository,
    DjangoUsuarioRepository,
    IRolRepository,
    IUsuarioRepository,
)


class UsuarioNoEncontradoError(Exception):
    pass


class RolNoEncontradoError(Exception):
    pass


class CorreoDuplicadoError(Exception):
    pass


class CambioRolNoPermitidoError(Exception):
    pass


class UsuarioService:
    """
    Gestiona las operaciones y reglas de negocio de usuarios.
    """

    def __init__(
        self,
        usuario_repository: IUsuarioRepository = None,
        rol_repository: IRolRepository = None
    ):
        self.usuario_repository = (
            usuario_repository
            if usuario_repository is not None
            else DjangoUsuarioRepository()
        )

        self.rol_repository = (
            rol_repository
            if rol_repository is not None
            else DjangoRolRepository()
        )

    def listar_usuarios(self):
        return self.usuario_repository.listar()

    def obtener_usuario(self, usuario_id):
        usuario = self.usuario_repository.obtener_por_id(
            usuario_id
        )

        if usuario is None:
            raise UsuarioNoEncontradoError()

        return usuario

    def listar_roles(self):
        return self.rol_repository.listar()

    def obtener_rol(self, rol_id):
        rol = self.rol_repository.obtener_por_id(rol_id)

        if rol is None:
            raise RolNoEncontradoError()

        return rol

    def validar_email_disponible(
        self,
        email,
        usuario_id=None
    ):
        existente = self.usuario_repository.obtener_por_email(
            email
        )

        if (
            existente is not None
            and existente.usuario_id != usuario_id
        ):
            raise CorreoDuplicadoError()

    def registrar_usuario(self, datos):
        email = datos['email'].strip().lower()

        self.validar_email_disponible(email)

        rol = self.obtener_rol(datos['rol_id'])

        usuario = Usuario(
            nombre=datos['nombre'].strip(),
            email=email,
            direccion=datos.get('direccion'),
            telefono=datos.get('telefono'),
            rol=rol
        )

        usuario.set_password(datos['password'])

        try:
            return self.usuario_repository.crear(usuario)
        except IntegrityError:
            raise CorreoDuplicadoError()

    def modificar_usuario(self, usuario_id, datos):
        usuario = self.obtener_usuario(usuario_id)

        campos_actualizados = []

        if 'nombre' in datos:
            usuario.nombre = datos['nombre'].strip()
            campos_actualizados.append('nombre')

        if 'email' in datos:
            email = datos['email'].strip().lower()

            self.validar_email_disponible(
                email,
                usuario.usuario_id
            )

            usuario.email = email
            campos_actualizados.append('email')

        if 'direccion' in datos:
            usuario.direccion = datos['direccion']
            campos_actualizados.append('direccion')

        if 'telefono' in datos:
            usuario.telefono = datos['telefono']
            campos_actualizados.append('telefono')

        if 'rol_id' in datos:
            nuevo_rol = self.obtener_rol(datos['rol_id'])

            es_bibliotecario = (
                nuevo_rol.nombre.strip().casefold()
                == 'bibliotecario'
            )

            cambio_de_rol = (
                usuario.rol_id != nuevo_rol.rol_id
            )

            if (
                es_bibliotecario
                and cambio_de_rol
                and self.usuario_repository.tiene_prestamos_activos(
                    usuario.usuario_id
                )
            ):
                raise CambioRolNoPermitidoError()

            usuario.rol = nuevo_rol
            campos_actualizados.append('rol')

        if not campos_actualizados:
            return usuario

        try:
            return self.usuario_repository.actualizar(
                usuario,
                campos_actualizados
            )
        except IntegrityError:
            raise CorreoDuplicadoError()
