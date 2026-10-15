// ---------------------------------------------------------------------------
// Modelos de libros y ejemplares - Ticket 3.3.1
// Fuente de verdad: Documentacion/API/libros_ejemplares.md
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Tipos compartidos
// ---------------------------------------------------------------------------

/** Autor resumido incluido en las respuestas de libro. */
export interface Autor {
  autor_id: number;
  nombre: string;
}

/** Categoría resumida incluida en las respuestas de libro. */
export interface Categoria {
  categoria_id: number;
  nombre_categoria: string;
}

/** Estados operativos válidos de un ejemplar (RN-03). */
export type EstadoEjemplar = 'ACTIVO' | 'MANTENIMIENTO' | 'BAJA';

// ---------------------------------------------------------------------------
// Libro - respuesta
// ---------------------------------------------------------------------------

/**
 * Objeto libro tal como lo devuelve la API en GET /api/libros/ y
 * GET /api/libros/{libro_id}/.
 */
export interface Libro {
  libro_id: number;
  titulo: string;
  isbn: string;
  /** Fecha en formato "YYYY-MM-DD" o null si no está registrada. */
  fecha_publicacion: string | null;
  autores: Autor[];
  categorias: Categoria[];
}

/** Envoltorio de respuesta paginada de la API de libros. */
export interface LibrosPaginados {
  count: number;
  next: string | null;
  previous: string | null;
  results: Libro[];
}

// ---------------------------------------------------------------------------
// Libro - solicitudes
// ---------------------------------------------------------------------------

/**
 * Cuerpo para POST /api/libros/.
 * Todos los campos del libro más las listas de IDs de asociaciones.
 */
export interface RegistrarLibroRequest {
  /** No vacío, máximo 100 caracteres. */
  titulo: string;
  /** No vacío, máximo 13 caracteres, único en el catálogo (RN-01). */
  isbn: string;
  /** Formato "YYYY-MM-DD". Opcional: se puede omitir o enviar null. */
  fecha_publicacion?: string | null;
  /** IDs de autores a asociar. Omitir deja el libro sin autores. */
  autor_ids?: number[];
  /** IDs de categorías a asociar. Omitir deja el libro sin categorías. */
  categoria_ids?: number[];
}

/**
 * Cuerpo para PATCH /api/libros/{libro_id}/.
 * Solo los campos presentes son actualizados; las asociaciones omitidas
 * se conservan intactas (comportamiento distinto al de PUT).
 */
export type ModificarLibroRequest = Partial<RegistrarLibroRequest>;

/**
 * Cuerpo para PUT /api/libros/{libro_id}/.
 * Exige titulo e isbn. La omisión de autor_ids o categoria_ids
 * vacía las asociaciones del libro.
 */
export interface ActualizarLibroRequest {
  /** Obligatorio. */
  titulo: string;
  /** Obligatorio. */
  isbn: string;
  fecha_publicacion?: string | null;
  /** Si se omite, las asociaciones de autores quedan vacías. */
  autor_ids?: number[];
  /** Si se omite, las asociaciones de categorías quedan vacías. */
  categoria_ids?: number[];
}

// ---------------------------------------------------------------------------
// Libro - filtros de consulta
// ---------------------------------------------------------------------------

/**
 * Parámetros opcionales aceptados por GET /api/libros/.
 */
export interface LibrosFiltros {
  /** Coincidencia parcial, insensible a mayúsculas/minúsculas. */
  titulo?: string;
  /** Coincidencia parcial en el código ISBN. */
  isbn?: string;
  /** ID del autor a filtrar. */
  autor_id?: number;
  /** ID de la categoría a filtrar. */
  categoria_id?: number;
  /** Página solicitada (inicia en 1). */
  page?: number;
  /** Registros por página (máximo 100). */
  page_size?: number;
}

// ---------------------------------------------------------------------------
// Ejemplar - respuesta
// ---------------------------------------------------------------------------

/** Referencia resumida del libro dentro de la respuesta de ejemplar. */
export interface EjemplarLibro {
  libro_id: number;
  titulo: string;
  isbn: string;
}

/**
 * Objeto ejemplar tal como lo devuelve la API en
 * GET /api/ejemplares/ y GET /api/ejemplares/{ejemplar_id}/.
 */
export interface Ejemplar {
  ejemplar_id: number;
  libro_id: number;
  libro: EjemplarLibro;
  /** Máximo 15 caracteres, único en el sistema (RN-02). */
  codigo_inventario: string;
  estado: EstadoEjemplar;
}

/** Envoltorio de respuesta paginada de la API de ejemplares. */
export interface EjemplaresPaginados {
  count: number;
  next: string | null;
  previous: string | null;
  results: Ejemplar[];
}

// ---------------------------------------------------------------------------
// Ejemplar - solicitudes
// ---------------------------------------------------------------------------

/**
 * Cuerpo para POST /api/ejemplares/.
 * El estado es opcional: si se omite, el backend asigna ACTIVO (RN-03).
 */
export interface RegistrarEjemplarRequest {
  /** ID de un libro existente en el catálogo. */
  libro_id: number;
  /** Máximo 15 caracteres, único (RN-02). */
  codigo_inventario: string;
  /** Opcional. Predeterminado: ACTIVO (RN-03). */
  estado?: EstadoEjemplar;
}

/**
 * Cuerpo para PATCH /api/ejemplares/{ejemplar_id}/.
 * Este endpoint acepta ÚNICAMENTE el campo estado.
 * Enviar codigo_inventario, libro_id u otros campos resulta en HTTP 400.
 */
export interface CambiarEstadoEjemplarRequest {
  estado: EstadoEjemplar;
}

// ---------------------------------------------------------------------------
// Ejemplar - filtros de consulta
// ---------------------------------------------------------------------------

/**
 * Parámetros opcionales aceptados por GET /api/ejemplares/.
 */
export interface EjemplaresFiltros {
  /** Filtra ejemplares de un libro específico. */
  libro_id?: number;
  /** Filtra por estado operativo. */
  estado?: EstadoEjemplar;
  /** Coincidencia parcial en código de inventario. */
  codigo_inventario?: string;
  /** Página solicitada (inicia en 1). */
  page?: number;
  /** Registros por página (máximo 100). */
  page_size?: number;
}
