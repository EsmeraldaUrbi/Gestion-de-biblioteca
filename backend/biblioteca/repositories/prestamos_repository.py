from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Optional

from django.db.models import Q, QuerySet

from biblioteca.models import (
    Ejemplar,
    Prestamo,
    Rol,
    Sancion,
    Usuario,
)


class IPrestamoRepository(ABC):
    """
    Contrato de acceso a datos para el módulo de préstamos.
    """

    @abstractmethod
    def listar_roles_lectores(self) -> QuerySet[Rol]:
        pass

    @abstractmethod
    def buscar_lectores(
        self,
        termino: str,
        limite: int = 10
    ) -> list[Usuario]:
        pass

    @abstractmethod
    def obtener_usuario(
        self,
        usuario_id: int,
        con_bloqueo: bool = False
    ) -> Optional[Usuario]:
        pass

    @abstractmethod
    def obtener_ejemplar(
        self,
        ejemplar_id: int,
        con_bloqueo: bool = False
    ) -> Optional[Ejemplar]:
        pass

    @abstractmethod
    def listar_prestamos_activos(
        self,
        usuario_id: int
    ) -> QuerySet[Prestamo]:
        pass

    @abstractmethod
    def contar_prestamos_activos(
        self,
        usuario_id: int,
        con_bloqueo: bool = False
    ) -> int:
        pass

    @abstractmethod
    def tiene_prestamo_activo(
        self,
        ejemplar_id: int,
        con_bloqueo: bool = False
    ) -> bool:
        pass

    @abstractmethod
    def listar_sanciones(
        self,
        usuario_id: int
    ) -> QuerySet[Sancion]:
        pass

    @abstractmethod
    def tiene_adeudos_pendientes(
        self,
        usuario_id: int
    ) -> bool:
        pass

    @abstractmethod
    def tiene_bloqueo_vigente(
        self,
        usuario_id: int,
        fecha: date
    ) -> bool:
        pass

    @abstractmethod
    def crear_prestamo(
        self,
        usuario_id: int,
        ejemplar_id: int,
        fecha_prestamo: date,
        fecha_limite: date
    ) -> Prestamo:
        pass


