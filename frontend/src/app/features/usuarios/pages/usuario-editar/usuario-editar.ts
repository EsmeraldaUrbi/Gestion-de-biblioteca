import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { finalize, forkJoin } from 'rxjs';

import { UsuarioFormComponent } from '../../components/usuario-form/usuario-form';
import {
  ModificarUsuarioRequest,
  RegistrarUsuarioRequest,
  Rol,
  Usuario,
} from '../../models/usuario.models';
import { UsuariosService } from '../../services/usuarios.service';

@Component({
  selector: 'app-usuario-editar',
  standalone: true,
  imports: [UsuarioFormComponent, RouterLink],
  templateUrl: './usuario-editar.html',
  styleUrl: './usuario-editar.css',
})
export class UsuarioEditarComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly usuariosService = inject(UsuariosService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly router = inject(Router);

  private usuarioId: number | null = null;

  readonly usuario = signal<Usuario | null>(null);
  readonly roles = signal<Rol[]>([]);

  readonly cargando = signal(false);
  readonly guardando = signal(false);

  readonly errorCarga = signal<string | null>(null);
  readonly errorGuardado = signal<string | null>(null);
  readonly erroresServidor = signal<Record<string, string[]>>({});

  readonly usuarioActualizado = signal<Usuario | null>(null);

  ngOnInit(): void {
    const parametro = this.route.snapshot.paramMap.get('id');
    const id = Number(parametro);

    if (
      !parametro ||
      !Number.isSafeInteger(id) ||
      id <= 0
    ) {
      this.errorCarga.set(
        'El identificador del usuario no es válido.'
      );
      return;
    }

    this.usuarioId = id;
    this.cargarDatos();
  }

  cargarDatos(): void {
    if (this.usuarioId === null || this.cargando()) {
      return;
    }

    this.cargando.set(true);
    this.errorCarga.set(null);

    forkJoin({
      usuario: this.usuariosService.obtenerUsuario(this.usuarioId),
      roles: this.usuariosService.listarRoles(),
    })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.cargando.set(false)),
      )
      .subscribe({
        next: ({ usuario, roles }) => {
          if (roles.length === 0) {
            this.errorCarga.set(
              'No hay roles disponibles para editar usuarios.'
            );
            return;
          }

          this.usuario.set(usuario);
          this.roles.set(roles);
        },
        error: (error: HttpErrorResponse) => {
          if (error.status === 404) {
            this.errorCarga.set(
              'No se encontró el usuario o algún recurso necesario.'
            );
          } else if (error.status === 0) {
            this.errorCarga.set(
              'No fue posible conectar con el servidor.'
            );
          } else if (error.status === 403) {
            this.errorCarga.set(
              'No tienes permiso para editar usuarios.'
            );
          } else if (error.status === 401) {
            this.errorCarga.set(
              'Tu sesión ha vencido.'
            );
          } else {
            this.errorCarga.set(
              'No fue posible cargar los datos del usuario.'
            );
          }
        },
      });
  }

  guardarCambios(
    datos: RegistrarUsuarioRequest | ModificarUsuarioRequest,
  ): void {
    if (
      this.usuarioId === null ||
      this.guardando() ||
      this.usuarioActualizado()
    ) {
      return;
    }

    // Incluimos exclusivamente los campos
    // permitidos por el endpoint PATCH.
    const cambios: ModificarUsuarioRequest = {
      nombre: datos.nombre,
      email: datos.email,
      direccion: datos.direccion,
      telefono: datos.telefono,
      rol_id: datos.rol_id,
    };

    this.guardando.set(true);
    this.errorGuardado.set(null);
    this.erroresServidor.set({});

    this.usuariosService
      .modificarUsuario(this.usuarioId, cambios)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.guardando.set(false)),
      )
      .subscribe({
        next: (usuario) => {
          this.usuarioActualizado.set(usuario);
        },
        error: (error: HttpErrorResponse) => {
          this.procesarError(error);
        },
      });
  }

  volverDetalle(): void {
    if (this.usuarioId !== null) {
      void this.router.navigate(['/usuarios', this.usuarioId]);
    }
  }

  private procesarError(error: HttpErrorResponse): void {
    if (
      error.status === 400 &&
      error.error &&
      typeof error.error === 'object' &&
      !Array.isArray(error.error)
    ) {
      const respuesta = error.error as Record<string, unknown>;
      const errores: Record<string, string[]> = {};

      for (const [campo, valor] of Object.entries(respuesta)) {
        if (Array.isArray(valor)) {
          errores[campo] = valor.map(String);
        } else if (typeof valor === 'string') {
          errores[campo] = [valor];
        }
      }

      this.erroresServidor.set(errores);
      this.errorGuardado.set(
        errores['non_field_errors']?.[0] ??
        errores['detail']?.[0] ??
        'Revisa los datos indicados e intenta guardar nuevamente.'
      );
      return;
    }

    if (error.status === 0) {
      this.errorGuardado.set(
        'No fue posible conectar con el servidor.'
      );
    } else if (error.status === 403) {
      this.errorGuardado.set(
        'No tienes permiso para modificar usuarios.'
      );
    } else if (error.status === 401) {
      this.errorGuardado.set(
        'Tu sesión ha vencido.'
      );
    } else if (error.status === 404) {
      this.errorGuardado.set(
        'El usuario ya no existe.'
      );
    } else {
      this.errorGuardado.set(
        'Ocurrió un error al guardar los cambios.'
      );
    }
  }
}
