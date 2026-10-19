from rest_framework import serializers

from biblioteca.models import Categoria
from biblioteca.presentation.usuarios_serializers import CamposPermitidosSerializer


class CategoriaSerializer(serializers.ModelSerializer):
    """
    Serializador de lectura para categorías en la administración bibliográfica.
    Expone los datos de la categoría junto con el conteo de libros asociados.
    """

    cantidad_libros = serializers.IntegerField(
        read_only=True,
        default=0,
    )

    class Meta:
        model = Categoria
        fields = [
            'categoria_id',
            'nombre_categoria',
            'cantidad_libros',
        ]


class CategoriaCreacionModificacionSerializer(CamposPermitidosSerializer):
    """
    Serializador para el registro y modificación de categorías.
    Rechaza campos no autorizados mediante CamposPermitidosSerializer.
    """

    nombre_categoria = serializers.CharField(
        max_length=50,
        allow_blank=False,
        required=True,
    )

    def validate_nombre_categoria(self, value):
        valor = value.strip()
        if not valor:
            raise serializers.ValidationError("El nombre de la categoría no puede estar vacío.")
        if len(valor) > 50:
            raise serializers.ValidationError("El nombre de la categoría no puede exceder los 50 caracteres.")
        return valor
