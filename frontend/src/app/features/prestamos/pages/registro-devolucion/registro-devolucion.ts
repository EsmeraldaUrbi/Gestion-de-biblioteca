import {
  HttpErrorResponse,
} from '@angular/common/http';

import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  inject,
  signal,
} from '@angular/core';

import {
  FormControl,
  ReactiveFormsModule,
} from '@angular/forms';

import {
  takeUntilDestroyed,
} from '@angular/core/rxjs-interop';

import type {
  DevolucionRegistrada,
  PrestamoActivoDevolucion,
} from '../../models/devolucion.models';

import {
  DevolucionesService,
} from '../../services/devoluciones.service';


@Component({
  selector: 'app-registro-devolucion',
  standalone: true,
  imports: [
    ReactiveFormsModule,
  ],
  templateUrl: './registro-devolucion.html',
  styleUrl: './registro-devolucion.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RegistroDevolucionComponent {
  private readonly service = inject(DevolucionesService);
  private readonly destroyRef = inject(DestroyRef);

  readonly busqueda = new FormControl(
    '',
    { nonNullable: true },
  );

  readonly resultados = signal<PrestamoActivoDevolucion[]>([]);
  readonly seleccionado = signal<PrestamoActivoDevolucion | null>(null);
  readonly devolucion = signal<DevolucionRegistrada | null>(null);

  readonly buscando = signal(false);
  readonly registrando = signal(false);
  readonly busquedaRealizada = signal(false);
  readonly confirmarAbierto = signal(false);

  readonly errorBusqueda = signal<string | null>(null);
  readonly errorRegistro = signal<string | null>(null);

  readonly pagina = signal(1);
  readonly total = signal(0);
  readonly hayAnterior = signal(false);
  readonly haySiguiente = signal(false);

  private terminoActual = '';
  private versionBusqueda = 0;

  buscar(): void {
    if (this.registrando()) {
      return;
    }

    const termino = this.busqueda.value.trim();

    if (!termino || termino.length > 100) {
      // Invalidar también cualquier consulta anterior pendiente.
      this.versionBusqueda++;
      this.buscando.set(false);
      this.resultados.set([]);
      this.seleccionado.set(null);
      this.devolucion.set(null);
      this.confirmarAbierto.set(false);
      this.errorRegistro.set(null);
      this.busquedaRealizada.set(false);
      this.total.set(0);
      this.pagina.set(1);
      this.hayAnterior.set(false);
      this.haySiguiente.set(false);
      this.errorBusqueda.set(
        'Escribe entre 1 y 100 caracteres para buscar.',
      );
      return;
    }

    this.terminoActual = termino;
    this.cargarPagina(1);
  }

  private cargarPagina(numero: number): void {
    const version = ++this.versionBusqueda;

    this.buscando.set(true);
    this.errorBusqueda.set(null);
    this.errorRegistro.set(null);
    this.resultados.set([]);
    this.seleccionado.set(null);
    this.devolucion.set(null);
    this.confirmarAbierto.set(false);
    this.busquedaRealizada.set(false);
    this.total.set(0);
    this.hayAnterior.set(false);
    this.haySiguiente.set(false);

    this.service
      .buscarPrestamosActivos(this.terminoActual, numero)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (respuesta) => {
          if (version !== this.versionBusqueda) {
            return;
          }

          this.resultados.set(respuesta.results);
          this.total.set(respuesta.count);
          this.pagina.set(numero);
          this.hayAnterior.set(respuesta.previous !== null);
          this.haySiguiente.set(respuesta.next !== null);
          this.busquedaRealizada.set(true);
          this.buscando.set(false);
        },
        error: (error: HttpErrorResponse) => {
          if (version !== this.versionBusqueda) {
            return;
          }

          this.errorBusqueda.set(
            this.mensajeError(
              error,
              'No fue posible consultar los préstamos.',
            ),
          );
          this.buscando.set(false);
        },
      });
  }

  paginaAnterior(): void {
    if (
      this.hayAnterior() &&
      !this.buscando() &&
      !this.registrando()
    ) {
      this.cargarPagina(this.pagina() - 1);
    }
  }

  paginaSiguiente(): void {
    if (
      this.haySiguiente() &&
      !this.buscando() &&
      !this.registrando()
    ) {
      this.cargarPagina(this.pagina() + 1);
    }
  }

  seleccionar(resultado: PrestamoActivoDevolucion): void {
    if (this.registrando() || this.devolucion()) {
      return;
    }

    this.seleccionado.set(resultado);
    this.errorRegistro.set(null);
    this.confirmarAbierto.set(false);
  }

  solicitarConfirmacion(): void {
    if (
      this.seleccionado() &&
      !this.registrando() &&
      !this.devolucion()
    ) {
      this.confirmarAbierto.set(true);
      this.errorRegistro.set(null);
    }
  }

  cancelarConfirmacion(): void {
    if (!this.registrando()) {
      this.confirmarAbierto.set(false);
    }
  }

  confirmarDevolucion(): void {
    const seleccionado = this.seleccionado();

    if (
      !seleccionado ||
      !this.confirmarAbierto() ||
      this.registrando() ||
      this.devolucion()
    ) {
      return;
    }

    this.registrando.set(true);
    this.errorRegistro.set(null);

    this.service
      .registrarDevolucion(seleccionado.prestamo.prestamo_id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (respuesta) => {
          this.devolucion.set(respuesta);
          this.confirmarAbierto.set(false);
          this.registrando.set(false);
        },
        error: (error: HttpErrorResponse) => {
          this.errorRegistro.set(
            this.mensajeError(
              error,
              'No fue posible confirmar la devolución. '
              + 'Consulta nuevamente el préstamo antes de reintentar.',
            ),
          );
          this.confirmarAbierto.set(false);
          this.registrando.set(false);

          // Si otro operador ya lo devolvió o eliminó,
          // exigir una nueva consulta antes de confirmar.
          if (
            error.status === 404 ||
            error.error?.codigo === 'PRESTAMO_YA_DEVUELTO'
          ) {
            this.seleccionado.set(null);
            this.resultados.set([]);
            this.busquedaRealizada.set(false);
            this.hayAnterior.set(false);
            this.haySiguiente.set(false);
            this.total.set(0);
          }
        },
      });
  }

  nuevaDevolucion(): void {
    if (this.registrando()) {
      return;
    }

    this.versionBusqueda++;
    this.busqueda.setValue('');
    this.terminoActual = '';
    this.resultados.set([]);
    this.seleccionado.set(null);
    this.devolucion.set(null);
    this.buscando.set(false);
    this.busquedaRealizada.set(false);
    this.confirmarAbierto.set(false);
    this.errorBusqueda.set(null);
    this.errorRegistro.set(null);
    this.pagina.set(1);
    this.total.set(0);
    this.hayAnterior.set(false);
    this.haySiguiente.set(false);
  }

  formatearFecha(fecha: string): string {
    // Mostrar fechas de calendario sin convertir zonas horarias.
    const [anio, mes, dia] = fecha.split('-');
    return `${dia}/${mes}/${anio}`;
  }

  private mensajeError(
    error: HttpErrorResponse,
    alternativa: string,
  ): string {
    if (error.status === 0) {
      return 'No se pudo conectar con el servidor. '
        + 'Si estabas confirmando una devolución, busca nuevamente '
        + 'el préstamo para comprobar si se registró.';
    }

    if (error.status === 401) {
      return 'La sesión no es válida. Inicia sesión nuevamente.';
    }

    if (error.status === 403) {
      return 'Solo el bibliotecario puede realizar esta operación.';
    }

    const detalle = error.error?.detail;

    if (typeof detalle === 'string') {
      return detalle;
    }

    const erroresBusqueda = error.error?.q;

    if (Array.isArray(erroresBusqueda)) {
      return erroresBusqueda.join(' ');
    }

    return alternativa;
  }
}