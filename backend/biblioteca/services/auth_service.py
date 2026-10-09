from dataclasses import dataclass
from datetime import datetime

from django.conf import settings

from biblioteca.models import Usuario
from biblioteca.repositories.auth_repository import (
    DjangoTokenAccesoRepository,
    DjangoUsuarioAuthRepository,
    ITokenAccesoRepository,
    IUsuarioAuthRepository,
)


class CredencialesInvalidasError(Exception):
    pass


@dataclass(frozen=True)
class ResultadoInicioSesion:
    usuario: Usuario
    token: str
    expira_en: datetime


class AuthService:

    def __init__(
        self,
        usuario_repository=None,
        token_repository=None
    ):
        self.usuario_repository = (
            usuario_repository
            or DjangoUsuarioAuthRepository()
        )

        self.token_repository = (
            token_repository
            or DjangoTokenAccesoRepository()
        )

    def iniciar_sesion(
        self,
        email,
        password
    ):
        email_normalizado = (
            email
            .strip()
            .lower()
        )

        usuario = (
            self.usuario_repository
            .obtener_por_email(
                email_normalizado
            )
        )

        if (
            usuario is None
            or not usuario.check_password(password)
        ):
            raise CredencialesInvalidasError()

        token_plano, token = (
            self.token_repository.crear(
                usuario=usuario,
                duracion_horas=(
                    settings.AUTH_TOKEN_TTL_HOURS
                )
            )
        )

        return ResultadoInicioSesion(
            usuario=usuario,
            token=token_plano,
            expira_en=token.expira_en
        )

    def cerrar_sesion(self, token):
        self.token_repository.revocar(token)