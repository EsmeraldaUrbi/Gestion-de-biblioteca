import {
  CommonModule,
} from '@angular/common';
import {
  HttpErrorResponse,
} from '@angular/common/http';
import {
  Component,
  computed,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import {
  catchError,
  debounceTime,
  distinctUntilChanged,
  finalize,
  map,
  merge,
  of,
  Subject,
  switchMap,
  tap,
} from 'rxjs';

import {
  AutorCatalogo,
  CategoriaCatalogo,
} from '../../../catalogo/models/catalogo.models';
import { CatalogoService } from '../../../catalogo/services/catalogo.service';
import {
  Autor,
  Libro,
  LibrosFiltros,
} from '../../models/libros.models';
import { LibrosService } from '../../services/libros.service';

@Component({
  selector: 'app-libros-lista',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
  ],
  templateUrl: './libros-lista.html',
  styleUrl: './libros-lista.css',
})
export class LibrosListaComponent implements OnInit {
  private readonly librosService = inject(LibrosService);
  private readonly catalogoService = inject(CatalogoService);
  private readonly destroyRef = inject(DestroyRef);

  readonly pageSize = 10;

  // Estado de libros
  readonly libros = signal<Libro[]>([]);
  readonly pagina = signal<number>(1);
  readonly total = signal<number>(0);
  readonly cargando = signal<boolean>(false);
  readonly error = signal<string | null>(null);

  // Filtros reactivos
  readonly busquedaTitulo = signal<string>('');
  readonly busquedaIsbn = signal<string>('');
  readonly autorSeleccionado = signal<number | null>(null);
  readonly categoriaSeleccionada = signal<number | null>(null);

  // Opciones de filtros obtenidas del catálogo
  readonly autoresOpciones = signal<AutorCatalogo[]>([]);
  readonly categoriasOpciones = signal<CategoriaCatalogo[]>([]);
  readonly cargandoFiltros = signal<boolean>(false);

  // Subject para cambios de búsqueda en campos de texto (con debounce)
  private readonly busquedaTextoSubject = new Subject<{
    titulo: string;
    isbn: string;
  }>();

  // Subject para recargas inmediatas (selects de autor/categoría, paginación, limpiar filtros)
  private readonly recargaInmediataSubject = new Subject<{
    resetPagina: boolean;
  }>();

  // Señales computadas para la paginación y el resumen
  readonly totalPaginas = computed(() =>
    Math.max(1, Math.ceil(this.total() / this.pageSize)),
  );

  readonly primerRegistro = computed(() =>
    this.total() === 0 ? 0 : (this.pagina() - 1) * this.pageSize + 1,
  );

  readonly ultimoRegistro = computed(() =>
    Math.min(this.pagina() * this.pageSize, this.total()),
  );

  readonly hayFiltrosActivos = computed(() => {
    return (
      this.busquedaTitulo().trim().length > 0 ||
      this.busquedaIsbn().trim().length > 0 ||
      this.autorSeleccionado() !== null ||
      this.categoriaSeleccionada() !== null
    );
  });

  constructor() {
    // Stream de búsquedas por texto con debounce y verificación de cambios reales
    const busquedasTexto$ = this.busquedaTextoSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(
        (prev, curr) => prev.titulo === curr.titulo && prev.isbn === curr.isbn,
      ),
      map(() => {
        this.pagina.set(1);
        return this.construirFiltros(1);
      }),
    );

    // Stream de acciones inmediatas (cambio de autor, categoría, página o limpieza)
    const accionesInmediatas$ = this.recargaInmediataSubject.pipe(
      map(({ resetPagina }) => {
        if (resetPagina) {
          this.pagina.set(1);
        }
        return this.construirFiltros(this.pagina());
      }),
    );

