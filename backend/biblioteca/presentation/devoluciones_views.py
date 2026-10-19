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

from django.utils import timezone
from rest_framework.pagination import PageNumberPagination

from biblioteca.presentation.devoluciones_serializers import (
    BusquedaDevolucionesSerializer,
    PrestamoActivoDevolucionSerializer,
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

class DevolucionesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class PrestamosActivosDevolucionView(APIView):
    """Consulta préstamos activos y estima su multa."""

    permission_classes = [
        IsAuthenticated,
        IsBibliotecario,
    ]

    def get(self, request):
        solicitud = BusquedaDevolucionesSerializer(
            data=dict(request.query_params.items())
        )
        solicitud.is_valid(raise_exception=True)

        service = DevolucionService()

        try:
            prestamos = service.buscar_prestamos_activos(
                termino=solicitud.validated_data['q']
            )
        except DatosDevolucionInvalidosError as error:
            return Response(
                {
                    'codigo': error.codigo,
                    'detail': str(error),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        paginador = DevolucionesPagination()
        pagina = paginador.paginate_queryset(
            prestamos,
            request,
            view=self
        )

        fecha_referencia = timezone.localdate()

        resultados = [
            service.estimar_devolucion(
                prestamo=prestamo,
                fecha_referencia=fecha_referencia
            )
            for prestamo in pagina
        ]

        serializer = PrestamoActivoDevolucionSerializer(
            resultados,
            many=True
        )

        return paginador.get_paginated_response(
            serializer.data
        )