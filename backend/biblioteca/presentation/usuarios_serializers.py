from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from biblioteca.models import Rol, Usuario


class CamposPermitidosSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            return super().to_internal_value(data)

        desconocidos = set(data) - set(self.fields)

        if desconocidos:
            raise serializers.ValidationError({
                campo: ["Este campo no está permitido."]
                for campo in sorted(desconocidos)
            })

        return super().to_internal_value(data)


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = [
            'rol_id',
            'nombre',
            'limite_prestamos_activos',
        ]


class UsuarioSerializer(serializers.ModelSerializer):
    rol = RolSerializer(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'usuario_id',
            'nombre',
            'email',
            'direccion',
            'telefono',
            'rol',
        ]


class UsuarioRegistroSerializer(CamposPermitidosSerializer):
    nombre = serializers.CharField(
        max_length=100,
        allow_blank=False
    )
    email = serializers.EmailField(
        max_length=50
    )
    direccion = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True
    )
    telefono = serializers.CharField(
        max_length=15,
        required=False,
        allow_blank=True,
        allow_null=True
    )
    rol_id = serializers.IntegerField(
        min_value=1
    )
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        allow_blank=False
    )

    def validate_nombre(self, value):
        return value.strip()

    def validate_email(self, value):
        return value.strip().lower()

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                error.messages
            )

        return value


class UsuarioModificacionSerializer(CamposPermitidosSerializer):
    nombre = serializers.CharField(
        max_length=100,
        allow_blank=False,
        required=False
    )
    email = serializers.EmailField(
        max_length=50,
        required=False
    )
    direccion = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True
    )
    telefono = serializers.CharField(
        max_length=15,
        required=False,
        allow_blank=True,
        allow_null=True
    )
    rol_id = serializers.IntegerField(
        min_value=1,
        required=False
    )

    def validate_nombre(self, value):
        return value.strip()

    def validate_email(self, value):
        return value.strip().lower()
