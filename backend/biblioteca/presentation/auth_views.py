from rest_framework import status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from biblioteca.permissions import (
    IsBibliotecario,
    IsEstudianteODocente,
)
from biblioteca.presentation.auth_serializers import (
    LoginSerializer,
    UsuarioSesionSerializer,
)
from biblioteca.services.auth_service import (
    AuthService,
    CredencialesInvalidasError,
)


class LoginView(APIView):

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        auth_service = AuthService()

        try:
            resultado = (
                auth_service.iniciar_sesion(
                    email=(
                        serializer
                        .validated_data['email']
                    ),
                    password=(
                        serializer
                        .validated_data['password']
                    )
                )
            )

        except CredencialesInvalidasError:
            return Response(
                {
                    'detail': (
                        'Credenciales incorrectas.'
                    )
                },
                status=(
                    status.HTTP_401_UNAUTHORIZED
                )
            )

        usuario_data = (
            UsuarioSesionSerializer(
                resultado.usuario
            ).data
        )

        return Response(
            {
                'token': resultado.token,
                'tipo_token': 'Bearer',
                'expira_en': (
                    resultado
                    .expira_en
                    .isoformat()
                ),
                'usuario': usuario_data,
            },
            status=status.HTTP_200_OK
        )


class LogoutView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def post(self, request):
        AuthService().cerrar_sesion(
            request.auth
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )


class UsuarioActualView(APIView):

    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        serializer = (
            UsuarioSesionSerializer(
                request.user
            )
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class AccesoBibliotecarioView(
    APIView
):

    permission_classes = [
        IsAuthenticated,
        IsBibliotecario,
    ]

    def get(self, request):
        return Response(
            {
                'detail': (
                    'Acceso autorizado '
                    'para bibliotecario.'
                )
            },
            status=status.HTTP_200_OK
        )


class AccesoLectorView(APIView):

    permission_classes = [
        IsAuthenticated,
        IsEstudianteODocente,
    ]

    def get(self, request):
        return Response(
            {
                'detail': (
                    'Acceso autorizado '
                    'para estudiante '
                    'o docente.'
                )
            },
            status=status.HTTP_200_OK
        )