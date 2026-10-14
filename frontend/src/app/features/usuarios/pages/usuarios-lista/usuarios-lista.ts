import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  computed,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { finalize } from 'rxjs';

import { Usuario } from '../../models/usuario.models';
import { UsuariosService } from '../../services/usuarios.service';

import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-usuarios-lista',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './usuarios-lista.html',
  styleUrl: './usuarios-lista.css',
})
export class UsuariosListaComponent implements OnInit {
  private readonly usuariosService = inject(UsuariosService);
  private readonly destroyRef = inject(DestroyRef);

  readonly pageSize = 10;

  readonly usuarios = signal<Usuario[]>([]);
  readonly pagina = signal(1);
  readonly total = signal(0);
  readonly cargando = signal(false);
  readonly error = signal<string | null>(null);

  readonly totalPaginas = computed(() =>
    Math.max(1, Math.ceil(this.total() / this.pageSize))
  );

  readonly primerRegistro = computed(() =>
    this.total() === 0
      ? 0
      : (this.pagina() - 1) * this.pageSize + 1
  );

  readonly ultimoRegistro = computed(() =>
    Math.min(this.pagina() * this.pageSize, this.total())
  );

  ngOnInit(): void {
    this.cargarUsuarios();
  }

  cargarUsuarios(paginaSolicitada = 1): void {
    if (this.cargando() || paginaSolicitada < 1) {
      return;
    }

    if (
      this.total() > 0 &&
      paginaSolicitada > this.totalPaginas()
    ) {
      return;
    }

    this.cargando.set(true);
    this.error.set(null);

    this.usuariosService
      .listarUsuarios(paginaSolicitada, this.pageSize)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.cargando.set(false)),
      )
      .subscribe({
        next: (respuesta) => {
          this.usuarios.set(respuesta.results);
          this.total.set(respuesta.count);
          this.pagina.set(paginaSolicitada);
        },
        error: (error: HttpErrorResponse) => {
          if (error.status === 0) {
            this.error.set(
              'No fue posible conectar con el servidor.'
            );
          } else if (error.status === 401) {
            this.error.set('Tu sesión ha vencido.');
          } else if (error.status === 403) {
            this.error.set(
              'No tienes permiso para consultar usuarios.'
            );
          } else {
            this.error.set(
              'No fue posible cargar los usuarios. Inténtalo nuevamente.'
            );
          }
        },
      });
  }
}
