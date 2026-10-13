from django.core.management.base import (
    BaseCommand,
)
from django.utils import timezone

from biblioteca.models import (
    Rol,
    TokenAcceso,
    Usuario,
)


class Command(BaseCommand):

    help = (
        'Crea roles y usuarios de demostración '
        'para probar autenticación.'
    )

    PASSWORD_DEMO = 'Biblioteca123*'

    ROLES = [
        {
            'nombre': 'estudiante',
            'limite': 5,
        },
        {
            'nombre': 'docente',
            'limite': 5,
        },
        {
            'nombre': 'bibliotecario',
            'limite': 0,
        },
    ]

    USUARIOS = [
        {
            'nombre': 'Esmeralda Urbina Cinto',
            'email': 'esme@bibliotech.com',
            'rol': 'estudiante',
        },
        {
            'nombre': 'Josué Saúl Torres Zamora',
            'email': 'saul@bibliotech.com',
            'rol': 'docente',
        },
        {
            'nombre': 'Kaltum Abdala Viveros Gómez',
            'email': 'kalt@bibliotech.com',
            'rol': 'bibliotecario',
        },
    ]

    def handle(self, *args, **options):
        roles = {}

        for rol_data in self.ROLES:
            nombre = rol_data['nombre']

            rol = (
                Rol.objects
                .filter(nombre__iexact=nombre)
                .order_by('rol_id')
                .first()
            )

            if rol is None:
                rol = Rol.objects.create(
                    nombre=nombre,
                    limite_prestamos_activos=(
                        rol_data['limite']
                    )
                )

            else:
                rol.nombre = nombre

                rol.limite_prestamos_activos = (
                    rol_data['limite']
                )

                rol.save(
                    update_fields=[
                        'nombre',
                        'limite_prestamos_activos',
                    ]
                )

            roles[nombre] = rol

        for usuario_data in self.USUARIOS:
            email = usuario_data['email']

            usuario = (
                Usuario.objects
                .filter(email__iexact=email)
                .first()
            )

            if usuario is None:
                usuario = Usuario(
                    email=email
                )

            usuario.nombre = (
                usuario_data['nombre']
            )

            usuario.rol = roles[
                usuario_data['rol']
            ]

            usuario.set_password(
                self.PASSWORD_DEMO
            )

            usuario.save()

            TokenAcceso.objects.filter(
                usuario=usuario,
                revocado_en__isnull=True
            ).update(
                revocado_en=timezone.now()
            )

        self.stdout.write(
            self.style.SUCCESS(
                'Datos de autenticación '
                'creados correctamente.'
            )
        )

        self.stdout.write('')

        self.stdout.write(
            'Credenciales de prueba:'
        )

        for usuario_data in self.USUARIOS:
            self.stdout.write(
                usuario_data['email']
            )

        self.stdout.write(
            f'Contraseña: {self.PASSWORD_DEMO}'
        )