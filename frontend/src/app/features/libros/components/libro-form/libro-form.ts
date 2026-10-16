import { CommonModule } from '@angular/common';
import {
  Component,
  EventEmitter,
  Input,
  OnChanges,
  OnInit,
  Output,
  SimpleChanges,
  signal,
} from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';

import {
  AutorCatalogo,
  CategoriaCatalogo,
} from '../../../catalogo/models/catalogo.models';
import {
  Libro,
  ModificarLibroRequest,
  RegistrarLibroRequest,
} from '../../models/libros.models';

export type ModoFormulario = 'registro' | 'edicion';

export type GuardarPayload = RegistrarLibroRequest | ModificarLibroRequest;

@Component({
  selector: 'app-libro-form',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './libro-form.html',
  styleUrl: './libro-form.css',
})
export class LibroFormComponent implements OnInit, OnChanges {
  @Input() modo: ModoFormulario = 'registro';
  @Input() libro: Libro | null = null;
  @Input() autoresDisponibles: AutorCatalogo[] = [];
  @Input() categoriasDisponibles: CategoriaCatalogo[] = [];
  @Input() guardando = false;
  @Input() erroresServidor: Record<string, string[]> = {};

  @Output() guardar = new EventEmitter<GuardarPayload>();
  @Output() cancelar = new EventEmitter<void>();

  form!: FormGroup;

  // Selecciones múltiples (gestionadas manualmente en UI chips)
  readonly autoresSeleccionados = signal<number[]>([]);
  readonly categoriasSeleccionadas = signal<number[]>([]);

  constructor(private readonly fb: FormBuilder) {}

