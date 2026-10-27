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

import {
  FormControl,
  ReactiveFormsModule,
} from '@angular/forms';

import {
  RouterLink,
} from '@angular/router';

import type {
  FiltroEstadoPrestamoAdmin,
  PrestamoAdmin,
  ResumenPrestamosAdmin,
} from '../../models/prestamos-admin.models';

import {
  PrestamosAdminService,
} from '../../services/prestamos-admin.service';


@Component({
  selector: 'app-historial-prestamos',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
  ],
  templateUrl: './historial-prestamos.html',
  styleUrl: './historial-prestamos.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class HistorialPrestamosComponent implements OnInit {
  private readonly prestamosService =
    inject(PrestamosAdminService);

  private readonly destroyRef =
    inject(DestroyRef);

  readonly busqueda = new FormControl(
    '',
    { nonNullable: true },
  );

  readonly estados: {
    valor: FiltroEstadoPrestamoAdmin;
    etiqueta: string;
  }[] = [
    {
      valor: 'todos',
      etiqueta: 'Todos los estados',
    },
    {
      valor: 'en_prestamo',
      etiqueta: 'En préstamo',
    },
    {
      valor: 'vencidos',
      etiqueta: 'Vencidos',
    },
    {
      valor: 'devueltos',
      etiqueta: 'Devueltos',
    },
  ];

  readonly prestamos = signal<PrestamoAdmin[]>([]);

  readonly resumen = signal<ResumenPrestamosAdmin>({
    total: 0,
    en_prestamo: 0,
    vencidos: 0,
    devueltos: 0,
  });

  readonly estado = signal<FiltroEstadoPrestamoAdmin>(
    'todos',
  );

  readonly pagina = signal(1);
  readonly total = signal(0);

  readonly cargando = signal(false);
  readonly error = signal<string | null>(null);

  readonly pageSize = 10;

  private versionConsulta = 0;

  readonly totalPaginas = computed(() =>
    Math.max(
      1,
      Math.ceil(this.total() / this.pageSize),
    ),
  );

  readonly primerRegistro = computed(() =>
    this.total() === 0
      ? 0
      : (this.pagina() - 1) * this.pageSize + 1,
  );

  readonly ultimoRegistro = computed(() =>
    Math.min(
      this.pagina() * this.pageSize,
      this.total(),
    ),
  );

  ngOnInit(): void {
    this.cargar();
  }

  cargar(paginaSolicitada = 1): void {
    if (paginaSolicitada < 1) {
      return;
    }

    const version = ++this.versionConsulta;

    this.cargando.set(true);
    this.error.set(null);

    this.prestamosService
      .listar({
        q: this.busqueda.value,
        estado: this.estado(),
        page: paginaSolicitada,
        pageSize: this.pageSize,
      })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (respuesta) => {
          if (version !== this.versionConsulta) {
            return;
          }

          this.prestamos.set(respuesta.results);
          this.resumen.set(respuesta.resumen);
          this.total.set(respuesta.count);
          this.pagina.set(paginaSolicitada);

          this.cargando.set(false);
        },

        error: (error: HttpErrorResponse) => {
          if (version !== this.versionConsulta) {
            return;
          }

          this.prestamos.set([]);

          this.error.set(
            this.obtenerMensajeError(error),
          );

          this.cargando.set(false);
        },
      });
  }

  buscar(): void {
    this.cargar(1);
  }

  cambiarEstado(valor: string): void {
    const estadosValidos = this.estados.map(
      (opcion) => opcion.valor,
    );

    if (
      !estadosValidos.includes(
        valor as FiltroEstadoPrestamoAdmin,
      )
    ) {
      return;
    }

    this.estado.set(
      valor as FiltroEstadoPrestamoAdmin,
    );

    this.cargar(1);
  }

  limpiarFiltros(): void {
    this.busqueda.setValue('');
    this.estado.set('todos');

    this.cargar(1);
  }

  actualizar(): void {
    this.cargar(this.pagina());
  }

  paginaAnterior(): void {
    if (
      this.pagina() > 1 &&
      !this.cargando()
    ) {
      this.cargar(this.pagina() - 1);
    }
  }

  paginaSiguiente(): void {
    if (
      this.pagina() < this.totalPaginas() &&
      !this.cargando()
    ) {
      this.cargar(this.pagina() + 1);
    }
  }

  formatearFecha(
    fecha: string | null,
  ): string {
    if (!fecha) {
      return '—';
    }

    const [anio, mes, dia] = fecha.split('-');

    return `${dia}/${mes}/${anio}`;
  }

  etiquetaEstado(
    estado: PrestamoAdmin['estado'],
  ): string {
    const etiquetas: Record<
      PrestamoAdmin['estado'],
      string
    > = {
      EN_PRESTAMO: 'En préstamo',
      VENCIDO: 'Vencido',
      DEVUELTO: 'Devuelto',
    };

    return etiquetas[estado];
  }

  detalleEstado(prestamo: PrestamoAdmin): string {
    if (prestamo.estado === 'DEVUELTO') {
      return 'Préstamo finalizado';
    }

    if (prestamo.estado === 'VENCIDO') {
      return 'Pendiente fuera de plazo';
    }

    if (prestamo.dias_restantes === 0) {
      return 'Vence hoy';
    }

    if (prestamo.dias_restantes === 1) {
      return 'Queda 1 día';
    }

    return `Quedan ${prestamo.dias_restantes ?? 0} días`;
  }

  private obtenerMensajeError(
    error: HttpErrorResponse,
  ): string {
    if (error.status === 0) {
      return 'No fue posible conectar con el servidor.';
    }

    if (error.status === 401) {
      return 'Tu sesión ha vencido. Inicia sesión nuevamente.';
    }

    if (error.status === 403) {
      return 'Esta consulta está reservada al bibliotecario.';
    }

    if (error.status === 404) {
      return 'La página solicitada no existe.';
    }

    if (
      typeof error.error?.detail === 'string'
    ) {
      return error.error.detail;
    }

    return 'No fue posible consultar los préstamos.';
  }
}