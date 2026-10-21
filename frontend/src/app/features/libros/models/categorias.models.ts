// ---------------------------------------------------------------------------
// Modelos de administración de categorías - Ticket 3.3
// Fuente de verdad: Documentacion/API/libros_ejemplares.md
// ---------------------------------------------------------------------------

import { Categoria } from './libros.models';

/**
 * Representación administrativa completa de una categoría temática devuelta por
 * GET /api/categorias/, POST /api/categorias/, GET /api/categorias/{id}/, etc.
 * Extiende la interfaz básica Categoria de libros.models.ts.
 */
export interface CategoriaAdministrativa extends Categoria {
  /** Cantidad de libros clasificados en esta categoría en el catálogo. */
  cantidad_libros: number;
}

/** Envoltorio de respuesta paginada de la API de categorías. */
export interface CategoriasPaginadas {
  count: number;
  next: string | null;
  previous: string | null;
  results: CategoriaAdministrativa[];
}

/**
 * Cuerpo para POST /api/categorias/.
 * El nombre de la categoría es obligatorio y único en el sistema.
 */
export interface RegistrarCategoriaRequest {
  /** Nombre no vacío de la categoría (máx 50 caracteres). */
  nombre_categoria: string;
}

/**
 * Cuerpo para PATCH /api/categorias/{categoria_id}/.
 * Modificación parcial de la categoría.
 */
export interface ModificarCategoriaRequest {
  /** Nuevo nombre no vacío para la categoría. */
  nombre_categoria?: string;
}

/**
 * Cuerpo para PUT /api/categorias/{categoria_id}/.
 * Reemplazo integral del recurso categoría.
 */
export interface ActualizarCategoriaRequest {
  /** Nombre obligatorio para la categoría. */
  nombre_categoria: string;
}

/**
 * Parámetros de consulta opcionales aceptados por GET /api/categorias/.
 */
export interface CategoriasFiltros {
  /** Coincidencia parcial insensible a mayúsculas/minúsculas sobre nombre_categoria. */
  nombre?: string;
  /** Alias de conveniencia para la búsqueda por texto. */
  search?: string;
  /** Página solicitada (inicia en 1). */
  page?: number;
  /** Registros por página (máximo 100). */
  page_size?: number;
}
