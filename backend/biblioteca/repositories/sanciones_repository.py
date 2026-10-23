from datetime import date

from django.db.models import Q, QuerySet

from biblioteca.models import Sancion


class DjangoSancionesRepository:
    """Consultas y escrituras persistentes para sanciones."""

    def _base_queryset(self) -> QuerySet[Sancion]:
        return Sancion.objects.select_related(
            'prestamo__usuario',
            'prestamo__ejemplar__libro',
        )

    def listar_administrativas(
        self,
        termino: str = '',
        tipo: str = 'todos',
        estado: str = 'todos',
        hoy: date | None = None,
    ) -> QuerySet[Sancion]:
        sanciones = self._base_queryset()

        if termino:
            sanciones = sanciones.filter(
                Q(prestamo__usuario__nombre__icontains=termino)
                | Q(prestamo__usuario__email__icontains=termino)
                | Q(prestamo__ejemplar__libro__titulo__icontains=termino)
                | Q(prestamo__ejemplar__libro__isbn__icontains=termino)
                | Q(prestamo__ejemplar__codigo_inventario__icontains=termino)
                | Q(sancion_id__icontains=termino)
                | Q(prestamo_id__icontains=termino)
            )

        if tipo != 'todos':
            sanciones = sanciones.filter(tipo=tipo)

        if estado == 'pendiente':
            sanciones = sanciones.filter(
                tipo='ECONOMICA',
                fecha_pago__isnull=True,
            )
        elif estado == 'pagada':
            sanciones = sanciones.filter(
                tipo='ECONOMICA',
                fecha_pago__isnull=False,
            )
        elif estado == 'vigente':
            sanciones = sanciones.filter(
                tipo='BLOQUEO',
                fecha_inicio_bloqueo__lte=hoy,
                fecha_fin_bloqueo__gte=hoy,
            )
        elif estado == 'finalizada':
            sanciones = sanciones.filter(
                tipo='BLOQUEO',
                fecha_fin_bloqueo__lt=hoy,
            )

        return sanciones.order_by('-sancion_id')

    def obtener_para_pago(self, sancion_id: int) -> Sancion | None:
        return (
            self._base_queryset()
            .select_for_update()
            .filter(sancion_id=sancion_id)
            .first()
        )

    def obtener_administrativa(self, sancion_id: int) -> Sancion | None:
        return self._base_queryset().filter(
            sancion_id=sancion_id,
        ).first()

    def listar_personales(self, usuario_id: int) -> QuerySet[Sancion]:
        return self._base_queryset().filter(
            prestamo__usuario_id=usuario_id,
        ).order_by('-sancion_id')

    def guardar(self, sancion: Sancion) -> Sancion:
        sancion.save(update_fields=['fecha_pago'])
        return sancion
