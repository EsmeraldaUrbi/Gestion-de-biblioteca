import type {
  EjemplarMiPrestamo,
  EstadoMiPrestamo,
  LibroMiPrestamo,
} from './mis-prestamos.models';


export type FiltroEstadoPrestamoAdmin =
  | 'todos'
  | 'en_prestamo'
  | 'vencidos'
  | 'devueltos';


export interface UsuarioPrestamoAdmin {
  usuario_id: number;
  nombre: string;
  email: string;
  rol: string;
}


export interface PrestamoAdmin {
  prestamo_id: number;
  usuario: UsuarioPrestamoAdmin;
  libro: LibroMiPrestamo;
  ejemplar: EjemplarMiPrestamo;
  fecha_prestamo: string;
  fecha_limite: string;
  fecha_devolucion: string | null;
  estado: EstadoMiPrestamo;
  dias_restantes: number | null;
}


export interface ResumenPrestamosAdmin {
  total: number;
  en_prestamo: number;
  vencidos: number;
  devueltos: number;
}


export interface PrestamosAdminResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: PrestamoAdmin[];
  resumen: ResumenPrestamosAdmin;
}


export interface FiltrosPrestamosAdmin {
  q: string;
  estado: FiltroEstadoPrestamoAdmin;
  page: number;
  pageSize: number;
}