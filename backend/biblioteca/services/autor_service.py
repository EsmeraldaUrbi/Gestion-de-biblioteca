from datetime import date, datetime
from typing import Dict, Optional

from django.db.models import QuerySet
from django.utils import timezone

from biblioteca.models import Autor
from biblioteca.repositories.autor_repository import (
    DjangoAutorRepository,
    IAutorRepository,
)


class AutorNoEncontradoError(Exception):
    pass


class AutorDatosInvalidosError(Exception):
    pass


class AutorOperacionNoPermitidaError(Exception):
    pass


class AutorService:
    """
    Lógica de negocio para la administración de autores.
    Aplica validaciones de campos del modelo, normalización de datos
    y política de protección de relaciones bibliográficas.
    """

    def __init__(self, autor_repository: Optional[IAutorRepository] = None):
        self.autor_repository = (
            autor_repository
            if autor_repository is not None
            else DjangoAutorRepository()
        )

    def validar_nombre(self, nombre: Optional[str]) -> str:
        if not nombre or not isinstance(nombre, str):
            raise AutorDatosInvalidosError("El nombre del autor no puede estar vacío.")

        nombre_limpio = nombre.strip()
        if not nombre_limpio:
            raise AutorDatosInvalidosError(
                "El nombre del autor no puede estar compuesto únicamente de espacios."
            )

        if len(nombre_limpio) > 100:
            raise AutorDatosInvalidosError(
                "El nombre del autor no puede exceder los 100 caracteres."
            )

        return nombre_limpio

    def validar_nacionalidad(self, nacionalidad: Optional[str]) -> Optional[str]:
        if nacionalidad is None:
            return None

        if not isinstance(nacionalidad, str):
            raise AutorDatosInvalidosError("La nacionalidad debe ser una cadena de texto.")

        nacionalidad_limpia = nacionalidad.strip()
        if not nacionalidad_limpia:
            return None

        if len(nacionalidad_limpia) > 50:
            raise AutorDatosInvalidosError(
                "La nacionalidad no puede exceder los 50 caracteres."
            )

        return nacionalidad_limpia

    def validar_fecha_nacimiento(
        self,
        fecha: Optional[date | str],
    ) -> Optional[date]:
        if fecha is None or fecha == '':
            return None

        fecha_objeto: date
        if isinstance(fecha, str):
            fecha_str = fecha.strip()
            if not fecha_str:
                return None
            try:
                fecha_objeto = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                raise AutorDatosInvalidosError(
                    f"La fecha de nacimiento '{fecha_str}' no tiene un formato válido (AAAA-MM-DD)."
                )
        elif isinstance(fecha, date):
            fecha_objeto = fecha
        else:
            raise AutorDatosInvalidosError("Formato de fecha de nacimiento no reconocido.")

        hoy = timezone.localdate() if hasattr(timezone, 'localdate') else date.today()
        if fecha_objeto > hoy:
            raise AutorDatosInvalidosError(
                "La fecha de nacimiento no puede ser una fecha futura."
            )

        return fecha_objeto

    def listar_autores(self, filtros: Optional[Dict] = None) -> QuerySet[Autor]:
        return self.autor_repository.listar(filtros)

    def obtener_autor(self, autor_id: int) -> Autor:
        autor = self.autor_repository.obtener_por_id(autor_id)
        if autor is None:
            raise AutorNoEncontradoError(f"No existe un autor con ID {autor_id}.")
        return autor

    def buscar_homonimos(self, nombre: str) -> QuerySet[Autor]:
        """
        Permite identificar autores con nombres idénticos o coincidentes
        sin bloquear su registro, permitiendo la existencia legítima de homónimos.
        """
        if not nombre or not isinstance(nombre, str):
            return self.autor_repository.buscar_por_nombre_exacto('')
        return self.autor_repository.buscar_por_nombre_exacto(nombre.strip())

    def registrar_autor(self, datos: Dict) -> Autor:
        """
        Registra un nuevo autor en el sistema tras validar sus campos.
        No bloquea la creación si existen homónimos.
        """
        nombre_limpio = self.validar_nombre(datos.get('nombre'))
        nacionalidad_limpia = self.validar_nacionalidad(datos.get('nacionalidad'))
        fecha_nacimiento_valida = self.validar_fecha_nacimiento(
            datos.get('fecha_nacimiento')
        )

        autor = Autor(
            nombre=nombre_limpio,
            nacionalidad=nacionalidad_limpia,
            fecha_nacimiento=fecha_nacimiento_valida,
        )

        return self.autor_repository.crear(autor)

    def modificar_autor(self, autor_id: int, datos: Dict) -> Autor:
        """
        Modifica los datos de un autor existente.
        Acepta modificaciones parciales o completas.
        """
        autor = self.obtener_autor(autor_id)
        campos_a_actualizar = []

        if 'nombre' in datos:
            autor.nombre = self.validar_nombre(datos['nombre'])
            campos_a_actualizar.append('nombre')

        if 'nacionalidad' in datos:
            autor.nacionalidad = self.validar_nacionalidad(datos['nacionalidad'])
            campos_a_actualizar.append('nacionalidad')

        if 'fecha_nacimiento' in datos:
            autor.fecha_nacimiento = self.validar_fecha_nacimiento(
                datos['fecha_nacimiento']
            )
            campos_a_actualizar.append('fecha_nacimiento')

        return self.autor_repository.actualizar(
            autor,
            campos=campos_a_actualizar if campos_a_actualizar else None,
        )

    def tiene_libros_asociados(self, autor_id: int) -> bool:
        return self.autor_repository.tiene_libros_asociados(autor_id)

    def contar_libros_asociados(self, autor_id: int) -> int:
        return self.autor_repository.contar_libros_asociados(autor_id)

    def eliminar_autor(self, autor_id: int) -> None:
        """
        Protege las relaciones bibliográficas existentes impidiendo eliminaciones
        físicas arbitrarias. Cualquier intento de eliminación es rechazado.
        """
        self.obtener_autor(autor_id)
        tiene_libros = self.tiene_libros_asociados(autor_id)
        if tiene_libros:
            raise AutorOperacionNoPermitidaError(
                "No se puede eliminar el autor porque tiene libros asociados en el catálogo (RN-20)."
            )
        raise AutorOperacionNoPermitidaError(
            "La eliminación física de autores no está habilitada en el sistema para conservar el historial."
        )
