import re
from typing import Dict, Iterable, Optional, Set
from django.db import IntegrityError

from biblioteca.models import Libro
from biblioteca.repositories.libro_repository import (
    DjangoLibroRepository,
    ILibroRepository,
)


def _es_error_isbn(exc: IntegrityError) -> bool:
    """
    Devuelve True si la IntegrityError corresponde a una colisión en el campo ISBN.
    Inspecciona el mensaje de la excepción para evitar enmascarar otras restricciones.
    """
    mensaje = " ".join(str(a) for a in exc.args).lower()
    return bool(re.search(r'\bisbn\b', mensaje))


class LibroNoEncontradoError(Exception):
    pass


class IsbnDuplicadoError(Exception):
    pass


class AutoresNoEncontradosError(Exception):
    def __init__(self, ids_inexistentes: Set[int]):
        self.ids_inexistentes = ids_inexistentes
        super().__init__(f"Los siguientes autores no existen: {sorted(ids_inexistentes)}")


class CategoriasNoEncontradasError(Exception):
    def __init__(self, ids_inexistentes: Set[int]):
        self.ids_inexistentes = ids_inexistentes
        super().__init__(f"Las siguientes categorías no existen: {sorted(ids_inexistentes)}")


class LibroConEjemplaresError(Exception):
    pass


class LibroService:
    """
    Gestiona la lógica de negocio y reglas para la administración bibliográfica de libros.
    Aplica RN-01 (Identificación e ISBN único) y RN-19 (Relaciones sin duplicados).
    """

    def __init__(self, libro_repository: Optional[ILibroRepository] = None):
        self.libro_repository = (
            libro_repository
            if libro_repository is not None
            else DjangoLibroRepository()
        )

    def listar_libros(self, filtros: Optional[Dict] = None):
        return self.libro_repository.listar(filtros)

    def obtener_libro(self, libro_id: int) -> Libro:
        libro = self.libro_repository.obtener_por_id(libro_id)
        if libro is None:
            raise LibroNoEncontradoError(f"No existe un libro con ID {libro_id}.")
        return libro

    def validar_isbn_disponible(self, isbn: str, libro_id: Optional[int] = None) -> None:
        isbn_normalizado = isbn.strip()
        existente = self.libro_repository.obtener_por_isbn(isbn_normalizado)
        if existente is not None and existente.libro_id != libro_id:
            raise IsbnDuplicadoError(f"El ISBN '{isbn_normalizado}' ya se encuentra registrado.")

    def validar_autores_existen(self, autor_ids: Iterable[int]) -> Set[int]:
        ids_solicitados = set(autor_ids)
        if not ids_solicitados:
            return set()
        ids_existentes = self.libro_repository.verificar_autores_existentes(ids_solicitados)
        inexistentes = ids_solicitados - ids_existentes
        if inexistentes:
            raise AutoresNoEncontradosError(inexistentes)
        return ids_solicitados

    def validar_categorias_existen(self, categoria_ids: Iterable[int]) -> Set[int]:
        ids_solicitados = set(categoria_ids)
        if not ids_solicitados:
            return set()
        ids_existentes = self.libro_repository.verificar_categorias_existentes(ids_solicitados)
        inexistentes = ids_solicitados - ids_existentes
        if inexistentes:
            raise CategoriasNoEncontradasError(inexistentes)
        return ids_solicitados

    def registrar_libro(self, datos: Dict) -> Libro:
        """
        Registra un nuevo libro bibliográfico con sus asociaciones.
        Aplica validación de ISBN (RN-01) y deduplicación atómica de autores/categorías (RN-19).
        """
        isbn = datos['isbn'].strip()
        self.validar_isbn_disponible(isbn)

        autor_ids = datos.get('autor_ids') or []
        categoria_ids = datos.get('categoria_ids') or []

        autores_validados = self.validar_autores_existen(autor_ids)
        categorias_validadas = self.validar_categorias_existen(categoria_ids)

        libro = Libro(
            titulo=datos['titulo'].strip(),
            isbn=isbn,
            fecha_publicacion=datos.get('fecha_publicacion')
        )

        try:
            return self.libro_repository.crear(
                libro=libro,
                autor_ids=autores_validados,
                categoria_ids=categorias_validadas
            )
        except IntegrityError as exc:
            if _es_error_isbn(exc):
                raise IsbnDuplicadoError(
                    f"El ISBN '{isbn}' ya está registrado."
                ) from exc
            raise

    def modificar_libro(self, libro_id: int, datos: Dict) -> Libro:
        """
        Modifica los datos bibliográficos de un libro existente y sincroniza sus asociaciones.
        """
        libro = self.obtener_libro(libro_id)
        campos_a_actualizar = []

        if 'titulo' in datos:
            libro.titulo = datos['titulo'].strip()
            campos_a_actualizar.append('titulo')

        if 'isbn' in datos:
            nuevo_isbn = datos['isbn'].strip()
            self.validar_isbn_disponible(nuevo_isbn, libro_id=libro.libro_id)
            libro.isbn = nuevo_isbn
            campos_a_actualizar.append('isbn')

        if 'fecha_publicacion' in datos:
            libro.fecha_publicacion = datos.get('fecha_publicacion')
            campos_a_actualizar.append('fecha_publicacion')

        autores_validados = None
        if 'autor_ids' in datos:
            autor_ids = datos['autor_ids'] or []
            autores_validados = self.validar_autores_existen(autor_ids)

        categorias_validadas = None
        if 'categoria_ids' in datos:
            categoria_ids = datos['categoria_ids'] or []
            categorias_validadas = self.validar_categorias_existen(categoria_ids)

        try:
            return self.libro_repository.actualizar(
                libro=libro,
                campos=campos_a_actualizar if campos_a_actualizar else None,
                autor_ids=autores_validados,
                categoria_ids=categorias_validadas
            )
        except IntegrityError as exc:
            if _es_error_isbn(exc):
                raise IsbnDuplicadoError(
                    f"El ISBN '{libro.isbn}' entra en conflicto con un registro existente."
                ) from exc
            raise

    def eliminar_libro(self, libro_id: int) -> None:
        """
        Elimina un libro solo si no tiene ejemplares físicos asociados (RN-20).
        """
        libro = self.obtener_libro(libro_id)
        if self.libro_repository.tiene_ejemplares(libro_id):
            raise LibroConEjemplaresError(
                f"No se puede eliminar el libro '{libro.titulo}' porque tiene ejemplares físicos asociados."
            )
        self.libro_repository.eliminar(libro)
