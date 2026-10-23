from django.utils import timezone
from rest_framework import serializers

from biblioteca.models import Ejemplar, Libro, Prestamo, Sancion, Usuario
from biblioteca.presentation.usuarios_serializers import CamposPermitidosSerializer


class SancionesConsultaSerializer(CamposPermitidosSerializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=100)
    tipo = serializers.ChoiceField(
        choices=['todos', 'ECONOMICA', 'BLOQUEO'],
        default='todos',
        required=False,
    )
    estado = serializers.ChoiceField(
        choices=['todos', 'pendiente', 'pagada', 'vigente', 'finalizada'],
        default='todos',
        required=False,
    )
    page = serializers.IntegerField(min_value=1, required=False)
    page_size = serializers.IntegerField(min_value=1, max_value=50, required=False)


class SancionUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['usuario_id', 'nombre', 'email']


class SancionLibroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Libro
        fields = ['libro_id', 'titulo', 'isbn']


class SancionEjemplarSerializer(serializers.ModelSerializer):
    libro = SancionLibroSerializer(read_only=True)

    class Meta:
        model = Ejemplar
        fields = ['ejemplar_id', 'codigo_inventario', 'libro']


class SancionPrestamoSerializer(serializers.ModelSerializer):
    usuario = SancionUsuarioSerializer(read_only=True)
    ejemplar = SancionEjemplarSerializer(read_only=True)

    class Meta:
        model = Prestamo
        fields = [
            'prestamo_id',
            'fecha_prestamo',
            'fecha_limite',
            'fecha_devolucion',
            'usuario',
            'ejemplar',
        ]


class SancionSerializer(serializers.ModelSerializer):
    prestamo = SancionPrestamoSerializer(read_only=True)
    estado = serializers.SerializerMethodField()

    class Meta:
        model = Sancion
        fields = [
            'sancion_id',
            'tipo',
            'monto',
            'fecha_pago',
            'fecha_inicio_bloqueo',
            'fecha_fin_bloqueo',
            'estado',
            'prestamo',
        ]
        read_only_fields = fields

    def get_estado(self, sancion):
        if sancion.tipo == 'ECONOMICA':
            return 'PAGADA' if sancion.fecha_pago else 'PENDIENTE'

        hoy = self.context.get('hoy', timezone.localdate())
        return 'VIGENTE' if sancion.fecha_fin_bloqueo >= hoy else 'FINALIZADA'


class PagoSancionSerializer(CamposPermitidosSerializer):
    """El pago es total y no acepta monto ni fecha del cliente."""

    pass
