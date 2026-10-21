// ---------------------------------------------------------------------------
// Modelos de administración de autores - Ticket 3.3
// Fuente de verdad: Documentacion/API/libros_ejemplares.md
// ---------------------------------------------------------------------------

import { Autor } from './libros.models';

/**
 * Representación administrativa completa de un autor devuelta por la API en
 * GET /api/autores/, POST /api/autores/, GET /api/autores/{id}/, etc.
 * Extiende la interfaz básica Autor de libros.models.ts.
 */
export interface AutorAdministrativo extends Autor {
  /** Nacionalidad del autor (máx 50 caracteres) o null si no se registró. */
  nacionalidad: string | null;
  /** Fecha en formato "YYYY-MM-DD" o null si no se registró. */
  fecha_nacimiento: string | null;
  /** Cantidad de libros asociados actualmente a este autor en el catálogo. */
  cantidad_libros: number;
}

/** Envoltorio de respuesta paginada de la API de autores. */
export interface AutoresPaginados {
  count: number;
  next: string | null;
  previous: string | null;
  results: AutorAdministrativo[];
}

/**
 * Cuerpo para POST /api/autores/.
 * El nombre es obligatorio. Nacionalidad y fecha de nacimiento son opcionales.
 */
export interface RegistrarAutorRequest {
  /** Nombre completo del autor. No vacío, máx 100 caracteres. */
  nombre: string;
  /** Nacionalidad opcional. Máx 50 caracteres o null. */
  nacionalidad?: string | null;
  /** Fecha de nacimiento opcional en formato "YYYY-MM-DD" (menor o igual a hoy) o null. */
  fecha_nacimiento?: string | null;
}

/**
 * Cuerpo para PATCH /api/autores/{autor_id}/.
 * Modificación parcial. Solo los campos provistos son modificados;
 * los omitidos conservan su valor previo en la base de datos.
 */
export interface ModificarAutorRequest {
  /** Nuevo nombre no vacío. */
  nombre?: string;
  /** Nueva nacionalidad o null. */
  nacionalidad?: string | null;
  /** Nueva fecha de nacimiento en formato "YYYY-MM-DD" o null. */
  fecha_nacimiento?: string | null;
}

/**
 * Cuerpo para PUT /api/autores/{autor_id}/.
 * Reemplazo integral: exige 'nombre'. Omitir 'nacionalidad' o 'fecha_nacimiento'
 * los restablece automáticamente a null en backend.
 */
export interface ActualizarAutorRequest {
  nombre: string;
  nacionalidad?: string | null;
  fecha_nacimiento?: string | null;
}

/**
 * Parámetros de consulta opcionales aceptados por GET /api/autores/.
 */
export interface AutoresFiltros {
  /** Coincidencia parcial insensible a mayúsculas/minúsculas sobre el nombre. */
  nombre?: string;
  /** Alias de conveniencia para la búsqueda por texto. */
  search?: string;
  /** Coincidencia parcial insensible a mayúsculas/minúsculas sobre la nacionalidad. */
  nacionalidad?: string;
  /** Página solicitada (inicia en 1). */
  page?: number;
  /** Registros por página (máximo 100). */
  page_size?: number;
}
