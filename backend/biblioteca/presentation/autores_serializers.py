from datetime import date

from django.utils import timezone
from rest_framework import serializers

from biblioteca.models import Autor
from biblioteca.presentation.usuarios_serializers import CamposPermitidosSerializer


class AutorSerializer(serializers.ModelSerializer):
    """
    Serializador de lectura para autores en la administración bibliográfica.
    Expone los datos del autor junto con el conteo de libros asociados.
    """

    cantidad_libros = serializers.IntegerField(
        read_only=True,
        default=0,
    )

    class Meta:
        model = Autor
        fields = [
            'autor_id',
            'nombre',
            'nacionalidad',
            'fecha_nacimiento',
            'cantidad_libros',
        ]


class AutorCreacionModificacionSerializer(CamposPermitidosSerializer):
    """
    Serializador para el registro y modificación de autores.
    Aplica CamposPermitidosSerializer para rechazar campos no reconocidos.
    En operaciones PATCH (partial=True), valida únicamente los campos provistos.
    """

    nombre = serializers.CharField(
        max_length=100,
        allow_blank=False,
        required=True,
    )
    nacionalidad = serializers.CharField(
        max_length=50,
        allow_blank=True,
        allow_null=True,
        required=False,
    )
    fecha_nacimiento = serializers.DateField(
        required=False,
        allow_null=True,
    )

    def validate_nombre(self, value):
        valor = value.strip()
        if not valor:
            raise serializers.ValidationError("El nombre del autor no puede estar vacío.")
        if len(valor) > 100:
            raise serializers.ValidationError("El nombre del autor no puede exceder los 100 caracteres.")
        return valor

    def validate_nacionalidad(self, value):
        if value is None:
            return None
        valor = value.strip()
        if not valor:
            return None
        if len(valor) > 50:
            raise serializers.ValidationError("La nacionalidad no puede exceder los 50 caracteres.")
        return valor

    def validate_fecha_nacimiento(self, value):
        if value is None:
            return None
        hoy = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
        if value > hoy:
            raise serializers.ValidationError("La fecha de nacimiento no puede ser una fecha futura.")
        return value
