from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from biblioteca.permissions import IsBibliotecario
from biblioteca.presentation.categorias_serializers import (
    CategoriaCreacionModificacionSerializer,
    CategoriaSerializer,
)
from biblioteca.services.categoria_service import (
    CategoriaDatosInvalidosError,
    CategoriaDuplicadaError,
    CategoriaNoEncontradaError,
    CategoriaService,
)


class CategoriasPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CategoriasListCreateView(APIView):
    """
    Vista administrativa para listar y registrar categorías temáticas.
    Requiere autenticación obligatoria y permiso IsBibliotecario.
    """

    permission_classes = [
        IsAuthenticated,
        IsBibliotecario,
    ]

    def get(self, request):
        service = CategoriaService()
        filtros = {}

        nombre = request.query_params.get('nombre')
        if nombre:
            filtros['nombre'] = nombre.strip()

        categorias = service.listar_categorias(filtros if filtros else None)

        paginador = CategoriasPagination()
        pagina = paginador.paginate_queryset(
            categorias,
            request,
            view=self,
        )

        serializer = CategoriaSerializer(
            pagina,
            many=True,
        )

        return paginador.get_paginated_response(
            serializer.data
        )

    def post(self, request):
        serializer = CategoriaCreacionModificacionSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        service = CategoriaService()

        try:
            categoria = service.registrar_categoria(
                serializer.validated_data
            )
        except CategoriaDuplicadaError as exc:
            raise ValidationError({
                'nombre_categoria': [str(exc)]
            })
        except CategoriaDatosInvalidosError as exc:
            raise ValidationError({
                'nombre_categoria': [str(exc)]
            })

        return Response(
            CategoriaSerializer(categoria).data,
            status=status.HTTP_201_CREATED,
        )


class CategoriaDetailView(APIView):
    """
    Vista administrativa para consultar el detalle y actualizar categorías existentes.
    Requiere autenticación obligatoria y permiso IsBibliotecario.
    Permite modificaciones parciales vía PATCH y completas vía PUT.
    No implementa DELETE conforme a la política de preservación histórica.
    """

    permission_classes = [
        IsAuthenticated,
        IsBibliotecario,
    ]

    def get(self, request, categoria_id):
        service = CategoriaService()

        try:
            categoria = service.obtener_categoria(categoria_id)
        except CategoriaNoEncontradaError:
            return Response(
                {'detail': 'Categoría no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            CategoriaSerializer(categoria).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, categoria_id):
        serializer = CategoriaCreacionModificacionSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        service = CategoriaService()

        try:
            categoria = service.modificar_categoria(
                categoria_id,
                serializer.validated_data,
            )
        except CategoriaNoEncontradaError:
            return Response(
                {'detail': 'Categoría no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except CategoriaDuplicadaError as exc:
            raise ValidationError({
                'nombre_categoria': [str(exc)]
            })
        except CategoriaDatosInvalidosError as exc:
            raise ValidationError({
                'nombre_categoria': [str(exc)]
            })

        return Response(
            CategoriaSerializer(categoria).data,
            status=status.HTTP_200_OK,
        )

    def put(self, request, categoria_id):
        serializer = CategoriaCreacionModificacionSerializer(
            data=request.data,
            partial=False,
        )
        serializer.is_valid(raise_exception=True)

        service = CategoriaService()

        try:
            categoria = service.modificar_categoria(
                categoria_id,
                serializer.validated_data,
            )
        except CategoriaNoEncontradaError:
            return Response(
                {'detail': 'Categoría no encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except CategoriaDuplicadaError as exc:
            raise ValidationError({
                'nombre_categoria': [str(exc)]
            })
        except CategoriaDatosInvalidosError as exc:
            raise ValidationError({
                'nombre_categoria': [str(exc)]
            })

        return Response(
            CategoriaSerializer(categoria).data,
            status=status.HTTP_200_OK,
        )
