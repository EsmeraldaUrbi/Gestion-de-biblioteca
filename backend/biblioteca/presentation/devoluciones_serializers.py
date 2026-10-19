from rest_framework import serializers

from biblioteca.presentation.usuarios_serializers import (
    CamposPermitidosSerializer,
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