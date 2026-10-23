export type TipoSancion = 'ECONOMICA' | 'BLOQUEO';

export type EstadoSancion =
  | 'PENDIENTE'
  | 'PAGADA'
  | 'VIGENTE'
  | 'FINALIZADA';

export type FiltroEstadoSancion =
  | 'todos'
  | 'pendiente'
  | 'pagada'
  | 'vigente'
  | 'finalizada';

export interface UsuarioSancion {
  usuario_id: number;
  nombre: string;
  email: string;
}

export interface LibroSancion {
  libro_id: number;
  titulo: string;
  isbn: string;
}

export interface EjemplarSancion {
  ejemplar_id: number;
  codigo_inventario: string;
  libro: LibroSancion;
}

export interface PrestamoSancion {
  prestamo_id: number;
  fecha_prestamo: string;
  fecha_limite: string;
  fecha_devolucion: string | null;
  usuario: UsuarioSancion;
  ejemplar: EjemplarSancion;
}

export interface Sancion {
  sancion_id: number;
  tipo: TipoSancion;
  monto: string | null;
  fecha_pago: string | null;
  fecha_inicio_bloqueo: string | null;
  fecha_fin_bloqueo: string | null;
  estado: EstadoSancion;
  prestamo: PrestamoSancion;
}

export interface ResumenSancionesAdministrativo {
  multas_pendientes: number;
  monto_pendiente: string;
  bloqueos_vigentes: number;
}

export interface ResumenMisSanciones {
  monto_pendiente: string;
  monto_pagado: string;
  bloqueos_vigentes: number;
}

export interface RespuestaPaginadaSanciones<TResumen> {
  count: number;
  next: string | null;
  previous: string | null;
  results: Sancion[];
  resumen: TResumen;
}
