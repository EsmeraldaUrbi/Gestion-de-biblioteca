from django.core.management.base import BaseCommand

from biblioteca.services.bloqueos_service import BloqueosService


class Command(BaseCommand):
    """
    Ejecuta la revision de prestamos para generar
    bloqueos temporales automaticos.

    Ticket 3.7.2
    """

    help = (
        'Revisa prestamos vencidos y aplica '
        'los bloqueos temporales correspondientes.'
    )

    def handle(self, *args, **options):
        self.stdout.write(
            'Iniciando revision automatica de bloqueos...'
        )

        servicio = BloqueosService()
        resultado = servicio.aplicar_bloqueos()

        fecha = resultado['fecha_revision']
        revisados = resultado['prestamos_revisados']
        creados = resultado['bloqueos_creados']

        self.stdout.write(
            f'Fecha de revision: {fecha.isoformat()}'
        )

        self.stdout.write(
            f'Prestamos revisados: {revisados}'
        )

        self.stdout.write(
            f'Bloqueos creados: {creados}'
        )

        self.stdout.write(
            self.style.SUCCESS(
                'Revision de bloqueos finalizada correctamente.'
            )
        )
