from rest_framework import serializers

from biblioteca.models import Prestamo
from biblioteca.presentation.usuarios_serializers import (
    CamposPermitidosSerializer,
    UsuarioSerializer,
)
from biblioteca.presentation.ejemplares_serializers import (
    EjemplarSerializer,
)


class PrestamoSolicitudSerializer(CamposPermitidosSerializer):
    """
    Datos necesarios para registrar o evaluar un préstamo.

    El frontend no puede enviar fechas ni estados:
    el backend los determina automáticamente.
    """

    usuario_id = serializers.IntegerField(
        min_value=1,
        required=True
    )

    ejemplar_id = serializers.IntegerField(
        min_value=1,
        required=True
    )


class BusquedaLectoresSerializer(CamposPermitidosSerializer):
    """
    Parámetros utilizados para localizar estudiantes
    y docentes en la operación de ventanilla.
    """

    q = serializers.CharField(
        max_length=100,
        min_length=1,
        allow_blank=False,
        trim_whitespace=True
    )

    limite = serializers.IntegerField(
        min_value=1,
        max_value=20,
        required=False,
        default=10
    )


class MotivoRechazoSerializer(serializers.Serializer):
    codigo = serializers.CharField()
    mensaje = serializers.CharField()

class BloqueoVigenteSerializer(serializers.Serializer):
    prestamo_id = serializers.IntegerField()
    motivo = serializers.CharField()
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()


class ElegibilidadPrestamoSerializer(serializers.Serializer):
    """
    Resultado informativo de la evaluación previa.
    """

    elegible = serializers.BooleanField()

    motivos = MotivoRechazoSerializer(
        many=True
    )

    bloqueos_vigentes = BloqueoVigenteSerializer(
        many=True,
        read_only=True
    )

    usuario = UsuarioSerializer(
        read_only=True
    )

    ejemplar = EjemplarSerializer(
        read_only=True
    )

    prestamos_activos = serializers.IntegerField()

    limite_prestamos_activos = serializers.IntegerField()

    fecha_prestamo = serializers.DateField()

    fecha_limite = serializers.DateField()


class PrestamoRegistroSerializer(serializers.ModelSerializer):
    """
    Representación del préstamo almacenado.

    Incluye los identificadores y la información
    relacionada con usuario y ejemplar.
    """

    usuario_id = serializers.IntegerField(
        read_only=True
    )

    ejemplar_id = serializers.IntegerField(
        read_only=True
    )

    usuario = UsuarioSerializer(
        read_only=True
    )

    ejemplar = EjemplarSerializer(
        read_only=True
    )

    class Meta:
        model = Prestamo

        fields = [
            'prestamo_id',
            'usuario_id',
            'usuario',
            'ejemplar_id',
            'ejemplar',
            'fecha_prestamo',
            'fecha_limite',
            'fecha_devolucion',
        ]

        read_only_fields = fields