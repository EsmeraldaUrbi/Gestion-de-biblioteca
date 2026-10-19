import re
from typing import Dict, Optional

from django.db import IntegrityError
from django.db.models import QuerySet

from biblioteca.models import Categoria
from biblioteca.repositories.categoria_repository import (
    DjangoCategoriaRepository,
    ICategoriaRepository,
)


def _es_error_nombre_categoria(exc: IntegrityError) -> bool:
    """
    Devuelve True si la excepción IntegrityError corresponde a una colisión de unicidad
    en el campo nombre_categoria, evitando enmascarar otros errores de integridad.
    """
    mensaje = " ".join(str(a) for a in exc.args).lower()
    return bool(
        re.search(r'\bnombre_categoria\b', mensaje)
        or 'duplicate entry' in mensaje
        or '1062' in mensaje
    )


class CategoriaNoEncontradaError(Exception):
    pass


class CategoriaDatosInvalidosError(Exception):
    pass


class CategoriaDuplicadaError(Exception):
    pass


class CategoriaOperacionNoPermitidaError(Exception):
    pass


class CategoriaService:
    """
    Lógica de negocio para la administración de categorías temáticas.
    Aplica validación de nombre obligatorio, normalización de espacios,
    prevención de duplicados y protección de relaciones bibliográficas.
    """

    def __init__(self, categoria_repository: Optional[ICategoriaRepository] = None):
        self.categoria_repository = (
            categoria_repository
            if categoria_repository is not None
            else DjangoCategoriaRepository()
        )

    def validar_nombre(self, nombre: Optional[str]) -> str:
        if not nombre or not isinstance(nombre, str):
            raise CategoriaDatosInvalidosError(
                "El nombre de la categoría no puede estar vacío."
            )

        nombre_limpio = nombre.strip()
        if not nombre_limpio:
            raise CategoriaDatosInvalidosError(
                "El nombre de la categoría no puede estar compuesto únicamente de espacios."
            )

        if len(nombre_limpio) > 50:
            raise CategoriaDatosInvalidosError(
                "El nombre de la categoría no puede exceder los 50 caracteres."
            )

        return nombre_limpio

    def validar_nombre_disponible(
        self,
        nombre: str,
        categoria_id: Optional[int] = None,
    ) -> None:
        nombre_limpio = self.validar_nombre(nombre)
        existente = self.categoria_repository.obtener_por_nombre(nombre_limpio)
        if existente is not None and existente.categoria_id != categoria_id:
            raise CategoriaDuplicadaError(
                f"La categoría '{nombre_limpio}' ya se encuentra registrada."
            )

    def listar_categorias(self, filtros: Optional[Dict] = None) -> QuerySet[Categoria]:
        return self.categoria_repository.listar(filtros)

    def obtener_categoria(self, categoria_id: int) -> Categoria:
        categoria = self.categoria_repository.obtener_por_id(categoria_id)
        if categoria is None:
            raise CategoriaNoEncontradaError(
                f"No existe una categoría con ID {categoria_id}."
            )
        return categoria

    def registrar_categoria(self, datos: Dict) -> Categoria:
        """
        Registra una nueva categoría temática tras verificar que su nombre sea válido y único.
        """
        nombre_raw = None
        if 'nombre_categoria' in datos:
            nombre_raw = datos['nombre_categoria']
        elif 'nombre' in datos:
            nombre_raw = datos['nombre']

        nombre_limpio = self.validar_nombre(nombre_raw)
        self.validar_nombre_disponible(nombre_limpio)

        categoria = Categoria(nombre_categoria=nombre_limpio)

        try:
            return self.categoria_repository.crear(categoria)
        except IntegrityError as exc:
            if _es_error_nombre_categoria(exc):
                raise CategoriaDuplicadaError(
                    f"La categoría '{nombre_limpio}' ya está registrada en la base de datos."
                ) from exc
            raise

    def modificar_categoria(self, categoria_id: int, datos: Dict) -> Categoria:
        """
        Modifica el nombre de una categoría existente validando que no colisione con otra.
        """
        categoria = self.obtener_categoria(categoria_id)
        campos_a_actualizar = []

        nuevo_nombre = None
        tiene_campo_nombre = False
        if 'nombre_categoria' in datos:
            nuevo_nombre = datos['nombre_categoria']
            tiene_campo_nombre = True
        elif 'nombre' in datos:
            nuevo_nombre = datos['nombre']
            tiene_campo_nombre = True

        if tiene_campo_nombre:
            nombre_limpio = self.validar_nombre(nuevo_nombre)
            self.validar_nombre_disponible(nombre_limpio, categoria_id=categoria.categoria_id)
            categoria.nombre_categoria = nombre_limpio
            campos_a_actualizar.append('nombre_categoria')

        try:
            return self.categoria_repository.actualizar(
                categoria,
                campos=campos_a_actualizar if campos_a_actualizar else None,
            )
        except IntegrityError as exc:
            if _es_error_nombre_categoria(exc):
                raise CategoriaDuplicadaError(
                    f"El nombre '{categoria.nombre_categoria}' entra en conflicto con otra categoría existente."
                ) from exc
            raise

    def tiene_libros_asociados(self, categoria_id: int) -> bool:
        return self.categoria_repository.tiene_libros_asociados(categoria_id)

    def contar_libros_asociados(self, categoria_id: int) -> int:
        return self.categoria_repository.contar_libros_asociados(categoria_id)

    def eliminar_categoria(self, categoria_id: int) -> None:
        """
        Protege las relaciones bibliográficas existentes impidiendo eliminaciones
        físicas arbitrarias. Cualquier intento de eliminación es rechazado.
        """
        self.obtener_categoria(categoria_id)
        tiene_libros = self.tiene_libros_asociados(categoria_id)
        if tiene_libros:
            raise CategoriaOperacionNoPermitidaError(
                "No se puede eliminar la categoría porque tiene libros asociados en el catálogo (RN-20)."
            )
        raise CategoriaOperacionNoPermitidaError(
            "La eliminación física de categorías no está habilitada en el sistema para conservar el historial."
        )