class DjangoPrestamoRepository(IPrestamoRepository):
    """
    Implementación de persistencia mediante Django ORM.

    Utiliza los modelos existentes del proyecto y concentra
    las consultas y operaciones de almacenamiento de préstamos.
    """

    def listar_roles_lectores(self) -> QuerySet[Rol]:
        return (
            Rol.objects
            .filter(
                Q(nombre__iexact='estudiante') |
                Q(nombre__iexact='docente')
            )
            .order_by('rol_id')
        )

    def buscar_lectores(
        self,
        termino: str,
        limite: int = 10
    ) -> list[Usuario]:
        """
        Busca estudiantes y docentes por nombre o correo.

        No incluye usuarios con rol bibliotecario.
        """
        termino = termino.strip()

        if not termino:
            return []

        usuarios = (
            Usuario.objects
            .select_related('rol')
            .filter(
                Q(rol__nombre__iexact='estudiante') |
                Q(rol__nombre__iexact='docente')
            )
            .filter(
                Q(nombre__icontains=termino) |
                Q(email__icontains=termino)
            )
            .order_by('nombre', 'usuario_id')
        )

        return list(usuarios[:limite])

    def obtener_usuario(
        self,
        usuario_id: int,
        con_bloqueo: bool = False
    ) -> Optional[Usuario]:
        """
        Obtiene el usuario correspondiente al identificador.

        Cuando se solicita bloqueo, utiliza SELECT FOR UPDATE.
        No realiza JOIN con Rol para evitar bloquear otras filas
        innecesariamente.
        """
        usuarios = Usuario.objects.all()

        if con_bloqueo:
            usuarios = usuarios.select_for_update()
        else:
            usuarios = usuarios.select_related('rol')

        return (
            usuarios
            .filter(usuario_id=usuario_id)
            .first()
        )

    def obtener_ejemplar(
        self,
        ejemplar_id: int,
        con_bloqueo: bool = False
    ) -> Optional[Ejemplar]:
        """
        Obtiene una copia física por identificador.

        El bloqueo es compatible con el utilizado por
        EjemplarService.cambiar_estado() del módulo 3.3.
        """
        ejemplares = Ejemplar.objects.all()

        if con_bloqueo:
            ejemplares = ejemplares.select_for_update()
        else:
            ejemplares = ejemplares.select_related('libro')

        return (
            ejemplares
            .filter(ejemplar_id=ejemplar_id)
            .first()
        )

    def listar_prestamos_activos(
        self,
        usuario_id: int
    ) -> QuerySet[Prestamo]:
        """
        Un préstamo se considera activo cuando no existe
        una fecha de devolución registrada.
        """
        return (
            Prestamo.objects
            .select_related(
                'ejemplar',
                'ejemplar__libro'
            )
            .filter(
                usuario_id=usuario_id,
                fecha_devolucion__isnull=True
            )
            .order_by(
                'fecha_prestamo',
                'prestamo_id'
            )
        )

    def contar_prestamos_activos(
        self,
        usuario_id: int,
        con_bloqueo: bool = False
    ) -> int:
        """
        Cuenta los préstamos que todavía no han sido devueltos.

        En una operación de registro utiliza una lectura
        bloqueante para consultar los datos confirmados más
        recientes, incluso bajo REPEATABLE READ de MySQL.
        """
        prestamos = Prestamo.objects.filter(
            usuario_id=usuario_id,
            fecha_devolucion__isnull=True
        )

        if con_bloqueo:
            identificadores = (
                prestamos
                .select_for_update()
                .values_list(
                    'prestamo_id',
                    flat=True
                )
            )

            return len(list(identificadores))

        return prestamos.count()

    def tiene_prestamo_activo(
        self,
        ejemplar_id: int,
        con_bloqueo: bool = False
    ) -> bool:
        """
        Determina si existe un préstamo activo sobre un ejemplar.

        La consulta bloqueante permite validar la ocupación
        después de obtener el bloqueo de la copia física.
        """
        prestamos = Prestamo.objects.filter(
            ejemplar_id=ejemplar_id,
            fecha_devolucion__isnull=True
        )

        if con_bloqueo:
            prestamos = prestamos.select_for_update()

        return prestamos.exists()

    def listar_sanciones(
        self,
        usuario_id: int
    ) -> QuerySet[Sancion]:
        """
        Consulta todas las sanciones relacionadas con
        los préstamos del usuario.
        """
        return (
            Sancion.objects
            .select_related('prestamo')
            .filter(
                prestamo__usuario_id=usuario_id
            )
            .order_by('sancion_id')
        )

    def tiene_adeudos_pendientes(
        self,
        usuario_id: int
    ) -> bool:
        """
        Identifica sanciones con un importe positivo
        que no tienen registrada una fecha de pago.
        """
        return (
            Sancion.objects
            .filter(
                prestamo__usuario_id=usuario_id,
                monto__gt=Decimal('0.00'),
                fecha_pago__isnull=True
            )
            .exists()
        )

    def tiene_bloqueo_vigente(
        self,
        usuario_id: int,
        fecha: date
    ) -> bool:
        """
        Determina si una sanción tiene un período de bloqueo
        que incluye la fecha consultada.
        """
        return (
            Sancion.objects
            .filter(
                prestamo__usuario_id=usuario_id,
                fecha_inicio_bloqueo__lte=fecha,
                fecha_fin_bloqueo__gte=fecha
            )
            .exists()
        )

    def crear_prestamo(
        self,
        usuario_id: int,
        ejemplar_id: int,
        fecha_prestamo: date,
        fecha_limite: date
    ) -> Prestamo:
        """
        Persiste el préstamo mediante Django ORM.

        Esta operación no valida por sí misma las reglas.
        Debe invocarse desde PrestamoService.registrar_prestamo(),
        dentro de la transacción correspondiente.
        """
        return Prestamo.objects.create(
            usuario_id=usuario_id,
            ejemplar_id=ejemplar_id,
            fecha_prestamo=fecha_prestamo,
            fecha_limite=fecha_limite,
            fecha_devolucion=None
        )