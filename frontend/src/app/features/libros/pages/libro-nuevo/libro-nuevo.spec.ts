import {
  provideHttpClient,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { API_BASE_URL } from '../../../../core/config/api.config';
import { Libro } from '../../models/libros.models';
import { LibroNuevoComponent } from './libro-nuevo';

const MOCK_LIBRO: Libro = {
  libro_id: 2,
  titulo: 'Don Quijote de la Mancha',
  isbn: '9788424116286',
  fecha_publicacion: '1605-01-16',
  autores: [{ autor_id: 1, nombre: 'Miguel de Cervantes' }],
  categorias: [{ categoria_id: 2, nombre_categoria: 'Novela Clásica' }],
};

const MOCK_FILTROS = {
  autores: [{ autor_id: 1, nombre: 'Miguel de Cervantes' }],
  categorias: [{ categoria_id: 2, nombre_categoria: 'Novela Clásica' }],
};

describe('LibroNuevoComponent', () => {
  let fixture: ComponentFixture<LibroNuevoComponent>;
  let component: LibroNuevoComponent;
  let httpTesting: HttpTestingController;
  const catalogoFiltrosUrl = `${API_BASE_URL}/catalogo/filtros/`;
  const librosUrl = `${API_BASE_URL}/libros/`;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LibroNuevoComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: '**', component: class {} }]),
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LibroNuevoComponent);
    component = fixture.componentInstance;
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  // -------------------------------------------------------------------------
  // Carga de opciones
  // -------------------------------------------------------------------------
  describe('carga de opciones del catálogo', () => {
    it('debe estar en estado cargando al iniciar', () => {
      fixture.detectChanges();
      expect(component.cargandoFiltros()).toBe(true);
      httpTesting.expectOne(catalogoFiltrosUrl).flush(MOCK_FILTROS);
    });

    it('debe cargar autores y categorías correctamente', () => {
      fixture.detectChanges();
      httpTesting.expectOne(catalogoFiltrosUrl).flush(MOCK_FILTROS);
      fixture.detectChanges();

      expect(component.autoresDisponibles()).toEqual(MOCK_FILTROS.autores);
      expect(component.categoriasDisponibles()).toEqual(MOCK_FILTROS.categorias);
      expect(component.cargandoFiltros()).toBe(false);
    });

    it('debe establecer error de filtros sin bloquear el formulario', () => {
      fixture.detectChanges();
      httpTesting.expectOne(catalogoFiltrosUrl).error(new ProgressEvent('error'));
      fixture.detectChanges();

      expect(component.errorFiltros()).not.toBeNull();
      expect(component.autoresDisponibles()).toEqual([]);
      expect(component.cargandoFiltros()).toBe(false);
    });

    it('debe reintentar la carga al llamar cargarOpciones()', () => {
      fixture.detectChanges();
      httpTesting.expectOne(catalogoFiltrosUrl).error(new ProgressEvent('error'));
      fixture.detectChanges();

      component.cargarOpciones();
      httpTesting.expectOne(catalogoFiltrosUrl).flush(MOCK_FILTROS);
      fixture.detectChanges();

      expect(component.autoresDisponibles()).toEqual(MOCK_FILTROS.autores);
      expect(component.errorFiltros()).toBeNull();
    });
  });

  // -------------------------------------------------------------------------
  // Registro de libro
  // -------------------------------------------------------------------------
  describe('registrar()', () => {
    beforeEach(() => {
      fixture.detectChanges();
      httpTesting.expectOne(catalogoFiltrosUrl).flush(MOCK_FILTROS);
      fixture.detectChanges();
    });

    it('debe llamar al endpoint POST /api/libros/', () => {
      component.registrar({ titulo: 'Don Quijote', isbn: '9788424116286' });

      const req = httpTesting.expectOne(librosUrl);
      expect(req.request.method).toBe('POST');
      req.flush(MOCK_LIBRO);
    });

    it('debe establecer libroCreado al recibir 201', () => {
      component.registrar({ titulo: 'Don Quijote', isbn: '9788424116286' });
      httpTesting.expectOne(librosUrl).flush(MOCK_LIBRO);
      fixture.detectChanges();

      expect(component.libroCreado()).toEqual(MOCK_LIBRO);
    });

    it('debe limpiar el estado de guardando al completar', () => {
      component.registrar({ titulo: 'Don Quijote', isbn: '9788424116286' });
      expect(component.guardando()).toBe(true);

      httpTesting.expectOne(librosUrl).flush(MOCK_LIBRO);
      fixture.detectChanges();

      expect(component.guardando()).toBe(false);
    });

    it('debe prevenir envíos duplicados mientras guardando es true', () => {
      component.registrar({ titulo: 'Don Quijote', isbn: '9788424116286' });
      expect(component.guardando()).toBe(true);

      // Segundo intento mientras está guardando
      component.registrar({ titulo: 'Don Quijote', isbn: '9788424116286' });

      // Solo debe haber una solicitud pendiente
      httpTesting.expectOne(librosUrl).flush(MOCK_LIBRO);
    });

    it('debe procesar errores 400 del servidor (ISBN duplicado)', () => {
      component.registrar({ titulo: 'Don Quijote', isbn: '9788424116286' });

      httpTesting.expectOne(librosUrl).flush(
        { isbn: ['Ya existe un libro con este ISBN.'] },
        { status: 400, statusText: 'Bad Request' },
      );
      fixture.detectChanges();

      expect(component.erroresServidor()).toEqual({
        isbn: ['Ya existe un libro con este ISBN.'],
      });
      expect(component.errorGeneral()).not.toBeNull();
    });

    it('debe establecer error 401 apropiado', () => {
      component.registrar({ titulo: 'Don Quijote', isbn: '9788424116286' });

      httpTesting.expectOne(librosUrl).flush(
        { detail: 'No autorizado' },
        { status: 401, statusText: 'Unauthorized' },
      );
      fixture.detectChanges();

      expect(component.errorGeneral()).toContain('sesión');
    });

    it('debe establecer error 403 apropiado', () => {
      component.registrar({ titulo: 'Don Quijote', isbn: '9788424116286' });

      httpTesting.expectOne(librosUrl).flush(
        { detail: 'Forbidden' },
        { status: 403, statusText: 'Forbidden' },
      );
      fixture.detectChanges();

      expect(component.errorGeneral()).toContain('permiso');
    });

    it('debe establecer error de red (status 0)', () => {
      component.registrar({ titulo: 'Don Quijote', isbn: '9788424116286' });

      httpTesting.expectOne(librosUrl).error(new ProgressEvent('error'));
      fixture.detectChanges();

      expect(component.errorGeneral()).toContain('servidor');
    });

    it('debe limpiar erroresServidor en un nuevo intento', () => {
      // Primer intento con error
      component.registrar({ titulo: 'Don Quijote', isbn: '9788424116286' });
      httpTesting.expectOne(librosUrl).flush(
        { isbn: ['ISBN duplicado'] },
        { status: 400, statusText: 'Bad Request' },
      );
      fixture.detectChanges();

      expect(Object.keys(component.erroresServidor()).length).toBeGreaterThan(0);

      // Segundo intento limpia los errores
      component.registrar({ titulo: 'Don Quijote', isbn: '9788424116287' });
      // Verificar que erroresServidor se limpió antes de la respuesta
      expect(component.erroresServidor()).toEqual({});
      httpTesting.expectOne(librosUrl).flush(MOCK_LIBRO);
    });
  });
});
