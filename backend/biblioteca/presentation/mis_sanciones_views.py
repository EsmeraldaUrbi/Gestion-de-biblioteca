from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from biblioteca.permissions import IsEstudianteODocente
from biblioteca.presentation.mis_sanciones_serializers import (
    MiSancionSerializer,
    MisSancionesConsultaSerializer,
)
from biblioteca.services.mis_sanciones_service import MisSancionesService


class MisSancionesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class MisSancionesView(APIView):
    """
    GET /api/sanciones/mias/

    Devuelve exclusivamente las sanciones económicas y bloqueos temporales
    del estudiante o docente autenticado.
    No acepta usuario_id en query params ni en cuerpo para evitar suplantaciones.
    """

    permission_classes = [
        IsAuthenticated,
        IsEstudianteODocente,
    ]

    def get(self, request):
        parametros = MisSancionesConsultaSerializer(
            data=dict(request.query_params.items())
        )
        parametros.is_valid(raise_exception=True)

        tipo = parametros.validated_data.get('tipo', 'todas')
        estado = parametros.validated_data.get('estado', 'todos')

        # La identidad se obtiene estrictamente de la sesión autenticada
        usuario_id = request.user.usuario_id

        service = MisSancionesService()
        sanciones, resumen, hoy = service.consultar(
            usuario_id=usuario_id,
            tipo=tipo,
            estado=estado,
        )

        paginador = MisSancionesPagination()
        pagina = paginador.paginate_queryset(
            sanciones,
            request,
            view=self,
        )

        serializer = MiSancionSerializer(
            pagina,
            many=True,
            context={'hoy': hoy},
        )

        respuesta = paginador.get_paginated_response(
            serializer.data
        )

        # Resumen calculado sobre el conjunto global de sanciones del usuario
        monto_adeudado = resumen.get('monto_total_adeudado')
        monto_str = f"{monto_adeudado:.2f}" if monto_adeudado is not None else "0.00"

        respuesta.data['resumen'] = {
            'total_sanciones': resumen.get('total_sanciones', 0),
            'multas_pendientes': resumen.get('multas_pendientes', 0),
            'monto_total_adeudado': monto_str,
            'bloqueos_vigentes': resumen.get('bloqueos_vigentes', 0),
        }

        return respuesta
