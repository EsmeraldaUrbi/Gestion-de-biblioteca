from rest_framework import serializers

from biblioteca.models import Ejemplar, EstadoEjemplar, Libro
from biblioteca.presentation.usuarios_serializers import CamposPermitidosSerializer


class EjemplarLibroResumenSerializer(serializers.ModelSerializer):
    """
    Serializador resumido del libro para incluir en la representación del ejemplar.
    """

    class Meta:
        model = Libro
        fields = [
            'libro_id',
            'titulo',
            'isbn',
        ]


class EjemplarSerializer(serializers.ModelSerializer):
    """
    Serializador de lectura para ejemplares físicos.
    """

    libro = EjemplarLibroResumenSerializer(read_only=True)
    libro_id = serializers.IntegerField(source='libro.libro_id', read_only=True)

    class Meta:
        model = Ejemplar
        fields = [
            'ejemplar_id',
            'libro_id',
            'libro',
            'codigo_inventario',
            'estado',
        ]


class EjemplarRegistroSerializer(CamposPermitidosSerializer):
    """
    Serializador para el registro de nuevos ejemplares físicos.
    Reutiliza CamposPermitidosSerializer para rechazar campos no permitidos.
    Aplica RN-02 y RN-03 (ACTIVO por defecto).
    """

    libro_id = serializers.IntegerField(
        min_value=1,
        required=True
    )
    codigo_inventario = serializers.CharField(
        max_length=15,
        required=True,
        allow_blank=False
    )
    estado = serializers.CharField(
        max_length=15,
        required=False,
        default=EstadoEjemplar.ACTIVO
    )

    def validate_codigo_inventario(self, value):
        limpio = value.strip()
        if not limpio:
            raise serializers.ValidationError(
                "El código de inventario no puede estar vacío."
            )
        if len(limpio) > 15:
            raise serializers.ValidationError(
                "El código de inventario no puede exceder los 15 caracteres."
            )
        return limpio

    def validate_estado(self, value):
        if not value:
            return EstadoEjemplar.ACTIVO
        normalizado = value.strip().upper()
        if normalizado not in EstadoEjemplar.values:
            raise serializers.ValidationError(
                f"Estado no válido (RN-03). Opciones permitidas: {list(EstadoEjemplar.values)}"
            )
        return normalizado


class EjemplarCambioEstadoSerializer(CamposPermitidosSerializer):
    """
    Serializador exclusivo para modificación del estado operativo del ejemplar.
    Rechaza cualquier otro campo (como libro_id o codigo_inventario) para impedir
    modificaciones arbitrarias o sustituciones silenciosas de ejemplares.
    """

    estado = serializers.CharField(
        max_length=15,
        required=True,
        allow_blank=False
    )

    def validate_estado(self, value):
        limpio = value.strip().upper()
        if limpio not in EstadoEjemplar.values:
            raise serializers.ValidationError(
                f"Estado no válido (RN-03). Opciones permitidas: {list(EstadoEjemplar.values)}"
            )
        return limpio
