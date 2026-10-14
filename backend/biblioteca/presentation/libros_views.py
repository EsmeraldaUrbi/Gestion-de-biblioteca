from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from biblioteca.permissions import IsBibliotecario
from biblioteca.presentation.libros_serializers import (
    LibroCreacionModificacionSerializer,
    LibroSerializer,
)
from biblioteca.services.libro_service import (
    AutoresNoEncontradosError,
    CategoriasNoEncontradasError,
    IsbnDuplicadoError,
    LibroNoEncontradoError,
    LibroService,
)


class LibrosPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class LibrosListCreateView(APIView):
    """
    Vista administrativa para listar y registrar libros en el catálogo general.
    Requiere autenticación obligatoria y permiso IsBibliotecario.
    """

    permission_classes = [
        IsAuthenticated,
        IsBibliotecario,
    ]

    def get(self, request):
        service = LibroService()
        filtros = {}

        titulo = request.query_params.get('titulo')
        if titulo:
            filtros['titulo'] = titulo.strip()

        isbn = request.query_params.get('isbn')
        if isbn:
            filtros['isbn'] = isbn.strip()

        autor_id = request.query_params.get('autor_id')
        if autor_id:
            try:
                filtros['autor_id'] = int(autor_id)
            except (ValueError, TypeError):
                pass

        categoria_id = request.query_params.get('categoria_id')
        if categoria_id:
            try:
                filtros['categoria_id'] = int(categoria_id)
            except (ValueError, TypeError):
                pass

        libros = service.listar_libros(filtros if filtros else None)

        paginador = LibrosPagination()
        pagina = paginador.paginate_queryset(
            libros,
            request,
            view=self
        )

        serializer = LibroSerializer(
            pagina,
            many=True
        )

        return paginador.get_paginated_response(
            serializer.data
        )

    def post(self, request):
        serializer = LibroCreacionModificacionSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        service = LibroService()

        try:
            libro = service.registrar_libro(
                serializer.validated_data
            )
        except IsbnDuplicadoError as exc:
            raise ValidationError({
                'isbn': [str(exc)]
            })
        except AutoresNoEncontradosError as exc:
            raise ValidationError({
                'autor_ids': [str(exc)]
            })
        except CategoriasNoEncontradasError as exc:
            raise ValidationError({
                'categoria_ids': [str(exc)]
            })

        return Response(
            LibroSerializer(libro).data,
            status=status.HTTP_201_CREATED
        )


class LibroDetailView(APIView):
    """
    Vista administrativa para consultar el detalle y actualizar libros existentes.
    Requiere autenticación obligatoria y permiso IsBibliotecario.
    Permite modificaciones parciales vía PATCH y completas vía PUT.
    No expone endpoint DELETE conforme a las instrucciones vigentes.
    """

    permission_classes = [
        IsAuthenticated,
        IsBibliotecario,
    ]

    def get(self, request, libro_id):
        service = LibroService()

        try:
            libro = service.obtener_libro(libro_id)
        except LibroNoEncontradoError:
            return Response(
                {'detail': 'Libro no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            LibroSerializer(libro).data,
            status=status.HTTP_200_OK
        )

    def patch(self, request, libro_id):
        serializer = LibroCreacionModificacionSerializer(
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        service = LibroService()

        try:
            libro = service.modificar_libro(
                libro_id,
                serializer.validated_data
            )
        except LibroNoEncontradoError:
            return Response(
                {'detail': 'Libro no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except IsbnDuplicadoError as exc:
            raise ValidationError({
                'isbn': [str(exc)]
            })
        except AutoresNoEncontradosError as exc:
            raise ValidationError({
                'autor_ids': [str(exc)]
            })
        except CategoriasNoEncontradasError as exc:
            raise ValidationError({
                'categoria_ids': [str(exc)]
            })

        return Response(
            LibroSerializer(libro).data,
            status=status.HTTP_200_OK
        )

    def put(self, request, libro_id):
        serializer = LibroCreacionModificacionSerializer(
            data=request.data,
            partial=False
        )
        serializer.is_valid(raise_exception=True)

        service = LibroService()

        datos = dict(serializer.validated_data)
        if 'autor_ids' not in datos:
            datos['autor_ids'] = []
        if 'categoria_ids' not in datos:
            datos['categoria_ids'] = []

        try:
            libro = service.modificar_libro(
                libro_id,
                datos
            )
        except LibroNoEncontradoError:
            return Response(
                {'detail': 'Libro no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except IsbnDuplicadoError as exc:
            raise ValidationError({
                'isbn': [str(exc)]
            })
        except AutoresNoEncontradosError as exc:
            raise ValidationError({
                'autor_ids': [str(exc)]
            })
        except CategoriasNoEncontradasError as exc:
            raise ValidationError({
                'categoria_ids': [str(exc)]
            })

        return Response(
            LibroSerializer(libro).data,
            status=status.HTTP_200_OK
        )
