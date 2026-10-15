import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { API_BASE_URL } from '../../../core/config/api.config';
import {
  CatalogoOpciones,
  CatalogoResponse,
  LibroCatalogo,
} from '../models/catalogo.models';
import { CatalogoService } from './catalogo.service';

describe('CatalogoService', () => {
  let service: CatalogoService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        CatalogoService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(CatalogoService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('debe crearse correctamente', () => {
    expect(service).toBeTruthy();
  });

  it('debe listar libros sin filtros adicionales', () => {
    const mockResponse: CatalogoResponse = {
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          libro_id: 1,
          titulo: 'Clean Code',
          isbn: '9780132350884',
          fecha_publicacion: '2008-08-01',
          autores: [{ autor_id: 1, nombre: 'Robert C. Martin' }],
          categorias: [{ categoria_id: 1, nombre_categoria: 'Software' }],
          stock_total: 2,
          stock_disponible: 1,
        },
      ],
    };

    service.listar().subscribe((resp) => {
      expect(resp.count).toBe(1);
      expect(resp.results.length).toBe(1);
      expect(resp.results[0].titulo).toBe('Clean Code');
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/catalogo/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });

  it('debe enviar parámetros de consulta correctamente al listar con filtros', () => {
    service
      .listar({
        titulo: 'clean',
        autor: 1,
        categoria: 2,
        disponible: true,
        page: 2,
        page_size: 10,
      })
      .subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/catalogo/` &&
        r.params.get('titulo') === 'clean' &&
        r.params.get('autor') === '1' &&
        r.params.get('categoria') === '2' &&
        r.params.get('disponible') === 'true' &&
        r.params.get('page') === '2' &&
        r.params.get('page_size') === '10',
    );
    expect(req.request.method).toBe('GET');
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });

  it('debe obtener las opciones de filtros', () => {
    const mockOpciones: CatalogoOpciones = {
      autores: [{ autor_id: 1, nombre: 'Ana' }],
      categorias: [{ categoria_id: 1, nombre_categoria: 'Ficción' }],
    };

    service.obtenerFiltros().subscribe((opciones) => {
      expect(opciones.autores.length).toBe(1);
      expect(opciones.categorias.length).toBe(1);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/catalogo/filtros/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockOpciones);
  });

  it('debe obtener el detalle de un libro por ID', () => {
    const mockLibro: LibroCatalogo = {
      libro_id: 10,
      titulo: 'Arquitectura Limpia',
      isbn: '9780134494166',
      fecha_publicacion: '2017-09-20',
      autores: [{ autor_id: 1, nombre: 'Robert C. Martin' }],
      categorias: [{ categoria_id: 1, nombre_categoria: 'Software' }],
      stock_total: 5,
      stock_disponible: 3,
    };

    service.obtenerDetalle(10).subscribe((libro) => {
      expect(libro.libro_id).toBe(10);
      expect(libro.titulo).toBe('Arquitectura Limpia');
      expect(libro.stock_disponible).toBe(3);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/catalogo/10/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockLibro);
  });
});
