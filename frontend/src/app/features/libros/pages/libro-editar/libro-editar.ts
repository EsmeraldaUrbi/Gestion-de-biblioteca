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
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { catchError, finalize, forkJoin, of } from 'rxjs';

import {
  AutorCatalogo,
  CategoriaCatalogo,
} from '../../../catalogo/models/catalogo.models';
import { CatalogoService } from '../../../catalogo/services/catalogo.service';
import {
  LibroFormComponent,
  GuardarPayload,
} from '../../components/libro-form/libro-form';
import { Libro, ModificarLibroRequest } from '../../models/libros.models';
import { LibrosService } from '../../services/libros.service';

@Component({
  selector: 'app-libro-editar',
  standalone: true,
  imports: [CommonModule, RouterLink, LibroFormComponent],
  templateUrl: './libro-editar.html',
  styleUrl: './libro-editar.css',
})
export class LibroEditarComponent implements OnInit {
  private readonly librosService = inject(LibrosService);
  private readonly catalogoService = inject(CatalogoService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  private libroId!: number;

  readonly libro = signal<Libro | null>(null);
  readonly autoresDisponibles = signal<AutorCatalogo[]>([]);
  readonly categoriasDisponibles = signal<CategoriaCatalogo[]>([]);

  readonly cargando = signal(true);
  readonly errorCarga = signal<string | null>(null);

  readonly guardando = signal(false);
  readonly errorGeneral = signal<string | null>(null);
  readonly erroresServidor = signal<Record<string, string[]>>({});
  readonly libroActualizado = signal<Libro | null>(null);

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    const id = Number(idParam);

    if (!idParam || isNaN(id) || id <= 0) {
      void this.router.navigateByUrl('/libros');
      return;
    }

    this.libroId = id;
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.cargando.set(true);
    this.errorCarga.set(null);

    forkJoin({
      libro: this.librosService.obtener(this.libroId),
      opciones: this.catalogoService
        .obtenerFiltros()
        .pipe(catchError(() => of({ autores: [], categorias: [] }))),
    })
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.cargando.set(false)),
      )
      .subscribe({
        next: ({ libro, opciones }) => {
          this.libro.set(libro);
          this.autoresDisponibles.set(opciones.autores ?? []);
          this.categoriasDisponibles.set(opciones.categorias ?? []);
        },
        error: (error: HttpErrorResponse) => {
          if (error.status === 404) {
            this.errorCarga.set('El libro solicitado no existe en el catálogo.');
          } else if (error.status === 401) {
            this.errorCarga.set(
              'Tu sesión ha vencido. Inicia sesión nuevamente.',
            );
          } else if (error.status === 403) {
            this.errorCarga.set('No tienes permiso para editar este libro.');
          } else if (error.status === 0) {
            this.errorCarga.set('No fue posible conectar con el servidor.');
          } else {
            this.errorCarga.set(
              'No fue posible cargar los datos del libro. Inténtalo nuevamente.',
            );
          }
        },
      });
  }

  modificar(payload: GuardarPayload): void {
    if (this.guardando()) return;

    this.guardando.set(true);
    this.errorGeneral.set(null);
    this.erroresServidor.set({});

    this.librosService
      .modificarParcial(this.libroId, payload as ModificarLibroRequest)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.guardando.set(false)),
      )
      .subscribe({
        next: (libro) => {
          this.libroActualizado.set(libro);
          // Actualizar el libro local para reflejar los cambios si se navega de vuelta
          this.libro.set(libro);
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

    if (error.status === 404) {
      this.errorGeneral.set('El libro ya no existe en el catálogo.');
    } else if (error.status === 0) {
      this.errorGeneral.set('No fue posible conectar con el servidor.');
    } else if (error.status === 401) {
      this.errorGeneral.set('Tu sesión ha vencido. Inicia sesión nuevamente.');
    } else if (error.status === 403) {
      this.errorGeneral.set('No tienes permiso para modificar este libro.');
    } else {
      this.errorGeneral.set('Ocurrió un error al guardar los cambios.');
    }
  }
}
