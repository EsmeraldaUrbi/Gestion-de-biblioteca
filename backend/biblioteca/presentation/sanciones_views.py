from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from biblioteca.permissions import IsBibliotecario, IsEstudianteODocente
from biblioteca.presentation.sanciones_serializers import (
    PagoSancionSerializer,
    SancionesConsultaSerializer,
    SancionSerializer,
)
from biblioteca.services.sanciones_service import (
    PagoSancionDuplicadoError,
    PagoSancionNoPermitidoError,
    SancionNoEncontradaError,
    SancionesService,
)


class SancionesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class SancionesListView(APIView):
    """GET /api/sanciones/ para consulta administrativa."""

    permission_classes = [IsAuthenticated, IsBibliotecario]

    def get(self, request):
        parametros = SancionesConsultaSerializer(data=dict(request.query_params.items()))
        parametros.is_valid(raise_exception=True)

        service = SancionesService()
        sanciones, resumen, hoy = service.listar_administrativas(
            termino=parametros.validated_data.get('q', '').strip(),
            tipo=parametros.validated_data.get('tipo', 'todos'),
            estado=parametros.validated_data.get('estado', 'todos'),
        )

        paginador = SancionesPagination()
        pagina = paginador.paginate_queryset(sanciones, request, view=self)
        respuesta = paginador.get_paginated_response(
            SancionSerializer(pagina, many=True, context={'hoy': hoy}).data,
        )
        respuesta.data['resumen'] = resumen
        return respuesta


class SancionDetailView(APIView):
    permission_classes = [IsAuthenticated, IsBibliotecario]

    def get(self, request, sancion_id):
        service = SancionesService()
        try:
            sancion, hoy = service.obtener_administrativa(sancion_id)
        except SancionNoEncontradaError as error:
            return Response(
                {'codigo': error.codigo, 'detail': str(error)},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(SancionSerializer(sancion, context={'hoy': hoy}).data)


class SancionPagoView(APIView):
    """POST /api/sanciones/{id}/pago/ registra el pago total en caja."""

    permission_classes = [IsAuthenticated, IsBibliotecario]

    def post(self, request, sancion_id):
        solicitud = PagoSancionSerializer(data=request.data)
        solicitud.is_valid(raise_exception=True)

        service = SancionesService()
        try:
            sancion, hoy = service.registrar_pago(sancion_id)
        except SancionNoEncontradaError as error:
            return Response(
                {'codigo': error.codigo, 'detail': str(error)},
                status=status.HTTP_404_NOT_FOUND,
            )
        except (PagoSancionNoPermitidoError, PagoSancionDuplicadoError) as error:
            return Response(
                {'codigo': error.codigo, 'detail': str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(SancionSerializer(sancion, context={'hoy': hoy}).data)


class MisSancionesView(APIView):
    """GET /api/sanciones/mias/ para el lector autenticado."""

    permission_classes = [IsAuthenticated, IsEstudianteODocente]

    def get(self, request):
        service = SancionesService()
        sanciones, resumen, hoy = service.listar_personales(request.user.usuario_id)

        paginador = SancionesPagination()
        pagina = paginador.paginate_queryset(sanciones, request, view=self)
        respuesta = paginador.get_paginated_response(
            SancionSerializer(pagina, many=True, context={'hoy': hoy}).data,
        )
        respuesta.data['resumen'] = resumen
        return respuesta
