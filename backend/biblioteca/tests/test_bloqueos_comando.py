from datetime import date
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import SimpleTestCase


class AplicarBloqueosCommandTests(SimpleTestCase):
    """
    Pruebas del comando administrativo del ticket 3.7.2.

    El servicio se simula para no escribir en MySQL.
    """

    @patch(
        'biblioteca.management.commands.aplicar_bloqueos.BloqueosService'
    )
    def test_ejecuta_servicio_y_muestra_resumen(
        self,
        servicio_mock
    ):
        servicio_mock.return_value.aplicar_bloqueos.return_value = {
            'fecha_revision': date(2026, 10, 18),
            'prestamos_revisados': 5,
            'bloqueos_creados': 2,
        }

        salida = StringIO()

        call_command(
            'aplicar_bloqueos',
            stdout=salida
        )

        servicio_mock.return_value.aplicar_bloqueos.assert_called_once_with()

        texto = salida.getvalue()

        self.assertIn(
            'Fecha de revision: 2026-10-18',
            texto
        )
        self.assertIn(
            'Prestamos revisados: 5',
            texto
        )
        self.assertIn(
            'Bloqueos creados: 2',
            texto
        )
        self.assertIn(
            'Revision de bloqueos finalizada correctamente.',
            texto
        )

    @patch(
        'biblioteca.management.commands.aplicar_bloqueos.BloqueosService'
    )
    def test_no_oculta_errores_del_servicio(
        self,
        servicio_mock
    ):
        servicio_mock.return_value.aplicar_bloqueos.side_effect = (
            RuntimeError('Fallo simulado del servicio')
        )

        with self.assertRaisesRegex(
            RuntimeError,
            'Fallo simulado del servicio'
        ):
            call_command(
                'aplicar_bloqueos',
                stdout=StringIO()
            )
