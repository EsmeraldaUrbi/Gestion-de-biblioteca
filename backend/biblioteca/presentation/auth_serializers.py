from rest_framework import serializers

from biblioteca.models import Rol, Usuario


class LoginSerializer(
    serializers.Serializer
):
    email = serializers.EmailField(
        max_length=50
    )

    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        allow_blank=False
    )

    def validate_email(
        self,
        value
    ):
        return (
            value
            .strip()
            .lower()
        )


class RolSesionSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = Rol

        fields = [
            'rol_id',
            'nombre',
            'limite_prestamos_activos',
        ]


class UsuarioSesionSerializer(
    serializers.ModelSerializer
):
    rol = RolSesionSerializer(
        read_only=True
    )

    class Meta:
        model = Usuario

        fields = [
            'usuario_id',
            'nombre',
            'email',
            'rol',
        ]