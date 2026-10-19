from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from biblioteca.permissions import IsBibliotecario
from biblioteca.presentation.devoluciones_serializers import (
    DevolucionRespuestaSerializer,
    DevolucionSolicitudSerializer,
)
from biblioteca.services.devoluciones_service import (
    DatosDevolucionInvalidosError,
    DevolucionService,
    PrestamoDevolucionNoEncontradoError,
    PrestamoYaDevueltoError,
)


class DevolucionRegistroView(APIView):
    """POST /api/prestamos/{prestamo_id}/devolucion/"""

    permission_classes = [
        IsAuthenticated,
        IsBibliotecario,
    ]

    def post(self, request, prestamo_id):
        solicitud = DevolucionSolicitudSerializer(
            data=request.data
        )
        solicitud.is_valid(raise_exception=True)

        service = DevolucionService()

        try:
            resultado = service.registrar_devolucion(
                prestamo_id=prestamo_id
            )

        except PrestamoDevolucionNoEncontradoError as error:
            return Response(
                {
                    'codigo': error.codigo,
                    'detail': str(error),
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except (
            PrestamoYaDevueltoError,
            DatosDevolucionInvalidosError
        ) as error:
            return Response(
                {
                    'codigo': error.codigo,
                    'detail': str(error),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            DevolucionRespuestaSerializer(resultado).data,
            status=status.HTTP_200_OK
        )