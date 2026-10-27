from rest_framework import serializers

from biblioteca.models import (
    Prestamo,
    Usuario,
)

from biblioteca.presentation.usuarios_serializers import (
    CamposPermitidosSerializer,
)

from biblioteca.presentation.mis_prestamos_serializers import (
    MiPrestamoSerializer,
)


class PrestamosAdminConsultaSerializer(
    CamposPermitidosSerializer
):
    """
    Parámetros aceptados por GET /api/prestamos/.
    """

    q = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        max_length=100,
        default='',
    )

    estado = serializers.ChoiceField(
        choices=[
            'todos',
            'en_prestamo',
            'vencidos',
            'devueltos',
        ],
        required=False,
        default='todos',
    )

    page = serializers.IntegerField(
        min_value=1,
        required=False,
    )

    page_size = serializers.IntegerField(
        min_value=1,
        max_value=50,
        required=False,
    )


class UsuarioPrestamoAdminSerializer(
    serializers.ModelSerializer
):
    rol = serializers.CharField(
        source='rol.nombre',
        read_only=True,
    )

    class Meta:
        model = Usuario
        fields = [
            'usuario_id',
            'nombre',
            'email',
            'rol',
        ]
        read_only_fields = fields


class PrestamoAdminSerializer(
    MiPrestamoSerializer
):
    """
    Extiende la representación de Mis préstamos
    con la identidad del lector.

    Se conserva la lógica de cálculo de estados.
    """

    usuario = UsuarioPrestamoAdminSerializer(
        read_only=True,
    )

    class Meta(MiPrestamoSerializer.Meta):
        model = Prestamo

        fields = [
            'prestamo_id',
            'usuario',
            'libro',
            'ejemplar',
            'fecha_prestamo',
            'fecha_limite',
            'fecha_devolucion',
            'estado',
            'dias_restantes',
        ]

        read_only_fields = fields