  ngOnInit(): void {
    this.inicializarFormulario();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['libro'] && this.form) {
      this.precargarDatos();
    }
    if (changes['erroresServidor'] && this.form) {
      this.aplicarErroresServidor();
    }
  }

  private inicializarFormulario(): void {
    this.form = this.fb.group({
      titulo: [
        '',
        [
          Validators.required,
          Validators.maxLength(100),
          this.noSoloEspaciosValidator,
        ],
      ],
      isbn: [
        '',
        [
          Validators.required,
          Validators.maxLength(13),
          this.noSoloEspaciosValidator,
        ],
      ],
      fecha_publicacion: [null],
    });

    if (this.libro) {
      this.precargarDatos();
    }
  }

  private precargarDatos(): void {
    if (!this.libro) return;

    this.form.patchValue({
      titulo: this.libro.titulo,
      isbn: this.libro.isbn,
      fecha_publicacion: this.libro.fecha_publicacion ?? null,
    });

    this.autoresSeleccionados.set(
      this.libro.autores.map((a) => a.autor_id),
    );
    this.categoriasSeleccionadas.set(
      this.libro.categorias.map((c) => c.categoria_id),
    );
  }

  private noSoloEspaciosValidator(
    control: AbstractControl,
  ): Record<string, boolean> | null {
    if (
      typeof control.value === 'string' &&
      control.value.trim().length === 0 &&
      control.value.length > 0
    ) {
      return { soloEspacios: true };
    }
    return null;
  }

  private aplicarErroresServidor(): void {
    const errores = this.erroresServidor;
    if (!errores || Object.keys(errores).length === 0) return;

    const camposFormulario: Record<string, string> = {
      titulo: 'titulo',
      isbn: 'isbn',
      fecha_publicacion: 'fecha_publicacion',
    };

    for (const [campoBE, campoForm] of Object.entries(camposFormulario)) {
      const control = this.form.get(campoForm);
      if (control && errores[campoBE]) {
        control.setErrors({ servidor: errores[campoBE].join(' ') });
        control.markAsTouched();
      }
    }
  }

  agregarAutor(autorId: number): void {
    const actuales = this.autoresSeleccionados();
    if (!actuales.includes(autorId)) {
      this.autoresSeleccionados.set([...actuales, autorId]);
    }
  }

  quitarAutor(autorId: number): void {
    this.autoresSeleccionados.set(
      this.autoresSeleccionados().filter((id) => id !== autorId),
    );
  }

  toggleAutor(autorId: number): void {
    if (this.estaAutorSeleccionado(autorId)) {
      this.quitarAutor(autorId);
    } else {
      this.agregarAutor(autorId);
    }
  }

  estaAutorSeleccionado(autorId: number): boolean {
    return this.autoresSeleccionados().includes(autorId);
  }

  obtenerNombreAutor(autorId: number): string {
    const deDisponibles = this.autoresDisponibles.find(
      (a) => a.autor_id === autorId,
    );
    if (deDisponibles) return deDisponibles.nombre;
    const delLibro = this.libro?.autores.find((a) => a.autor_id === autorId);
    if (delLibro) return delLibro.nombre;
    return `Autor #${autorId}`;
  }

  onSelectAutorChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    const valor = target.value;
    if (valor) {
      const id = Number(valor);
      if (!isNaN(id) && id > 0) {
        this.agregarAutor(id);
      }
      target.value = '';
    }
  }

  agregarCategoria(categoriaId: number): void {
    const actuales = this.categoriasSeleccionadas();
    if (!actuales.includes(categoriaId)) {
      this.categoriasSeleccionadas.set([...actuales, categoriaId]);
    }
  }

  quitarCategoria(categoriaId: number): void {
    this.categoriasSeleccionadas.set(
      this.categoriasSeleccionadas().filter((id) => id !== categoriaId),
    );
  }

  toggleCategoria(categoriaId: number): void {
    if (this.estaCategoriaSeleccionada(categoriaId)) {
      this.quitarCategoria(categoriaId);
    } else {
      this.agregarCategoria(categoriaId);
    }
  }

  estaCategoriaSeleccionada(categoriaId: number): boolean {
    return this.categoriasSeleccionadas().includes(categoriaId);
  }

  obtenerNombreCategoria(categoriaId: number): string {
    const deDisponibles = this.categoriasDisponibles.find(
      (c) => c.categoria_id === categoriaId,
    );
    if (deDisponibles) return deDisponibles.nombre_categoria;
    const delLibro = this.libro?.categorias.find(
      (c) => c.categoria_id === categoriaId,
    );
    if (delLibro) return delLibro.nombre_categoria;
    return `Categoría #${categoriaId}`;
  }

  onSelectCategoriaChange(event: Event): void {
    const target = event.target as HTMLSelectElement;
    const valor = target.value;
    if (valor) {
      const id = Number(valor);
      if (!isNaN(id) && id > 0) {
        this.agregarCategoria(id);
      }
      target.value = '';
    }
  }

  errorDe(campo: string): string | null {
    const control = this.form.get(campo);
    if (!control || !control.touched || !control.errors) return null;

    if (control.errors['required']) return 'Este campo es obligatorio.';
    if (control.errors['maxlength']) {
      const max = control.errors['maxlength'].requiredLength as number;
      return `Máximo ${max} caracteres.`;
    }
    if (control.errors['soloEspacios']) {
      return 'No puede contener solo espacios en blanco.';
    }
    if (control.errors['servidor']) {
      return control.errors['servidor'] as string;
    }
    return null;
  }

  erroresAsociaciones(tipo: 'autor_ids' | 'categoria_ids'): string | null {
    const lista = this.erroresServidor[tipo];
    return lista && lista.length > 0 ? lista.join(' ') : null;
  }

  onSubmit(): void {
    if (this.guardando) return;

    this.form.markAllAsTouched();
    if (this.form.invalid) return;

    const { titulo, isbn, fecha_publicacion } = this.form.value as {
      titulo: string;
      isbn: string;
      fecha_publicacion: string | null;
    };

    if (this.modo === 'registro') {
      const payload: RegistrarLibroRequest = {
        titulo: titulo.trim(),
        isbn: isbn.trim(),
      };

      if (fecha_publicacion && fecha_publicacion.trim().length > 0) {
        payload.fecha_publicacion = fecha_publicacion.trim();
      } else {
        payload.fecha_publicacion = null;
      }

      const autores = this.autoresSeleccionados();
      if (autores.length > 0) {
        payload.autor_ids = [...new Set(autores)];
      }

      const categorias = this.categoriasSeleccionadas();
      if (categorias.length > 0) {
        payload.categoria_ids = [...new Set(categorias)];
      }

      this.guardar.emit(payload);
    } else {
      // Modo edición: PATCH — solo enviar lo que cambió
      const payload: ModificarLibroRequest = {};

      const tituloOriginal = this.libro?.titulo ?? '';
      const isbnOriginal = this.libro?.isbn ?? '';
      const fechaOriginal = this.libro?.fecha_publicacion ?? null;
      const autoresOriginales = (this.libro?.autores ?? []).map(
        (a) => a.autor_id,
      );
      const categoriasOriginales = (this.libro?.categorias ?? []).map(
        (c) => c.categoria_id,
      );

      const tituloNuevo = titulo.trim();
      const isbnNuevo = isbn.trim();
      const fechaNueva =
        fecha_publicacion && fecha_publicacion.trim().length > 0
          ? fecha_publicacion.trim()
          : null;

      if (tituloNuevo !== tituloOriginal) payload.titulo = tituloNuevo;
      if (isbnNuevo !== isbnOriginal) payload.isbn = isbnNuevo;
      if (fechaNueva !== fechaOriginal) payload.fecha_publicacion = fechaNueva;

      const autoresNuevos = [...new Set(this.autoresSeleccionados())].sort(
        (a, b) => a - b,
      );
      const autoresOriginalesOrdenados = [...autoresOriginales].sort(
        (a, b) => a - b,
      );
      if (
        JSON.stringify(autoresNuevos) !==
        JSON.stringify(autoresOriginalesOrdenados)
      ) {
        payload.autor_ids = autoresNuevos;
      }

      const categoriasNuevas = [
        ...new Set(this.categoriasSeleccionadas()),
      ].sort((a, b) => a - b);
      const categoriasOriginalesOrdenadas = [...categoriasOriginales].sort(
        (a, b) => a - b,
      );
      if (
        JSON.stringify(categoriasNuevas) !==
        JSON.stringify(categoriasOriginalesOrdenadas)
      ) {
        payload.categoria_ids = categoriasNuevas;
      }

      this.guardar.emit(payload);
    }
  }

  onCancelar(): void {
    this.cancelar.emit();
  }

  get tituloBoton(): string {
    if (this.guardando) return 'Guardando...';
    return this.modo === 'registro' ? 'Registrar libro' : 'Guardar cambios';
  }

  get tituloPagina(): string {
    return this.modo === 'registro' ? 'Registrar nuevo libro' : 'Editar libro';
  }
}
