import logging
from signal import SIGINT, SIGTERM, signal
from threading import Event

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Ejecuta periodicamente el proceso de bloqueos.

    Se utiliza como proceso independiente en Docker.
    """

    help = (
        'Ejecuta revisiones periodicas de prestamos '
        'para aplicar bloqueos automaticos.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--intervalo-segundos',
            type=int,
            default=3600,
            help='Segundos entre revisiones (minimo 60).'
        )

    def handle(self, *args, **options):
        intervalo = options['intervalo_segundos']

        if intervalo < 60:
            raise CommandError(
                'El intervalo debe ser de al menos 60 segundos.'
            )

        detener = Event()

        def solicitar_detencion(signum, frame):
            detener.set()

        # Docker envia SIGTERM cuando detiene el servicio.
        manejador_term = signal(
            SIGTERM,
            solicitar_detencion
        )

        manejador_int = signal(
            SIGINT,
            solicitar_detencion
        )

        self.stdout.write(
            f'Worker de bloqueos iniciado. '
            f'Intervalo: {intervalo} segundos.'
        )

        try:
            while not detener.is_set():
                espera = intervalo

                try:
                    # Recupera conexiones si MySQL estuvo
                    # inactivo durante mucho tiempo.
                    close_old_connections()

                    call_command(
                        'aplicar_bloqueos',
                        stdout=self.stdout,
                        stderr=self.stderr
                    )

                except Exception:
                    logger.exception(
                        'Error durante la revision de bloqueos.'
                    )

                    # Si falla MySQL u otro componente,
                    # reintentar en un minuto.
                    espera = min(intervalo, 60)

                finally:
                    close_old_connections()

                if not detener.is_set():
                    detener.wait(espera)

        finally:
            signal(SIGTERM, manejador_term)
            signal(SIGINT, manejador_int)
            close_old_connections()

        self.stdout.write(
            'Worker de bloqueos detenido.'
        )
