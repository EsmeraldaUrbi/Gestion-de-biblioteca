from rest_framework import serializers

from biblioteca.models import Sancion
from biblioteca.presentation.mis_prestamos_serializers import (
    EjemplarMiPrestamoSerializer,
    LibroMiPrestamoSerializer,
)
from biblioteca.presentation.usuarios_serializers import CamposPermitidosSerializer
from biblioteca.services.mis_sanciones_service import MisSancionesService


class MisSancionesConsultaSerializer(CamposPermitidosSerializer):
    """
    Validador de parámetros de consulta para GET /api/sanciones/mias/.
    Aplica CamposPermitidosSerializer para rechazar de inmediato parámetros
    no autorizados (por ejemplo usuario_id o prestamo_id).
    """

    tipo = serializers.ChoiceField(
        choices=['todas', 'economicas', 'bloqueos'],
        default='todas',
        required=False,
    )

    estado = serializers.ChoiceField(
        choices=[
            'todos',
            'pendientes',
            'pagadas',
            'programados',
            'vigentes',
            'concluidos',
        ],
        default='todos',
        required=False,
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

    def validate(self, attrs):
        tipo = attrs.get('tipo', 'todas')
        estado = attrs.get('estado', 'todos')

        try:
            MisSancionesService.validar_filtros(tipo, estado)
        except ValueError as exc:
            raise serializers.ValidationError({
                'estado': str(exc),
            })

        return attrs


class MiSancionSerializer(serializers.ModelSerializer):
    """
    Serializador de solo lectura para la presentación de sanciones y bloqueos personales.
    Conserva precisión decimal de los importes serializados como cadena.
    """

    prestamo_id = serializers.IntegerField(
        source='prestamo.prestamo_id',
        read_only=True,
    )

    libro = LibroMiPrestamoSerializer(
        source='prestamo.ejemplar.libro',
        read_only=True,
    )

    ejemplar = EjemplarMiPrestamoSerializer(
        source='prestamo.ejemplar',
        read_only=True,
    )

    estado = serializers.SerializerMethodField()

    monto = serializers.SerializerMethodField()

    class Meta:
        model = Sancion
        fields = [
            'sancion_id',
            'prestamo_id',
            'libro',
            'ejemplar',
            'tipo',
            'estado',
            'monto',
            'fecha_pago',
            'fecha_inicio_bloqueo',
            'fecha_fin_bloqueo',
        ]
        read_only_fields = fields

    def get_estado(self, sancion: Sancion) -> str:
        hoy = self.context.get('hoy')
        if hoy is None:
            from django.utils import timezone
            hoy = timezone.localdate()
        return MisSancionesService.determinar_estado(sancion, hoy)

    def get_monto(self, sancion: Sancion) -> str | None:
        if sancion.monto is None:
            return None
        return f"{sancion.monto:.2f}"
