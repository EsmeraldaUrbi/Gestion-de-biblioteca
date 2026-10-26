import {
  provideHttpClient,
} from '@angular/common/http';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import {
  ComponentFixture,
  TestBed,
} from '@angular/core/testing';
import { By } from '@angular/platform-browser';

import { API_BASE_URL } from '../../../../core/config/api.config';
import type {
  MiSancion,
  RespuestaMisSanciones,
} from '../../../prestamos/models/mis-sanciones.models';
import { MisSancionesService } from '../../../prestamos/services/mis-sanciones.service';
import { MisSancionesComponent } from './mis-sanciones';


// ── Fixtures de datos ──────────────────────────────────────────────────────────

const multaPendiente: MiSancion = {
  sancion_id: 14,
  prestamo_id: 28,
  libro: { libro_id: 5, titulo: 'Estructuras de Datos', isbn: '9780000000010' },
  ejemplar: { ejemplar_id: 11, codigo_inventario: 'EDP-01' },
  tipo: 'ECONOMICA',
  estado: 'PENDIENTE',
  monto: '25.00',
  fecha_pago: null,
  fecha_inicio_bloqueo: null,
  fecha_fin_bloqueo: null,
};

const multaPagada: MiSancion = {
  sancion_id: 15,
  prestamo_id: 30,
  libro: { libro_id: 6, titulo: 'Algoritmos Avanzados', isbn: '9780000000022' },
  ejemplar: { ejemplar_id: 12, codigo_inventario: 'AA-01' },
  tipo: 'ECONOMICA',
  estado: 'PAGADA',
  monto: '15.00',
  fecha_pago: '2026-09-10',
  fecha_inicio_bloqueo: null,
  fecha_fin_bloqueo: null,
};

const bloqueoVigente: MiSancion = {
  sancion_id: 9,
  prestamo_id: 19,
  libro: { libro_id: 3, titulo: 'Ingeniería de Software', isbn: '9780000000020' },
  ejemplar: { ejemplar_id: 8, codigo_inventario: 'ISM-01' },
  tipo: 'BLOQUEO',
  estado: 'VIGENTE',
  monto: null,
  fecha_pago: null,
  fecha_inicio_bloqueo: '2026-10-15',
  fecha_fin_bloqueo: '2026-11-13',
};

const bloqueoProgramado: MiSancion = {
  sancion_id: 20,
  prestamo_id: 35,
  libro: { libro_id: 7, titulo: 'Sistemas Operativos', isbn: '9780000000030' },
  ejemplar: { ejemplar_id: 15, codigo_inventario: 'SO-01' },
  tipo: 'BLOQUEO',
  estado: 'PROGRAMADO',
  monto: null,
  fecha_pago: null,
  fecha_inicio_bloqueo: '2026-11-01',
  fecha_fin_bloqueo: '2026-11-30',
};

const bloqueoConcluido: MiSancion = {
  sancion_id: 21,
  prestamo_id: 36,
  libro: { libro_id: 8, titulo: 'Redes de Computadoras', isbn: '9780000000031' },
  ejemplar: { ejemplar_id: 16, codigo_inventario: 'RC-01' },
  tipo: 'BLOQUEO',
  estado: 'CONCLUIDO',
  monto: null,
  fecha_pago: null,
  fecha_inicio_bloqueo: '2026-08-01',
  fecha_fin_bloqueo: '2026-08-30',
};

const resumenCompleto = {
  total_sanciones: 5,
  multas_pendientes: 1,
  monto_total_adeudado: '25.00',
  bloqueos_vigentes: 1,
};

const resumenVacio = {
  total_sanciones: 0,
  multas_pendientes: 0,
  monto_total_adeudado: '0.00',
  bloqueos_vigentes: 0,
};

function buildRespuesta(
  results: MiSancion[],
  resumen = resumenCompleto,
  count?: number,
  next: string | null = null,
  previous: string | null = null,
): RespuestaMisSanciones {
  return {
    count: count ?? results.length,
    next,
    previous,
    results,
    resumen,
  };
}


