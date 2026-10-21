import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  computed,
  DestroyRef,
  ElementRef,
  HostListener,
  inject,
  OnInit,
  signal,
  ViewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  FormBuilder,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import {
  catchError,
  debounceTime,
  distinctUntilChanged,
  map,
  merge,
  of,
  Subject,
  switchMap,
  tap,
} from 'rxjs';

import {
  CategoriaAdministrativa,
  CategoriasFiltros,
  CategoriasPaginadas,
} from '../../models/categorias.models';
import { CategoriasService } from '../../services/categorias.service';

@Component({
  selector: 'app-categorias-lista',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './categorias-lista.html',
  styleUrls: ['./categorias-lista.css'],
})
export class CategoriasListaComponent implements OnInit {
  private readonly categoriasService = inject(CategoriasService);
  private readonly fb = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);

  @ViewChild('inputNombre') inputNombreRef?: ElementRef<HTMLInputElement>;
  @ViewChild('modalDialog') modalDialogRef?: ElementRef<HTMLElement>;

  private elementoPrevioFoco: HTMLElement | null = null;

  // ---------------------------------------------------------------------------
  // Estado de listado
  // ---------------------------------------------------------------------------
  readonly categorias = signal<CategoriaAdministrativa[]>([]);
  readonly total = signal<number>(0);
  readonly pagina = signal<number>(1);
  readonly pageSize = signal<number>(10);
  readonly cargando = signal<boolean>(false);
  readonly guardando = signal<boolean>(false);
  readonly errorListado = signal<string | null>(null);
  readonly mensajeExito = signal<string | null>(null);

  // ---------------------------------------------------------------------------
  // Búsqueda y recargas reactivas (con debounce y switchMap)
  // ---------------------------------------------------------------------------
  readonly busquedaNombre = signal<string>('');
  private readonly busquedaSubject = new Subject<string>();
  private readonly recargaInmediataSubject = new Subject<boolean>();

  // ---------------------------------------------------------------------------
  // Modal unificado (Registro / Edición)
  // ---------------------------------------------------------------------------
  readonly modalAbierto = signal<boolean>(false);
  readonly modoEdicion = signal<boolean>(false);
  readonly categoriaSeleccionada = signal<CategoriaAdministrativa | null>(null);
  readonly errorCampoNombre = signal<string | null>(null);
  readonly errorGeneralModal = signal<string | null>(null);

  readonly formCategoria = this.fb.group({
    nombre_categoria: ['', [Validators.required, Validators.maxLength(50)]],
  });

  // ---------------------------------------------------------------------------
  // Cálculos derivados
  // ---------------------------------------------------------------------------
  readonly totalPaginas = computed(() => {
    const count = this.total();
    const size = this.pageSize();
    return count > 0 ? Math.ceil(count / size) : 1;
  });

  readonly primerRegistro = computed(() => {
    if (this.total() === 0) return 0;
    return (this.pagina() - 1) * this.pageSize() + 1;
  });

  readonly ultimoRegistro = computed(() => {
    return Math.min(this.pagina() * this.pageSize(), this.total());
  });

  constructor() {
    this.configurarFlujoDeDatos();
  }

  ngOnInit(): void {
    this.cargarCategorias();
  }

  // ---------------------------------------------------------------------------
  // Configuración reactiva de búsqueda y recarga (switchMap para evitar colisiones)
  // ---------------------------------------------------------------------------
  private configurarFlujoDeDatos(): void {
    const busquedas$ = this.busquedaSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      tap((termino) => {
        this.busquedaNombre.set(termino);
        this.pagina.set(1);
      }),
      map(() => this.construirFiltros()),
    );

    const recargas$ = this.recargaInmediataSubject.pipe(
      map((resetPagina) => {
        if (resetPagina) {
          this.pagina.set(1);
        }
        return this.construirFiltros();
      }),
    );

    merge(busquedas$, recargas$)
      .pipe(
        tap(() => {
          this.cargando.set(true);
          this.errorListado.set(null);
        }),
        switchMap((filtros) =>
          this.categoriasService.listar(filtros).pipe(
            catchError((err: HttpErrorResponse) => {
              this.procesarErrorListado(err);
              return of(null);
            }),
          ),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((respuesta: CategoriasPaginadas | null) => {
        this.cargando.set(false);
        if (respuesta) {
          this.categorias.set(respuesta.results);
          this.total.set(respuesta.count);
        } else {
          this.categorias.set([]);
          this.total.set(0);
        }
      });
  }

  private construirFiltros(): CategoriasFiltros {
    const termino = this.busquedaNombre().trim();
    return {
      nombre: termino.length > 0 ? termino : undefined,
      page: this.pagina(),
      page_size: this.pageSize(),
    };
  }

  private procesarErrorListado(err: HttpErrorResponse): void {
    if (err.status === 403) {
      this.errorListado.set('Acceso denegado. Se requiere rol de bibliotecario.');
    } else if (err.status === 0) {
      this.errorListado.set('No fue posible conectar con el servidor. Verifique su conexión.');
    } else {
      this.errorListado.set(
        'No fue posible cargar el listado de categorías. Intente nuevamente.',
      );
    }
  }

  // ---------------------------------------------------------------------------
  // Acciones de búsqueda y paginación
  // ---------------------------------------------------------------------------
  actualizarBusqueda(termino: string): void {
    this.busquedaSubject.next(termino);
  }

  limpiarBusqueda(): void {
    this.busquedaNombre.set('');
    this.recargaInmediataSubject.next(true);
  }

  cambiarPagina(nuevaPagina: number): void {
    if (
      nuevaPagina < 1 ||
      nuevaPagina > this.totalPaginas() ||
      nuevaPagina === this.pagina() ||
      this.cargando()
    ) {
      return;
    }
    this.pagina.set(nuevaPagina);
    this.recargaInmediataSubject.next(false);
  }

  cargarCategorias(): void {
    this.recargaInmediataSubject.next(false);
  }

  // ---------------------------------------------------------------------------
  // Modal: Registro y Edición unificados
  // ---------------------------------------------------------------------------
  abrirModalRegistro(): void {
    this.guardarFocoActual();
    this.modoEdicion.set(false);
    this.categoriaSeleccionada.set(null);
    this.formCategoria.reset({ nombre_categoria: '' });
    this.errorCampoNombre.set(null);
    this.errorGeneralModal.set(null);
    this.modalAbierto.set(true);
    this.enfocarInputInicial();
  }

  abrirModalEdicion(categoria: CategoriaAdministrativa): void {
    this.guardarFocoActual();
    this.modoEdicion.set(true);
    this.categoriaSeleccionada.set(categoria);
    this.formCategoria.reset({ nombre_categoria: categoria.nombre_categoria });
    this.errorCampoNombre.set(null);
    this.errorGeneralModal.set(null);
    this.modalAbierto.set(true);
    this.enfocarInputInicial();
  }

  cerrarModal(): void {
    if (this.guardando()) return;
    this.modalAbierto.set(false);
    this.modoEdicion.set(false);
    this.categoriaSeleccionada.set(null);
    this.formCategoria.reset({ nombre_categoria: '' });
    this.errorCampoNombre.set(null);
    this.errorGeneralModal.set(null);
    this.restaurarFocoPrevio();
  }

  onSubmit(): void {
    if (this.guardando()) return;

    const control = this.formCategoria.get('nombre_categoria');
    const valorOriginal = control?.value ?? '';
    const valorLimpio = valorOriginal.trim();

    if (!valorLimpio) {
      control?.setErrors({ required: true });
      control?.markAsTouched();
      return;
    }

    if (valorLimpio.length > 50) {
      control?.setErrors({
        maxlength: { requiredLength: 50, actualLength: valorLimpio.length },
      });
      control?.markAsTouched();
      return;
    }

    // En edición: no hacer peticiones innecesarias si no hubo cambios
    if (this.modoEdicion()) {
      const actual = this.categoriaSeleccionada();
      if (actual && actual.nombre_categoria.trim() === valorLimpio) {
        this.cerrarModal();
        return;
      }
    }

    this.guardando.set(true);
    this.errorCampoNombre.set(null);
    this.errorGeneralModal.set(null);

    if (this.modoEdicion()) {
      const cat = this.categoriaSeleccionada();
      if (!cat) return;

      // PATCH con el nombre modificado
      this.categoriasService
        .modificar(cat.categoria_id, { nombre_categoria: valorLimpio })
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: (catActualizada) => {
            this.guardando.set(false);
            this.modalAbierto.set(false);
            this.mensajeExito.set(
              `Categoría #${catActualizada.categoria_id} actualizada exitosamente a "${catActualizada.nombre_categoria}".`,
            );
            this.cargarCategorias();
            this.restaurarFocoPrevio();
          },
          error: (err: HttpErrorResponse) => {
            this.guardando.set(false);
            this.procesarErrorFormulario(err);
          },
        });
    } else {
      // POST para nueva categoría
      this.categoriasService
        .registrar({ nombre_categoria: valorLimpio })
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: (catCreada) => {
            this.guardando.set(false);
            this.modalAbierto.set(false);
            this.mensajeExito.set(
              `Categoría "${catCreada.nombre_categoria}" (#${catCreada.categoria_id}) registrada exitosamente.`,
            );
            this.cargarCategorias();
            this.restaurarFocoPrevio();
          },
          error: (err: HttpErrorResponse) => {
            this.guardando.set(false);
            this.procesarErrorFormulario(err);
          },
        });
    }
  }

  // ---------------------------------------------------------------------------
  // Extracción e interpretación precisa de errores del backend
  // ---------------------------------------------------------------------------
  private procesarErrorFormulario(err: HttpErrorResponse): void {
    const errorData = err?.error;

    // 1. Error directo sobre el campo nombre_categoria (validación o duplicidad de backend)
    if (errorData?.nombre_categoria) {
      const msg = Array.isArray(errorData.nombre_categoria)
        ? errorData.nombre_categoria[0]
        : String(errorData.nombre_categoria);
      this.errorCampoNombre.set(msg);
      return;
    }

    // 2. Error general en detail o error
    if (typeof errorData === 'string') {
      this.errorGeneralModal.set(errorData);
      return;
    }

    if (errorData?.detail) {
      this.errorGeneralModal.set(String(errorData.detail));
      return;
    }

    if (errorData?.error) {
      this.errorGeneralModal.set(String(errorData.error));
      return;
    }

    if (errorData?.non_field_errors) {
      const msg = Array.isArray(errorData.non_field_errors)
        ? errorData.non_field_errors[0]
        : String(errorData.non_field_errors);
      this.errorGeneralModal.set(msg);
      return;
    }

    if (err.status === 403) {
      this.errorGeneralModal.set('Acceso denegado. Se requiere rol de bibliotecario.');
      return;
    }

    this.errorGeneralModal.set(
      'Ocurrió un error inesperado al procesar la categoría. Intente nuevamente.',
    );
  }

  obtenerErrorNombre(): string | null {
    // Si el backend devolvió un error específico (ej. duplicidad), tiene prioridad
    if (this.errorCampoNombre()) {
      return this.errorCampoNombre();
    }

    const ctrl = this.formCategoria.get('nombre_categoria');
    if (!ctrl || !ctrl.touched || !ctrl.errors) return null;

    if (ctrl.errors['required']) {
      return 'El nombre de la categoría es obligatorio.';
    }
    if (ctrl.errors['maxlength']) {
      return 'El nombre no puede exceder 50 caracteres.';
    }
    return null;
  }

  cerrarMensajeExito(): void {
    this.mensajeExito.set(null);
  }

  // ---------------------------------------------------------------------------
  // Accesibilidad: gestión de foco y atajos de teclado
  // ---------------------------------------------------------------------------
  private guardarFocoActual(): void {
    if (typeof document !== 'undefined') {
      this.elementoPrevioFoco = document.activeElement as HTMLElement | null;
    }
  }

  private enfocarInputInicial(): void {
    setTimeout(() => {
      this.inputNombreRef?.nativeElement?.focus();
    }, 50);
  }

  private restaurarFocoPrevio(): void {
    if (this.elementoPrevioFoco && typeof this.elementoPrevioFoco.focus === 'function') {
      setTimeout(() => {
        this.elementoPrevioFoco?.focus();
        this.elementoPrevioFoco = null;
      }, 50);
    }
  }

  @HostListener('document:keydown', ['$event'])
  manejarTecladoModal(event: KeyboardEvent): void {
    if (!this.modalAbierto()) return;

    if (event.key === 'Escape' && !this.guardando()) {
      event.preventDefault();
      this.cerrarModal();
      return;
    }

    if (event.key === 'Tab') {
      this.contenerFoco(event);
    }
  }

  private contenerFoco(event: KeyboardEvent): void {
    const dialog = this.modalDialogRef?.nativeElement;
    if (!dialog) return;

    const elementosFocusables = dialog.querySelectorAll<HTMLElement>(
      'button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])',
    );

    if (elementosFocusables.length === 0) return;

    const primerElemento = elementosFocusables[0];
    const ultimoElemento = elementosFocusables[elementosFocusables.length - 1];

    if (event.shiftKey) {
      if (document.activeElement === primerElemento) {
        event.preventDefault();
        ultimoElemento.focus();
      }
    } else {
      if (document.activeElement === ultimoElemento) {
        event.preventDefault();
        primerElemento.focus();
      }
    }
  }
}
