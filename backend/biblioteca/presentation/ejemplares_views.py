from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from biblioteca.permissions import IsBibliotecario
from biblioteca.presentation.ejemplares_serializers import (
    EjemplarCambioEstadoSerializer,
    EjemplarRegistroSerializer,
    EjemplarSerializer,
)
from biblioteca.services.ejemplar_service import (
    CodigoInventarioDuplicadoError,
    CodigoInventarioInvalidoError,
    EjemplarConPrestamoActivoError,
    EjemplarNoEncontradoError,
    EjemplarService,
    EstadoEjemplarInvalidoError,
)
from biblioteca.services.libro_service import LibroNoEncontradoError


class EjemplaresPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class EjemplaresListCreateView(APIView):
    """
    Vista administrativa para listar y registrar ejemplares físicos.
    Requiere autenticación obligatoria y permiso IsBibliotecario.
    """

    permission_classes = [
        IsAuthenticated,
        IsBibliotecario,
    ]

    def get(self, request):
        service = EjemplarService()
        filtros = {}

        libro_id = request.query_params.get('libro_id')
        if libro_id:
            try:
                filtros['libro_id'] = int(libro_id)
            except (ValueError, TypeError):
                pass

        estado = request.query_params.get('estado')
        if estado:
            filtros['estado'] = estado.strip().upper()

        codigo_inventario = request.query_params.get('codigo_inventario')
        if codigo_inventario:
            filtros['codigo_inventario'] = codigo_inventario.strip()

        ejemplares = service.listar_ejemplares(filtros if filtros else None)

        paginador = EjemplaresPagination()
        pagina = paginador.paginate_queryset(
            ejemplares,
            request,
            view=self
        )

        serializer = EjemplarSerializer(
            pagina,
            many=True
        )

        return paginador.get_paginated_response(
            serializer.data
        )

    def post(self, request):
        serializer = EjemplarRegistroSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        service = EjemplarService()

        try:
            ejemplar = service.registrar_ejemplar(
                serializer.validated_data
            )
        except LibroNoEncontradoError:
            raise ValidationError({
                'libro_id': ['No existe un libro registrado con el ID proporcionado.']
            })
        except CodigoInventarioDuplicadoError as exc:
            raise ValidationError({
                'codigo_inventario': [str(exc)]
            })
        except CodigoInventarioInvalidoError as exc:
            raise ValidationError({
                'codigo_inventario': [str(exc)]
            })
        except EstadoEjemplarInvalidoError as exc:
            raise ValidationError({
                'estado': [str(exc)]
            })

        return Response(
            EjemplarSerializer(ejemplar).data,
            status=status.HTTP_201_CREATED
        )


class EjemplarDetailView(APIView):
    """
    Vista administrativa para consultar el detalle de un ejemplar y modificar
    su estado operativo (ACTIVO, MANTENIMIENTO, BAJA).
    Requiere autenticación obligatoria y permiso IsBibliotecario.
    No expone endpoint DELETE conforme a RN-04 (baja lógica vía PATCH).
    """

    permission_classes = [
        IsAuthenticated,
        IsBibliotecario,
    ]

    def get(self, request, ejemplar_id):
        service = EjemplarService()

        try:
            ejemplar = service.obtener_ejemplar(ejemplar_id)
        except EjemplarNoEncontradoError:
            return Response(
                {'detail': 'Ejemplar no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            EjemplarSerializer(ejemplar).data,
            status=status.HTTP_200_OK
        )

    def patch(self, request, ejemplar_id):
        serializer = EjemplarCambioEstadoSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        service = EjemplarService()

        try:
            ejemplar = service.cambiar_estado(
                ejemplar_id,
                serializer.validated_data['estado']
            )
        except EjemplarNoEncontradoError:
            return Response(
                {'detail': 'Ejemplar no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except EjemplarConPrestamoActivoError as exc:
            raise ValidationError({
                'estado': [str(exc)]
            })
        except EstadoEjemplarInvalidoError as exc:
            raise ValidationError({
                'estado': [str(exc)]
            })

        return Response(
            EjemplarSerializer(ejemplar).data,
            status=status.HTTP_200_OK
        )
