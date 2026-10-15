from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from biblioteca.permissions import IsBibliotecario

from biblioteca.presentation.usuarios_serializers import (
    UsuarioSerializer,
)

from biblioteca.presentation.prestamos_serializers import (
    BusquedaLectoresSerializer,
    ElegibilidadPrestamoSerializer,
    PrestamoRegistroSerializer,
    PrestamoSolicitudSerializer,
)

from biblioteca.services.prestamos_service import (
    AdeudoPendienteError,
    BloqueoVigenteError,
    EjemplarNoDisponibleError,
    EjemplarOcupadoError,
    EjemplarPrestamoNoEncontradoError,
    IdentificadorPrestamoInvalidoError,
    LimitePrestamosAlcanzadoError,
    PrestamoService,
    RolNoHabilitadoError,
    UsuarioPrestamoNoEncontradoError,
)


ERRORES_NO_ENCONTRADOS = (
    UsuarioPrestamoNoEncontradoError,
    EjemplarPrestamoNoEncontradoError,
)

ERRORES_CONFLICTO = (
    RolNoHabilitadoError,
    LimitePrestamosAlcanzadoError,
    EjemplarNoDisponibleError,
    EjemplarOcupadoError,
    AdeudoPendienteError,
    BloqueoVigenteError,
)


def respuesta_error_prestamo(error):
    """
    Convierte errores conocidos del servicio en
    respuestas HTTP consistentes.

    Los errores inesperados no deben ocultarse.
    """

    if isinstance(
        error,
        ERRORES_NO_ENCONTRADOS
    ):
        codigo_http = status.HTTP_404_NOT_FOUND

    elif isinstance(
        error,
        IdentificadorPrestamoInvalidoError
    ):
        codigo_http = status.HTTP_400_BAD_REQUEST

    elif isinstance(
        error,
        ERRORES_CONFLICTO
    ):
        codigo_http = status.HTTP_409_CONFLICT

    else:
        raise error

    return Response(
        {
            'codigo': error.codigo,
            'detail': str(error),
        },
        status=codigo_http
    )


class PrestamoBaseView(APIView):
    """
    Base de las operaciones administrativas de préstamos.

    Solo los bibliotecarios autenticados pueden acceder.
    """

    permission_classes = [
        IsAuthenticated,
        IsBibliotecario,
    ]


class BusquedaLectoresView(PrestamoBaseView):
    """
    GET /api/prestamos/seleccion/usuarios/

    Busca estudiantes y docentes por nombre o correo.
    """

    def get(self, request):
        serializer = BusquedaLectoresSerializer(
            data=dict(request.query_params.items())
        )

        serializer.is_valid(
            raise_exception=True
        )

        datos = serializer.validated_data

        service = PrestamoService()

        usuarios = service.buscar_lectores(
            termino=datos['q'],
            limite=datos['limite']
        )

        return Response(
            {
                'count': len(usuarios),
                'results': UsuarioSerializer(
                    usuarios,
                    many=True
                ).data,
            },
            status=status.HTTP_200_OK
        )


class PrestamoElegibilidadView(PrestamoBaseView):
    """
    GET /api/prestamos/elegibilidad/

    Evalúa las condiciones sin registrar un préstamo.
    """

    def get(self, request):
        serializer = PrestamoSolicitudSerializer(
            data=dict(request.query_params.items())
        )

        serializer.is_valid(
            raise_exception=True
        )

        datos = serializer.validated_data

        service = PrestamoService()

        try:
            resultado = service.evaluar_elegibilidad(
                usuario_id=datos['usuario_id'],
                ejemplar_id=datos['ejemplar_id']
            )

        except (
            UsuarioPrestamoNoEncontradoError,
            EjemplarPrestamoNoEncontradoError,
            IdentificadorPrestamoInvalidoError
        ) as error:
            return respuesta_error_prestamo(error)

        return Response(
            ElegibilidadPrestamoSerializer(
                resultado
            ).data,
            status=status.HTTP_200_OK
        )


class PrestamosRegistroView(PrestamoBaseView):
    """
    POST /api/prestamos/

    Registra un préstamo aplicando las reglas del servicio.
    """

    def post(self, request):
        serializer = PrestamoSolicitudSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        datos = serializer.validated_data

        service = PrestamoService()

        try:
            prestamo = service.registrar_prestamo(
                usuario_id=datos['usuario_id'],
                ejemplar_id=datos['ejemplar_id']
            )

        except (
            UsuarioPrestamoNoEncontradoError,
            EjemplarPrestamoNoEncontradoError,
            IdentificadorPrestamoInvalidoError,
            RolNoHabilitadoError,
            LimitePrestamosAlcanzadoError,
            EjemplarNoDisponibleError,
            EjemplarOcupadoError,
            AdeudoPendienteError,
            BloqueoVigenteError
        ) as error:
            return respuesta_error_prestamo(error)

        return Response(
            PrestamoRegistroSerializer(
                prestamo
            ).data,
            status=status.HTTP_201_CREATED
        )