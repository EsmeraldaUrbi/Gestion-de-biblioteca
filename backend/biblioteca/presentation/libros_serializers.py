from rest_framework import serializers

from biblioteca.models import Autor, Categoria, Libro
from biblioteca.presentation.usuarios_serializers import CamposPermitidosSerializer


class AutorResumenSerializer(serializers.ModelSerializer):
    """
    Serializador de lectura resumida para autores asociados a un libro.
    """

    class Meta:
        model = Autor
        fields = [
            'autor_id',
            'nombre',
        ]


class CategoriaResumenSerializer(serializers.ModelSerializer):
    """
    Serializador de lectura resumida para categorías asociadas a un libro.
    """

    class Meta:
        model = Categoria
        fields = [
            'categoria_id',
            'nombre_categoria',
        ]


class LibroSerializer(serializers.ModelSerializer):
    """
    Serializador de lectura para la gestión bibliográfica de libros y sus asociaciones.
    """

    autores = AutorResumenSerializer(many=True, read_only=True)
    categorias = CategoriaResumenSerializer(many=True, read_only=True)

    class Meta:
        model = Libro
        fields = [
            'libro_id',
            'titulo',
            'isbn',
            'fecha_publicacion',
            'autores',
            'categorias',
        ]


class LibroCreacionModificacionSerializer(CamposPermitidosSerializer):
    """
    Serializador para creación y modificación de libros.
    Rechaza campos no permitidos mediante CamposPermitidosSerializer.
    No exige autores ni categorías obligatorios conforme a las reglas de negocio.
    En modificaciones parciales (partial=True), conserva asociaciones omitidas.
    """

    titulo = serializers.CharField(
        max_length=100,
        allow_blank=False,
        required=True
    )
    isbn = serializers.CharField(
        max_length=13,
        allow_blank=False,
        required=True
    )
    fecha_publicacion = serializers.DateField(
        required=False,
        allow_null=True
    )
    autor_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False
    )
    categoria_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False
    )

    def validate_titulo(self, value):
        valor = value.strip()
        if not valor:
            raise serializers.ValidationError("El título no puede estar vacío.")
        return valor

    def validate_isbn(self, value):
        valor = value.strip()
        if not valor:
            raise serializers.ValidationError("El ISBN no puede estar vacío.")
        return valor


# Alias para máxima compatibilidad con distintas convenciones de nombres del proyecto
LibroRegistroSerializer = LibroCreacionModificacionSerializer
LibroCreacionSerializer = LibroCreacionModificacionSerializer
LibroModificacionSerializer = LibroCreacionModificacionSerializer
