import type {
  Usuario,
} from '../../usuarios/models/usuario.models';

export interface RespuestaPaginada<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface BusquedaLectores {
  count: number;
  results: Usuario[];
}

export interface AutorLibro {
  autor_id: number;
  nombre: string;
}

export interface CategoriaLibro {
  categoria_id: number;
  nombre_categoria: string;
}

export interface LibroPrestamo {
  libro_id: number;
  titulo: string;
  isbn: string;
  fecha_publicacion: string | null;
  autores: AutorLibro[];
  categorias: CategoriaLibro[];
}

export type EstadoEjemplar =
  | 'ACTIVO'
  | 'MANTENIMIENTO'
  | 'BAJA';

export interface EjemplarPrestamo {
  ejemplar_id: number;
  libro_id: number;
  libro: {
    libro_id: number;
    titulo: string;
    isbn: string;
  };
  codigo_inventario: string;
  estado: EstadoEjemplar;
}

export interface MotivoRechazo {
  codigo: string;
  mensaje: string;
}

export interface ElegibilidadPrestamo {
  elegible: boolean;
  motivos: MotivoRechazo[];
  usuario: Usuario;
  ejemplar: EjemplarPrestamo;
  prestamos_activos: number;
  limite_prestamos_activos: number;
  fecha_prestamo: string;
  fecha_limite: string;
}

export interface SolicitudPrestamo {
  usuario_id: number;
  ejemplar_id: number;
}

export interface PrestamoRegistrado {
  prestamo_id: number;
  usuario_id: number;
  usuario: Usuario;
  ejemplar_id: number;
  ejemplar: EjemplarPrestamo;
  fecha_prestamo: string;
  fecha_limite: string;
  fecha_devolucion: string | null;
}

export interface ErrorPrestamo {
  codigo?: string;
  detail?: string;
  [campo: string]: unknown;
}