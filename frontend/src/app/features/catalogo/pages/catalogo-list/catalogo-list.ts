import {
  CommonModule,
} from '@angular/common';
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
import { Router, RouterLink } from '@angular/router';
import {
  catchError,
  debounceTime,
  distinctUntilChanged,
  filter,
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
  LibroCatalogo,
} from '../../models/catalogo.models';
import { CatalogoService } from '../../services/catalogo.service';

@Component({
  selector: 'app-catalogo-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
  ],
  templateUrl: './catalogo-list.html',
  styleUrl: './catalogo-list.css',
})
export class CatalogoListComponent implements OnInit {
  private readonly catalogoService = inject(CatalogoService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  // Estados de datos
  readonly libros = signal<LibroCatalogo[]>([]);
  readonly autores = signal<AutorCatalogo[]>([]);
  readonly categorias = signal<CategoriaCatalogo[]>([]);
  readonly totalRegistros = signal<number>(0);
  readonly cargando = signal<boolean>(false);
  readonly error = signal<string | null>(null);

  // Filtros reactivos
  readonly busqueda = signal<string>('');
  readonly autorSeleccionado = signal<number | null>(null);
  readonly categoriaSeleccionada = signal<number | null>(null);
  readonly soloDisponibles = signal<boolean>(false);

  // Paginación (6 por página para cuadrícula de 3 columnas x 2 filas como en el prototipo)
  readonly paginaActual = signal<number>(1);
  readonly tamanioPagina = signal<number>(6);

  // Flujos reactivos de búsqueda
  readonly busquedaSubject = new Subject<string>();
  private readonly ejecutarInmediatoSubject = new Subject<void>();
  private ultimoTituloEjecutado: string | null = null;

  // Computados
  readonly totalPaginas = computed(() => {
    const total = this.totalRegistros();
    const tamanio = this.tamanioPagina();
    return total > 0 ? Math.ceil(total / tamanio) : 1;
  });

  readonly rangoMostrado = computed(() => {
    const total = this.totalRegistros();
    if (total === 0) return '0 de 0';
    const inicio = (this.paginaActual() - 1) * this.tamanioPagina() + 1;
    const fin = Math.min(this.paginaActual() * this.tamanioPagina(), total);
    return `${inicio}-${fin} de ${total}`;
  });

  readonly totalDisponibles = computed(() => {
    return this.libros().reduce((acc, l) => acc + l.stock_disponible, 0);
  });

  readonly hayFiltrosActivos = computed(() => {
    return (
      !!this.busqueda().trim() ||
      this.autorSeleccionado() !== null ||
      this.categoriaSeleccionada() !== null ||
      this.soloDisponibles()
    );
  });

  constructor() {
    this.iniciarFlujoBusqueda();
  }

  ngOnInit(): void {
    this.cargarFiltros();
    this.cargarCatalogo();
  }

  private iniciarFlujoBusqueda(): void {
    const busquedaDebounced$ = this.busquedaSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      tap(() => {
        this.paginaActual.set(1);
      }),
      filter((texto) => {
        const textoLimpio = texto.trim();
        if (this.ultimoTituloEjecutado === textoLimpio && this.paginaActual() === 1) {
          return false;
        }
        return true;
      }),
      map(() => void 0),
    );

    merge(busquedaDebounced$, this.ejecutarInmediatoSubject)
      .pipe(
        tap(() => {
          this.cargando.set(true);
          this.error.set(null);
        }),
        switchMap(() => {
          const filtros = this.construirFiltros();
          this.ultimoTituloEjecutado = this.busqueda().trim();
          return this.catalogoService.listar(filtros).pipe(
            catchError((err) => {
              this.cargando.set(false);
              this.error.set(
                err.status === 404
                  ? 'Página fuera de rango.'
                  : 'Error al cargar los libros del catálogo. Intenta nuevamente.',
              );
              return of(null);
            }),
          );
        }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((resp) => {
        if (resp) {
          this.libros.set(resp.results);
          this.totalRegistros.set(resp.count);
          this.cargando.set(false);
        }
      });
  }

  private construirFiltros() {
    const busquedaTexto = this.busqueda().trim();
    return {
      titulo: busquedaTexto.length > 0 ? busquedaTexto : undefined,
      autor: this.autorSeleccionado() ?? undefined,
      categoria: this.categoriaSeleccionada() ?? undefined,
      disponible: this.soloDisponibles() ? true : undefined,
      page: this.paginaActual(),
      page_size: this.tamanioPagina(),
    };
  }

  cargarFiltros(): void {
    this.catalogoService.obtenerFiltros().subscribe({
      next: (opciones) => {
        this.autores.set(opciones.autores);
        this.categorias.set(opciones.categorias);
      },
      error: () => {},
    });
  }

  cargarCatalogo(): void {
    this.ejecutarInmediatoSubject.next();
  }

  onBusquedaChange(valor: string): void {
    this.busqueda.set(valor);
    this.busquedaSubject.next(valor);
  }

  onBuscar(event?: Event): void {
    if (event) {
      event.preventDefault();
    }
    this.paginaActual.set(1);
    this.cargarCatalogo();
  }

  onFiltroChange(): void {
    this.paginaActual.set(1);
    this.cargarCatalogo();
  }

  limpiarFiltros(): void {
    this.busqueda.set('');
    this.ultimoTituloEjecutado = '';
    this.autorSeleccionado.set(null);
    this.categoriaSeleccionada.set(null);
    this.soloDisponibles.set(false);
    this.paginaActual.set(1);
    this.cargarCatalogo();
  }

  irAPagina(pagina: number): void {
    if (pagina >= 1 && pagina <= this.totalPaginas() && pagina !== this.paginaActual()) {
      this.paginaActual.set(pagina);
      this.cargarCatalogo();
    }
  }

  paginaAnterior(): void {
    if (this.paginaActual() > 1) {
      this.irAPagina(this.paginaActual() - 1);
    }
  }

  paginaSiguiente(): void {
    if (this.paginaActual() < this.totalPaginas()) {
      this.irAPagina(this.paginaActual() + 1);
    }
  }

  verDetalle(libroId: number): void {
    void this.router.navigate(['/catalogo', libroId]);
  }

  formatearAutores(libro: LibroCatalogo): string {
    if (!libro.autores || libro.autores.length === 0) {
      return 'Autor no registrado';
    }
    return libro.autores.map((a) => a.nombre).join(', ');
  }

  obtenerEstadoDisponibilidad(libro: LibroCatalogo): {
    clase: string;
    etiqueta: string;
  } {
    if (libro.stock_disponible > 1) {
      return {
        clase: 'status-pill--available',
        etiqueta: 'Disponible',
      };
    }
    if (libro.stock_disponible === 1) {
      return {
        clase: 'status-pill--last-unit',
        etiqueta: '1 disponible (Último)',
      };
    }
    return {
      clase: 'status-pill--unavailable',
      etiqueta: 'No disponible',
    };
  }
}