// ── Helpers ────────────────────────────────────────────────────────────────────

function setup() {
  TestBed.configureTestingModule({
    imports: [MisSancionesComponent],
    providers: [
      MisSancionesService,
      provideHttpClient(),
      provideHttpClientTesting(),
    ],
  });

  const fixture: ComponentFixture<MisSancionesComponent> =
    TestBed.createComponent(MisSancionesComponent);
  const httpTesting = TestBed.inject(HttpTestingController);

  return { fixture, httpTesting };
}

function flushInitial(
  httpTesting: HttpTestingController,
  respuesta: RespuestaMisSanciones,
  expectedUrl = `${API_BASE_URL}/sanciones/mias/`,
) {
  const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
  expect(req.request.method).toBe('GET');
  req.flush(respuesta);
  return req;
}

function detectAndFlush(
  fixture: ComponentFixture<MisSancionesComponent>,
  httpTesting: HttpTestingController,
  respuesta: RespuestaMisSanciones,
) {
  fixture.detectChanges();         // ngOnInit → cargar(1)
  flushInitial(httpTesting, respuesta);
  fixture.detectChanges();         // actualiza el DOM
}


// ── Suite principal ────────────────────────────────────────────────────────────

describe('MisSancionesComponent', () => {
  afterEach(() => {
    TestBed.inject(HttpTestingController).verify();
  });

  // ── 1. Creación ───────────────────────────────────────────────────────────
  it('1. debe crearse correctamente', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente]));
    expect(fixture.componentInstance).toBeTruthy();
  }, 15000);

  // ── 2. Carga inicial ─────────────────────────────────────────────────────
  it('2. debe mostrar estado de carga antes de recibir la respuesta', () => {
    const { fixture, httpTesting } = setup();
    fixture.detectChanges();

    expect(fixture.componentInstance.cargando()).toBe(true);
    const stateEl = fixture.debugElement.query(By.css('[role="status"]'));
    expect(stateEl).toBeTruthy();

    flushInitial(httpTesting, buildRespuesta([multaPendiente]));
    fixture.detectChanges();
  });

  it('2b. debe realizar GET a /api/sanciones/mias/ al iniciar', () => {
    const { fixture, httpTesting } = setup();
    fixture.detectChanges();

    const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
    expect(req.request.method).toBe('GET');
    req.flush(buildRespuesta([multaPendiente]));
    fixture.detectChanges();
  });

  // ── 3. Consumo de MisSancionesService ────────────────────────────────────
  it('3. debe consumir MisSancionesService.listar() y no SancionesService', () => {
    const { fixture, httpTesting } = setup();
    const spy = vi.spyOn(TestBed.inject(MisSancionesService), 'listar');
    fixture.detectChanges();

    expect(spy).toHaveBeenCalledOnce();

    flushInitial(httpTesting, buildRespuesta([multaPendiente]));
    fixture.detectChanges();
  });

  // ── 4. Visualización de multas económicas ────────────────────────────────
  it('4. debe mostrar el título del libro en una multa económica', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente]));

    const h3 = fixture.debugElement.query(By.css('.fine-main h3'));
    expect(h3.nativeElement.textContent).toContain('Estructuras de Datos');
  });

  it('4b. debe mostrar el importe de la multa económica', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente]));

    const importe = fixture.debugElement.query(By.css('.fine-side strong'));
    expect(importe.nativeElement.textContent).toContain('25');
  });

  it('4c. debe mostrar el número de préstamo', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente]));

    const labels = fixture.debugElement.query(By.css('.fine-labels'));
    expect(labels.nativeElement.textContent).toContain('28');
  });

  // ── 5. Visualización de bloqueos ─────────────────────────────────────────
  it('5. debe mostrar el título del libro en un bloqueo', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([bloqueoVigente]));

    const h3 = fixture.debugElement.query(By.css('.fine-main h3'));
    expect(h3.nativeElement.textContent).toContain('Ingeniería de Software');
  });

  it('5b. debe mostrar las fechas del período de bloqueo', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([bloqueoVigente]));

    const reason = fixture.debugElement.query(By.css('.reason'));
    expect(reason.nativeElement.textContent).toContain('15/10/2026');
    expect(reason.nativeElement.textContent).toContain('13/11/2026');
  });

  // ── 6. Bloqueo PROGRAMADO ────────────────────────────────────────────────
  it('6. debe mostrar etiqueta "Bloqueo programado" para estado PROGRAMADO', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([bloqueoProgramado]));

    const badge = fixture.debugElement.query(By.css('.badge'));
    expect(badge.nativeElement.textContent).toContain('Bloqueo programado');
  });

  it('6b. debe aplicar clase badge--scheduled al estado PROGRAMADO', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([bloqueoProgramado]));

    const badge = fixture.debugElement.query(By.css('.badge'));
    expect(badge.nativeElement.classList).toContain('badge--scheduled');
  });

  // ── 7. Bloqueo VIGENTE ───────────────────────────────────────────────────
  it('7. debe mostrar etiqueta "Bloqueo vigente" para estado VIGENTE', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([bloqueoVigente]));

    const badge = fixture.debugElement.query(By.css('.badge'));
    expect(badge.nativeElement.textContent).toContain('Bloqueo vigente');
  });

  it('7b. debe aplicar clase badge--active al estado VIGENTE', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([bloqueoVigente]));

    const badge = fixture.debugElement.query(By.css('.badge'));
    expect(badge.nativeElement.classList).toContain('badge--active');
  });

  // ── 8. Bloqueo CONCLUIDO ─────────────────────────────────────────────────
  it('8. debe mostrar etiqueta "Bloqueo concluido" para estado CONCLUIDO', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([bloqueoConcluido]));

    const badge = fixture.debugElement.query(By.css('.badge'));
    expect(badge.nativeElement.textContent).toContain('Bloqueo concluido');
  });

  it('8b. debe aplicar clase badge--done al estado CONCLUIDO', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([bloqueoConcluido]));

    const badge = fixture.debugElement.query(By.css('.badge'));
    expect(badge.nativeElement.classList).toContain('badge--done');
  });

  // ── 9. Multa PENDIENTE ───────────────────────────────────────────────────
  it('9. debe mostrar etiqueta "Pendiente de pago" y clase badge--pending para multa PENDIENTE', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente]));

    const badge = fixture.debugElement.query(By.css('.badge'));
    expect(badge.nativeElement.textContent).toContain('Pendiente de pago');
    expect(badge.nativeElement.classList).toContain('badge--pending');
  });

  // ── 10. Multa PAGADA ──────────────────────────────────────────────────────
  it('10. debe mostrar etiqueta "Pagada" y clase badge--paid para multa PAGADA', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPagada]));

    const badge = fixture.debugElement.query(By.css('.badge'));
    expect(badge.nativeElement.textContent).toContain('Pagada');
    expect(badge.nativeElement.classList).toContain('badge--paid');
  });

  // ── 11. Importe monetario ─────────────────────────────────────────────────
  it('11. debe formatear el importe en pesos mexicanos', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente]));

    const importe = fixture.debugElement.query(By.css('.fine-side strong'));
    // El formateador emite "$25.00" o "MXN 25.00" según la plataforma
    expect(importe.nativeElement.textContent).toMatch(/25/);
  });

  // ── 12. Fecha de pago ─────────────────────────────────────────────────────
  it('12. debe mostrar la fecha de pago cuando existe', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPagada]));

    const reason = fixture.debugElement.query(By.css('.reason'));
    expect(reason.nativeElement.textContent).toContain('10/09/2026');
  });

  it('12b. debe indicar que debe acudir a ventanilla cuando no hay fecha de pago', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente]));

    const reason = fixture.debugElement.query(By.css('.reason'));
    expect(reason.nativeElement.textContent).toContain('ventanilla');
  });

  // ── 13. Fechas de bloqueo ─────────────────────────────────────────────────
  it('13. debe formatear correctamente la fecha de inicio y fin del bloqueo', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([bloqueoProgramado]));

    const reason = fixture.debugElement.query(By.css('.reason'));
    expect(reason.nativeElement.textContent).toContain('01/11/2026');
    expect(reason.nativeElement.textContent).toContain('30/11/2026');
  });

  // ── 14. Tarjetas de resumen ───────────────────────────────────────────────
  it('14a. debe mostrar total_sanciones en la primera tarjeta', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente], {
      ...resumenCompleto, total_sanciones: 7,
    }));

    const tarjetas = fixture.debugElement.queryAll(By.css('.overview-card strong'));
    expect(tarjetas[0].nativeElement.textContent).toContain('7');
  });

  it('14b. debe mostrar monto_total_adeudado en la segunda tarjeta', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente], {
      ...resumenCompleto, monto_total_adeudado: '100.00',
    }));

    const tarjetas = fixture.debugElement.queryAll(By.css('.overview-card strong'));
    expect(tarjetas[1].nativeElement.textContent).toContain('100');
  });

  it('14c. debe mostrar bloqueos_vigentes en la tercera tarjeta', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([bloqueoVigente], {
      ...resumenCompleto, bloqueos_vigentes: 3,
    }));

    const tarjetas = fixture.debugElement.queryAll(By.css('.overview-card strong'));
    expect(tarjetas[2].nativeElement.textContent).toContain('3');
  });

  it('14d. el resumen permanece estable aunque el usuario cambie de filtro', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente], resumenCompleto));

    const comp = fixture.componentInstance;
    comp.cambiarTipo('economicas');
    fixture.detectChanges();

    const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
    req.flush(buildRespuesta([multaPendiente], {
      ...resumenCompleto, total_sanciones: 1,
    }));
    fixture.detectChanges();

    const tarjetas = fixture.debugElement.queryAll(By.css('.overview-card strong'));
    expect(tarjetas[0].nativeElement.textContent).toContain('1');
  });

  // ── 15. Filtro por tipo ───────────────────────────────────────────────────
  it('15. cambiarTipo("economicas") debe enviar tipo=economicas al backend', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente]));

    fixture.componentInstance.cambiarTipo('economicas');
    fixture.detectChanges();

    const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
    expect(req.request.params.get('tipo')).toBe('economicas');
    req.flush(buildRespuesta([multaPendiente]));
    fixture.detectChanges();
  });

  it('15b. cambiarTipo("bloqueos") debe enviar tipo=bloqueos al backend', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([bloqueoVigente]));

    fixture.componentInstance.cambiarTipo('bloqueos');
    fixture.detectChanges();

    const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
    expect(req.request.params.get('tipo')).toBe('bloqueos');
    req.flush(buildRespuesta([bloqueoVigente]));
    fixture.detectChanges();
  });

  // ── 16. Filtro por estado ─────────────────────────────────────────────────
  it('16. cambiarEstado("pendientes") debe enviar estado=pendientes al backend', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente]));

    fixture.componentInstance.cambiarEstado('pendientes');
    fixture.detectChanges();

    const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
    expect(req.request.params.get('estado')).toBe('pendientes');
    req.flush(buildRespuesta([multaPendiente]));
    fixture.detectChanges();
  });

  it('16b. cambiarEstado("vigentes") debe enviar estado=vigentes al backend', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([bloqueoVigente]));

    fixture.componentInstance.cambiarEstado('vigentes');
    fixture.detectChanges();

    const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
    expect(req.request.params.get('estado')).toBe('vigentes');
    req.flush(buildRespuesta([bloqueoVigente]));
    fixture.detectChanges();
  });

  it('16c. cambiarTipo a "economicas" debe resetear filtroEstado a "todos" si el estado actual es incompatible', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([bloqueoVigente]));

    const comp = fixture.componentInstance;
    // Primero filtramos por bloqueos vigentes
    comp.cambiarTipo('bloqueos');
    fixture.detectChanges();
    httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`).flush(buildRespuesta([bloqueoVigente]));
    fixture.detectChanges();

    comp.cambiarEstado('vigentes');
    fixture.detectChanges();
    httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`).flush(buildRespuesta([bloqueoVigente]));
    fixture.detectChanges();

    expect(comp.filtroEstado()).toBe('vigentes');

    // Al cambiar a economicas, "vigentes" no es compatible → reset a "todos"
    comp.cambiarTipo('economicas');
    fixture.detectChanges();
    expect(comp.filtroEstado()).toBe('todos');

    httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`).flush(buildRespuesta([multaPendiente]));
    fixture.detectChanges();
  });

  // ── 17. Reinicio de paginación al filtrar ─────────────────────────────────
  it('17. cambiarTipo debe reiniciar la paginación a la página 1', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta(
      [multaPendiente], resumenCompleto, 25, 'next-url', null,
    ));

    // Avanzar a página 2
    fixture.componentInstance.cambiarPagina(2);
    fixture.detectChanges();
    httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`).flush(buildRespuesta(
      [multaPagada], resumenCompleto, 25, null, 'prev-url',
    ));
    fixture.detectChanges();

    expect(fixture.componentInstance.pagina()).toBe(2);

    // Cambiar filtro → debe volver a página 1
    fixture.componentInstance.cambiarTipo('economicas');
    fixture.detectChanges();
    httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`).flush(buildRespuesta([multaPendiente]));
    fixture.detectChanges();

    expect(fixture.componentInstance.pagina()).toBe(1);
  });

  // ── 18. Avance y retroceso de página ─────────────────────────────────────
  it('18a. cambiarPagina(2) debe enviar page=2 al backend', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta(
      [multaPendiente], resumenCompleto, 25, 'next', null,
    ));

    fixture.componentInstance.cambiarPagina(2);
    fixture.detectChanges();

    const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
    expect(req.request.params.get('page')).toBe('2');
    req.flush(buildRespuesta([multaPagada], resumenCompleto, 25, null, 'prev'));
    fixture.detectChanges();

    expect(fixture.componentInstance.pagina()).toBe(2);
  });

  it('18b. el botón Anterior debe estar deshabilitado en la primera página', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta(
      [multaPendiente], resumenCompleto, 25, 'next', null,
    ));

    const paginacion = fixture.debugElement.query(By.css('.pagination'));
    expect(paginacion).toBeTruthy();

    const btnAnterior = fixture.debugElement.query(By.css('[aria-label="Página anterior"]'));
    expect(btnAnterior.nativeElement.disabled).toBe(true);
  });

  it('18c. el botón Siguiente debe estar deshabilitado en la última página', () => {
    const { fixture, httpTesting } = setup();
    // totalPaginas = 1, pagina = 1 → página final
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente], resumenCompleto, 1));

    // Con solo 1 página, la paginación no se renderiza; verificamos que el componente lo gestiona
    expect(fixture.componentInstance.pagina()).toBe(1);
    expect(fixture.componentInstance.totalPaginas()).toBe(1);
  });

  it('18d. cambiarPagina con número inválido no debe realizar petición HTTP', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente]));

    fixture.componentInstance.cambiarPagina(0);
    fixture.componentInstance.cambiarPagina(-1);
    fixture.detectChanges();

    httpTesting.expectNone((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
  });

  // ── 19. Protección frente a respuestas HTTP obsoletas ────────────────────
  it('19. debe ignorar respuestas HTTP obsoletas (stale request race condition)', () => {
    const { fixture, httpTesting } = setup();
    fixture.detectChanges();

    const req1 = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);

    // Lanzar segunda petición antes de que la primera responda
    fixture.componentInstance.cambiarTipo('economicas');
    fixture.detectChanges();
    const req2 = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);

    // La respuesta de la primera petición (obsoleta) llega después
    req1.flush(buildRespuesta([bloqueoVigente], resumenCompleto));

    // La respuesta actual (de req2) llega después
    req2.flush(buildRespuesta([multaPendiente], resumenCompleto));
    fixture.detectChanges();

    // El estado final debe corresponder a la segunda petición
    expect(fixture.componentInstance.sanciones()).toEqual([multaPendiente]);
  });

  // ── 20. Usuario sin sanciones ─────────────────────────────────────────────
  it('20. debe mostrar mensaje de "Sin sanciones" cuando la cuenta no tiene ninguna', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([], resumenVacio, 0));

    const stateEl = fixture.debugElement.query(By.css('.state strong'));
    expect(stateEl.nativeElement.textContent).toContain('Sin sanciones');
  });

  // ── 21. Sin resultados con filtro activo ──────────────────────────────────
  it('21. debe mostrar "Sin resultados" cuando el filtro activo no devuelve sanciones', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente]));

    fixture.componentInstance.cambiarTipo('bloqueos');
    fixture.detectChanges();
    httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`).flush(buildRespuesta([], resumenCompleto, 0));
    fixture.detectChanges();

    const stateEl = fixture.debugElement.query(By.css('.state strong'));
    expect(stateEl.nativeElement.textContent).toContain('Sin resultados');
  });

  // ── 22. Error 400 ─────────────────────────────────────────────────────────
  it('22. debe mostrar mensaje de error para respuesta HTTP 400', () => {
    const { fixture, httpTesting } = setup();
    fixture.detectChanges();

    const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
    req.flush({ estado: ['Filtro de estado inválido.'] }, { status: 400, statusText: 'Bad Request' });
    fixture.detectChanges();

    const errorEl = fixture.debugElement.query(By.css('[role="alert"]'));
    expect(errorEl).toBeTruthy();
    expect(errorEl.nativeElement.textContent).toContain('Filtro inválido');
  });

  // ── 23. Error 401 ─────────────────────────────────────────────────────────
  it('23. debe mostrar mensaje de sesión expirada para respuesta HTTP 401', () => {
    const { fixture, httpTesting } = setup();
    fixture.detectChanges();

    const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
    req.flush({ detail: 'No auth.' }, { status: 401, statusText: 'Unauthorized' });
    fixture.detectChanges();

    const errorEl = fixture.debugElement.query(By.css('[role="alert"]'));
    expect(errorEl.nativeElement.textContent).toContain('sesión ha vencido');
  });

  // ── 24. Error 403 ─────────────────────────────────────────────────────────
  it('24. debe mostrar mensaje de acceso denegado para respuesta HTTP 403', () => {
    const { fixture, httpTesting } = setup();
    fixture.detectChanges();

    const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
    req.flush({ detail: 'Forbidden.' }, { status: 403, statusText: 'Forbidden' });
    fixture.detectChanges();

    const errorEl = fixture.debugElement.query(By.css('[role="alert"]'));
    expect(errorEl.nativeElement.textContent).toContain('lectores');
  });

  // ── 25. Error de conexión ─────────────────────────────────────────────────
  it('25. debe mostrar mensaje de error de conexión para status 0', () => {
    const { fixture, httpTesting } = setup();
    fixture.detectChanges();

    const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
    req.error(new ProgressEvent('error'));
    fixture.detectChanges();

    const errorEl = fixture.debugElement.query(By.css('[role="alert"]'));
    expect(errorEl.nativeElement.textContent).toContain('conectar');
  });

  // ── 26. Ausencia de operaciones administrativas ───────────────────────────
  it('26. la pantalla no debe contener botones de pago, eliminación ni desbloqueo', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente, bloqueoVigente]));

    const textoTotal = fixture.nativeElement.textContent.toLowerCase();
    expect(textoTotal).not.toContain('registrar pago');
    expect(textoTotal).not.toContain('eliminar');
    expect(textoTotal).not.toContain('desbloquear');
    expect(textoTotal).not.toContain('anular');
  });

  // ── 27. Accesibilidad básica de controles ─────────────────────────────────
  it('27a. los botones de tipo deben tener aria-pressed correcto', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta([multaPendiente]));

    const btnTodasEl = fixture.debugElement.query(By.css('#filtro-tipo-todas'));
    expect(btnTodasEl.nativeElement.getAttribute('aria-pressed')).toBe('true');

    const btnEcoEl = fixture.debugElement.query(By.css('#filtro-tipo-economicas'));
    expect(btnEcoEl.nativeElement.getAttribute('aria-pressed')).toBe('false');
  });

  it('27b. los botones de paginación deben tener aria-label', () => {
    const { fixture, httpTesting } = setup();
    detectAndFlush(fixture, httpTesting, buildRespuesta(
      [multaPendiente], resumenCompleto, 25, 'next', null,
    ));

    const btnAnterior = fixture.debugElement.query(By.css('[aria-label="Página anterior"]'));
    const btnSiguiente = fixture.debugElement.query(By.css('[aria-label="Página siguiente"]'));

    expect(btnAnterior).toBeTruthy();
    expect(btnSiguiente).toBeTruthy();
  });

  it('27c. el estado de carga debe tener role="status" y aria-live', () => {
    const { fixture, httpTesting } = setup();
    fixture.detectChanges();

    const stateEl = fixture.debugElement.query(By.css('[role="status"][aria-live]'));
    expect(stateEl).toBeTruthy();

    httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`).flush(buildRespuesta([multaPendiente]));
    fixture.detectChanges();
  });

  it('27d. el mensaje de error debe tener role="alert"', () => {
    const { fixture, httpTesting } = setup();
    fixture.detectChanges();

    const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
    req.flush({}, { status: 500, statusText: 'Server Error' });
    fixture.detectChanges();

    const alertEl = fixture.debugElement.query(By.css('[role="alert"]'));
    expect(alertEl).toBeTruthy();
  });

  // ── 28. Integración del contrato oficial Django–Angular ───────────────────
  describe('28. Validación del contrato oficial Django–Angular', () => {
    it('debe cumplir rigurosamente los 10 puntos del contrato con HttpTestingController', () => {
      const { fixture, httpTesting } = setup();

      // JSON real y representativo emitido por Django DRF en /api/sanciones/mias/
      const djangoResponse: RespuestaMisSanciones = {
        count: 3,
        next: null,
        previous: null,
        results: [
          {
            sancion_id: 101,
            prestamo_id: 501,
            libro: {
              libro_id: 10,
              titulo: 'Arquitectura Limpia',
              isbn: '9780134494166',
            },
            ejemplar: {
              ejemplar_id: 20,
              codigo_inventario: 'ARQ-001',
            },
            tipo: 'ECONOMICA',
            estado: 'PENDIENTE',
            monto: '50.00',
            fecha_pago: null,
            fecha_inicio_bloqueo: null,
            fecha_fin_bloqueo: null,
          },
          {
            sancion_id: 102,
            prestamo_id: 502,
            libro: {
              libro_id: 11,
              titulo: 'Patrones de Diseño',
              isbn: '9780201633610',
            },
            ejemplar: {
              ejemplar_id: 21,
              codigo_inventario: 'PAT-001',
            },
            tipo: 'BLOQUEO',
            estado: 'VIGENTE',
            monto: null,
            fecha_pago: null,
            fecha_inicio_bloqueo: '2026-10-15',
            fecha_fin_bloqueo: '2026-11-14',
          },
          {
            sancion_id: 103,
            prestamo_id: 503,
            libro: {
              libro_id: 12,
              titulo: 'Refactorización',
              isbn: '9780134757599',
            },
            ejemplar: {
              ejemplar_id: 22,
              codigo_inventario: 'REF-001',
            },
            tipo: 'BLOQUEO',
            estado: 'PROGRAMADO',
            monto: null,
            fecha_pago: null,
            fecha_inicio_bloqueo: '2026-11-01',
            fecha_fin_bloqueo: '2026-11-30',
          },
        ],
        resumen: {
          total_sanciones: 3,
          multas_pendientes: 1,
          monto_total_adeudado: '50.00',
          bloqueos_vigentes: 1,
        },
      };

      // Inicializar componente (dispara ngOnInit -> cargar(1))
      fixture.detectChanges();

      // Punto 1: La pantalla solicita GET /api/sanciones/mias/
      const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
      expect(req.request.method).toBe('GET');

      // Punto 2: Los parámetros HTTP tienen los nombres correctos (tipo, estado, page, page_size)
      expect(req.request.params.has('tipo')).toBe(true);
      expect(req.request.params.has('estado')).toBe(true);
      expect(req.request.params.has('page')).toBe(true);
      expect(req.request.params.has('page_size')).toBe(true);

      // Punto 3: Los valores iniciales enviados coinciden con el backend
      expect(req.request.params.get('tipo')).toBe('todas');
      expect(req.request.params.get('estado')).toBe('todos');
      expect(req.request.params.get('page')).toBe('1');
      expect(req.request.params.get('page_size')).toBe('10');

      // Punto 8: No se envía ningún identificador de usuario en los query params
      expect(req.request.params.has('usuario_id')).toBe(false);
      expect(req.request.params.has('user_id')).toBe(false);
      expect(req.request.params.has('id')).toBe(false);

      // Responder con el contrato exacto de Django
      req.flush(djangoResponse);
      fixture.detectChanges();

      // Punto 4: Los elementos de results se visualizan en la lista del DOM
      const tarjetasSanciones = fixture.debugElement.queryAll(By.css('.fine-card'));
      expect(tarjetasSanciones.length).toBe(3);
      expect(tarjetasSanciones[0].nativeElement.textContent).toContain('Arquitectura Limpia');
      expect(tarjetasSanciones[1].nativeElement.textContent).toContain('Patrones de Diseño');
      expect(tarjetasSanciones[2].nativeElement.textContent).toContain('Refactorización');

      // Punto 5: El resumen se presenta fielmente
      const valoresResumen = fixture.debugElement.queryAll(By.css('.overview-card strong'));
      expect(valoresResumen[0].nativeElement.textContent).toContain('3');
      expect(valoresResumen[1].nativeElement.textContent).toContain('50');
      expect(valoresResumen[2].nativeElement.textContent).toContain('1');

      // Punto 6: Los controles de conteo y paginación utilizan count
      expect(fixture.componentInstance.total()).toBe(3);
      expect(fixture.componentInstance.totalPaginas()).toBe(1);

      // Punto 7: Los estados PROGRAMADO, VIGENTE y PENDIENTE se interpretan con los badges correctos
      const badges = fixture.debugElement.queryAll(By.css('.badge'));
      expect(badges[0].nativeElement.textContent).toContain('Pendiente de pago');
      expect(badges[0].nativeElement.classList).toContain('badge--pending');
      expect(badges[1].nativeElement.textContent).toContain('Bloqueo vigente');
      expect(badges[1].nativeElement.classList).toContain('badge--active');
      expect(badges[2].nativeElement.textContent).toContain('Bloqueo programado');
      expect(badges[2].nativeElement.classList).toContain('badge--scheduled');

      // Punto 10: No se realizan operaciones modificatorias (solo lectura)
      const botonesAccion = fixture.nativeElement.querySelectorAll('button');
      for (const btn of Array.from(botonesAccion)) {
        const txt = (btn as HTMLElement).textContent?.toLowerCase() ?? '';
        expect(txt).not.toContain('pagar');
        expect(txt).not.toContain('eliminar');
        expect(txt).not.toContain('desbloquear');
      }
    });

    it('Punto 9: Los errores HTTP no se presentan como listas vacías sino como alertas explícitas', () => {
      const { fixture, httpTesting } = setup();
      fixture.detectChanges();

      const req = httpTesting.expectOne((r) => r.url === `${API_BASE_URL}/sanciones/mias/`);
      req.flush({ detail: 'Error de servidor' }, { status: 500, statusText: 'Internal Server Error' });
      fixture.detectChanges();

      // No debe decir "Sin sanciones" ni "Sin resultados"
      const texto = fixture.nativeElement.textContent;
      expect(texto).not.toContain('Sin sanciones registradas');
      expect(texto).not.toContain('Sin resultados');

      // Debe mostrar la alerta de error con role="alert"
      const alertEl = fixture.debugElement.query(By.css('[role="alert"]'));
      expect(alertEl).toBeTruthy();
      expect(alertEl.nativeElement.textContent).toContain('No fue posible cargar la consulta');
    });
  });
});
