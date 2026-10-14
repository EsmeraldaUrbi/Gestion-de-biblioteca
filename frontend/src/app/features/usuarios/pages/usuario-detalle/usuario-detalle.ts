import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { finalize } from 'rxjs';

import { Usuario } from '../../models/usuario.models';
import { UsuariosService } from '../../services/usuarios.service';

@Component({
  selector: 'app-usuario-detalle',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './usuario-detalle.html',
  styleUrl: './usuario-detalle.css',
})
export class UsuarioDetalleComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly usuariosService = inject(UsuariosService);
  private readonly destroyRef = inject(DestroyRef);

  readonly usuario = signal<Usuario | null>(null);
  readonly cargando = signal(false);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.cargarUsuario();
  }

  cargarUsuario(): void {
    const parametro = this.route.snapshot.paramMap.get('id');
    const usuarioId = Number(parametro);

    if (
      !parametro ||
      !Number.isSafeInteger(usuarioId) ||
      usuarioId <= 0
    ) {
      this.error.set('El identificador del usuario no es válido.');
      return;
    }

    if (this.cargando()) {
      return;
    }

    this.cargando.set(true);
    this.error.set(null);
    this.usuario.set(null);

    this.usuariosService
      .obtenerUsuario(usuarioId)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.cargando.set(false)),
      )
      .subscribe({
        next: (usuario) => {
          this.usuario.set(usuario);
        },
        error: (error: HttpErrorResponse) => {
          if (error.status === 404) {
            this.error.set(
              'El usuario solicitado no existe.'
            );
          } else if (error.status === 0) {
            this.error.set(
              'No fue posible conectar con el servidor.'
            );
          } else if (error.status === 403) {
            this.error.set(
              'No tienes permiso para consultar este usuario.'
            );
          } else if (error.status === 401) {
            this.error.set(
              'Tu sesión ha vencido.'
            );
          } else {
            this.error.set(
              'Ocurrió un error al consultar el usuario.'
            );
          }
        },
      });
  }
}
