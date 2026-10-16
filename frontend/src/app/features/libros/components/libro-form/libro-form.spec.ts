import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';

import { AutorCatalogo, CategoriaCatalogo } from '../../../catalogo/models/catalogo.models';
import { Libro } from '../../models/libros.models';
import { GuardarPayload, LibroFormComponent } from './libro-form';

// Datos de prueba comunes
const AUTORES: AutorCatalogo[] = [
  { autor_id: 1, nombre: 'Gabriel García Márquez' },
  { autor_id: 2, nombre: 'Miguel de Cervantes' },
];

const CATEGORIAS: CategoriaCatalogo[] = [
  { categoria_id: 1, nombre_categoria: 'Realismo Mágico' },
  { categoria_id: 2, nombre_categoria: 'Novela Clásica' },
];

const LIBRO_EXISTENTE: Libro = {
  libro_id: 1,
  titulo: 'Cien Años de Soledad',
  isbn: '9780307474728',
  fecha_publicacion: '1967-05-30',
  autores: [{ autor_id: 1, nombre: 'Gabriel García Márquez' }],
  categorias: [{ categoria_id: 1, nombre_categoria: 'Realismo Mágico' }],
};

describe('LibroFormComponent', () => {
  let fixture: ComponentFixture<LibroFormComponent>;
  let component: LibroFormComponent;

  function crearComponente(
    overrides: Partial<{
      modo: 'registro' | 'edicion';
      libro: Libro | null;
      autores: AutorCatalogo[];
      categorias: CategoriaCatalogo[];
      guardando: boolean;
      erroresServidor: Record<string, string[]>;
    }> = {},
  ): void {
    TestBed.configureTestingModule({
      imports: [LibroFormComponent, CommonModule, ReactiveFormsModule],
    });

    fixture = TestBed.createComponent(LibroFormComponent);
    component = fixture.componentInstance;

    component.modo = overrides.modo ?? 'registro';
    component.libro = overrides.libro ?? null;
    component.autoresDisponibles = overrides.autores ?? AUTORES;
    component.categoriasDisponibles = overrides.categorias ?? CATEGORIAS;
    component.guardando = overrides.guardando ?? false;
    component.erroresServidor = overrides.erroresServidor ?? {};

    fixture.detectChanges();
  }

  afterEach(() => {
    TestBed.resetTestingModule();
  });

  // -------------------------------------------------------------------------
  // Inicialización en modo registro
  // -------------------------------------------------------------------------
  describe('modo registro', () => {
    beforeEach(() => crearComponente({ modo: 'registro' }));

    it('debe crear el componente', () => {
      expect(component).toBeTruthy();
    });

    it('debe inicializar el formulario vacío', () => {
      expect(component.form.get('titulo')?.value).toBe('');
      expect(component.form.get('isbn')?.value).toBe('');
      expect(component.form.get('fecha_publicacion')?.value).toBeNull();
    });

    it('debe tener título de botón "Registrar libro"', () => {
      expect(component.tituloBoton).toBe('Registrar libro');
    });

    it('debe tener título de página "Registrar nuevo libro"', () => {
      expect(component.tituloPagina).toBe('Registrar nuevo libro');
    });

    it('debe inicializar sin autores ni categorías seleccionadas', () => {
      expect(component.autoresSeleccionados()).toEqual([]);
      expect(component.categoriasSeleccionadas()).toEqual([]);
    });
  });

  // -------------------------------------------------------------------------
  // Inicialización en modo edición (precarga)
  // -------------------------------------------------------------------------
  describe('modo edición — precarga', () => {
    beforeEach(() =>
      crearComponente({ modo: 'edicion', libro: LIBRO_EXISTENTE }),
    );

    it('debe precargar el título del libro', () => {
      expect(component.form.get('titulo')?.value).toBe('Cien Años de Soledad');
    });

    it('debe precargar el ISBN', () => {
      expect(component.form.get('isbn')?.value).toBe('9780307474728');
    });

    it('debe precargar la fecha de publicación', () => {
      expect(component.form.get('fecha_publicacion')?.value).toBe('1967-05-30');
    });

    it('debe precargar los autores seleccionados', () => {
      expect(component.autoresSeleccionados()).toEqual([1]);
    });

    it('debe precargar las categorías seleccionadas', () => {
      expect(component.categoriasSeleccionadas()).toEqual([1]);
    });

    it('debe tener título de botón "Guardar cambios"', () => {
      expect(component.tituloBoton).toBe('Guardar cambios');
    });
  });

  // -------------------------------------------------------------------------
  // Validaciones del formulario
  // -------------------------------------------------------------------------
  describe('validaciones', () => {
    beforeEach(() => crearComponente({ modo: 'registro' }));

    it('debe ser inválido con campos vacíos', () => {
      expect(component.form.invalid).toBe(true);
    });

    it('debe requerir título', () => {
      component.form.get('titulo')?.setValue('');
      component.form.get('titulo')?.markAsTouched();
      expect(component.errorDe('titulo')).toBe('Este campo es obligatorio.');
    });

    it('debe requerir ISBN', () => {
      component.form.get('isbn')?.setValue('');
      component.form.get('isbn')?.markAsTouched();
      expect(component.errorDe('isbn')).toBe('Este campo es obligatorio.');
    });

    it('debe validar longitud máxima de título (100)', () => {
      component.form.get('titulo')?.setValue('A'.repeat(101));
      component.form.get('titulo')?.markAsTouched();
      expect(component.errorDe('titulo')).toContain('100');
    });

    it('debe validar longitud máxima de ISBN (13)', () => {
      component.form.get('isbn')?.setValue('1'.repeat(14));
      component.form.get('isbn')?.markAsTouched();
      expect(component.errorDe('isbn')).toContain('13');
    });

    it('debe rechazar títulos con solo espacios', () => {
      component.form.get('titulo')?.setValue('   ');
      component.form.get('titulo')?.markAsTouched();
      expect(component.errorDe('titulo')).toBe(
        'No puede contener solo espacios en blanco.',
      );
    });

    it('no debe mostrar error si el campo no está tocado', () => {
      component.form.get('titulo')?.setValue('');
      expect(component.errorDe('titulo')).toBeNull();
    });

    it('debe ser válido con título e ISBN válidos', () => {
      component.form.get('titulo')?.setValue('Don Quijote');
      component.form.get('isbn')?.setValue('9788424116286');
      expect(component.form.valid).toBe(true);
    });
  });

  // -------------------------------------------------------------------------
  // Selección múltiple — chips de autores
  // -------------------------------------------------------------------------
  describe('selección de autores', () => {
    beforeEach(() => crearComponente({ modo: 'registro' }));

    it('debe agregar un autor al seleccionarlo', () => {
      component.toggleAutor(1);
      expect(component.autoresSeleccionados()).toContain(1);
    });

    it('debe quitar un autor al seleccionarlo de nuevo', () => {
      component.toggleAutor(1);
      component.toggleAutor(1);
      expect(component.autoresSeleccionados()).not.toContain(1);
    });

    it('debe permitir múltiples autores sin duplicados', () => {
      component.toggleAutor(1);
      component.toggleAutor(2);
      component.toggleAutor(1); // des-selecciona
      expect(component.autoresSeleccionados()).toEqual([2]);
    });

    it('debe reportar correctamente estaAutorSeleccionado', () => {
      component.toggleAutor(1);
      expect(component.estaAutorSeleccionado(1)).toBe(true);
      expect(component.estaAutorSeleccionado(2)).toBe(false);
    });
  });

  // -------------------------------------------------------------------------
  // Selección múltiple — chips de categorías
  // -------------------------------------------------------------------------
  describe('selección de categorías', () => {
    beforeEach(() => crearComponente({ modo: 'registro' }));

    it('debe agregar una categoría al seleccionarla', () => {
      component.toggleCategoria(1);
      expect(component.categoriasSeleccionadas()).toContain(1);
    });

    it('debe quitar una categoría al seleccionarla de nuevo', () => {
      component.toggleCategoria(1);
      component.toggleCategoria(1);
      expect(component.categoriasSeleccionadas()).not.toContain(1);
    });

    it('debe reportar correctamente estaCategoriaSeleccionada', () => {
      component.toggleCategoria(2);
      expect(component.estaCategoriaSeleccionada(2)).toBe(true);
      expect(component.estaCategoriaSeleccionada(1)).toBe(false);
    });
  });

  // -------------------------------------------------------------------------
  // Emisión del evento guardar — modo registro
  // -------------------------------------------------------------------------
  describe('onSubmit — modo registro', () => {
    beforeEach(() => crearComponente({ modo: 'registro' }));

    it('no debe emitir si el formulario es inválido', () => {
      const spy = vi.fn();
      component.guardar.subscribe(spy);

      component.onSubmit();

      expect(spy).not.toHaveBeenCalled();
    });

    it('debe emitir el payload correcto con campos obligatorios', () => {
      let payload: GuardarPayload | undefined;
      component.guardar.subscribe((p) => (payload = p));

      component.form.get('titulo')?.setValue('Don Quijote');
      component.form.get('isbn')?.setValue('9788424116286');

      component.onSubmit();

      expect(payload).toEqual(
        expect.objectContaining({ titulo: 'Don Quijote', isbn: '9788424116286' }),
      );
    });

    it('debe incluir fecha_publicacion: null si está vacía', () => {
      let payload: GuardarPayload | undefined;
      component.guardar.subscribe((p) => (payload = p));

      component.form.get('titulo')?.setValue('Don Quijote');
      component.form.get('isbn')?.setValue('9788424116286');
      component.form.get('fecha_publicacion')?.setValue(null);

      component.onSubmit();

      expect((payload as Record<string, unknown>)['fecha_publicacion']).toBeNull();
    });

    it('debe incluir autor_ids cuando hay autores seleccionados', () => {
      let payload: GuardarPayload | undefined;
      component.guardar.subscribe((p) => (payload = p));

      component.form.get('titulo')?.setValue('Don Quijote');
      component.form.get('isbn')?.setValue('9788424116286');
      component.toggleAutor(1);
      component.toggleAutor(2);

      component.onSubmit();

      expect((payload as Record<string, unknown>)['autor_ids']).toEqual(
        expect.arrayContaining([1, 2]),
      );
    });

    it('no debe incluir autor_ids si no se seleccionó ningún autor', () => {
      let payload: GuardarPayload | undefined;
      component.guardar.subscribe((p) => (payload = p));

      component.form.get('titulo')?.setValue('Don Quijote');
      component.form.get('isbn')?.setValue('9788424116286');

      component.onSubmit();

      expect((payload as Record<string, unknown>)['autor_ids']).toBeUndefined();
    });

    it('no debe emitir si guardando está activo', () => {
      const spy = vi.fn();
      component.guardar.subscribe(spy);

      component.guardando = true;
      component.form.get('titulo')?.setValue('Don Quijote');
      component.form.get('isbn')?.setValue('9788424116286');

      component.onSubmit();

      expect(spy).not.toHaveBeenCalled();
    });
  });

  // -------------------------------------------------------------------------
  // Emisión del evento guardar — modo edición (PATCH diferencial)
  // -------------------------------------------------------------------------
  describe('onSubmit — modo edición (PATCH diferencial)', () => {
    beforeEach(() =>
      crearComponente({ modo: 'edicion', libro: LIBRO_EXISTENTE }),
    );

    it('debe emitir payload vacío si no cambió nada', () => {
      let payload: GuardarPayload | undefined;
      component.guardar.subscribe((p) => (payload = p));

      component.onSubmit();

      expect(payload).toEqual({});
    });

    it('debe incluir solo el campo titulo si solo cambió el título', () => {
      let payload: GuardarPayload | undefined;
      component.guardar.subscribe((p) => (payload = p));

      component.form.get('titulo')?.setValue('Nuevo Título');
      component.onSubmit();

      expect(payload).toEqual({ titulo: 'Nuevo Título' });
    });

    it('debe incluir autor_ids si los autores cambiaron', () => {
      let payload: GuardarPayload | undefined;
      component.guardar.subscribe((p) => (payload = p));

      // El libro original tiene autor_id=1. Añadimos autor_id=2
      component.toggleAutor(2);
      component.onSubmit();

      expect((payload as Record<string, unknown>)['autor_ids']).toEqual(
        expect.arrayContaining([1, 2]),
      );
    });

    it('no debe incluir autor_ids si los autores no cambiaron', () => {
      let payload: GuardarPayload | undefined;
      component.guardar.subscribe((p) => (payload = p));

      // El libro original tiene autor_id=1, y la precarga lo mantiene
      component.onSubmit();

      expect((payload as Record<string, unknown>)['autor_ids']).toBeUndefined();
    });
  });

  // -------------------------------------------------------------------------
  // Errores del servidor
  // -------------------------------------------------------------------------
  describe('errores del servidor', () => {
    it('debe mostrar error de servidor en campo isbn', () => {
      crearComponente({
        modo: 'registro',
        erroresServidor: { isbn: ['Ya existe un libro con este ISBN.'] },
      });

      // Forzar aplicación de errores mediante ngOnChanges
      component.erroresServidor = { isbn: ['Ya existe un libro con este ISBN.'] };
      component.ngOnChanges({
        erroresServidor: {
          currentValue: { isbn: ['Ya existe un libro con este ISBN.'] },
          previousValue: {},
          firstChange: false,
          isFirstChange: () => false,
        },
      });

      component.form.get('isbn')?.markAsTouched();
      fixture.detectChanges();

      expect(component.errorDe('isbn')).toBe('Ya existe un libro con este ISBN.');
    });

    it('debe mostrar error de asociación de autor_ids', () => {
      crearComponente({
        modo: 'registro',
        erroresServidor: { autor_ids: ['El autor con id=99 no existe.'] },
      });

      expect(component.erroresAsociaciones('autor_ids')).toBe(
        'El autor con id=99 no existe.',
      );
    });

    it('debe devolver null si no hay errores de asociación', () => {
      crearComponente({ modo: 'registro' });
      expect(component.erroresAsociaciones('autor_ids')).toBeNull();
    });
  });

  // -------------------------------------------------------------------------
  // Evento cancelar
  // -------------------------------------------------------------------------
  describe('cancelar', () => {
    it('debe emitir el evento cancelar al llamar onCancelar', () => {
      crearComponente({ modo: 'registro' });

      const spy = vi.fn();
      component.cancelar.subscribe(spy);

      component.onCancelar();

      expect(spy).toHaveBeenCalled();
    });
  });

  // -------------------------------------------------------------------------
  // Pruebas de regresión — Selectores y chips de autores/categorías
  // -------------------------------------------------------------------------
  describe('Pruebas de regresión — Selectores y chips de autores/categorías', () => {
    it('debe renderizar los selectores de autor y categoría con las opciones disponibles', () => {
      crearComponente({ modo: 'registro' });
      const compiled = fixture.nativeElement as HTMLElement;

      const selectAutor = compiled.querySelector('#select-autor') as HTMLSelectElement;
      const selectCategoria = compiled.querySelector('#select-categoria') as HTMLSelectElement;

      expect(selectAutor).toBeTruthy();
      expect(selectCategoria).toBeTruthy();

      const opcionesAutores = Array.from(selectAutor.options).map((o) => o.text);
      expect(opcionesAutores).toContain('Gabriel García Márquez');
      expect(opcionesAutores).toContain('Miguel de Cervantes');

      const opcionesCategorias = Array.from(selectCategoria.options).map((o) => o.text);
      expect(opcionesCategorias).toContain('Realismo Mágico');
      expect(opcionesCategorias).toContain('Novela Clásica');
    });

    it('debe agregar un autor mediante el selector y permitir eliminarlo con el chip', () => {
      crearComponente({ modo: 'registro' });
      const compiled = fixture.nativeElement as HTMLElement;

      // Seleccionar un autor via agregarAutor
      component.agregarAutor(1);
      fixture.detectChanges();

      expect(component.autoresSeleccionados()).toEqual([1]);
      const chips = compiled.querySelectorAll('.chip-removable');
      expect(chips.length).toBe(1);
      expect(chips[0].textContent).toContain('Gabriel García Márquez');

      // Eliminar el autor haciendo clic en el botón de quitar del chip
      const btnQuitar = chips[0].querySelector('.chip__remove') as HTMLButtonElement;
      btnQuitar.click();
      fixture.detectChanges();

      expect(component.autoresSeleccionados()).toEqual([]);
      expect(compiled.querySelectorAll('.chip-removable').length).toBe(0);
    });

    it('debe agregar una categoría mediante el selector y permitir eliminarla con el chip', () => {
      crearComponente({ modo: 'registro' });
      const compiled = fixture.nativeElement as HTMLElement;

      component.agregarCategoria(2);
      fixture.detectChanges();

      expect(component.categoriasSeleccionadas()).toEqual([2]);
      const chips = compiled.querySelectorAll('.chip-removable');
      expect(chips.length).toBe(1);
      expect(chips[0].textContent).toContain('Novela Clásica');

      const btnQuitar = chips[0].querySelector('.chip__remove') as HTMLButtonElement;
      btnQuitar.click();
      fixture.detectChanges();

      expect(component.categoriasSeleccionadas()).toEqual([]);
      expect(compiled.querySelectorAll('.chip-removable').length).toBe(0);
    });

    it('no debe duplicar asociaciones si se intenta agregar el mismo autor o categoría dos veces', () => {
      crearComponente({ modo: 'registro' });

      component.agregarAutor(1);
      component.agregarAutor(1);
      expect(component.autoresSeleccionados()).toEqual([1]);

      component.agregarCategoria(2);
      component.agregarCategoria(2);
      expect(component.categoriasSeleccionadas()).toEqual([2]);
    });

    it('debe mostrar mensaje informativo y selector deshabilitado cuando las listas están vacías', () => {
      crearComponente({ modo: 'registro', autores: [], categorias: [] });
      const compiled = fixture.nativeElement as HTMLElement;

      const selectAutor = compiled.querySelector('#select-autor') as HTMLSelectElement;
      const selectCategoria = compiled.querySelector('#select-categoria') as HTMLSelectElement;

      expect(selectAutor.disabled).toBe(true);
      expect(selectAutor.textContent).toContain('No hay autores registrados');

      const msgAutores = compiled.querySelector('.chips-empty');
      expect(msgAutores?.textContent).toContain('No hay autores registrados');

      expect(selectCategoria.disabled).toBe(true);
      expect(selectCategoria.textContent).toContain('No hay categorías registradas');
    });

    it('debe precargar asociaciones existentes al editar y reflejarlas en los chips', () => {
      crearComponente({ modo: 'edicion', libro: LIBRO_EXISTENTE });
      const compiled = fixture.nativeElement as HTMLElement;

      expect(component.autoresSeleccionados()).toEqual([1]);
      expect(component.categoriasSeleccionadas()).toEqual([1]);

      const chips = compiled.querySelectorAll('.chip-removable');
      expect(chips.length).toBe(2);
      expect(chips[0].textContent).toContain('Gabriel García Márquez');
      expect(chips[1].textContent).toContain('Realismo Mágico');
    });

    it('debe conservar asociaciones en PATCH diferencial si no se modificaron', () => {
      crearComponente({ modo: 'edicion', libro: LIBRO_EXISTENTE });

      let payload: GuardarPayload | undefined;
      component.guardar.subscribe((p) => (payload = p));

      // Solo modificamos el título
      component.form.get('titulo')?.setValue('Cien Años de Soledad (Edición Ilustrada)');
      component.onSubmit();

      expect(payload).toBeDefined();
      expect((payload as Record<string, unknown>)['titulo']).toBe(
        'Cien Años de Soledad (Edición Ilustrada)',
      );
      // No debe contener autor_ids ni categoria_ids si no se cambiaron
      expect((payload as Record<string, unknown>)['autor_ids']).toBeUndefined();
      expect((payload as Record<string, unknown>)['categoria_ids']).toBeUndefined();
    });

    it('debe enviar autor_ids en PATCH diferencial solo si las asociaciones cambiaron', () => {
      crearComponente({ modo: 'edicion', libro: LIBRO_EXISTENTE });

      let payload: GuardarPayload | undefined;
      component.guardar.subscribe((p) => (payload = p));

      // Añadimos autor 2
      component.agregarAutor(2);
      component.onSubmit();

      expect(payload).toBeDefined();
      expect((payload as Record<string, unknown>)['autor_ids']).toEqual([1, 2]);
      // Categorías no cambiaron -> omitida
      expect((payload as Record<string, unknown>)['categoria_ids']).toBeUndefined();
    });
  });
});
