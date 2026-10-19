from rest_framework import serializers

from biblioteca.presentation.usuarios_serializers import (
    CamposPermitidosSerializer,
)

from biblioteca.presentation.prestamos_serializers import (
    PrestamoRegistroSerializer,
)

class DevolucionSolicitudSerializer(CamposPermitidosSerializer):
    """
    La solicitud no admite campos.

    La fecha y el importe los determina el servidor.
    """
    pass


class DevolucionRespuestaSerializer(serializers.Serializer):
    mensaje = serializers.CharField()
    prestamo_id = serializers.IntegerField()
    fecha_devolucion = serializers.DateField()
    dias_retraso = serializers.IntegerField()
    monto_multa = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        coerce_to_string=True
    )
    sancion_generada = serializers.BooleanField()
    sancion_id = serializers.IntegerField(required=False)
    ejemplar_estado = serializers.CharField()

class BusquedaDevolucionesSerializer(CamposPermitidosSerializer):
    q = serializers.CharField(
        max_length=100,
        allow_blank=False,
        trim_whitespace=True
    )
    page = serializers.IntegerField(
        min_value=1,
        required=False,
        default=1
    )
    page_size = serializers.IntegerField(
        min_value=1,
        max_value=100,
        required=False,
        default=10
    )


class PrestamoActivoDevolucionSerializer(serializers.Serializer):
    prestamo = PrestamoRegistroSerializer(read_only=True)
    fecha_referencia = serializers.DateField()
    dias_retraso = serializers.IntegerField()
    monto_multa = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        coerce_to_string=True
    )