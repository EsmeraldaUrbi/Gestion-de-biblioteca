import {
  HttpErrorResponse,
} from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import {
  takeUntilDestroyed,
} from '@angular/core/rxjs-interop';

import type {
  ResumenMisSanciones,
  Sancion,
} from '../../models/sanciones.models';
import {
  SancionesService,
} from '../../services/sanciones.service';


type FiltroPersonal = 'todas' | 'pendientes' | 'pagadas' | 'bloqueos';


@Component({
  selector: 'app-mis-sanciones',
  standalone: true,
  templateUrl: './mis-sanciones.html',
  styleUrl: './mis-sanciones.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MisSancionesComponent implements OnInit {
  private readonly service = inject(SancionesService);
  private readonly destroyRef = inject(DestroyRef);

  readonly sanciones = signal<Sancion[]>([]);
  readonly resumen = signal<ResumenMisSanciones>({
    monto_pendiente: '0.00', monto_pagado: '0.00', bloqueos_vigentes: 0,
  });
  readonly cargando = signal(false);
  readonly error = signal<string | null>(null);
  readonly filtro = signal<FiltroPersonal>('todas');

  readonly visibles = computed(() => this.sanciones().filter((sancion) => {
    switch (this.filtro()) {
      case 'pendientes': return sancion.estado === 'PENDIENTE';
      case 'pagadas': return sancion.estado === 'PAGADA';
      case 'bloqueos': return sancion.tipo === 'BLOQUEO';
      default: return true;
    }
  }));

  ngOnInit(): void { this.cargar(); }

  cargar(): void {
    this.cargando.set(true);
    this.error.set(null);
    this.service.obtenerMias().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (respuesta) => {
        this.sanciones.set(respuesta.results);
        this.resumen.set(respuesta.resumen);
        this.cargando.set(false);
      },
      error: (error: HttpErrorResponse) => {
        this.sanciones.set([]);
        this.cargando.set(false);
        this.error.set(this.mensajeError(error));
      },
    });
  }

  cambiarFiltro(filtro: FiltroPersonal): void { this.filtro.set(filtro); }

  formatoMoneda(monto: string | null): string {
    return new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' })
      .format(Number(monto ?? 0));
  }

  formatoFecha(fecha: string | null): string {
    if (!fecha) return '—';
    const [anio, mes, dia] = fecha.split('-');
    return `${dia}/${mes}/${anio}`;
  }

  etiquetaEstado(sancion: Sancion): string {
    const etiquetas: Record<Sancion['estado'], string> = {
      PENDIENTE: 'Pendiente de pago', PAGADA: 'Pagada',
      VIGENTE: 'Bloqueo vigente', FINALIZADA: 'Bloqueo finalizado',
    };
    return etiquetas[sancion.estado];
  }

  private mensajeError(error: HttpErrorResponse): string {
    if (error.status === 0) return 'No fue posible conectar con el servidor.';
    if (error.status === 401) return 'Tu sesión ha vencido. Inicia sesión nuevamente.';
    if (error.status === 403) return 'Esta consulta está disponible para lectores.';
    return 'No fue posible consultar tus sanciones. Inténtalo nuevamente.';
  }
}
