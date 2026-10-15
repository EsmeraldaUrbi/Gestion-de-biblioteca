export type FiltroMisPrestamos =
  | 'todos'
  | 'activos'
  | 'vencidos'
  | 'devueltos';

export type EstadoMiPrestamo =
  | 'EN_PRESTAMO'
  | 'VENCIDO'
  | 'DEVUELTO';

export interface LibroMiPrestamo {
  libro_id: number;
  titulo: string;
  isbn: string;
}

export interface EjemplarMiPrestamo {
  ejemplar_id: number;
  codigo_inventario: string;
}

export interface MiPrestamo {
  prestamo_id: number;
  libro: LibroMiPrestamo;
  ejemplar: EjemplarMiPrestamo;
  fecha_prestamo: string;
  fecha_limite: string;
  fecha_devolucion: string | null;
  estado: EstadoMiPrestamo;
  dias_restantes: number | null;
}

export interface ResumenMisPrestamos {
  total: number;
  activos: number;
  vencidos: number;
  devueltos: number;
}

export interface MisPrestamosResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: MiPrestamo[];
  resumen: ResumenMisPrestamos;
}