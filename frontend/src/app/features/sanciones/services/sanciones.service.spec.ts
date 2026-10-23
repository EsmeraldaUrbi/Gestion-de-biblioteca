import { provideHttpClient } from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { API_BASE_URL } from '../../../core/config/api.config';
import { SancionesService } from './sanciones.service';


describe('SancionesService', () => {
  let service: SancionesService;
  let httpTesting: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        SancionesService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(SancionesService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpTesting.verify());

  it('consulta sanciones administrativas con filtros', () => {
    service.obtenerAdministrativas({
      q: 'ana', tipo: 'ECONOMICA', estado: 'pendiente', page: 2, pageSize: 20,
    }).subscribe();

    const request = httpTesting.expectOne((req) =>
      req.url === `${API_BASE_URL}/sanciones/`
      && req.params.get('q') === 'ana'
      && req.params.get('tipo') === 'ECONOMICA'
      && req.params.get('estado') === 'pendiente'
      && req.params.get('page') === '2'
      && req.params.get('page_size') === '20',
    );
    expect(request.request.method).toBe('GET');
    request.flush({ count: 0, next: null, previous: null, results: [], resumen: {} });
  });

  it('consulta únicamente las sanciones propias', () => {
    service.obtenerMias(3, 8).subscribe();
    const request = httpTesting.expectOne(`${API_BASE_URL}/sanciones/mias/?page=3&page_size=8`);
    expect(request.request.method).toBe('GET');
    request.flush({ count: 0, next: null, previous: null, results: [], resumen: {} });
  });

  it('registra el pago con POST sin monto cliente', () => {
    service.registrarPago(42).subscribe();
    const request = httpTesting.expectOne(`${API_BASE_URL}/sanciones/42/pago/`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({});
    request.flush({ sancion_id: 42 });
  });
});
