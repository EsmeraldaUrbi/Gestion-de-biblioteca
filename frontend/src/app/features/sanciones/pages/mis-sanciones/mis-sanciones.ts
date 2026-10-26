import {
  NgClass,
} from '@angular/common';
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
  EstadoFiltroMisSanciones,
  MiSancion,
  ResumenMisSanciones,
  TipoFiltroMisSanciones,
} from '../../../prestamos/models/mis-sanciones.models';
import {
  esCombinacionFiltrosValida,
} from '../../../prestamos/models/mis-sanciones.models';
import {
  MisSancionesService,
} from '../../../prestamos/services/mis-sanciones.service';


interface OpcionTipo {
  valor: TipoFiltroMisSanciones;
  etiqueta: string;
}

interface OpcionEstado {
  valor: EstadoFiltroMisSanciones;
  etiqueta: string;
  tipos: TipoFiltroMisSanciones[];
}


const OPCIONES_TIPO: OpcionTipo[] = [
  { valor: 'todas', etiqueta: 'Todas' },
  { valor: 'economicas', etiqueta: 'Multas económicas' },
  { valor: 'bloqueos', etiqueta: 'Bloqueos' },
];

const OPCIONES_ESTADO: OpcionEstado[] = [
  { valor: 'todos', etiqueta: 'Todos los estados', tipos: ['todas', 'economicas', 'bloqueos'] },
  { valor: 'pendientes', etiqueta: 'Pendiente', tipos: ['todas', 'economicas'] },
  { valor: 'pagadas', etiqueta: 'Pagada', tipos: ['todas', 'economicas'] },
  { valor: 'programados', etiqueta: 'Programado', tipos: ['todas', 'bloqueos'] },
  { valor: 'vigentes', etiqueta: 'Vigente', tipos: ['todas', 'bloqueos'] },
  { valor: 'concluidos', etiqueta: 'Concluido', tipos: ['todas', 'bloqueos'] },
];


@Component({
  selector: 'app-mis-sanciones',
  standalone: true,
  imports: [NgClass],
  templateUrl: './mis-sanciones.html',
  styleUrl: './mis-sanciones.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MisSancionesComponent implements OnInit {
  private readonly service = inject(MisSancionesService);
  private readonly destroyRef = inject(DestroyRef);

  readonly pageSize = 10;

  readonly opcionesTipo = OPCIONES_TIPO;

  readonly sanciones = signal<MiSancion[]>([]);
  readonly resumen = signal<ResumenMisSanciones>({
    total_sanciones: 0,
    multas_pendientes: 0,
    monto_total_adeudado: '0.00',
    bloqueos_vigentes: 0,
  });

  readonly filtroTipo = signal<TipoFiltroMisSanciones>('todas');
  readonly filtroEstado = signal<EstadoFiltroMisSanciones>('todos');
  readonly pagina = signal(1);
  readonly total = signal(0);
  readonly cargando = signal(false);
  readonly error = signal<string | null>(null);

  private versionConsulta = 0;

  readonly opcionesEstadoDisponibles = computed<OpcionEstado[]>(() => {
    const tipo = this.filtroTipo();
    return OPCIONES_ESTADO.filter((o) => o.tipos.includes(tipo));
  });

  readonly totalPaginas = computed(() =>
    Math.max(1, Math.ceil(this.total() / this.pageSize)),
  );

  readonly primerRegistro = computed(() =>
    this.total() === 0 ? 0 : (this.pagina() - 1) * this.pageSize + 1,
  );

  readonly ultimoRegistro = computed(() =>
    Math.min(this.pagina() * this.pageSize, this.total()),
  );

  ngOnInit(): void {
    this.cargar(1);
  }

  cargar(paginaSolicitada = 1): void {
    if (paginaSolicitada < 1) {
      return;
    }

    const version = ++this.versionConsulta;
    this.cargando.set(true);
    this.error.set(null);

    this.service
      .listar({
        tipo: this.filtroTipo(),
        estado: this.filtroEstado(),
        page: paginaSolicitada,
        page_size: this.pageSize,
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (respuesta) => {
          if (version !== this.versionConsulta) {
            return;
          }
          this.sanciones.set(respuesta.results);
          this.resumen.set(respuesta.resumen);
          this.total.set(respuesta.count);
          this.pagina.set(paginaSolicitada);
          this.cargando.set(false);
        },
        error: (err: HttpErrorResponse) => {
          if (version !== this.versionConsulta) {
            return;
          }
          this.sanciones.set([]);
          this.error.set(this.mensajeError(err));
          this.cargando.set(false);
        },
      });
  }

  cambiarTipo(tipo: TipoFiltroMisSanciones): void {
    if (this.filtroTipo() === tipo) {
      return;
    }

    this.filtroTipo.set(tipo);

    // Si el estado actual no es compatible con el nuevo tipo, resetear a 'todos'.
    if (!esCombinacionFiltrosValida(tipo, this.filtroEstado())) {
      this.filtroEstado.set('todos');
    }

    this.cargar(1);
  }

  cambiarEstado(estado: EstadoFiltroMisSanciones): void {
    if (this.filtroEstado() === estado) {
      return;
    }

    this.filtroEstado.set(estado);
    this.cargar(1);
  }

  cambiarPagina(paginaSolicitada: number): void {
    if (
      paginaSolicitada < 1 ||
      paginaSolicitada > this.totalPaginas() ||
      this.cargando()
    ) {
      return;
    }

    this.cargar(paginaSolicitada);
  }

  actualizar(): void {
    this.cargar(this.pagina());
  }

  formatoMoneda(monto: string | null): string {
    return new Intl.NumberFormat('es-MX', {
      style: 'currency',
      currency: 'MXN',
    }).format(Number(monto ?? 0));
  }

  formatoFecha(fecha: string | null): string {
    if (!fecha) {
      return '—';
    }

    const partes = fecha.split('-');

    if (partes.length !== 3) {
      return fecha;
    }

    return `${partes[2]}/${partes[1]}/${partes[0]}`;
  }

  etiquetaEstado(sancion: MiSancion): string {
    switch (sancion.estado) {
      case 'PENDIENTE':
        return 'Pendiente de pago';
      case 'PAGADA':
        return 'Pagada';
      case 'PROGRAMADO':
        return 'Bloqueo programado';
      case 'VIGENTE':
        return 'Bloqueo vigente';
      case 'CONCLUIDO':
        return 'Bloqueo concluido';
    }
  }

  claseEstado(sancion: MiSancion): string {
    switch (sancion.estado) {
      case 'PENDIENTE':
        return 'badge--pending';
      case 'PAGADA':
        return 'badge--paid';
      case 'PROGRAMADO':
        return 'badge--scheduled';
      case 'VIGENTE':
        return 'badge--active';
      case 'CONCLUIDO':
        return 'badge--done';
    }
  }

  private mensajeError(err: HttpErrorResponse): string {
    if (err.status === 0) {
      return 'No fue posible conectar con el servidor.';
    }

    if (err.status === 400) {
      const detalle = err.error?.estado?.[0] ?? err.error?.detail ?? null;
      return detalle
        ? `Filtro inválido: ${detalle}`
        : 'Los filtros seleccionados no son compatibles.';
    }

    if (err.status === 401) {
      return 'Tu sesión ha vencido. Inicia sesión nuevamente.';
    }

    if (err.status === 403) {
      return 'Esta consulta está disponible únicamente para lectores.';
    }

    if (err.status === 404) {
      return 'La página solicitada no existe.';
    }

    return 'No fue posible consultar tus sanciones. Inténtalo nuevamente.';
  }
}
