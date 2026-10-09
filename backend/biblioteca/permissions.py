from rest_framework.permissions import (
    BasePermission,
)


class RolPermission(BasePermission):

    roles_permitidos = set()

    def has_permission(
        self,
        request,
        view
    ):
        usuario = request.user

        if (
            usuario is None
            or not getattr(
                usuario,
                'is_authenticated',
                False
            )
        ):
            return False

        rol = getattr(
            usuario,
            'rol',
            None
        )

        if rol is None:
            return False

        nombre_rol = (
            rol.nombre
            .strip()
            .casefold()
        )

        return (
            nombre_rol
            in self.roles_permitidos
        )


class IsBibliotecario(RolPermission):
    roles_permitidos = {
        'bibliotecario'
    }

    message = (
        'Esta operación requiere '
        'el rol de bibliotecario.'
    )


class IsEstudiante(RolPermission):
    roles_permitidos = {
        'estudiante'
    }

    message = (
        'Esta operación requiere '
        'el rol de estudiante.'
    )


class IsDocente(RolPermission):
    roles_permitidos = {
        'docente'
    }

    message = (
        'Esta operación requiere '
        'el rol de docente.'
    )


class IsEstudianteODocente(
    RolPermission
):
    roles_permitidos = {
        'estudiante',
        'docente'
    }

    message = (
        'Esta operación está disponible '
        'únicamente para estudiantes '
        'y docentes.'
    )