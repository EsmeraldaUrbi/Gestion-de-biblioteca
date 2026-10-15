from rest_framework import serializers

from biblioteca.models import (
    Ejemplar,
    Libro,
    Prestamo,
)

from biblioteca.presentation.usuarios_serializers import (
    CamposPermitidosSerializer,
)


class MisPrestamosConsultaSerializer(
    CamposPermitidosSerializer
):
    """
    Parámetros aceptados por la consulta personal.
    """

    filtro = serializers.ChoiceField(
        choices=[
            'todos',
            'activos',
            'vencidos',
            'devueltos',
        ],
        default='todos',
        required=False
    )

    page = serializers.IntegerField(
        min_value=1,
        required=False
    )

    page_size = serializers.IntegerField(
        min_value=1,
        max_value=20,
        required=False
    )


class LibroMiPrestamoSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Libro
        fields = [
            'libro_id',
            'titulo',
            'isbn',
        ]


class EjemplarMiPrestamoSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = Ejemplar
        fields = [
            'ejemplar_id',
            'codigo_inventario',
        ]


class MiPrestamoSerializer(
    serializers.ModelSerializer
):
    """
    Representación de un préstamo personal.

    El estado se calcula a partir de la fecha límite
    y la fecha de devolución, sin añadir columnas
    al modelo existente.
    """

    libro = LibroMiPrestamoSerializer(
        source='ejemplar.libro',
        read_only=True
    )

    ejemplar = EjemplarMiPrestamoSerializer(
        read_only=True
    )

    estado = serializers.SerializerMethodField()

    dias_restantes = serializers.SerializerMethodField()

    class Meta:
        model = Prestamo

        fields = [
            'prestamo_id',
            'libro',
            'ejemplar',
            'fecha_prestamo',
            'fecha_limite',
            'fecha_devolucion',
            'estado',
            'dias_restantes',
        ]

        read_only_fields = fields

    def get_estado(self, prestamo):
        if prestamo.fecha_devolucion is not None:
            return 'DEVUELTO'

        hoy = self.context['hoy']

        if prestamo.fecha_limite < hoy:
            return 'VENCIDO'

        return 'EN_PRESTAMO'

    def get_dias_restantes(self, prestamo):
        if prestamo.fecha_devolucion is not None:
            return None

        hoy = self.context['hoy']

        dias = (
            prestamo.fecha_limite - hoy
        ).days

        return max(0, dias)