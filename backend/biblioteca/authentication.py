from django.utils import timezone
from rest_framework.authentication import (
    BaseAuthentication,
    get_authorization_header,
)
from rest_framework.exceptions import (
    AuthenticationFailed,
)

from biblioteca.repositories.auth_repository import (
    DjangoTokenAccesoRepository,
)


class BibliotecaTokenAuthentication(
    BaseAuthentication
):

    keyword = b'bearer'

    def __init__(self):
        self.token_repository = (
            DjangoTokenAccesoRepository()
        )

    def authenticate(self, request):
        auth = (
            get_authorization_header(request)
            .split()
        )

        if not auth:
            return None

        if auth[0].lower() != self.keyword:
            return None

        if len(auth) != 2:
            raise AuthenticationFailed(
                'Formato de autorización inválido.'
            )

        try:
            token_plano = auth[1].decode(
                'utf-8'
            )
        except UnicodeDecodeError:
            raise AuthenticationFailed(
                'Token inválido.'
            )

        token = (
            self.token_repository
            .obtener_por_token_plano(
                token_plano
            )
        )

        if token is None:
            raise AuthenticationFailed(
                'Token inválido o revocado.'
            )

        if token.expira_en <= timezone.now():
            self.token_repository.revocar(
                token
            )

            raise AuthenticationFailed(
                'La sesión ha vencido.'
            )

        return (
            token.usuario,
            token
        )

    def authenticate_header(self, request):
        return 'Bearer'