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
import {
  debounceTime,
  distinctUntilChanged,
  finalize,
  Subject,
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

  // Subject para debounce en búsquedas de texto
  private readonly busquedaSubject = new Subject<void>();

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
    this.busquedaSubject
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe(() => {
        this.pagina.set(1);
        this.cargarLibros();
      });
  }

  ngOnInit(): void {
    this.cargarOpcionesFiltros();
    this.cargarLibros();
  }

  cargarLibros(): void {
    this.cargando.set(true);
    this.error.set(null);

    const filtros: LibrosFiltros = {
      page: this.pagina(),
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

    this.librosService
      .listar(filtros)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.cargando.set(false)),
      )
      .subscribe({
        next: (respuesta) => {
          this.libros.set(respuesta.results);
          this.total.set(respuesta.count);
        },
        error: (error: HttpErrorResponse) => {
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
        },
      });
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
          // Si la carga de filtros falla, el listado de libros sigue siendo funcional.
          this.autoresOpciones.set([]);
          this.categoriasOpciones.set([]);
        },
      });
  }

  actualizarBusquedaTitulo(valor: string): void {
    this.busquedaTitulo.set(valor);
    this.busquedaSubject.next();
  }

  actualizarBusquedaIsbn(valor: string): void {
    this.busquedaIsbn.set(valor);
    this.busquedaSubject.next();
  }

  cambiarAutor(autorId: number | null): void {
    this.autorSeleccionado.set(autorId);
    this.pagina.set(1);
    this.cargarLibros();
  }

  cambiarCategoria(categoriaId: number | null): void {
    this.categoriaSeleccionada.set(categoriaId);
    this.pagina.set(1);
    this.cargarLibros();
  }

  limpiarFiltros(): void {
    this.busquedaTitulo.set('');
    this.busquedaIsbn.set('');
    this.autorSeleccionado.set(null);
    this.categoriaSeleccionada.set(null);
    this.pagina.set(1);
    this.cargarLibros();
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
