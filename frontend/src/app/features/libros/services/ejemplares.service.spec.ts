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
  CambiarEstadoEjemplarRequest,
  Ejemplar,
  EjemplaresPaginados,
  RegistrarEjemplarRequest,
} from '../models/libros.models';
import { EjemplaresService } from './ejemplares.service';

describe('EjemplaresService', () => {
  let service: EjemplaresService;
  let httpTesting: HttpTestingController;

  const mockEjemplar: Ejemplar = {
    ejemplar_id: 1,
    libro_id: 1,
    libro: {
      libro_id: 1,
      titulo: 'Cien Años de Soledad',
      isbn: '9780307474728',
    },
    codigo_inventario: 'CAS-001',
    estado: 'ACTIVO',
  };

  const mockPaginados: EjemplaresPaginados = {
    count: 2,
    next: null,
    previous: null,
    results: [
      mockEjemplar,
      {
        ejemplar_id: 2,
        libro_id: 1,
        libro: {
          libro_id: 1,
          titulo: 'Cien Años de Soledad',
          isbn: '9780307474728',
        },
        codigo_inventario: 'CAS-002',
        estado: 'MANTENIMIENTO',
      },
    ],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        EjemplaresService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(EjemplaresService);
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

  it('listar(): debe hacer GET a /api/ejemplares/ sin parámetros si no se pasan filtros', () => {
    service.listar().subscribe((res) => {
      expect(res).toEqual(mockPaginados);
      expect(res.results.length).toBe(2);
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/ejemplares/`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.keys().length).toBe(0);
    req.flush(mockPaginados);
  });

  it('listar(): debe filtrar por libro_id', () => {
    service.listar({ libro_id: 1 }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/ejemplares/` &&
        r.params.get('libro_id') === '1',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): debe filtrar por estado ACTIVO', () => {
    service.listar({ estado: 'ACTIVO' }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/ejemplares/` &&
        r.params.get('estado') === 'ACTIVO',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): debe filtrar por estado MANTENIMIENTO', () => {
    service.listar({ estado: 'MANTENIMIENTO' }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/ejemplares/` &&
        r.params.get('estado') === 'MANTENIMIENTO',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): debe filtrar por estado BAJA', () => {
    service.listar({ estado: 'BAJA' }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/ejemplares/` &&
        r.params.get('estado') === 'BAJA',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): debe filtrar por codigo_inventario recortado', () => {
    service.listar({ codigo_inventario: '  CAS-001  ' }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/ejemplares/` &&
        r.params.get('codigo_inventario') === 'CAS-001',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): no debe enviar codigo_inventario si la cadena es solo espacios', () => {
    service.listar({ codigo_inventario: '   ' }).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/ejemplares/`);
    expect(req.request.params.has('codigo_inventario')).toBe(false);
    req.flush(mockPaginados);
  });

  it('listar(): debe enviar page y page_size para paginación', () => {
    service.listar({ page: 2, page_size: 10 }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/ejemplares/` &&
        r.params.get('page') === '2' &&
        r.params.get('page_size') === '10',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  it('listar(): debe combinar libro_id, estado y paginación', () => {
    service.listar({ libro_id: 5, estado: 'ACTIVO', page: 1, page_size: 10 }).subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/ejemplares/` &&
        r.params.get('libro_id') === '5' &&
        r.params.get('estado') === 'ACTIVO' &&
        r.params.get('page') === '1' &&
        r.params.get('page_size') === '10',
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockPaginados);
  });

  // -------------------------------------------------------------------------
  // obtener()
  // -------------------------------------------------------------------------

  it('obtener(): debe hacer GET a /api/ejemplares/{id}/', () => {
    service.obtener(1).subscribe((ej) => {
      expect(ej.ejemplar_id).toBe(1);
      expect(ej.codigo_inventario).toBe('CAS-001');
      expect(ej.estado).toBe('ACTIVO');
      expect(ej.libro.titulo).toBe('Cien Años de Soledad');
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/ejemplares/1/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockEjemplar);
  });

  it('obtener(): debe construir la URL con el ID correcto', () => {
    service.obtener(99).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/ejemplares/99/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockEjemplar);
  });

  // -------------------------------------------------------------------------
  // registrar()
  // -------------------------------------------------------------------------

  it('registrar(): debe hacer POST a /api/ejemplares/ con libro_id y codigo_inventario', () => {
    const solicitud: RegistrarEjemplarRequest = {
      libro_id: 1,
      codigo_inventario: 'CAS-003',
    };

    const respuesta: Ejemplar = {
      ...mockEjemplar,
      ejemplar_id: 3,
      codigo_inventario: 'CAS-003',
      estado: 'ACTIVO',
    };

    service.registrar(solicitud).subscribe((ej) => {
      expect(ej.ejemplar_id).toBe(3);
      expect(ej.codigo_inventario).toBe('CAS-003');
      expect(ej.estado).toBe('ACTIVO');
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/ejemplares/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(solicitud);
    req.flush(respuesta, { status: 201, statusText: 'Created' });
  });

  it('registrar(): puede enviar estado explícito al crear', () => {
    const solicitud: RegistrarEjemplarRequest = {
      libro_id: 1,
      codigo_inventario: 'CAS-004',
      estado: 'MANTENIMIENTO',
    };

    service.registrar(solicitud).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/ejemplares/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.estado).toBe('MANTENIMIENTO');
    req.flush(
      { ...mockEjemplar, ejemplar_id: 4, codigo_inventario: 'CAS-004', estado: 'MANTENIMIENTO' },
      { status: 201, statusText: 'Created' },
    );
  });

  it('registrar(): no debe enviar estado si se omite (backend asigna ACTIVO)', () => {
    const solicitud: RegistrarEjemplarRequest = {
      libro_id: 1,
      codigo_inventario: 'CAS-005',
    };

    service.registrar(solicitud).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/ejemplares/`);
    expect(req.request.body.estado).toBeUndefined();
    req.flush({ ...mockEjemplar, ejemplar_id: 5 }, { status: 201, statusText: 'Created' });
  });

  // -------------------------------------------------------------------------
  // cambiarEstado() - PATCH exclusivo de estado
  // -------------------------------------------------------------------------

  it('cambiarEstado(): debe hacer PATCH a /api/ejemplares/{id}/ con solo el campo estado', () => {
    const cambio: CambiarEstadoEjemplarRequest = { estado: 'MANTENIMIENTO' };

    service.cambiarEstado(1, cambio).subscribe((ej) => {
      expect(ej.estado).toBe('MANTENIMIENTO');
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/ejemplares/1/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ estado: 'MANTENIMIENTO' });
    expect(Object.keys(req.request.body as object).length).toBe(1);
    req.flush({ ...mockEjemplar, estado: 'MANTENIMIENTO' });
  });

  it('cambiarEstado(): debe permitir pasar a BAJA (baja lógica, RN-04)', () => {
    const cambio: CambiarEstadoEjemplarRequest = { estado: 'BAJA' };

    service.cambiarEstado(1, cambio).subscribe((ej) => {
      expect(ej.estado).toBe('BAJA');
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/ejemplares/1/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ estado: 'BAJA' });
    req.flush({ ...mockEjemplar, estado: 'BAJA' });
  });

  it('cambiarEstado(): debe permitir reactivar a ACTIVO', () => {
    const cambio: CambiarEstadoEjemplarRequest = { estado: 'ACTIVO' };

    service.cambiarEstado(2, cambio).subscribe((ej) => {
      expect(ej.estado).toBe('ACTIVO');
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/ejemplares/2/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ estado: 'ACTIVO' });
    req.flush({ ...mockEjemplar, ejemplar_id: 2, estado: 'ACTIVO' });
  });

  it('cambiarEstado(): el cuerpo enviado contiene ÚNICAMENTE el campo estado', () => {
    const cambio: CambiarEstadoEjemplarRequest = { estado: 'BAJA' };

    service.cambiarEstado(3, cambio).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/ejemplares/3/`);
    const body = req.request.body as Record<string, unknown>;
    // Verificar que no se envían campos prohibidos como codigo_inventario o libro_id
    expect(body['codigo_inventario']).toBeUndefined();
    expect(body['libro_id']).toBeUndefined();
    expect(Object.keys(body).length).toBe(1);
    req.flush({ ...mockEjemplar, estado: 'BAJA' });
  });

  it('cambiarEstado(): debe construir la URL con el ID correcto', () => {
    service.cambiarEstado(77, { estado: 'MANTENIMIENTO' }).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/ejemplares/77/`);
    expect(req.request.method).toBe('PATCH');
    req.flush({ ...mockEjemplar, ejemplar_id: 77, estado: 'MANTENIMIENTO' });
  });
});
