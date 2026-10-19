import type {
  EstadoEjemplar,
  PrestamoRegistrado,
} from './prestamo.models';

export interface PrestamoActivoDevolucion {
  prestamo: PrestamoRegistrado;
  fecha_referencia: string;
  dias_retraso: number;
  monto_multa: string;
}

export interface DevolucionRegistrada {
  mensaje: string;
  prestamo_id: number;
  fecha_devolucion: string;
  dias_retraso: number;
  monto_multa: string;
  sancion_generada: boolean;
  sancion_id?: number;
  ejemplar_estado: EstadoEjemplar;
}