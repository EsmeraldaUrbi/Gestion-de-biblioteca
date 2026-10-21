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
  ActualizarAutorRequest,
  AutorAdministrativo,
  AutoresPaginados,
  ModificarAutorRequest,
  RegistrarAutorRequest,
} from '../models/autores.models';
import { AutoresService } from './autores.service';

describe('AutoresService', () => {
  let service: AutoresService;
  let httpTesting: HttpTestingController;

  const mockAutor: AutorAdministrativo = {
    autor_id: 1,
    nombre: 'Gabriel García Márquez',
    nacionalidad: 'Colombiana',
    fecha_nacimiento: '1927-03-06',
    cantidad_libros: 2,
  };

  const mockPaginados: AutoresPaginados = {
    count: 1,
    next: null,
    previous: null,
    results: [mockAutor],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        AutoresService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(AutoresService);
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

  it('listar(): debe hacer GET a /api/autores/ sin parámetros si no se pasan filtros', () => {
    service.listar().subscribe((res) => {
      expect(res).toEqual(mockPaginados);
      expect(res.results.length).toBe(1);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.keys().length).toBe(0);
    req.flush(mockPaginados);
  });

  it('listar(): debe filtrar por nombre recortado', () => {
    service.listar({ nombre: '  garcia  ' }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/autores/` &&
        r.params.get('nombre') === 'garcia',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): debe admitir search como alias de nombre', () => {
    service.listar({ search: 'allende' }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/autores/` &&
        r.params.get('nombre') === 'allende',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): no debe enviar nombre si es solo espacios', () => {
    service.listar({ nombre: '   ' }).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/`);
    expect(req.request.params.has('nombre')).toBe(false);
    req.flush(mockPaginados);
  });

  it('listar(): debe filtrar por nacionalidad recortada', () => {
    service.listar({ nacionalidad: '  Colombiana  ' }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/autores/` &&
        r.params.get('nacionalidad') === 'Colombiana',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): no debe enviar nacionalidad si es solo espacios', () => {
    service.listar({ nacionalidad: '   ' }).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/`);
    expect(req.request.params.has('nacionalidad')).toBe(false);
    req.flush(mockPaginados);
  });

  it('listar(): debe enviar page y page_size', () => {
    service.listar({ page: 2, page_size: 25 }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/autores/` &&
        r.params.get('page') === '2' &&
        r.params.get('page_size') === '25',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): debe combinar múltiples filtros simultáneamente', () => {
    service
      .listar({
        nombre: 'garcia',
        nacionalidad: 'mexicana',
        page: 3,
        page_size: 50,
      })
      .subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/autores/` &&
        r.params.get('nombre') === 'garcia' &&
        r.params.get('nacionalidad') === 'mexicana' &&
        r.params.get('page') === '3' &&
        r.params.get('page_size') === '50',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  // -------------------------------------------------------------------------
  // obtenerPorId() y obtener()
  // -------------------------------------------------------------------------

  it('obtenerPorId(): debe hacer GET a /api/autores/{id}/ con URL y método correcto', () => {
    service.obtenerPorId(1).subscribe((autor) => {
      expect(autor.autor_id).toBe(1);
      expect(autor.nombre).toBe('Gabriel García Márquez');
      expect(autor.cantidad_libros).toBe(2);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/1/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockAutor);
  });

  it('obtener(): alias debe retornar el mismo autor que obtenerPorId', () => {
    service.obtener(42).subscribe((autor) => {
      expect(autor.autor_id).toBe(1);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/42/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockAutor);
  });

  // -------------------------------------------------------------------------
  // registrar() - POST
  // -------------------------------------------------------------------------

  it('registrar(): debe hacer POST a /api/autores/ con cuerpo completo', () => {
    const solicitud: RegistrarAutorRequest = {
      nombre: 'Gabriel García Márquez',
      nacionalidad: 'Colombiana',
      fecha_nacimiento: '1927-03-06',
    };

    service.registrar(solicitud).subscribe((autor) => {
      expect(autor.autor_id).toBe(1);
      expect(autor.nombre).toBe('Gabriel García Márquez');
      expect(autor.cantidad_libros).toBe(0);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(solicitud);
    req.flush({ ...mockAutor, cantidad_libros: 0 }, { status: 201, statusText: 'Created' });
  });

  it('registrar(): debe hacer POST solo con nombre cuando campos opcionales son omitidos', () => {
    const solicitud: RegistrarAutorRequest = {
      nombre: 'Isabel Allende',
    };

    service.registrar(solicitud).subscribe((autor) => {
      expect(autor.nombre).toBe('Isabel Allende');
      expect(autor.nacionalidad).toBeNull();
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(solicitud);
    req.flush(
      { autor_id: 2, nombre: 'Isabel Allende', nacionalidad: null, fecha_nacimiento: null, cantidad_libros: 0 },
      { status: 201, statusText: 'Created' },
    );
  });

  it('registrar(): debe admitir nacionalidad y fecha_nacimiento explícitamente en null', () => {
    const solicitud: RegistrarAutorRequest = {
      nombre: 'Autor Anónimo',
      nacionalidad: null,
      fecha_nacimiento: null,
    };

    service.registrar(solicitud).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.nacionalidad).toBeNull();
    expect(req.request.body.fecha_nacimiento).toBeNull();
    req.flush({ ...mockAutor, autor_id: 3 }, { status: 201, statusText: 'Created' });
  });

  // -------------------------------------------------------------------------
  // modificar() - PATCH
  // -------------------------------------------------------------------------

  it('modificar(): debe hacer PATCH a /api/autores/{id}/ con modificación parcial', () => {
    const cambio: ModificarAutorRequest = {
      nombre: 'Gabriel José García Márquez',
    };

    service.modificar(1, cambio).subscribe((autor) => {
      expect(autor.nombre).toBe('Gabriel José García Márquez');
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/1/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual(cambio);
    req.flush({ ...mockAutor, nombre: 'Gabriel José García Márquez' });
  });

  it('modificar(): puede actualizar exclusivamente la nacionalidad', () => {
    const cambio: ModificarAutorRequest = {
      nacionalidad: 'Latinoamericana',
    };

    service.modificar(1, cambio).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/1/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual(cambio);
    req.flush(mockAutor);
  });

  // -------------------------------------------------------------------------
  // actualizar() - PUT
  // -------------------------------------------------------------------------

  it('actualizar(): debe hacer PUT a /api/autores/{id}/ con reemplazo integral', () => {
    const datosPut: ActualizarAutorRequest = {
      nombre: 'Gabriel García Márquez',
      nacionalidad: null,
      fecha_nacimiento: null,
    };

    service.actualizar(1, datosPut).subscribe((autor) => {
      expect(autor.nacionalidad).toBeNull();
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/1/`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual(datosPut);
    req.flush({ ...mockAutor, nacionalidad: null, fecha_nacimiento: null });
  });

  it('PUT y PATCH difieren en el método HTTP aunque compartan URL', () => {
    const patchData: ModificarAutorRequest = { nombre: 'Nombre Parcial' };
    const putData: ActualizarAutorRequest = { nombre: 'Nombre Completo' };

    service.modificar(10, patchData).subscribe();
    service.actualizar(10, putData).subscribe();

    const reqPatch = httpTesting.expectOne(
      (r) => r.url === `${API_BASE_URL}/autores/10/` && r.method === 'PATCH',
    );
    const reqPut = httpTesting.expectOne(
      (r) => r.url === `${API_BASE_URL}/autores/10/` && r.method === 'PUT',
    );

    expect(reqPatch.request.method).toBe('PATCH');
    expect(reqPut.request.method).toBe('PUT');

    reqPatch.flush(mockAutor);
    reqPut.flush(mockAutor);
  });

  // -------------------------------------------------------------------------
  // Propagación de errores HTTP
  // -------------------------------------------------------------------------

  it('debe propagar errores HTTP 400 (validación) sin alterarlos', () => {
    const errorBody = { error: 'El nombre del autor no puede estar vacío.' };

    service.registrar({ nombre: '' }).subscribe({
      next: () => expect.unreachable('No debió resolverse'),
      error: (err) => {
        expect(err.status).toBe(400);
        expect(err.error).toEqual(errorBody);
      },
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/`);
    req.flush(errorBody, { status: 400, statusText: 'Bad Request' });
  });

  it('debe propagar errores HTTP 404 (no encontrado) al consultar por id inexistente', () => {
    service.obtenerPorId(999).subscribe({
      next: () => expect.unreachable('No debió resolverse'),
      error: (err) => {
        expect(err.status).toBe(404);
      },
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/999/`);
    req.flush({ error: 'Autor no encontrado.' }, { status: 404, statusText: 'Not Found' });
  });
});

describe('AutoresService - Compatibilidad con authInterceptor', () => {
  let service: AutoresService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        AutoresService,
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

    service = TestBed.inject(AutoresService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('debe incluir cabecera Authorization con token de sesión en peticiones a /api/autores/', () => {
    service.listar().subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/autores/`);
    expect(req.request.headers.get('Authorization')).toBe('Bearer token-prueba-bibliotecario');
    req.flush({ count: 0, next: null, previous: null, results: [] });
  });
});
