
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
        usuario_id: int
    ) -> int:
        pass

    @abstractmethod
    def tiene_prestamo_activo(
        self,
        ejemplar_id: int
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

    Utiliza los modelos existentes del sistema y concentra
    las operaciones de consulta y escritura de préstamos.
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

        Devuelve una lista limitada y ordenada.
        No incorpora al personal bibliotecario.
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
        Recupera un usuario por su identificador.

        El bloqueo opcional se utilizará posteriormente
        dentro de la transacción del registro de préstamos.
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
        Recupera una copia física por su identificador.

        Para bloquear, se consulta únicamente la fila
        del ejemplar, evitando bloquear tablas relacionadas
        innecesariamente mediante JOIN.
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
        Un préstamo permanece activo mientras no exista
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
            .order_by('fecha_prestamo', 'prestamo_id')
        )

    def contar_prestamos_activos(
        self,
        usuario_id: int
    ) -> int:
        return (
            Prestamo.objects
            .filter(
                usuario_id=usuario_id,
                fecha_devolucion__isnull=True
            )
            .count()
        )

    def tiene_prestamo_activo(
        self,
        ejemplar_id: int
    ) -> bool:
        return (
            Prestamo.objects
            .filter(
                ejemplar_id=ejemplar_id,
                fecha_devolucion__isnull=True
            )
            .exists()
        )

    def listar_sanciones(
        self,
        usuario_id: int
    ) -> QuerySet[Sancion]:
        """
        Consulta las sanciones relacionadas con préstamos
        de un usuario, incluyendo registros históricos.
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
        que todavía no tienen fecha de pago.
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
        Consulta bloqueos registrados cuyo intervalo
        incluye la fecha proporcionada.

        Ambos extremos del intervalo son inclusivos.
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
        Operación de persistencia de bajo nivel.

        No valida la elegibilidad ni la disponibilidad.
        El servicio del commit 2 deberá invocarla
        exclusivamente dentro de una transacción que
        haya validado todas las reglas de negocio.
        """
        return Prestamo.objects.create(
            usuario_id=usuario_id,
            ejemplar_id=ejemplar_id,
            fecha_prestamo=fecha_prestamo,
            fecha_limite=fecha_limite,
            fecha_devolucion=None
        )
