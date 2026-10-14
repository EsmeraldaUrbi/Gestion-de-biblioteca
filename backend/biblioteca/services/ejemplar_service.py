import re
from typing import Dict, Optional

from django.db import IntegrityError, transaction
from django.db.models import QuerySet

from biblioteca.models import Ejemplar, EstadoEjemplar
from biblioteca.repositories.ejemplar_repository import (
    DjangoEjemplarRepository,
    IEjemplarRepository,
)
from biblioteca.services.libro_service import LibroNoEncontradoError


def _es_error_codigo_inventario(exc: IntegrityError) -> bool:
    """
    Devuelve True si la excepción IntegrityError corresponde a una colisión en codigo_inventario.
    """
    mensaje = " ".join(str(a) for a in exc.args).lower()
    return 'codigo_inventario' in mensaje or 'codigo' in mensaje


class EjemplarNoEncontradoError(Exception):
    pass


class CodigoInventarioDuplicadoError(Exception):
    pass


class CodigoInventarioInvalidoError(Exception):
    pass


class EstadoEjemplarInvalidoError(Exception):
    pass


class EjemplarConPrestamoActivoError(Exception):
    pass


class EjemplarConHistorialPrestamosError(Exception):
    pass


class EjemplarService:
    """
    Lógica de negocio para la gestión de ejemplares físicos.
    Aplica RN-02 (Código único), RN-03 (Estados válidos y ACTIVO por defecto),
    RN-04 (Bloqueo de cambios ante préstamos activos) y RN-20 (Preservación de historial).
    """

    def __init__(self, ejemplar_repository: Optional[IEjemplarRepository] = None):
        self.ejemplar_repository = (
            ejemplar_repository
            if ejemplar_repository is not None
            else DjangoEjemplarRepository()
        )

    def validar_codigo_inventario(
        self,
        codigo: Optional[str],
        ejemplar_id: Optional[int] = None
    ) -> str:
        if not codigo or not isinstance(codigo, str):
            raise CodigoInventarioInvalidoError(
                "El código de inventario no puede estar vacío."
            )

        codigo_limpio = codigo.strip()
        if not codigo_limpio:
            raise CodigoInventarioInvalidoError(
                "El código de inventario no puede estar compuesto únicamente de espacios."
            )

        if len(codigo_limpio) > 15:
            raise CodigoInventarioInvalidoError(
                "El código de inventario no puede exceder los 15 caracteres."
            )

        existente = self.ejemplar_repository.obtener_por_codigo(codigo_limpio)
        if existente is not None and existente.ejemplar_id != ejemplar_id:
            raise CodigoInventarioDuplicadoError(
                f"El código de inventario '{codigo_limpio}' ya se encuentra registrado (RN-02)."
            )

        return codigo_limpio

    def validar_estado(self, estado: Optional[str]) -> str:
        if not estado or not isinstance(estado, str):
            raise EstadoEjemplarInvalidoError(
                "El estado del ejemplar no puede estar vacío."
            )

        estado_normalizado = estado.strip().upper()
        if estado_normalizado not in EstadoEjemplar.values:
            raise EstadoEjemplarInvalidoError(
                f"El estado '{estado}' no es válido (RN-03). "
                f"Debe ser uno de: {list(EstadoEjemplar.values)}."
            )

        return estado_normalizado

    def registrar_ejemplar(self, datos: Dict) -> Ejemplar:
        """
        Registra un ejemplar físico asociado a un libro existente.
        Aplica RN-02 (código de inventario único) y RN-03 (estado predeterminado ACTIVO).
        """
        libro_id = datos.get('libro_id')
        if not libro_id:
            raise LibroNoEncontradoError(
                "Debe indicarse el identificador de un libro para registrar un ejemplar."
            )

        if not self.ejemplar_repository.existe_libro(libro_id):
            raise LibroNoEncontradoError(
                f"No existe un libro registrado con ID {libro_id}."
            )

        codigo_limpio = self.validar_codigo_inventario(
            datos.get('codigo_inventario')
        )

        estado_solicitado = datos.get('estado')
        if not estado_solicitado:
            estado_final = EstadoEjemplar.ACTIVO
        else:
            estado_final = self.validar_estado(estado_solicitado)

        ejemplar = Ejemplar(
            libro_id=libro_id,
            codigo_inventario=codigo_limpio,
            estado=estado_final
        )

        try:
            return self.ejemplar_repository.crear(ejemplar)
        except IntegrityError as exc:
            if _es_error_codigo_inventario(exc):
                raise CodigoInventarioDuplicadoError(
                    f"El código de inventario '{codigo_limpio}' ya está registrado."
                ) from exc
            raise

    def obtener_ejemplar(self, ejemplar_id: int) -> Ejemplar:
        ejemplar = self.ejemplar_repository.obtener_por_id(ejemplar_id)
        if ejemplar is None:
            raise EjemplarNoEncontradoError(
                f"No existe un ejemplar con ID {ejemplar_id}."
            )
        return ejemplar

    def listar_ejemplares(self, filtros: Optional[Dict] = None) -> QuerySet[Ejemplar]:
        return self.ejemplar_repository.listar(filtros)

    def listar_ejemplares_por_libro(self, libro_id: int) -> QuerySet[Ejemplar]:
        if not self.ejemplar_repository.existe_libro(libro_id):
            raise LibroNoEncontradoError(
                f"No existe un libro registrado con ID {libro_id}."
            )
        return self.ejemplar_repository.listar_por_libro(libro_id)

    def cambiar_estado(self, ejemplar_id: int, nuevo_estado: str) -> Ejemplar:
        """
        Modifica el estado de un ejemplar físico aplicando concurrencia segura
        (select_for_update) y validando que no tenga préstamos activos (RN-04).
        """
        estado_normalizado = self.validar_estado(nuevo_estado)

        with transaction.atomic():
            ejemplar = self.ejemplar_repository.obtener_por_id(
                ejemplar_id,
                con_bloqueo=True
            )
            if ejemplar is None:
                raise EjemplarNoEncontradoError(
                    f"No existe un ejemplar con ID {ejemplar_id}."
                )

            if estado_normalizado in (
                EstadoEjemplar.MANTENIMIENTO,
                EstadoEjemplar.BAJA,
            ):
                if self.ejemplar_repository.tiene_prestamos_activos(ejemplar_id):
                    raise EjemplarConPrestamoActivoError(
                        f"No se puede cambiar el estado a '{estado_normalizado}' "
                        f"porque el ejemplar '{ejemplar.codigo_inventario}' "
                        f"tiene un préstamo activo en curso (RN-04)."
                    )

            if ejemplar.estado != estado_normalizado:
                ejemplar.estado = estado_normalizado
                self.ejemplar_repository.actualizar(
                    ejemplar,
                    campos=['estado']
                )

            return ejemplar

    def dar_de_baja(self, ejemplar_id: int) -> Ejemplar:
        """
        Realiza la baja lógica de un ejemplar (RN-20) impidiendo su uso futuro,
        siempre que no tenga préstamos activos (RN-04).
        """
        return self.cambiar_estado(ejemplar_id, EstadoEjemplar.BAJA)

    def eliminar_ejemplar(self, ejemplar_id: int) -> None:
        """
        Elimina físicamente un ejemplar solo si carece de historial de préstamos (RN-20).
        Si tiene historial, rechaza la operación para preservar la integridad histórica.
        """
        with transaction.atomic():
            ejemplar = self.ejemplar_repository.obtener_por_id(
                ejemplar_id,
                con_bloqueo=True
            )
            if ejemplar is None:
                raise EjemplarNoEncontradoError(
                    f"No existe un ejemplar con ID {ejemplar_id}."
                )

            if self.ejemplar_repository.tiene_prestamos_historicos(ejemplar_id):
                raise EjemplarConHistorialPrestamosError(
                    f"No se puede eliminar físicamente el ejemplar "
                    f"'{ejemplar.codigo_inventario}' porque cuenta con un historial "
                    f"de préstamos registrado (RN-20). Debe aplicarse una baja lógica."
                )

            self.ejemplar_repository.eliminar_fisico(ejemplar)
