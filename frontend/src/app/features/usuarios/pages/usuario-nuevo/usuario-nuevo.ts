import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { UsuarioFormComponent } from '../../components/usuario-form/usuario-form';
import {
  ModificarUsuarioRequest,
  RegistrarUsuarioRequest,
  Rol,
  Usuario,
} from '../../models/usuario.models';
import { UsuariosService } from '../../services/usuarios.service';

@Component({
  selector: 'app-usuario-nuevo',
  standalone: true,
  imports: [UsuarioFormComponent, RouterLink],
  templateUrl: './usuario-nuevo.html',
  styleUrl: './usuario-nuevo.css',
})
export class UsuarioNuevoComponent implements OnInit {
  private readonly usuariosService = inject(UsuariosService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly roles = signal<Rol[]>([]);
  readonly cargandoRoles = signal(false);
  readonly errorRoles = signal<string | null>(null);

  readonly guardando = signal(false);
  readonly errorGeneral = signal<string | null>(null);
  readonly erroresServidor = signal<Record<string, string[]>>({});
  readonly usuarioCreado = signal<Usuario | null>(null);

  ngOnInit(): void {
    this.cargarRoles();
  }

  cargarRoles(): void {
    if (this.cargandoRoles()) {
      return;
    }

    this.cargandoRoles.set(true);
    this.errorRoles.set(null);

    this.usuariosService
      .listarRoles()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.cargandoRoles.set(false)),
      )
      .subscribe({
        next: (roles) => {
          this.roles.set(roles);

          if (roles.length === 0) {
            this.errorRoles.set(
              'No hay roles disponibles para registrar usuarios.'
            );
          }
        },
        error: () => {
          this.errorRoles.set(
            'No fue posible obtener los roles. Inténtalo nuevamente.'
          );
        },
      });
  }

  registrarUsuario(
    datos: RegistrarUsuarioRequest | ModificarUsuarioRequest,
  ): void {
    if (
      this.guardando() ||
      !('password' in datos) ||
      !datos.password
    ) {
      return;
    }

    this.guardando.set(true);
    this.errorGeneral.set(null);
    this.erroresServidor.set({});

    this.usuariosService
      .registrarUsuario(datos)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.guardando.set(false)),
      )
      .subscribe({
        next: (usuario) => {
          this.usuarioCreado.set(usuario);
        },
        error: (error: HttpErrorResponse) => {
          this.procesarError(error);
        },
      });
  }

  volver(): void {
    void this.router.navigateByUrl('/usuarios');
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
      this.errorGeneral.set(
        errores['non_field_errors']?.[0] ??
        errores['detail']?.[0] ??
        'Revisa los campos señalados e inténtalo nuevamente.'
      );
      return;
    }

    if (error.status === 0) {
      this.errorGeneral.set(
        'No fue posible conectar con el servidor.'
      );
    } else if (error.status === 401) {
      this.errorGeneral.set(
        'Tu sesión ha vencido. Inicia sesión nuevamente.'
      );
    } else if (error.status === 403) {
      this.errorGeneral.set(
        'No tienes permiso para registrar usuarios.'
      );
    } else {
      this.errorGeneral.set(
        'Ocurrió un error al registrar el usuario.'
      );
    }
  }
}
