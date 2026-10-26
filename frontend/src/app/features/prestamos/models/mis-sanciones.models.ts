import type {
  EjemplarMiPrestamo,
  LibroMiPrestamo,
} from './mis-prestamos.models';

export type LibroMiSancion = LibroMiPrestamo;
export type EjemplarMiSancion = EjemplarMiPrestamo;

export type TipoSancion = 'ECONOMICA' | 'BLOQUEO';

export type EstadoSancionEconomica = 'PENDIENTE' | 'PAGADA';

export type EstadoSancionBloqueo =
  | 'PROGRAMADO'
  | 'VIGENTE'
  | 'CONCLUIDO';

export type EstadoMiSancion =
  | EstadoSancionEconomica
  | EstadoSancionBloqueo;

export interface MiSancionBase {
  sancion_id: number;
  prestamo_id: number;
  libro: LibroMiSancion | null;
  ejemplar: EjemplarMiSancion | null;
  tipo: TipoSancion;
  estado: EstadoMiSancion;
  monto: string | null;
  fecha_pago: string | null;
  fecha_inicio_bloqueo: string | null;
  fecha_fin_bloqueo: string | null;
}

export interface MiSancionEconomica extends MiSancionBase {
  tipo: 'ECONOMICA';
  estado: EstadoSancionEconomica;
  monto: string;
  fecha_pago: string | null;
  fecha_inicio_bloqueo: null;
  fecha_fin_bloqueo: null;
}

export interface MiSancionBloqueo extends MiSancionBase {
  tipo: 'BLOQUEO';
  estado: EstadoSancionBloqueo;
  monto: null;
  fecha_pago: null;
  fecha_inicio_bloqueo: string;
  fecha_fin_bloqueo: string;
}

export type MiSancion = MiSancionEconomica | MiSancionBloqueo;

export interface ResumenMisSanciones {
  total_sanciones: number;
  multas_pendientes: number;
  monto_total_adeudado: string;
  bloqueos_vigentes: number;
}

export interface RespuestaMisSanciones {
  count: number;
  next: string | null;
  previous: string | null;
  results: MiSancion[];
  resumen: ResumenMisSanciones;
}

export type TipoFiltroMisSanciones =
  | 'todas'
  | 'economicas'
  | 'bloqueos';

export type EstadoFiltroMisSanciones =
  | 'todos'
  | 'pendientes'
  | 'pagadas'
  | 'programados'
  | 'vigentes'
  | 'concluidos';

export interface FiltrosMisSanciones {
  tipo?: TipoFiltroMisSanciones;
  estado?: EstadoFiltroMisSanciones;
  page?: number;
  page_size?: number;
}

export const ESTADOS_VALIDOS_POR_TIPO: Record<
  TipoFiltroMisSanciones,
  readonly EstadoFiltroMisSanciones[]
> = {
  todas: [
    'todos',
    'pendientes',
    'pagadas',
    'programados',
    'vigentes',
    'concluidos',
  ],
  economicas: ['todos', 'pendientes', 'pagadas'],
  bloqueos: ['todos', 'programados', 'vigentes', 'concluidos'],
} as const;

export function esCombinacionFiltrosValida(
  tipo: TipoFiltroMisSanciones = 'todas',
  estado: EstadoFiltroMisSanciones = 'todos',
): boolean {
  if (tipo === 'todas' || estado === 'todos') {
    return true;
  }
  return ESTADOS_VALIDOS_POR_TIPO[tipo].includes(estado);
}
