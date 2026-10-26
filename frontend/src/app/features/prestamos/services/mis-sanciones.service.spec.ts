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
  esCombinacionFiltrosValida,
  RespuestaMisSanciones,
} from '../models/mis-sanciones.models';
import { MisSancionesService } from './mis-sanciones.service';

describe('MisSancionesService', () => {
  let service: MisSancionesService;
  let httpTesting: HttpTestingController;

  const mockRespuestaCompleta: RespuestaMisSanciones = {
    count: 2,
    next: null,
    previous: null,
    results: [
      {
        sancion_id: 14,
        prestamo_id: 28,
        libro: {
          libro_id: 5,
          titulo: 'Estructuras de Datos en Python',
          isbn: '9780000000010',
        },
        ejemplar: {
          ejemplar_id: 11,
          codigo_inventario: 'EDP-01',
        },
        tipo: 'ECONOMICA',
        estado: 'PENDIENTE',
        monto: '25.00',
        fecha_pago: null,
        fecha_inicio_bloqueo: null,
        fecha_fin_bloqueo: null,
      },
      {
        sancion_id: 9,
        prestamo_id: 19,
        libro: {
          libro_id: 3,
          titulo: 'Ingeniería de Software Moderna',
          isbn: '9780000000020',
        },
        ejemplar: {
          ejemplar_id: 8,
          codigo_inventario: 'ISM-01',
        },
        tipo: 'BLOQUEO',
        estado: 'VIGENTE',
        monto: null,
        fecha_pago: null,
        fecha_inicio_bloqueo: '2026-10-15',
        fecha_fin_bloqueo: '2026-11-13',
      },
    ],
    resumen: {
      total_sanciones: 2,
      multas_pendientes: 1,
      monto_total_adeudado: '25.00',
      bloqueos_vigentes: 1,
    },
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        MisSancionesService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(MisSancionesService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('1. debe crearse e inyectarse correctamente', () => {
    expect(service).toBeTruthy();
  });

  it('2. debe realizar GET a /api/sanciones/mias/ sin parámetros cuando no se especifican filtros', () => {
    let respuestaRecibida: RespuestaMisSanciones | undefined;

    service.listar().subscribe((res) => {
      respuestaRecibida = res;
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/sanciones/mias/`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.keys().length).toBe(0);

    req.flush(mockRespuestaCompleta);
    expect(respuestaRecibida).toEqual(mockRespuestaCompleta);
  });

  it('3. debe enviar parámetro tipo=economicas al filtrar por multas', () => {
    service.listar({ tipo: 'economicas' }).subscribe();

    const req = httpTesting.expectOne(
      `${API_BASE_URL}/sanciones/mias/?tipo=economicas`,
    );
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('tipo')).toBe('economicas');
    expect(req.request.params.has('estado')).toBe(false);

    req.flush(mockRespuestaCompleta);
  });

  it('4. debe enviar parámetro tipo=bloqueos al filtrar por suspensiones', () => {
    service.listar({ tipo: 'bloqueos' }).subscribe();

    const req = httpTesting.expectOne(
      `${API_BASE_URL}/sanciones/mias/?tipo=bloqueos`,
    );
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('tipo')).toBe('bloqueos');

    req.flush(mockRespuestaCompleta);
  });

  it('5. debe enviar parámetro estado al filtrar por estado operativo', () => {
    service.listar({ estado: 'pendientes' }).subscribe();

    const req = httpTesting.expectOne(
      `${API_BASE_URL}/sanciones/mias/?estado=pendientes`,
    );
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('estado')).toBe('pendientes');

    req.flush(mockRespuestaCompleta);
  });

  it('6. debe combinar adecuadamente múltiples filtros válidos', () => {
    service
      .listar({
        tipo: 'economicas',
        estado: 'pagadas',
        page: 2,
        page_size: 15,
      })
      .subscribe();

    const req = httpTesting.expectOne(
      (r) =>
        r.url === `${API_BASE_URL}/sanciones/mias/` &&
        r.params.get('tipo') === 'economicas' &&
        r.params.get('estado') === 'pagadas' &&
        r.params.get('page') === '2' &&
        r.params.get('page_size') === '15',
    );
    expect(req.request.method).toBe('GET');
    expect(req.request.params.keys().length).toBe(4);

    req.flush(mockRespuestaCompleta);
  });

  it('7. debe enviar el parámetro page para paginación', () => {
    service.listar({ page: 3 }).subscribe();

    const req = httpTesting.expectOne(
      `${API_BASE_URL}/sanciones/mias/?page=3`,
    );
    expect(req.request.params.get('page')).toBe('3');

    req.flush(mockRespuestaCompleta);
  });

  it('8. debe enviar el parámetro page_size para tamaño de página', () => {
    service.listar({ page_size: 25 }).subscribe();

    const req = httpTesting.expectOne(
      `${API_BASE_URL}/sanciones/mias/?page_size=25`,
    );
    expect(req.request.params.get('page_size')).toBe('25');

    req.flush(mockRespuestaCompleta);
  });

  it('9. debe omitir parámetros no proporcionados o vacíos en el objeto de filtros', () => {
    service.listar({}).subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/sanciones/mias/`);
    expect(req.request.params.keys().length).toBe(0);

    req.flush(mockRespuestaCompleta);
  });

  it('10. debe interpretar tipadamente los resultados del arreglo results', () => {
    let respuesta: RespuestaMisSanciones | undefined;

    service.listar().subscribe((res) => {
      respuesta = res;
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/sanciones/mias/`);
    req.flush(mockRespuestaCompleta);

    expect(respuesta?.results.length).toBe(2);
    const multa = respuesta?.results[0];
    expect(multa?.tipo).toBe('ECONOMICA');
    expect(multa?.estado).toBe('PENDIENTE');
    expect(multa?.libro?.titulo).toBe('Estructuras de Datos en Python');
    expect(multa?.ejemplar?.codigo_inventario).toBe('EDP-01');

    const bloqueo = respuesta?.results[1];
    expect(bloqueo?.tipo).toBe('BLOQUEO');
    expect(bloqueo?.estado).toBe('VIGENTE');
    expect(bloqueo?.fecha_inicio_bloqueo).toBe('2026-10-15');
    expect(bloqueo?.fecha_fin_bloqueo).toBe('2026-11-13');
  });

  it('11. debe leer y mapear correctamente el objeto resumen', () => {
    let respuesta: RespuestaMisSanciones | undefined;

    service.listar().subscribe((res) => {
      respuesta = res;
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/sanciones/mias/`);
    req.flush(mockRespuestaCompleta);

    expect(respuesta?.resumen).toBeDefined();
    expect(respuesta?.resumen.total_sanciones).toBe(2);
    expect(respuesta?.resumen.multas_pendientes).toBe(1);
    expect(respuesta?.resumen.monto_total_adeudado).toBe('25.00');
    expect(respuesta?.resumen.bloqueos_vigentes).toBe(1);
  });

  it('12. debe conservar los montos monetarios estrictamente como cadenas decimales', () => {
    let respuesta: RespuestaMisSanciones | undefined;

    service.listar().subscribe((res) => {
      respuesta = res;
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/sanciones/mias/`);
    req.flush(mockRespuestaCompleta);

    expect(typeof respuesta?.resumen.monto_total_adeudado).toBe('string');
    expect(respuesta?.resumen.monto_total_adeudado).toBe('25.00');
    expect(typeof respuesta?.results[0].monto).toBe('string');
    expect(respuesta?.results[0].monto).toBe('25.00');
    expect(respuesta?.results[1].monto).toBeNull();
  });

  it('13. debe manejar correctamente una lista vacía de sanciones', () => {
    let respuesta: RespuestaMisSanciones | undefined;

    service.listar().subscribe((res) => {
      respuesta = res;
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/sanciones/mias/`);
    const respuestaVacia: RespuestaMisSanciones = {
      count: 0,
      next: null,
      previous: null,
      results: [],
      resumen: {
        total_sanciones: 0,
        multas_pendientes: 0,
        monto_total_adeudado: '0.00',
        bloqueos_vigentes: 0,
      },
    };
    req.flush(respuestaVacia);

    expect(respuesta?.count).toBe(0);
    expect(respuesta?.results).toEqual([]);
    expect(respuesta?.resumen.total_sanciones).toBe(0);
    expect(respuesta?.resumen.monto_total_adeudado).toBe('0.00');
  });

  it('14. debe propagar errores HTTP 400 Bad Request sin suprimirlos', () => {
    let errorCapturado: unknown;

    service.listar({ tipo: 'economicas', estado: 'vigentes' }).subscribe({
      next: () => expect.unreachable('No debía completarse con éxito'),
      error: (err) => {
        errorCapturado = err;
      },
    });

    const req = httpTesting.expectOne(
      `${API_BASE_URL}/sanciones/mias/?tipo=economicas&estado=vigentes`,
    );
    req.flush(
      {
        estado: ['El estado solicitado no es aplicable a multas económicas.'],
      },
      { status: 400, statusText: 'Bad Request' },
    );

    expect(errorCapturado).toBeDefined();
    const httpError = errorCapturado as {
      status: number;
      error: { estado: string[] };
    };
    expect(httpError.status).toBe(400);
    expect(httpError.error.estado[0]).toContain('no es aplicable');
  });

  it('15. debe propagar errores HTTP 401 Unauthorized cuando la sesión es inválida', () => {
    let errorCapturado: unknown;

    service.listar().subscribe({
      next: () => expect.unreachable('No debía completarse con éxito'),
      error: (err) => {
        errorCapturado = err;
      },
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/sanciones/mias/`);
    req.flush(
      {
        detail:
          'Las credenciales de autenticación no se proveyeron o son inválidas.',
      },
      { status: 401, statusText: 'Unauthorized' },
    );

    expect(errorCapturado).toBeDefined();
    const httpError = errorCapturado as {
      status: number;
      error: { detail: string };
    };
    expect(httpError.status).toBe(401);
    expect(httpError.error.detail).toContain('credenciales');
  });

  it('16. debe propagar errores HTTP 403 Forbidden cuando el rol no está autorizado', () => {
    let errorCapturado: unknown;

    service.listar().subscribe({
      next: () => expect.unreachable('No debía completarse con éxito'),
      error: (err) => {
        errorCapturado = err;
      },
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/sanciones/mias/`);
    req.flush(
      {
        detail: 'No tienes permiso para acceder a este recurso personal.',
      },
      { status: 403, statusText: 'Forbidden' },
    );

    expect(errorCapturado).toBeDefined();
    const httpError = errorCapturado as {
      status: number;
      error: { detail: string };
    };
    expect(httpError.status).toBe(403);
    expect(httpError.error.detail).toContain('No tienes permiso');
  });

  it('17. debe propagar errores HTTP 500 del servidor', () => {
    let errorCapturado: unknown;

    service.listar().subscribe({
      next: () => expect.unreachable('No debía completarse con éxito'),
      error: (err) => {
        errorCapturado = err;
      },
    });

    const req = httpTesting.expectOne(`${API_BASE_URL}/sanciones/mias/`);
    req.flush(
      { detail: 'Error interno inesperado.' },
      { status: 500, statusText: 'Internal Server Error' },
    );

    expect(errorCapturado).toBeDefined();
    const httpError = errorCapturado as { status: number };
    expect(httpError.status).toBe(500);
  });

  it('20. no debe incluir identificadores de usuario en parámetros de consulta ni en cabeceras cliente', () => {
    service.listar({ tipo: 'todas', estado: 'todos' }).subscribe();

    const req = httpTesting.expectOne(
      (r) => r.url === `${API_BASE_URL}/sanciones/mias/`,
    );

    expect(req.request.params.has('usuario_id')).toBe(false);
    expect(req.request.params.has('prestamo_id')).toBe(false);
    expect(req.request.params.has('prestamo__usuario_id')).toBe(false);
    expect(req.request.urlWithParams).not.toContain('usuario_id');

    req.flush(mockRespuestaCompleta);
  });

  it('21. confirma que el servicio es estrictamente de solo lectura y únicamente emite peticiones GET', () => {
    service.listar().subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/sanciones/mias/`);
    expect(req.request.method).toBe('GET');
    expect(req.request.body).toBeNull();

    // Comprobar ausencia de métodos modificatorios en la instancia del servicio
    const anyService = service as unknown as Record<string, unknown>;
    expect(anyService['crear']).toBeUndefined();
    expect(anyService['actualizar']).toBeUndefined();
    expect(anyService['eliminar']).toBeUndefined();
    expect(anyService['registrarPago']).toBeUndefined();
    expect(anyService['pagar']).toBeUndefined();

    req.flush(mockRespuestaCompleta);
  });
});

describe('MisSancionesService - Integración con authInterceptor', () => {
  let service: MisSancionesService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        MisSancionesService,
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        {
          provide: AuthSessionService,
          useValue: {
            token: signal('token-prueba-estudiante-309'),
            hasSession: () => true,
          },
        },
      ],
    });

    service = TestBed.inject(MisSancionesService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('18. debe integrarse correctamente con authInterceptor para endpoints API', () => {
    service.listar().subscribe();

    const req = httpTesting.expectOne(`${API_BASE_URL}/sanciones/mias/`);
    expect(req).toBeTruthy();
    req.flush({
      count: 0,
      next: null,
      previous: null,
      results: [],
      resumen: {
        total_sanciones: 0,
        multas_pendientes: 0,
        monto_total_adeudado: '0.00',
        bloqueos_vigentes: 0,
      },
    });
  });

  it('19. debe adjuntar automáticamente la cabecera Authorization: Bearer <token>', () => {
    service.listar({ tipo: 'economicas' }).subscribe();

    const req = httpTesting.expectOne(
      `${API_BASE_URL}/sanciones/mias/?tipo=economicas`,
    );
    expect(req.request.headers.has('Authorization')).toBe(true);
    expect(req.request.headers.get('Authorization')).toBe(
      'Bearer token-prueba-estudiante-309',
    );

    req.flush({
      count: 0,
      next: null,
      previous: null,
      results: [],
      resumen: {
        total_sanciones: 0,
        multas_pendientes: 0,
        monto_total_adeudado: '0.00',
        bloqueos_vigentes: 0,
      },
    });
  });
});

describe('esCombinacionFiltrosValida (función pura auxiliar)', () => {
  it('permite combinaciones válidas para tipo todas', () => {
    expect(esCombinacionFiltrosValida('todas', 'todos')).toBe(true);
    expect(esCombinacionFiltrosValida('todas', 'pendientes')).toBe(true);
    expect(esCombinacionFiltrosValida('todas', 'pagadas')).toBe(true);
    expect(esCombinacionFiltrosValida('todas', 'programados')).toBe(true);
    expect(esCombinacionFiltrosValida('todas', 'vigentes')).toBe(true);
    expect(esCombinacionFiltrosValida('todas', 'concluidos')).toBe(true);
  });

  it('permite combinaciones válidas para tipo economicas', () => {
    expect(esCombinacionFiltrosValida('economicas', 'todos')).toBe(true);
    expect(esCombinacionFiltrosValida('economicas', 'pendientes')).toBe(true);
    expect(esCombinacionFiltrosValida('economicas', 'pagadas')).toBe(true);
  });

  it('rechaza combinaciones inválidas para tipo economicas con estados de bloqueo', () => {
    expect(esCombinacionFiltrosValida('economicas', 'programados')).toBe(false);
    expect(esCombinacionFiltrosValida('economicas', 'vigentes')).toBe(false);
    expect(esCombinacionFiltrosValida('economicas', 'concluidos')).toBe(false);
  });

  it('permite combinaciones válidas para tipo bloqueos', () => {
    expect(esCombinacionFiltrosValida('bloqueos', 'todos')).toBe(true);
    expect(esCombinacionFiltrosValida('bloqueos', 'programados')).toBe(true);
    expect(esCombinacionFiltrosValida('bloqueos', 'vigentes')).toBe(true);
    expect(esCombinacionFiltrosValida('bloqueos', 'concluidos')).toBe(true);
  });

  it('rechaza combinaciones inválidas para tipo bloqueos con estados de multa', () => {
    expect(esCombinacionFiltrosValida('bloqueos', 'pendientes')).toBe(false);
    expect(esCombinacionFiltrosValida('bloqueos', 'pagadas')).toBe(false);
  });
});
