from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from biblioteca.permissions import RolPermission
from biblioteca.presentation.catalogo_serializers import (
    AutorCatalogoSerializer, CategoriaCatalogoSerializer,
    CatalogoFiltrosSerializer, LibroCatalogoSerializer,
)
from biblioteca.services.catalogo_service import CatalogoService, LibroNoEncontradoError


class PuedeConsultarCatalogo(RolPermission):
    roles_permitidos = {'estudiante', 'docente', 'bibliotecario'}


class CatalogoPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CatalogoBaseView(APIView):
    permission_classes = [IsAuthenticated, PuedeConsultarCatalogo]


class CatalogoListView(CatalogoBaseView):
    def get(self, request):
        filtros = CatalogoFiltrosSerializer(data=dict(request.query_params.items()))
        filtros.is_valid(raise_exception=True)
        libros = CatalogoService().listar(filtros.validated_data)
        paginador = CatalogoPagination()
        pagina = paginador.paginate_queryset(libros, request, view=self)
        return paginador.get_paginated_response(
            LibroCatalogoSerializer(pagina, many=True).data
        )


class CatalogoDetailView(CatalogoBaseView):
    def get(self, request, libro_id):
        try:
            libro = CatalogoService().obtener(libro_id)
        except LibroNoEncontradoError:
            return Response({'detail': 'Libro no encontrado.'}, status=404)
        return Response(LibroCatalogoSerializer(libro).data)


class CatalogoFiltrosView(CatalogoBaseView):
    def get(self, request):
        opciones = CatalogoService().opciones()
        return Response({
            'autores': AutorCatalogoSerializer(opciones['autores'], many=True).data,
            'categorias': CategoriaCatalogoSerializer(opciones['categorias'], many=True).data,
        })

