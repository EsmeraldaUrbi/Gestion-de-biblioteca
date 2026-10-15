import {
  provideHttpClient,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { API_BASE_URL } from '../../../core/config/api.config';
import {
  ActualizarLibroRequest,
  Libro,
  LibrosPaginados,
  ModificarLibroRequest,
  RegistrarLibroRequest,
} from '../models/libros.models';
import { LibrosService } from './libros.service';

describe('LibrosService', () => {
  let service: LibrosService;
  let httpTesting: HttpTestingController;

  const mockLibro: Libro = {
    libro_id: 1,
    titulo: 'Cien Años de Soledad',
    isbn: '9780307474728',
    fecha_publicacion: '1967-05-30',
    autores: [{ autor_id: 1, nombre: 'Gabriel García Márquez' }],
    categorias: [{ categoria_id: 1, nombre_categoria: 'Realismo Mágico' }],
  };

  const mockPaginados: LibrosPaginados = {
    count: 1,
    next: null,
    previous: null,
    results: [mockLibro],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        LibrosService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(LibrosService);
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

  it('listar(): debe hacer GET a /api/libros/ sin parámetros si no se pasan filtros', () => {
    service.listar().subscribe((res) => {
      expect(res).toEqual(mockPaginados);
      expect(res.results.length).toBe(1);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/libros/`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.keys().length).toBe(0);
    req.flush(mockPaginados);
  });

  it('listar(): debe filtrar por titulo recortado', () => {
    service.listar({ titulo: '  soledad  ' }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/libros/` &&
        r.params.get('titulo') === 'soledad',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): debe filtrar por isbn recortado', () => {
    service.listar({ isbn: '  9780307474728  ' }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/libros/` &&
        r.params.get('isbn') === '9780307474728',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): debe filtrar por autor_id', () => {
    service.listar({ autor_id: 1 }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/libros/` &&
        r.params.get('autor_id') === '1',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): debe filtrar por categoria_id', () => {
    service.listar({ categoria_id: 2 }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/libros/` &&
        r.params.get('categoria_id') === '2',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): debe enviar page y page_size', () => {
    service.listar({ page: 2, page_size: 20 }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/libros/` &&
        r.params.get('page') === '2' &&
        r.params.get('page_size') === '20',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): debe combinar múltiples filtros simultáneamente', () => {
    service
      .listar({
        titulo: 'quijote',
        isbn: '978',
        autor_id: 1,
        categoria_id: 1,
        page: 3,
        page_size: 50,
      })
      .subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/libros/` &&
        r.params.get('titulo') === 'quijote' &&
        r.params.get('isbn') === '978' &&
        r.params.get('autor_id') === '1' &&
        r.params.get('categoria_id') === '1' &&
        r.params.get('page') === '3' &&
        r.params.get('page_size') === '50',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): no debe enviar título si la cadena es solo espacios', () => {
    service.listar({ titulo: '   ' }).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/libros/`);
    expect(req.request.params.has('titulo')).toBe(false);
    req.flush(mockPaginados);
  });

  it('listar(): no debe enviar isbn si la cadena es solo espacios', () => {
    service.listar({ isbn: '   ' }).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/libros/`);
    expect(req.request.params.has('isbn')).toBe(false);
    req.flush(mockPaginados);
  });

  // -------------------------------------------------------------------------
  // obtener()
  // -------------------------------------------------------------------------

  it('obtener(): debe hacer GET a /api/libros/{id}/', () => {
    service.obtener(1).subscribe((libro) => {
      expect(libro.libro_id).toBe(1);
      expect(libro.titulo).toBe('Cien Años de Soledad');
      expect(libro.autores.length).toBe(1);
      expect(libro.categorias.length).toBe(1);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/libros/1/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockLibro);
  });

  it('obtener(): debe construir la URL con el ID correcto', () => {
    service.obtener(42).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/libros/42/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockLibro);
  });

  // -------------------------------------------------------------------------
  // registrar()
  // -------------------------------------------------------------------------

  it('registrar(): debe hacer POST a /api/libros/ con todos los campos', () => {
    const solicitud: RegistrarLibroRequest = {
      titulo: 'Don Quijote de la Mancha',
      isbn: '9788424116286',
      fecha_publicacion: '1605-01-16',
      autor_ids: [1],
      categoria_ids: [2],
    };

    const respuesta: Libro = {
      libro_id: 2,
      titulo: 'Don Quijote de la Mancha',
      isbn: '9788424116286',
      fecha_publicacion: '1605-01-16',
      autores: [{ autor_id: 1, nombre: 'Miguel de Cervantes' }],
      categorias: [{ categoria_id: 2, nombre_categoria: 'Novela Clásica' }],
    };

    service.registrar(solicitud).subscribe((libro) => {
      expect(libro.libro_id).toBe(2);
      expect(libro.titulo).toBe('Don Quijote de la Mancha');
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/libros/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(solicitud);
    req.flush(respuesta, { status: 201, statusText: 'Created' });
  });

  it('registrar(): debe funcionar sin autor_ids ni categoria_ids', () => {
    const solicitud: RegistrarLibroRequest = {
      titulo: 'Libro sin asociaciones',
      isbn: '9781234567890',
    };

    service.registrar(solicitud).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/libros/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.autor_ids).toBeUndefined();
    expect(req.request.body.categoria_ids).toBeUndefined();
    req.flush({ ...mockLibro, libro_id: 3 }, { status: 201, statusText: 'Created' });
  });

  it('registrar(): debe admitir fecha_publicacion null', () => {
    const solicitud: RegistrarLibroRequest = {
      titulo: 'Libro sin fecha',
      isbn: '9780000000001',
      fecha_publicacion: null,
    };

    service.registrar(solicitud).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/libros/`);
    expect(req.request.body.fecha_publicacion).toBeNull();
    req.flush({ ...mockLibro, libro_id: 4 }, { status: 201, statusText: 'Created' });
  });

  // -------------------------------------------------------------------------
  // modificarParcial() - PATCH
  // -------------------------------------------------------------------------

  it('modificarParcial(): debe hacer PATCH a /api/libros/{id}/', () => {
    const cambio: ModificarLibroRequest = {
      titulo: 'Cien Años de Soledad (Edición Conmemorativa)',
    };

    service.modificarParcial(1, cambio).subscribe((libro) => {
      expect(libro.isbn).toBe('9780307474728');
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/libros/1/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual(cambio);
    req.flush(mockLibro);
  });

  it('modificarParcial(): puede reemplazar solo los autor_ids', () => {
    const cambio: ModificarLibroRequest = { autor_ids: [2] };

    service.modificarParcial(1, cambio).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/libros/1/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ autor_ids: [2] });
    req.flush(mockLibro);
  });

  it('modificarParcial(): puede reemplazar solo las categoria_ids', () => {
    const cambio: ModificarLibroRequest = { categoria_ids: [3, 4] };

    service.modificarParcial(1, cambio).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/libros/1/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ categoria_ids: [3, 4] });
    req.flush(mockLibro);
  });

  // -------------------------------------------------------------------------
  // actualizarCompleto() - PUT
  // -------------------------------------------------------------------------

  it('actualizarCompleto(): debe hacer PUT a /api/libros/{id}/ con campos obligatorios', () => {
    const solicitud: ActualizarLibroRequest = {
      titulo: 'Cien Años de Soledad (Edición Conmemorativa)',
      isbn: '9780307474728',
      fecha_publicacion: '2007-03-01',
      autor_ids: [1],
      categoria_ids: [1, 2],
    };

    service.actualizarCompleto(1, solicitud).subscribe((libro) => {
      expect(libro.libro_id).toBe(1);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/libros/1/`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body).toEqual(solicitud);
    req.flush(mockLibro);
  });

  it('actualizarCompleto(): la omisión de autor_ids es válida (vacía asociaciones en backend)', () => {
    const solicitud: ActualizarLibroRequest = {
      titulo: 'Libro sin autores',
      isbn: '9780307474728',
    };

    service.actualizarCompleto(1, solicitud).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/libros/1/`);
    expect(req.request.method).toBe('PUT');
    expect(req.request.body.autor_ids).toBeUndefined();
    req.flush(mockLibro);
  });

  it('PUT y PATCH difieren en el método HTTP aunque apunten a la misma URL', () => {
    const datosPatch: ModificarLibroRequest = { titulo: 'Nuevo título' };
    const datosPut: ActualizarLibroRequest = { titulo: 'Otro título', isbn: '9780307474728' };

    service.modificarParcial(5, datosPatch).subscribe();
    service.actualizarCompleto(5, datosPut).subscribe();

    const reqPatch = httpTesting.expectOne(
      (r) => r.url === `${API_BASE_URL}/libros/5/` && r.method === 'PATCH',
    );
    const reqPut = httpTesting.expectOne(
      (r) => r.url === `${API_BASE_URL}/libros/5/` && r.method === 'PUT',
    );

    expect(reqPatch.request.method).toBe('PATCH');
    expect(reqPut.request.method).toBe('PUT');

    reqPatch.flush(mockLibro);
    reqPut.flush(mockLibro);
  });
});
