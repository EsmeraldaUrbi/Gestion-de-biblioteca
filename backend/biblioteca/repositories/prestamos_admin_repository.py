from datetime import date

from django.db.models import Count, Q

from biblioteca.models import Prestamo


class DjangoPrestamosAdminRepository:
    """
    Consultas de lectura administrativa de préstamos.

    No registra, actualiza ni elimina préstamos.
    """

    def listar(
        self,
        estado: str,
        termino: str,
        hoy: date,
    ):
        prestamos = (
            Prestamo.objects
            .select_related(
                'usuario',
                'usuario__rol',
                'ejemplar',
                'ejemplar__libro',
            )
        )

        if termino:
            condicion = (
                Q(usuario__nombre__icontains=termino)
                | Q(usuario__email__icontains=termino)
                | Q(ejemplar__codigo_inventario__icontains=termino)
                | Q(ejemplar__libro__titulo__icontains=termino)
                | Q(ejemplar__libro__isbn__icontains=termino)
            )

            if termino.isdecimal() and len(termino) <= 9:
                identificador = int(termino)

                condicion |= Q(
                    prestamo_id=identificador
                )

            prestamos = prestamos.filter(condicion)

        if estado == 'en_prestamo':
            prestamos = prestamos.filter(
                fecha_devolucion__isnull=True,
                fecha_limite__gte=hoy,
            )

        elif estado == 'vencidos':
            prestamos = prestamos.filter(
                fecha_devolucion__isnull=True,
                fecha_limite__lt=hoy,
            )

        elif estado == 'devueltos':
            prestamos = prestamos.filter(
                fecha_devolucion__isnull=False,
            )

        return prestamos.order_by(
            '-fecha_prestamo',
            '-prestamo_id',
        )

    def obtener_resumen(self, hoy: date) -> dict:
        """
        Resumen general de toda la biblioteca.

        No depende de los filtros ni de la página.
        Cada préstamo pertenece a un único estado.
        """

        return Prestamo.objects.aggregate(
            total=Count('prestamo_id'),

            en_prestamo=Count(
                'prestamo_id',
                filter=Q(
                    fecha_devolucion__isnull=True,
                    fecha_limite__gte=hoy,
                ),
            ),

            vencidos=Count(
                'prestamo_id',
                filter=Q(
                    fecha_devolucion__isnull=True,
                    fecha_limite__lt=hoy,
                ),
            ),

            devueltos=Count(
                'prestamo_id',
                filter=Q(
                    fecha_devolucion__isnull=False,
                ),
            ),
        )