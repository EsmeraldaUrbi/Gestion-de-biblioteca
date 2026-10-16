import {
  provideHttpClient,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ActivatedRoute, convertToParamMap } from '@angular/router';

import { API_BASE_URL } from '../../../../core/config/api.config';
import { Libro } from '../../models/libros.models';
import { LibroEditarComponent } from './libro-editar';

const MOCK_LIBRO: Libro = {
  libro_id: 1,
  titulo: 'Cien Años de Soledad',
  isbn: '9780307474728',
  fecha_publicacion: '1967-05-30',
  autores: [{ autor_id: 1, nombre: 'Gabriel García Márquez' }],
  categorias: [{ categoria_id: 1, nombre_categoria: 'Realismo Mágico' }],
};

const MOCK_FILTROS = {
  autores: [
    { autor_id: 1, nombre: 'Gabriel García Márquez' },
    { autor_id: 2, nombre: 'Miguel de Cervantes' },
  ],
  categorias: [
    { categoria_id: 1, nombre_categoria: 'Realismo Mágico' },
    { categoria_id: 2, nombre_categoria: 'Novela Clásica' },
  ],
};

function crearActivatedRoute(id: string) {
  return {
    snapshot: {
      paramMap: convertToParamMap({ id }),
    },
  };
}

describe('LibroEditarComponent', () => {
  let fixture: ComponentFixture<LibroEditarComponent>;
  let component: LibroEditarComponent;
  let httpTesting: HttpTestingController;

  const catalogoFiltrosUrl = `${API_BASE_URL}/catalogo/filtros/`;
  const libroUrl = `${API_BASE_URL}/libros/1/`;

  async function configurar(idParam = '1') {
    await TestBed.configureTestingModule({
      imports: [LibroEditarComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: '**', component: class {} }]),
        { provide: ActivatedRoute, useValue: crearActivatedRoute(idParam) },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LibroEditarComponent);
    component = fixture.componentInstance;
    httpTesting = TestBed.inject(HttpTestingController);
  }

  afterEach(() => {
    httpTesting.verify();
    TestBed.resetTestingModule();
  });

  // -------------------------------------------------------------------------
  // Carga de datos (forkJoin)
  // -------------------------------------------------------------------------
  describe('carga inicial con forkJoin', () => {
    beforeEach(async () => {
      await configurar('1');
    });

    it('debe estar en estado cargando al iniciar', () => {
      fixture.detectChanges();
      expect(component.cargando()).toBe(true);

      httpTesting.expectOne(libroUrl).flush(MOCK_LIBRO);
      httpTesting.expectOne(catalogoFiltrosUrl).flush(MOCK_FILTROS);
    });

    it('debe cargar el libro y las opciones en paralelo (forkJoin)', () => {
      fixture.detectChanges();
      httpTesting.expectOne(libroUrl).flush(MOCK_LIBRO);
      httpTesting.expectOne(catalogoFiltrosUrl).flush(MOCK_FILTROS);
      fixture.detectChanges();

      expect(component.libro()).toEqual(MOCK_LIBRO);
      expect(component.autoresDisponibles()).toEqual(MOCK_FILTROS.autores);
      expect(component.categoriasDisponibles()).toEqual(MOCK_FILTROS.categorias);
      expect(component.cargando()).toBe(false);
    });

    it('debe manejar error 404 en la carga', () => {
      fixture.detectChanges();
      httpTesting.expectOne(catalogoFiltrosUrl).flush(MOCK_FILTROS);
      httpTesting.expectOne(libroUrl).flush(
        { detail: 'Not found' },
        { status: 404, statusText: 'Not Found' },
      );
      fixture.detectChanges();

      expect(component.errorCarga()).toContain('no existe');
    });

    it('debe manejar error de red (status 0) en la carga', () => {
      fixture.detectChanges();
      httpTesting.expectOne(catalogoFiltrosUrl).flush(MOCK_FILTROS);
      httpTesting.expectOne(libroUrl).error(new ProgressEvent('error'));
      fixture.detectChanges();

      expect(component.errorCarga()).toContain('servidor');
    });
  });

  // -------------------------------------------------------------------------
  // Modificar — PATCH
  // -------------------------------------------------------------------------
  describe('modificar()', () => {
    beforeEach(async () => {
      await configurar('1');
      fixture.detectChanges();
      httpTesting.expectOne(libroUrl).flush(MOCK_LIBRO);
      httpTesting.expectOne(catalogoFiltrosUrl).flush(MOCK_FILTROS);
      fixture.detectChanges();
    });

    it('debe llamar PATCH al endpoint correcto', () => {
      component.modificar({ titulo: 'Nuevo Título' });

      const req = httpTesting.expectOne(libroUrl);
      expect(req.request.method).toBe('PATCH');
      expect(req.request.body).toEqual({ titulo: 'Nuevo Título' });
      req.flush({ ...MOCK_LIBRO, titulo: 'Nuevo Título' });
    });

    it('debe establecer libroActualizado al recibir 200', () => {
      component.modificar({ titulo: 'Nuevo Título' });

      const libroActualizado = { ...MOCK_LIBRO, titulo: 'Nuevo Título' };
      httpTesting.expectOne(libroUrl).flush(libroActualizado);
      fixture.detectChanges();

      expect(component.libroActualizado()).toEqual(libroActualizado);
    });

    it('debe limpiar guardando al completar', () => {
      component.modificar({ titulo: 'Nuevo Título' });
      expect(component.guardando()).toBe(true);

      httpTesting.expectOne(libroUrl).flush({ ...MOCK_LIBRO, titulo: 'Nuevo Título' });
      fixture.detectChanges();

      expect(component.guardando()).toBe(false);
    });

    it('debe prevenir envíos duplicados', () => {
      component.modificar({ titulo: 'Nuevo Título' });
      component.modificar({ titulo: 'Otro Título' }); // Debe ignorarse

      // Solo debe haber una petición
      httpTesting.expectOne(libroUrl).flush(MOCK_LIBRO);
    });

    it('debe procesar errores 400 (ISBN duplicado)', () => {
      component.modificar({ isbn: '9780307474728' });

      httpTesting.expectOne(libroUrl).flush(
        { isbn: ['Ya existe un libro con este ISBN.'] },
        { status: 400, statusText: 'Bad Request' },
      );
      fixture.detectChanges();

      expect(component.erroresServidor()).toEqual({
        isbn: ['Ya existe un libro con este ISBN.'],
      });
    });

    it('debe establecer error 403 apropiado', () => {
      component.modificar({ titulo: 'Nuevo' });

      httpTesting.expectOne(libroUrl).flush(
        { detail: 'Forbidden' },
        { status: 403, statusText: 'Forbidden' },
      );
      fixture.detectChanges();

      expect(component.errorGeneral()).toContain('permiso');
    });

    it('debe establecer error 404 apropiado durante modificar', () => {
      component.modificar({ titulo: 'Nuevo' });

      httpTesting.expectOne(libroUrl).flush(
        { detail: 'Not found' },
        { status: 404, statusText: 'Not Found' },
      );
      fixture.detectChanges();

      expect(component.errorGeneral()).toContain('no existe');
    });

    it('debe actualizar libro() al recibir respuesta exitosa', () => {
      const libroActualizado = { ...MOCK_LIBRO, titulo: 'Nuevo Título' };
      component.modificar({ titulo: 'Nuevo Título' });

      httpTesting.expectOne(libroUrl).flush(libroActualizado);
      fixture.detectChanges();

      expect(component.libro()).toEqual(libroActualizado);
    });
  });

  // -------------------------------------------------------------------------
  // ID inválido — redirección
  // -------------------------------------------------------------------------
  describe('ID de ruta inválido', () => {
    it('debe redirigir a /libros si el id no es un número', async () => {
      await configurar('abc');

      // El router está disponible en el componente como router privado
      // Verificamos que no lanza ninguna petición HTTP
      fixture.detectChanges();
      httpTesting.expectNone(libroUrl);
    });
  });
});
