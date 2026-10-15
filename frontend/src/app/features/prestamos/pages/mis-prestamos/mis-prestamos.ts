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
  AuthSessionService,
} from '../../../../core/auth/services/auth-session.service';

import {
  EstadoCuentaPrestamos,
  FiltroMisPrestamos,
  MiPrestamo,
  ResumenMisPrestamos,
} from '../../models/mis-prestamos.models';

import {
  MisPrestamosService,
} from '../../services/mis-prestamos.service';


interface OpcionFiltro {
  valor: FiltroMisPrestamos;
  etiqueta: string;
}


@Component({
  selector: 'app-mis-prestamos',
  standalone: true,
  templateUrl: './mis-prestamos.html',
  styleUrl: './mis-prestamos.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MisPrestamosComponent implements OnInit {
  private readonly misPrestamosService =
    inject(MisPrestamosService);

  private readonly destroyRef =
    inject(DestroyRef);

  readonly session =
    inject(AuthSessionService);

  readonly pageSize = 8;

  readonly filtros: OpcionFiltro[] = [
    {
      valor: 'todos',
      etiqueta: 'Todos',
    },
    {
      valor: 'activos',
      etiqueta: 'Activos',
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

  readonly prestamos = signal<MiPrestamo[]>([]);

  readonly resumen = signal<ResumenMisPrestamos>({
    total: 0,
    activos: 0,
    vencidos: 0,
    devueltos: 0,
  });

  readonly estadoCuenta =
    signal<EstadoCuentaPrestamos | null>(null);

  readonly filtroActual =
    signal<FiltroMisPrestamos>('todos');

  readonly pagina = signal(1);
  readonly total = signal(0);

  readonly cargando = signal(false);
  readonly error = signal<string | null>(null);

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

  readonly rolUsuario = computed(() =>
    this.session.rol() === 'docente'
      ? 'Docente'
      : 'Estudiante',
  );

  readonly porcentajeCapacidad = computed(() => {
    const cuenta = this.estadoCuenta();

    if (!cuenta || cuenta.limite_prestamos_activos <= 0) {
      return 0;
    }

    return Math.min(
      100,
      Math.round(
        cuenta.prestamos_activos * 100 /
        cuenta.limite_prestamos_activos,
      ),
    );
  });

  ngOnInit(): void {
    this.cargarPrestamos();
  }

  cargarPrestamos(paginaSolicitada = 1): void {
    if (paginaSolicitada < 1) {
      return;
    }

    const version = ++this.versionConsulta;

    this.cargando.set(true);
    this.error.set(null);

    this.misPrestamosService
      .obtenerMisPrestamos(
        this.filtroActual(),
        paginaSolicitada,
        this.pageSize,
      )
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
          this.estadoCuenta.set(
            respuesta.estado_cuenta,
          );

          this.total.set(respuesta.count);
          this.pagina.set(paginaSolicitada);

          this.cargando.set(false);
        },

        error: (error: HttpErrorResponse) => {
          if (version !== this.versionConsulta) {
            return;
          }

          this.prestamos.set([]);
          this.estadoCuenta.set(null);

          this.error.set(
            this.obtenerMensajeError(error),
          );

          this.cargando.set(false);
        },
      });
  }

  cambiarFiltro(filtro: FiltroMisPrestamos): void {
    if (this.filtroActual() === filtro) {
      return;
    }

    this.filtroActual.set(filtro);
    this.cargarPrestamos(1);
  }

  cambiarPagina(paginaSolicitada: number): void {
    if (
      paginaSolicitada < 1 ||
      paginaSolicitada > this.totalPaginas() ||
      this.cargando()
    ) {
      return;
    }

    this.cargarPrestamos(paginaSolicitada);
  }

  actualizar(): void {
    this.cargarPrestamos(this.pagina());
  }

  formatearFecha(fecha: string | null): string {
    if (!fecha) {
      return '—';
    }

    const partes = fecha.split('-');

    if (partes.length !== 3) {
      return fecha;
    }

    return `${partes[2]}/${partes[1]}/${partes[0]}`;
  }

  etiquetaEstado(prestamo: MiPrestamo): string {
    switch (prestamo.estado) {
      case 'EN_PRESTAMO':
        return 'En préstamo';

      case 'VENCIDO':
        return 'Vencido';

      case 'DEVUELTO':
        return 'Devuelto';
    }
  }

  textoPlazo(prestamo: MiPrestamo): string {
    if (prestamo.estado === 'DEVUELTO') {
      return 'Préstamo finalizado';
    }

    if (prestamo.estado === 'VENCIDO') {
      return 'Plazo de devolución vencido';
    }

    const dias = prestamo.dias_restantes;

    if (dias === 0) {
      return 'La devolución corresponde a hoy';
    }

    if (dias === 1) {
      return 'Queda 1 día';
    }

    return `Quedan ${dias ?? 0} días`;
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
      return 'No tienes permisos para consultar esta información.';
    }

    if (error.status === 404) {
      return 'La página de resultados solicitada no existe.';
    }

    return 'No fue posible consultar tus préstamos. Inténtalo nuevamente.';
  }
}