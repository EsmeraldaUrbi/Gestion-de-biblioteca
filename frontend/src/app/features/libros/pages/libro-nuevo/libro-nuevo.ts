import { CommonModule } from '@angular/common';
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

import {
  AutorCatalogo,
  CategoriaCatalogo,
} from '../../../catalogo/models/catalogo.models';
import { CatalogoService } from '../../../catalogo/services/catalogo.service';
import {
  LibroFormComponent,
  GuardarPayload,
} from '../../components/libro-form/libro-form';
import { Libro, RegistrarLibroRequest } from '../../models/libros.models';
import { LibrosService } from '../../services/libros.service';

@Component({
  selector: 'app-libro-nuevo',
  standalone: true,
  imports: [CommonModule, RouterLink, LibroFormComponent],
  templateUrl: './libro-nuevo.html',
  styleUrl: './libro-nuevo.css',
})
export class LibroNuevoComponent implements OnInit {
  private readonly librosService = inject(LibrosService);
  private readonly catalogoService = inject(CatalogoService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly autoresDisponibles = signal<AutorCatalogo[]>([]);
  readonly categoriasDisponibles = signal<CategoriaCatalogo[]>([]);
  readonly cargandoFiltros = signal(false);
  readonly errorFiltros = signal<string | null>(null);

  readonly guardando = signal(false);
  readonly errorGeneral = signal<string | null>(null);
  readonly erroresServidor = signal<Record<string, string[]>>({});
  readonly libroCreado = signal<Libro | null>(null);

  ngOnInit(): void {
    this.cargarOpciones();
  }

  cargarOpciones(): void {
    if (this.cargandoFiltros()) return;

    this.cargandoFiltros.set(true);
    this.errorFiltros.set(null);

    this.catalogoService
      .obtenerFiltros()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.cargandoFiltros.set(false)),
      )
      .subscribe({
        next: (opciones) => {
          this.autoresDisponibles.set(opciones.autores ?? []);
          this.categoriasDisponibles.set(opciones.categorias ?? []);
        },
        error: () => {
          // El formulario sigue siendo funcional sin opciones precargadas
          this.autoresDisponibles.set([]);
          this.categoriasDisponibles.set([]);
          this.errorFiltros.set(
            'No fue posible cargar las opciones de autores y categorías.',
          );
        },
      });
  }

  registrar(payload: GuardarPayload): void {
    if (this.guardando()) return;

    this.guardando.set(true);
    this.errorGeneral.set(null);
    this.erroresServidor.set({});

    this.librosService
      .registrar(payload as RegistrarLibroRequest)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.guardando.set(false)),
      )
      .subscribe({
        next: (libro) => {
          this.libroCreado.set(libro);
        },
        error: (error: HttpErrorResponse) => {
          this.procesarError(error);
        },
      });
  }

  volver(): void {
    void this.router.navigateByUrl('/libros');
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
          'Revisa los campos señalados e inténtalo nuevamente.',
      );
      return;
    }

    if (error.status === 0) {
      this.errorGeneral.set('No fue posible conectar con el servidor.');
    } else if (error.status === 401) {
      this.errorGeneral.set('Tu sesión ha vencido. Inicia sesión nuevamente.');
    } else if (error.status === 403) {
      this.errorGeneral.set('No tienes permiso para registrar libros.');
    } else {
      this.errorGeneral.set('Ocurrió un error al registrar el libro.');
    }
  }
}
