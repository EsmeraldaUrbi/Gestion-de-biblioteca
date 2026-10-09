from abc import ABC, abstractmethod
from datetime import timedelta
from hashlib import sha256
import secrets

from django.utils import timezone

from biblioteca.models import TokenAcceso, Usuario


class IUsuarioAuthRepository(ABC):

    @abstractmethod
    def obtener_por_email(self, email):
        pass


class ITokenAccesoRepository(ABC):

    @abstractmethod
    def crear(self, usuario, duracion_horas):
        pass

    @abstractmethod
    def obtener_por_token_plano(self, token_plano):
        pass

    @abstractmethod
    def revocar(self, token):
        pass


class DjangoUsuarioAuthRepository(
    IUsuarioAuthRepository
):

    def obtener_por_email(self, email):
        return (
            Usuario.objects
            .select_related('rol')
            .filter(email__iexact=email)
            .first()
        )


class DjangoTokenAccesoRepository(
    ITokenAccesoRepository
):

    @staticmethod
    def _calcular_hash(token_plano):
        return sha256(
            token_plano.encode('utf-8')
        ).hexdigest()

    def crear(self, usuario, duracion_horas):
        token_plano = secrets.token_urlsafe(48)

        token_hash = self._calcular_hash(
            token_plano
        )

        expira_en = (
            timezone.now()
            + timedelta(hours=duracion_horas)
        )

        token = TokenAcceso.objects.create(
            usuario=usuario,
            token_hash=token_hash,
            expira_en=expira_en
        )

        return token_plano, token

    def obtener_por_token_plano(
        self,
        token_plano
    ):
        token_hash = self._calcular_hash(
            token_plano
        )

        return (
            TokenAcceso.objects
            .select_related('usuario__rol')
            .filter(
                token_hash=token_hash,
                revocado_en__isnull=True
            )
            .first()
        )

    def revocar(self, token):
        if token.revocado_en is not None:
            return

        token.revocado_en = timezone.now()

        token.save(
            update_fields=['revocado_en']
        )