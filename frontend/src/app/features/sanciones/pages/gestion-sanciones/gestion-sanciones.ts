import {
  HttpErrorResponse,
} from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import {
  takeUntilDestroyed,
} from '@angular/core/rxjs-interop';
import {
  FormControl,
  ReactiveFormsModule,
} from '@angular/forms';

import type {
  FiltroEstadoSancion,
  ResumenSancionesAdministrativo,
  Sancion,
  TipoSancion,
} from '../../models/sanciones.models';
import {
  SancionesService,
} from '../../services/sanciones.service';


@Component({
  selector: 'app-gestion-sanciones',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './gestion-sanciones.html',
  styleUrl: './gestion-sanciones.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class GestionSancionesComponent implements OnInit {
  private readonly service = inject(SancionesService);
  private readonly destroyRef = inject(DestroyRef);

  readonly busqueda = new FormControl('', { nonNullable: true });
  readonly sanciones = signal<Sancion[]>([]);
  readonly resumen = signal<ResumenSancionesAdministrativo>({
    multas_pendientes: 0,
    monto_pendiente: '0.00',
    bloqueos_vigentes: 0,
  });
  readonly cargando = signal(false);
  readonly registrandoPago = signal(false);
  readonly error = signal<string | null>(null);
  readonly confirmacion = signal<Sancion | null>(null);
  readonly exito = signal<string | null>(null);

  readonly tipo = signal<TipoSancion | 'todos'>('todos');
  // La consulta administrativa debe mostrar multas y bloqueos al entrar.
  // "pendiente" solo contempla multas económicas y ocultaba los bloqueos.
  readonly estado = signal<FiltroEstadoSancion>('todos');
  readonly pagina = signal(1);
  readonly total = signal(0);
  readonly pageSize = 10;

  ngOnInit(): void {
    this.cargar();
  }

  cargar(pagina = 1): void {
    this.cargando.set(true);
    this.error.set(null);

    this.service.obtenerAdministrativas({
      q: this.busqueda.value,
      tipo: this.tipo(),
      estado: this.estado(),
      page: pagina,
      pageSize: this.pageSize,
    }).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (respuesta) => {
        this.sanciones.set(respuesta.results);
        this.resumen.set(respuesta.resumen);
        this.total.set(respuesta.count);
        this.pagina.set(pagina);
        this.cargando.set(false);
      },
      error: (error: HttpErrorResponse) => {
        this.sanciones.set([]);
        this.cargando.set(false);
        this.error.set(this.mensajeError(error));
      },
    });
  }

  buscar(): void {
    this.exito.set(null);
    this.cargar(1);
  }

  cambiarTipo(valor: string): void {
    this.tipo.set(valor as TipoSancion | 'todos');
    this.cargar(1);
  }

  cambiarEstado(valor: string): void {
    this.estado.set(valor as FiltroEstadoSancion);
    this.cargar(1);
  }

  abrirConfirmacion(sancion: Sancion): void {
    if (sancion.estado === 'PENDIENTE' && sancion.tipo === 'ECONOMICA') {
      this.confirmacion.set(sancion);
      this.error.set(null);
    }
  }

  cerrarConfirmacion(): void {
    if (!this.registrandoPago()) {
      this.confirmacion.set(null);
    }
  }

  confirmarPago(): void {
    const sancion = this.confirmacion();
    if (!sancion || this.registrandoPago()) {
      return;
    }

    this.registrandoPago.set(true);
    this.error.set(null);
    this.service.registrarPago(sancion.sancion_id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (pagada) => {
          this.registrandoPago.set(false);
          this.confirmacion.set(null);
          this.exito.set(`Pago de multa #${pagada.sancion_id} registrado correctamente.`);
          this.cargar(this.pagina());
        },
        error: (error: HttpErrorResponse) => {
          this.registrandoPago.set(false);
          this.confirmacion.set(null);
          this.error.set(this.mensajeError(error));
          this.cargar(this.pagina());
        },
      });
  }

  paginaAnterior(): void {
    if (this.pagina() > 1 && !this.cargando()) {
      this.cargar(this.pagina() - 1);
    }
  }

  paginaSiguiente(): void {
    if (this.pagina() * this.pageSize < this.total() && !this.cargando()) {
      this.cargar(this.pagina() + 1);
    }
  }

  esCobrable(sancion: Sancion): boolean {
    return sancion.tipo === 'ECONOMICA' && sancion.estado === 'PENDIENTE';
  }

  etiquetaTipo(sancion: Sancion): string {
    return sancion.tipo === 'ECONOMICA' ? 'Multa económica' : 'Bloqueo temporal';
  }

  etiquetaEstado(sancion: Sancion): string {
    const etiquetas: Record<Sancion['estado'], string> = {
      PENDIENTE: 'Pendiente de cobro',
      PAGADA: 'Pagada en caja',
      VIGENTE: 'Bloqueo vigente',
      FINALIZADA: 'Bloqueo finalizado',
    };
    return etiquetas[sancion.estado];
  }

  formatoMoneda(monto: string | null): string {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency', currency: 'MXN',
    }).format(Number(monto ?? 0));
  }

  formatoFecha(fecha: string | null): string {
    if (!fecha) return '—';
    const [anio, mes, dia] = fecha.split('-');
    return `${dia}/${mes}/${anio}`;
  }

  private mensajeError(error: HttpErrorResponse): string {
    if (error.status === 0) return 'No fue posible conectar con el servidor.';
    if (error.status === 401) return 'Tu sesión ha vencido. Inicia sesión nuevamente.';
    if (error.status === 403) return 'Solo el bibliotecario puede gestionar sanciones.';
    if (typeof error.error?.detail === 'string') return error.error.detail;
    return 'No fue posible completar la operación. Inténtalo nuevamente.';
  }
}
