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

import { AutorAdministrativo, AutoresPaginados } from '../../models/autores.models';

import { AutoresService } from '../../services/autores.service';

@Component({
  selector: 'app-autores-lista',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './autores-lista.html',
  styleUrls: ['./autores-lista.css'],
})
export class AutoresListaComponent implements OnInit {
  private readonly autoresService = inject(AutoresService);
  private readonly fb = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);

  // Referencias para accesibilidad de modales
  @ViewChild('modalRegistroDialog') modalRegistroDialogRef?: ElementRef<HTMLElement>;
  @ViewChild('modalEdicionDialog') modalEdicionDialogRef?: ElementRef<HTMLElement>;
  @ViewChild('inputNombreRegistro') inputNombreRegistroRef?: ElementRef<HTMLInputElement>;
  @ViewChild('inputNombreEdicion') inputNombreEdicionRef?: ElementRef<HTMLInputElement>;

  private elementoPrevioFoco: HTMLElement | null = null;

  // ---------------------------------------------------------------------------
  // Estado de listado
  // ---------------------------------------------------------------------------
  readonly autores = signal<AutorAdministrativo[]>([]);
  readonly total = signal<number>(0);
  readonly pagina = signal<number>(1);
  readonly pageSize = signal<number>(10);
  readonly cargando = signal<boolean>(false);
  readonly guardando = signal<boolean>(false);
  readonly errorListado = signal<string | null>(null);
  readonly mensajeExito = signal<string | null>(null);

  // ---------------------------------------------------------------------------
  // Búsqueda con debounce y recarga inmediata (switchMap para evitar race conditions)
  // ---------------------------------------------------------------------------
  readonly busquedaNombre = signal<string>('');
  private readonly searchSubject = new Subject<string>();
  private readonly recargaInmediataSubject = new Subject<boolean>();

  // ---------------------------------------------------------------------------
  // Modales
  // ---------------------------------------------------------------------------
  readonly modalRegistroAbierto = signal<boolean>(false);
  readonly modalEdicionAbierto = signal<boolean>(false);
  readonly autorSeleccionado = signal<AutorAdministrativo | null>(null);
  readonly errorRegistro = signal<string | null>(null);
  readonly errorEdicion = signal<string | null>(null);

  // ---------------------------------------------------------------------------
  // Formularios reactivos (alcance simplificado: únicamente nombre)
  // ---------------------------------------------------------------------------
  readonly formRegistro = this.fb.group({
    nombre: ['', [Validators.required, Validators.maxLength(100)]],
  });

  readonly formEdicion = this.fb.group({
    nombre: ['', [Validators.required, Validators.maxLength(100)]],
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
    this.recargaInmediataSubject.next(false);
  }

  // ---------------------------------------------------------------------------
  // Configuración reactiva de búsqueda y recarga (switchMap para evitar colisiones)
  // ---------------------------------------------------------------------------
  private configurarFlujoDeDatos(): void {
    const busquedas$ = this.searchSubject.pipe(
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
          this.autoresService.listar(filtros).pipe(
            catchError((err: HttpErrorResponse) => {
              this.procesarErrorListado(err);
              return of(null);
            }),
          ),
        ),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((respuesta: AutoresPaginados | null) => {
        this.cargando.set(false);
        if (respuesta) {
          this.autores.set(respuesta.results);
          this.total.set(respuesta.count);
        } else {
          this.autores.set([]);
          this.total.set(0);
        }
      });
  }

  private construirFiltros() {
    const nombreFiltro = this.busquedaNombre().trim();
    return {
      nombre: nombreFiltro.length > 0 ? nombreFiltro : undefined,
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
        'No fue posible cargar el listado de autores. Verifique la conexión con el servidor.',
      );
    }
  }

  // ---------------------------------------------------------------------------
  // Acciones de búsqueda y paginación
  // ---------------------------------------------------------------------------
  actualizarBusqueda(termino: string): void {
    this.searchSubject.next(termino);
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

  // ---------------------------------------------------------------------------
  // Disparo de recarga (delegado al flujo reactivo con switchMap)
  // ---------------------------------------------------------------------------
  cargarAutores(): void {
    this.recargaInmediataSubject.next(false);
  }

  // ---------------------------------------------------------------------------
  // Modal de registro (POST)
  // ---------------------------------------------------------------------------
  abrirModalRegistro(): void {
    this.guardarFocoActual();
    this.formRegistro.reset({ nombre: '' });
    this.errorRegistro.set(null);
    this.modalRegistroAbierto.set(true);
    this.enfocarInput(this.inputNombreRegistroRef);
  }

  cerrarModalRegistro(): void {
    if (this.guardando()) return;
    this.modalRegistroAbierto.set(false);
    this.formRegistro.reset({ nombre: '' });
    this.errorRegistro.set(null);
    this.restaurarFocoPrevio();
  }

  onSubmitRegistro(): void {
    if (this.guardando()) return;

    const nombreCtrl = this.formRegistro.get('nombre');
    const valorOriginal = nombreCtrl?.value ?? '';
    const nombreValor = valorOriginal.trim();

    if (!nombreValor) {
      nombreCtrl?.setErrors({ required: true });
      nombreCtrl?.markAsTouched();
      return;
    }

    if (nombreValor.length > 100) {
      nombreCtrl?.setErrors({ maxlength: { requiredLength: 100, actualLength: nombreValor.length } });
      nombreCtrl?.markAsTouched();
      return;
    }

    this.guardando.set(true);
    this.errorRegistro.set(null);

    // Envía únicamente el nombre, permitiendo homónimos según el contrato
    this.autoresService
      .registrar({ nombre: nombreValor })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (autorCreado) => {
          this.guardando.set(false);
          this.modalRegistroAbierto.set(false);
          this.formRegistro.reset({ nombre: '' });
          this.mensajeExito.set(
            `Autor "${autorCreado.nombre}" (#${autorCreado.autor_id}) registrado exitosamente.`,
          );
          this.cargarAutores();
        },
        error: (err) => {
          this.guardando.set(false);
          const detalle =
            err.error?.error ||
            err.error?.nombre?.[0] ||
            'Ocurrió un error al registrar el autor. Intente nuevamente.';
          this.errorRegistro.set(detalle);
        },
      });
  }

  // ---------------------------------------------------------------------------
  // Modal de edición (PATCH)
  // ---------------------------------------------------------------------------
  abrirModalEdicion(autor: AutorAdministrativo): void {
    this.guardarFocoActual();
    this.autorSeleccionado.set(autor);
    this.formEdicion.reset({ nombre: autor.nombre });
    this.errorEdicion.set(null);
    this.modalEdicionAbierto.set(true);
    this.enfocarInput(this.inputNombreEdicionRef);
  }

  cerrarModalEdicion(): void {
    if (this.guardando()) return;
    this.modalEdicionAbierto.set(false);
    this.autorSeleccionado.set(null);
    this.formEdicion.reset({ nombre: '' });
    this.errorEdicion.set(null);
    this.restaurarFocoPrevio();
  }

  onSubmitEdicion(): void {
    if (this.guardando()) return;
    const autor = this.autorSeleccionado();
    if (!autor) return;

    const nombreCtrl = this.formEdicion.get('nombre');
    const valorOriginal = nombreCtrl?.value ?? '';
    const nombreValor = valorOriginal.trim();

    if (!nombreValor) {
      nombreCtrl?.setErrors({ required: true });
      nombreCtrl?.markAsTouched();
      return;
    }

    if (nombreValor.length > 100) {
      nombreCtrl?.setErrors({ maxlength: { requiredLength: 100, actualLength: nombreValor.length } });
      nombreCtrl?.markAsTouched();
      return;
    }

    this.guardando.set(true);
    this.errorEdicion.set(null);

    // Exclusivamente PATCH para no alterar los atributos opcionales existentes
    this.autoresService
      .modificar(autor.autor_id, { nombre: nombreValor })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (autorActualizado) => {
          this.guardando.set(false);
          this.modalEdicionAbierto.set(false);
          this.autorSeleccionado.set(null);
          this.formEdicion.reset({ nombre: '' });
          this.mensajeExito.set(
            `Autor #${autorActualizado.autor_id} actualizado exitosamente a "${autorActualizado.nombre}".`,
          );
          this.cargarAutores();
          this.restaurarFocoPrevio();
        },
        error: (err) => {
          this.guardando.set(false);
          const detalle =
            err.error?.error ||
            err.error?.nombre?.[0] ||
            'Ocurrió un error al actualizar el autor. Intente nuevamente.';
          this.errorEdicion.set(detalle);
        },
      });
  }

  // ---------------------------------------------------------------------------
  // Helpers de mensajes de error de formulario
  // ---------------------------------------------------------------------------
  obtenerErrorNombre(controlName: 'formRegistro' | 'formEdicion'): string | null {
    const form = controlName === 'formRegistro' ? this.formRegistro : this.formEdicion;
    const ctrl = form.get('nombre');
    if (!ctrl || !ctrl.touched || !ctrl.errors) return null;

    if (ctrl.errors['required']) {
      return 'El nombre del autor es obligatorio.';
    }
    if (ctrl.errors['maxlength']) {
      return 'El nombre no puede exceder 100 caracteres.';
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

  private enfocarInput(ref?: ElementRef<HTMLInputElement>): void {
    setTimeout(() => {
      ref?.nativeElement?.focus();
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
    const modalAbierto = this.modalRegistroAbierto() || this.modalEdicionAbierto();
    if (!modalAbierto) return;

    if (event.key === 'Escape' && !this.guardando()) {
      event.preventDefault();
      if (this.modalRegistroAbierto()) {
        this.cerrarModalRegistro();
      } else {
        this.cerrarModalEdicion();
      }
      return;
    }

    if (event.key === 'Tab') {
      const dialogRef = this.modalRegistroAbierto()
        ? this.modalRegistroDialogRef
        : this.modalEdicionDialogRef;
      this.contenerFoco(event, dialogRef?.nativeElement);
    }
  }

  private contenerFoco(event: KeyboardEvent, dialog: HTMLElement | undefined): void {
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
