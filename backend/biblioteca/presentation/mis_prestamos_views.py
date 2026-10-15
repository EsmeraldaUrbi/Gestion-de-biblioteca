from rest_framework.permissions import IsAuthenticated

from rest_framework.pagination import (
    PageNumberPagination,
)

from rest_framework.views import APIView

from biblioteca.permissions import (
    IsEstudianteODocente,
)

from biblioteca.presentation.mis_prestamos_serializers import (
    MiPrestamoSerializer,
    MisPrestamosConsultaSerializer,
)

from biblioteca.services.mis_prestamos_service import (
    MisPrestamosService,
)


class MisPrestamosPagination(PageNumberPagination):
    page_size = 8
    page_size_query_param = 'page_size'
    max_page_size = 20


class MisPrestamosView(APIView):
    """
    GET /api/prestamos/mios/

    Devuelve exclusivamente los préstamos del
    estudiante o docente autenticado.
    """

    permission_classes = [
        IsAuthenticated,
        IsEstudianteODocente,
    ]

    def get(self, request):
        parametros = MisPrestamosConsultaSerializer(
            data=dict(request.query_params.items())
        )

        parametros.is_valid(
            raise_exception=True
        )

        filtro = parametros.validated_data.get(
            'filtro',
            'todos'
        )

        # Nunca se recibe el usuario_id del cliente.
        usuario_id = request.user.usuario_id

        limite_prestamos = (
            request.user.rol.limite_prestamos_activos
        )

        service = MisPrestamosService()

        prestamos, resumen, hoy = service.consultar(
            usuario_id=usuario_id,
            filtro=filtro
        )

        estado_cuenta = service.obtener_estado_cuenta(
            usuario_id=usuario_id,
            limite_prestamos=limite_prestamos,
            resumen=resumen,
            hoy=hoy
        )

        paginador = MisPrestamosPagination()

        pagina = paginador.paginate_queryset(
            prestamos,
            request,
            view=self
        )

        serializer = MiPrestamoSerializer(
            pagina,
            many=True,
            context={
                'hoy': hoy
            }
        )

        respuesta = paginador.get_paginated_response(
            serializer.data
        )

        respuesta.data['resumen'] = resumen
        respuesta.data['estado_cuenta'] = estado_cuenta

        return respuesta