    // Fusión de streams con switchMap para cancelar peticiones previas en vuelo
    // y catchError interno para no romper el stream ante errores HTTP
    merge(busquedasTexto$, accionesInmediatas$)
      .pipe(
        tap(() => {
          this.cargando.set(true);
          this.error.set(null);
        }),
        switchMap((filtros) =>
          this.librosService.listar(filtros).pipe(
            catchError((err: HttpErrorResponse) => {
              this.procesarErrorListado(err);
              return of(null);
            }),
          ),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((respuesta) => {
        this.cargando.set(false);
        if (respuesta) {
          this.libros.set(respuesta.results);
          this.total.set(respuesta.count);
        } else {
          this.libros.set([]);
          this.total.set(0);
        }
      });
  }

  ngOnInit(): void {
    this.cargarOpcionesFiltros();
    this.cargarLibros();
  }

  construirFiltros(paginaActual: number): LibrosFiltros {
    const filtros: LibrosFiltros = {
      page: paginaActual,
      page_size: this.pageSize,
    };

    const tituloLimpio = this.busquedaTitulo().trim();
    if (tituloLimpio.length > 0) {
      filtros.titulo = tituloLimpio;
    }

    const isbnLimpio = this.busquedaIsbn().trim();
    if (isbnLimpio.length > 0) {
      filtros.isbn = isbnLimpio;
    }

    const autorId = this.autorSeleccionado();
    if (autorId !== null) {
      filtros.autor_id = autorId;
    }

    const categoriaId = this.categoriaSeleccionada();
    if (categoriaId !== null) {
      filtros.categoria_id = categoriaId;
    }

    return filtros;
  }

  cargarLibros(): void {
    this.recargaInmediataSubject.next({ resetPagina: false });
  }

  private procesarErrorListado(error: HttpErrorResponse): void {
    if (error.status === 0) {
      this.error.set('No fue posible conectar con el servidor.');
    } else if (error.status === 401) {
      this.error.set('Tu sesión ha vencido.');
    } else if (error.status === 403) {
      this.error.set('No tienes permiso para consultar libros.');
    } else {
      this.error.set(
        'No fue posible cargar los libros. Inténtalo nuevamente.',
      );
    }
  }

  cargarOpcionesFiltros(): void {
    this.cargandoFiltros.set(true);
    this.catalogoService
      .obtenerFiltros()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.cargandoFiltros.set(false)),
      )
      .subscribe({
        next: (opciones) => {
          this.autoresOpciones.set(opciones.autores || []);
          this.categoriasOpciones.set(opciones.categorias || []);
        },
        error: () => {
          this.autoresOpciones.set([]);
          this.categoriasOpciones.set([]);
        },
      });
  }

  actualizarBusquedaTitulo(valor: string): void {
    this.busquedaTitulo.set(valor);
    this.busquedaTextoSubject.next({
      titulo: valor.trim(),
      isbn: this.busquedaIsbn().trim(),
    });
  }

  actualizarBusquedaIsbn(valor: string): void {
    this.busquedaIsbn.set(valor);
    this.busquedaTextoSubject.next({
      titulo: this.busquedaTitulo().trim(),
      isbn: valor.trim(),
    });
  }

  cambiarAutor(autorId: number | null): void {
    this.autorSeleccionado.set(autorId);
    this.recargaInmediataSubject.next({ resetPagina: true });
  }

  cambiarCategoria(categoriaId: number | null): void {
    this.categoriaSeleccionada.set(categoriaId);
    this.recargaInmediataSubject.next({ resetPagina: true });
  }

  limpiarFiltros(): void {
    this.busquedaTitulo.set('');
    this.busquedaIsbn.set('');
    this.autorSeleccionado.set(null);
    this.categoriaSeleccionada.set(null);
    this.recargaInmediataSubject.next({ resetPagina: true });
  }

  cambiarPagina(nuevaPagina: number): void {
    if (
      this.cargando() ||
      nuevaPagina < 1 ||
      (this.total() > 0 && nuevaPagina > this.totalPaginas()) ||
      nuevaPagina === this.pagina()
    ) {
      return;
    }
    this.pagina.set(nuevaPagina);
    this.cargarLibros();
  }

  formatearAutores(autores: Autor[]): string {
    if (!autores || autores.length === 0) {
      return 'Sin autores asignados';
    }
    return autores.map((a) => a.nombre).join(', ');
  }

  formatearFecha(fecha: string | null): string {
    if (!fecha) {
      return 'No registrada';
    }
    return fecha;
  }
}
