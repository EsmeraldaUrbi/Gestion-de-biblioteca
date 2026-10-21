import {
  provideHttpClient,
  withInterceptors,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { authInterceptor } from '../../../core/auth/interceptors/auth.interceptor';
import { AuthSessionService } from '../../../core/auth/services/auth-session.service';
import { API_BASE_URL } from '../../../core/config/api.config';
import {
  ActualizarCategoriaRequest,
  CategoriaAdministrativa,
  CategoriasPaginadas,
  ModificarCategoriaRequest,
  RegistrarCategoriaRequest,
} from '../models/categorias.models';
import { CategoriasService } from './categorias.service';

describe('CategoriasService', () => {
  let service: CategoriasService;
  let httpTesting: HttpTestingController;

  const mockCategoria: CategoriaAdministrativa = {
    categoria_id: 1,
    nombre_categoria: 'Realismo Mágico',
    cantidad_libros: 3,
  };

  const mockPaginadas: CategoriasPaginadas = {
    count: 1,
    next: null,
    previous: null,
    results: [mockCategoria],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        CategoriasService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(CategoriasService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('debe crearse correctamente', () => {
    expect(service).toBeTruthy();
  });

  // -------------------------------------------------------------------------
  // listar()
  // -------------------------------------------------------------------------

  it('listar(): debe hacer GET a /api/categorias/ sin parámetros si no se pasan filtros', () => {
    service.listar().subscribe((res) => {
      expect(res).toEqual(mockPaginadas);
      expect(res.results.length).toBe(1);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/categorias/`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.keys().length).toBe(0);
    req.flush(mockPaginadas);
  });

  it('listar(): debe filtrar por nombre recortado', () => {
    service.listar({ nombre: '  realismo  ' }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/categorias/` &&
        r.params.get('nombre') === 'realismo',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginadas);
  });

  it('listar(): debe admitir search como alias de nombre', () => {
    service.listar({ search: 'ciencia' }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/categorias/` &&
        r.params.get('nombre') === 'ciencia',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginadas);
  });

  it('listar(): no debe enviar nombre si es solo espacios', () => {
    service.listar({ nombre: '   ' }).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/categorias/`);
    expect(req.request.params.has('nombre')).toBe(false);
    req.flush(mockPaginadas);
  });

  it('listar(): debe enviar page y page_size', () => {
    service.listar({ page: 2, page_size: 20 }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/categorias/` &&
        r.params.get('page') === '2' &&
        r.params.get('page_size') === '20',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginadas);
  });

  // -------------------------------------------------------------------------
  // obtenerPorId() y obtener()
  // -------------------------------------------------------------------------

  it('obtenerPorId(): debe hacer GET a /api/categorias/{id}/ con URL y método correcto', () => {
    service.obtenerPorId(1).subscribe((cat) => {
      expect(cat.categoria_id).toBe(1);
      expect(cat.nombre_categoria).toBe('Realismo Mágico');
      expect(cat.cantidad_libros).toBe(3);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/categorias/1/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockCategoria);
  });

  it('obtener(): alias debe retornar la misma categoría que obtenerPorId', () => {
    service.obtener(99).subscribe((cat) => {
      expect(cat.categoria_id).toBe(1);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/categorias/99/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockCategoria);
  });

  // -------------------------------------------------------------------------
  // registrar() - POST
  // -------------------------------------------------------------------------

  it('registrar(): debe hacer POST a /api/categorias/ con nombre_categoria', () => {
    const solicitud: RegistrarCategoriaRequest = {
      nombre_categoria: 'Ciencia Ficción',
    };

    service.registrar(solicitud).subscribe((cat) => {
      expect(cat.categoria_id).toBe(2);
      expect(cat.nombre_categoria).toBe('Ciencia Ficción');
      expect(cat.cantidad_libros).toBe(0);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/categorias/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(solicitud);
    req.flush(
      { categoria_id: 2, nombre_categoria: 'Ciencia Ficción', cantidad_libros: 0 },
      { status: 201, statusText: 'Created' },
    );
  });

  // -------------------------------------------------------------------------
  // modificar() - PATCH
  // -------------------------------------------------------------------------

  it('modificar(): debe hacer PATCH a /api/categorias/{id}/ con datos parciales', () => {
    const cambio: ModificarCategoriaRequest = {
      nombre_categoria: 'Ficción Especulativa',
    };

    service.modificar(1, cambio).subscribe((cat) => {
      expect(cat.nombre_categoria).toBe('Ficción Especulativa');
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/categorias/1/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual(cambio);
    req.flush({ ...mockCategoria, nombre_categoria: 'Ficción Especulativa' });
  });

  // -------------------------------------------------------------------------
  // actualizar() - PUT
  // -------------------------------------------------------------------------

  it('actualizar(): debe hacer PUT a /api/categorias/{id}/ con datos completos', () => {
    const datosPut: ActualizarCategoriaRequest = {
      nombre_categoria: 'Novela Histórica',
    };

    service.actualizar(1, datosPut).subscribe((cat) => {
      expect(cat.nombre_categoria).toBe('Novela Histórica');
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/categorias/1/`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual(datosPut);
    req.flush({ ...mockCategoria, nombre_categoria: 'Novela Histórica' });
  });

  it('PUT y PATCH difieren en el método HTTP aunque compartan URL', () => {
    const patchData: ModificarCategoriaRequest = { nombre_categoria: 'Cat Patch' };
    const putData: ActualizarCategoriaRequest = { nombre_categoria: 'Cat Put' };

    service.modificar(5, patchData).subscribe();
    service.actualizar(5, putData).subscribe();

    const reqPatch = httpTesting.expectOne(
      (r) => r.url === `${API_BASE_URL}/categorias/5/` && r.method === 'PATCH',
    );
    const reqPut = httpTesting.expectOne(
      (r) => r.url === `${API_BASE_URL}/categorias/5/` && r.method === 'PUT',
    );

    expect(reqPatch.request.method).toBe('PATCH');
    expect(reqPut.request.method).toBe('PUT');

    reqPatch.flush(mockCategoria);
    reqPut.flush(mockCategoria);
  });

  // -------------------------------------------------------------------------
  // Propagación de errores HTTP
  // -------------------------------------------------------------------------

  it('debe propagar errores HTTP 400 por duplicidad sin enmascararlos ni transformarlos', () => {
    const errorBody = {
      error: 'Ya existe una categoría con el nombre "Realismo Mágico".',
    };

    service.registrar({ nombre_categoria: 'Realismo Mágico' }).subscribe({
      next: () => expect.unreachable('No debió resolverse'),
      error: (err) => {
        expect(err.status).toBe(400);
        expect(err.error).toEqual(errorBody);
      },
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/categorias/`);
    req.flush(errorBody, { status: 400, statusText: 'Bad Request' });
  });

  it('debe propagar otros errores HTTP (404, 500) transparentemente sin asumir duplicidad', () => {
    service.obtenerPorId(999).subscribe({
      next: () => expect.unreachable('No debió resolverse'),
      error: (err) => {
        expect(err.status).toBe(404);
      },
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/categorias/999/`);
    req.flush({ error: 'Categoría no encontrada.' }, { status: 404, statusText: 'Not Found' });
  });
});

describe('CategoriasService - Compatibilidad con authInterceptor', () => {
  let service: CategoriasService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        CategoriasService,
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        {
          provide: AuthSessionService,
          useValue: {
            token: signal('token-prueba-bibliotecario'),
            hasSession: () => true,
          },
        },
      ],
    });

    service = TestBed.inject(CategoriasService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('debe incluir cabecera Authorization con token de sesión en peticiones a /api/categorias/', () => {
    service.listar().subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/categorias/`);
    expect(req.request.headers.get('Authorization')).toBe('Bearer token-prueba-bibliotecario');
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });
});
