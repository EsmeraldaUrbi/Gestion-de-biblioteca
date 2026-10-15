import {
  HttpErrorResponse,
} from '@angular/common/http';

import {
  ChangeDetectionStrategy,
  Component,
  computed,
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
  Usuario,
} from '../../../usuarios/models/usuario.models';

import {
  EjemplarPrestamo,
  ElegibilidadPrestamo,
  ErrorPrestamo,
  LibroPrestamo,
  PrestamoRegistrado,
  SolicitudPrestamo,
} from '../../models/prestamo.models';

import {
  PrestamosService,
} from '../../services/prestamos.service';


@Component({
  selector: 'app-registro-prestamo',
  standalone: true,
  imports: [
    ReactiveFormsModule,
  ],
  templateUrl: './registro-prestamo.html',
  styleUrl: './registro-prestamo.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RegistroPrestamoComponent {
  private readonly prestamosService =
    inject(PrestamosService);

  private readonly destroyRef =
    inject(DestroyRef);

  readonly busquedaUsuario = new FormControl(
    '',
    { nonNullable: true },
  );

  readonly busquedaLibro = new FormControl(
    '',
    { nonNullable: true },
  );

  readonly usuarios = signal<Usuario[]>([]);
  readonly libros = signal<LibroPrestamo[]>([]);
  readonly ejemplares = signal<EjemplarPrestamo[]>([]);

  readonly usuarioSeleccionado =
    signal<Usuario | null>(null);

  readonly libroSeleccionado =
    signal<LibroPrestamo | null>(null);

  readonly ejemplarSeleccionado =
    signal<EjemplarPrestamo | null>(null);

  readonly elegibilidad =
    signal<ElegibilidadPrestamo | null>(null);

  readonly prestamoRegistrado =
    signal<PrestamoRegistrado | null>(null);

  readonly cargandoUsuarios = signal(false);
  readonly cargandoLibros = signal(false);
  readonly cargandoEjemplares = signal(false);
  readonly evaluando = signal(false);
  readonly registrando = signal(false);

  readonly busquedaUsuariosRealizada = signal(false);
  readonly busquedaLibrosRealizada = signal(false);

  readonly errorUsuarios = signal<string | null>(null);
  readonly errorLibros = signal<string | null>(null);
  readonly errorEjemplares = signal<string | null>(null);
  readonly errorElegibilidad = signal<string | null>(null);
  readonly errorRegistro = signal<string | null>(null);

  // Identificadores para descartar respuestas asíncronas
  // que pertenecen a búsquedas o selecciones anteriores.
  private versionUsuarios = 0;
  private versionLibros = 0;
  private versionEjemplares = 0;
  private versionElegibilidad = 0;

  readonly puedeRegistrar = computed(() =>
    this.usuarioSeleccionado() !== null &&
    this.libroSeleccionado() !== null &&
    this.ejemplarSeleccionado() !== null &&
    this.elegibilidad()?.elegible === true &&
    !this.evaluando() &&
    !this.registrando() &&
    this.prestamoRegistrado() === null,
  );

  readonly ejemplaresActivos = computed(() =>
    this.ejemplares().filter(
      (ejemplar) => ejemplar.estado === 'ACTIVO',
    ).length,
  );

  // -----------------------------------------
  // Búsqueda y selección de usuarios
  // -----------------------------------------

  buscarUsuarios(): void {
    const termino = this.busquedaUsuario.value.trim();
    const version = ++this.versionUsuarios;

    this.errorUsuarios.set(null);
    this.usuarios.set([]);
    this.busquedaUsuariosRealizada.set(false);

    if (termino.length < 2) {
      this.cargandoUsuarios.set(false);
      this.errorUsuarios.set(
        'Escribe al menos dos caracteres del nombre o correo.',
      );
      return;
    }

    this.cargandoUsuarios.set(true);

    this.prestamosService
      .buscarLectores(termino)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (respuesta) => {
          if (version !== this.versionUsuarios) {
            return;
          }

          this.usuarios.set(respuesta.results);
          this.busquedaUsuariosRealizada.set(true);
          this.cargandoUsuarios.set(false);
        },
        error: (error: HttpErrorResponse) => {
          if (version !== this.versionUsuarios) {
            return;
          }

          this.errorUsuarios.set(
            this.obtenerMensajeError(
              error,
              'No fue posible buscar lectores.',
            ),
          );
          this.cargandoUsuarios.set(false);
        },
      });
  }

  seleccionarUsuario(usuario: Usuario): void {
    this.usuarioSeleccionado.set(usuario);
    this.prestamoRegistrado.set(null);
    this.errorRegistro.set(null);

    this.invalidarElegibilidad();

    if (this.ejemplarSeleccionado()) {
      this.consultarElegibilidad();
    }
  }

  // -----------------------------------------
  // Búsqueda y selección de libros
  // -----------------------------------------

  buscarLibros(): void {
    const termino = this.busquedaLibro.value.trim();
    const version = ++this.versionLibros;

    this.errorLibros.set(null);
    this.libros.set([]);
    this.busquedaLibrosRealizada.set(false);

    if (termino.length < 2) {
      this.cargandoLibros.set(false);
      this.errorLibros.set(
        'Escribe al menos dos caracteres del título o ISBN.',
      );
      return;
    }

    this.cargandoLibros.set(true);

    this.prestamosService
      .buscarLibros(termino)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (respuesta) => {
          if (version !== this.versionLibros) {
            return;
          }

          this.libros.set(respuesta.results);
          this.busquedaLibrosRealizada.set(true);
          this.cargandoLibros.set(false);
        },
        error: (error: HttpErrorResponse) => {
          if (version !== this.versionLibros) {
            return;
          }

          this.errorLibros.set(
            this.obtenerMensajeError(
              error,
              'No fue posible consultar los libros.',
            ),
          );
          this.cargandoLibros.set(false);
        },
      });
  }

  seleccionarLibro(libro: LibroPrestamo): void {
    this.libroSeleccionado.set(libro);
    this.ejemplarSeleccionado.set(null);
    this.ejemplares.set([]);

    this.prestamoRegistrado.set(null);
    this.errorRegistro.set(null);
    this.invalidarElegibilidad();

    this.cargarEjemplares(libro);
  }

  private cargarEjemplares(
    libro: LibroPrestamo,
  ): void {
    const version = ++this.versionEjemplares;

    this.errorEjemplares.set(null);
    this.cargandoEjemplares.set(true);
    this.ejemplares.set([]);

    this.prestamosService
      .obtenerEjemplares(libro.libro_id)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (ejemplares) => {
          if (version !== this.versionEjemplares) {
            return;
          }

          this.ejemplares.set(ejemplares);
          this.cargandoEjemplares.set(false);
        },
        error: (error: HttpErrorResponse) => {
          if (version !== this.versionEjemplares) {
            return;
          }

          this.errorEjemplares.set(
            this.obtenerMensajeError(
              error,
              'No fue posible cargar los ejemplares.',
            ),
          );
          this.cargandoEjemplares.set(false);
        },
      });
  }

  reintentarEjemplares(): void {
    const libro = this.libroSeleccionado();

    if (libro) {
      this.cargarEjemplares(libro);
    }
  }

  seleccionarEjemplar(
    ejemplar: EjemplarPrestamo,
  ): void {
    if (ejemplar.estado !== 'ACTIVO') {
      return;
    }

    this.ejemplarSeleccionado.set(ejemplar);
    this.prestamoRegistrado.set(null);
    this.errorRegistro.set(null);
    this.invalidarElegibilidad();

    if (this.usuarioSeleccionado()) {
      this.consultarElegibilidad();
    }
  }

  // -----------------------------------------
  // Consulta de elegibilidad
  // -----------------------------------------

  private invalidarElegibilidad(): void {
    this.versionElegibilidad++;

    this.elegibilidad.set(null);
    this.errorElegibilidad.set(null);
    this.evaluando.set(false);
  }

  consultarElegibilidad(): void {
    const solicitud = this.obtenerSolicitud();

    this.invalidarElegibilidad();

    if (!solicitud) {
      return;
    }

    const version = this.versionElegibilidad;

    this.evaluando.set(true);

    this.prestamosService
      .evaluarElegibilidad(solicitud)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (respuesta) => {
          if (version !== this.versionElegibilidad) {
            return;
          }

          this.elegibilidad.set(respuesta);
          this.evaluando.set(false);
        },
        error: (error: HttpErrorResponse) => {
          if (version !== this.versionElegibilidad) {
            return;
          }

          this.errorElegibilidad.set(
            this.obtenerMensajeError(
              error,
              'No fue posible verificar la elegibilidad.',
            ),
          );
          this.evaluando.set(false);
        },
      });
  }

  // -----------------------------------------
  // Registro del préstamo
  // -----------------------------------------

  registrarPrestamo(): void {
    if (!this.puedeRegistrar()) {
      return;
    }

    const solicitud = this.obtenerSolicitud();

    if (!solicitud) {
      return;
    }

    this.errorRegistro.set(null);
    this.registrando.set(true);

    this.prestamosService
      .registrarPrestamo(solicitud)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (prestamo) => {
          this.registrando.set(false);
          this.prestamoRegistrado.set(prestamo);

          // La operación ya se registró. No debe
          // ser posible enviarla una segunda vez.
          this.invalidarElegibilidad();
        },
        error: (error: HttpErrorResponse) => {
          this.registrando.set(false);

          this.errorRegistro.set(
            this.obtenerMensajeError(
              error,
              'No fue posible registrar el préstamo.',
            ),
          );

          // Si cambió la disponibilidad o el límite,
          // recuperamos las condiciones actuales.
          if (error.status === 409) {
            this.consultarElegibilidad();
          } else {
            this.invalidarElegibilidad();
          }
        },
      });
  }

  private obtenerSolicitud(): SolicitudPrestamo | null {
    const usuario = this.usuarioSeleccionado();
    const ejemplar = this.ejemplarSeleccionado();

    if (!usuario || !ejemplar) {
      return null;
    }

    return {
      usuario_id: usuario.usuario_id,
      ejemplar_id: ejemplar.ejemplar_id,
    };
  }

  // -----------------------------------------
  // Ayudas de presentación
  // -----------------------------------------

  formatearFecha(fecha: string): string {
    const partes = fecha.split('-');

    if (partes.length !== 3) {
      return fecha;
    }

    return `${partes[2]}/${partes[1]}/${partes[0]}`;
  }

  nombreRol(usuario: Usuario): string {
    return usuario.rol.nombre === 'docente'
      ? 'Docente'
      : usuario.rol.nombre === 'estudiante'
        ? 'Estudiante'
        : 'Bibliotecario';
  }

  nuevaOperacion(): void {
    this.versionUsuarios++;
    this.versionLibros++;
    this.versionEjemplares++;
    this.versionElegibilidad++;

    this.busquedaUsuario.setValue('');
    this.busquedaLibro.setValue('');

    this.usuarios.set([]);
    this.libros.set([]);
    this.ejemplares.set([]);

    this.usuarioSeleccionado.set(null);
    this.libroSeleccionado.set(null);
    this.ejemplarSeleccionado.set(null);
    this.elegibilidad.set(null);
    this.prestamoRegistrado.set(null);

    this.cargandoUsuarios.set(false);
    this.cargandoLibros.set(false);
    this.cargandoEjemplares.set(false);
    this.evaluando.set(false);
    this.registrando.set(false);

    this.busquedaUsuariosRealizada.set(false);
    this.busquedaLibrosRealizada.set(false);

    this.errorUsuarios.set(null);
    this.errorLibros.set(null);
    this.errorEjemplares.set(null);
    this.errorElegibilidad.set(null);
    this.errorRegistro.set(null);
  }

  private obtenerMensajeError(
    error: HttpErrorResponse,
    mensajePredeterminado: string,
  ): string {
    if (error.status === 0) {
      return 'No fue posible conectar con el servidor.';
    }

    if (error.status === 401) {
      return 'Tu sesión ha vencido. Inicia sesión nuevamente.';
    }

    if (error.status === 403) {
      return 'No tienes permisos para realizar esta operación.';
    }

    const cuerpo = error.error as
      | ErrorPrestamo
      | null;

    if (cuerpo && typeof cuerpo.detail === 'string') {
      return cuerpo.detail;
    }

    if (cuerpo && typeof cuerpo === 'object') {
      for (const valor of Object.values(cuerpo)) {
        if (
          Array.isArray(valor) &&
          valor.length > 0 &&
          typeof valor[0] === 'string'
        ) {
          return valor[0];
        }
      }
    }

    return mensajePredeterminado;
  }
}