from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from biblioteca.permissions import IsBibliotecario
from biblioteca.presentation.autores_serializers import (
    AutorCreacionModificacionSerializer,
    AutorSerializer,
)
from biblioteca.services.autor_service import (
    AutorDatosInvalidosError,
    AutorNoEncontradoError,
    AutorService,
)


class AutoresPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class AutoresListCreateView(APIView):
    """
    Vista administrativa para listar y registrar autores.
    Requiere autenticación obligatoria y permiso IsBibliotecario.
    """

    permission_classes = [
        IsAuthenticated,
        IsBibliotecario,
    ]

    def get(self, request):
        service = AutorService()
        filtros = {}

        nombre = request.query_params.get('nombre')
        if nombre:
            filtros['nombre'] = nombre.strip()

        nacionalidad = request.query_params.get('nacionalidad')
        if nacionalidad:
            filtros['nacionalidad'] = nacionalidad.strip()

        autores = service.listar_autores(filtros if filtros else None)

        paginador = AutoresPagination()
        pagina = paginador.paginate_queryset(
            autores,
            request,
            view=self,
        )

        serializer = AutorSerializer(
            pagina,
            many=True,
        )

        return paginador.get_paginated_response(
            serializer.data
        )

    def post(self, request):
        serializer = AutorCreacionModificacionSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        service = AutorService()

        try:
            autor = service.registrar_autor(
                serializer.validated_data
            )
        except AutorDatosInvalidosError as exc:
            raise ValidationError({
                'detail': str(exc)
            })

        return Response(
            AutorSerializer(autor).data,
            status=status.HTTP_201_CREATED,
        )


class AutorDetailView(APIView):
    """
    Vista administrativa para consultar el detalle y actualizar autores.
    Requiere autenticación obligatoria y permiso IsBibliotecario.
    Permite modificaciones parciales vía PATCH y completas vía PUT.
    No implementa DELETE conforme a la política de preservación histórica.
    """

    permission_classes = [
        IsAuthenticated,
        IsBibliotecario,
    ]

    def get(self, request, autor_id):
        service = AutorService()

        try:
            autor = service.obtener_autor(autor_id)
        except AutorNoEncontradoError:
            return Response(
                {'detail': 'Autor no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            AutorSerializer(autor).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, autor_id):
        serializer = AutorCreacionModificacionSerializer(
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)

        service = AutorService()

        try:
            autor = service.modificar_autor(
                autor_id,
                serializer.validated_data,
            )
        except AutorNoEncontradoError:
            return Response(
                {'detail': 'Autor no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except AutorDatosInvalidosError as exc:
            raise ValidationError({
                'detail': str(exc)
            })

        return Response(
            AutorSerializer(autor).data,
            status=status.HTTP_200_OK,
        )

    def put(self, request, autor_id):
        serializer = AutorCreacionModificacionSerializer(
            data=request.data,
            partial=False,
        )
        serializer.is_valid(raise_exception=True)

        service = AutorService()

        datos = dict(serializer.validated_data)
        if 'nacionalidad' not in datos:
            datos['nacionalidad'] = None
        if 'fecha_nacimiento' not in datos:
            datos['fecha_nacimiento'] = None

        try:
            autor = service.modificar_autor(
                autor_id,
                datos,
            )
        except AutorNoEncontradoError:
            return Response(
                {'detail': 'Autor no encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except AutorDatosInvalidosError as exc:
            raise ValidationError({
                'detail': str(exc)
            })

        return Response(
            AutorSerializer(autor).data,
            status=status.HTTP_200_OK,
        )
