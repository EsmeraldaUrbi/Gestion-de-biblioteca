import {
  ComponentFixture,
  TestBed,
} from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import {
  CategoriaAdministrativa,
  CategoriasPaginadas,
} from '../../models/categorias.models';
import { CategoriasService } from '../../services/categorias.service';
import { CategoriasListaComponent } from './categorias-lista';

describe('CategoriasListaComponent (Ticket 3.3 Etapa 3)', () => {
  let component: CategoriasListaComponent;
  let fixture: ComponentFixture<CategoriasListaComponent>;
  let categoriasServiceMock: {
    listar: ReturnType<typeof vi.fn>;
    registrar: ReturnType<typeof vi.fn>;
    modificar: ReturnType<typeof vi.fn>;
    obtenerPorId: ReturnType<typeof vi.fn>;
    obtener: ReturnType<typeof vi.fn>;
    actualizar: ReturnType<typeof vi.fn>;
  };

  const mockCategorias: CategoriaAdministrativa[] = [
    {
      categoria_id: 1,
      nombre_categoria: 'Novela Histórica',
      cantidad_libros: 5,
    },
    {
      categoria_id: 2,
      nombre_categoria: 'Ciencia Ficción',
      cantidad_libros: 3,
    },
    {
      categoria_id: 3,
      nombre_categoria: 'Filosofía',
      cantidad_libros: 0,
    },
  ];

  const mockRespuestaPaginada: CategoriasPaginadas = {
    count: 3,
    next: null,
    previous: null,
    results: mockCategorias,
  };

  beforeEach(async () => {
    categoriasServiceMock = {
      listar: vi.fn().mockReturnValue(of(mockRespuestaPaginada)),
      registrar: vi.fn(),
      modificar: vi.fn(),
      obtenerPorId: vi.fn(),
      obtener: vi.fn(),
      actualizar: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [CategoriasListaComponent],
      providers: [
        { provide: CategoriasService, useValue: categoriasServiceMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CategoriasListaComponent);
    component = fixture.componentInstance;
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ---------------------------------------------------------------------------
  // 1. Inicialización y renderizado
  // ---------------------------------------------------------------------------

  it('debe crearse e inicializar el listado de categorías', () => {
    fixture.detectChanges();

    expect(component).toBeTruthy();
    expect(categoriasServiceMock.listar).toHaveBeenCalledTimes(1);
    expect(component.categorias().length).toBe(3);
    expect(component.total()).toBe(3);
  });

  it('debe renderizar las categorías en la tabla mostrando ID, nombre, libros asociados y botón Editar', () => {
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const filas = compiled.querySelectorAll('tbody tr');
    expect(filas.length).toBe(3);

    // Primera fila
    const fila1 = filas[0];
    expect(fila1.querySelector('.id-badge')?.textContent?.trim()).toBe('#1');
    expect(fila1.querySelector('.categoria-nombre')?.textContent?.trim()).toBe('Novela Histórica');
    expect(fila1.querySelector('.count-badge')?.textContent).toContain('5');
    expect(fila1.querySelector('.count-badge')?.textContent).toContain('libros');

    // Botón de acción Editar
    const btnEditar = fila1.querySelector('.table-action-btn--edit');
    expect(btnEditar).toBeTruthy();
    expect(btnEditar?.textContent?.trim()).toBe('Editar');
  });

  it('debe mostrar el total de categorías en la tarjeta de resumen estadístico', () => {
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const totalEl = compiled.querySelector('.summary-card strong');
    expect(totalEl?.textContent?.trim()).toBe('3');
  });

  // ---------------------------------------------------------------------------
  // 2. Búsqueda reactiva con debounce (300 ms) y limpieza rápida
  // ---------------------------------------------------------------------------

  it('debe filtrar categorías tras el debounce de 300 ms y reiniciar la paginación a la página 1', () => {
    vi.useFakeTimers();
    fixture.detectChanges();
    categoriasServiceMock.listar.mockClear();

    const resultadoBusqueda: CategoriasPaginadas = {
      count: 1,
      next: null,
      previous: null,
      results: [mockCategorias[1]], // Ciencia Ficción
    };
    categoriasServiceMock.listar.mockReturnValue(of(resultadoBusqueda));

    component.pagina.set(2);
    expect(component.pagina()).toBe(2);
    categoriasServiceMock.listar.mockClear();

    component.actualizarBusqueda('ciencia');

    // Antes de 300 ms no debe haber emitido la petición
    vi.advanceTimersByTime(150);
    expect(categoriasServiceMock.listar).not.toHaveBeenCalled();

    // Tras 300 ms se dispara la petición con debounce
    vi.advanceTimersByTime(150);
    expect(categoriasServiceMock.listar).toHaveBeenCalledWith({
      nombre: 'ciencia',
      page: 1,
      page_size: 10,
    });
    expect(component.pagina()).toBe(1);
    expect(component.categorias().length).toBe(1);
  });

  it('limpiarBusqueda() debe restablecer el término a vacío y recargar desde la página 1', () => {
    fixture.detectChanges();
    categoriasServiceMock.listar.mockClear();

    component.busquedaNombre.set('algo');
    component.pagina.set(3);

    component.limpiarBusqueda();

    expect(component.busquedaNombre()).toBe('');
    expect(component.pagina()).toBe(1);
    expect(categoriasServiceMock.listar).toHaveBeenCalledWith({
      nombre: undefined,
      page: 1,
      page_size: 10,
    });
  });

  // ---------------------------------------------------------------------------
  // 3. Paginación y navegación
  // ---------------------------------------------------------------------------

  it('debe calcular totalPaginas, primerRegistro y ultimoRegistro correctamente', () => {
    fixture.detectChanges();

    // 3 categorías, pageSize 10 -> 1 página
    expect(component.totalPaginas()).toBe(1);
    expect(component.primerRegistro()).toBe(1);
    expect(component.ultimoRegistro()).toBe(3);

    // Simular 35 categorías en la página 2
    component.total.set(35);
    component.pagina.set(2);
    expect(component.totalPaginas()).toBe(4);
    expect(component.primerRegistro()).toBe(11);
    expect(component.ultimoRegistro()).toBe(20);
  });

  it('cambiarPagina() debe cambiar de página y solicitar los registros al backend', () => {
    fixture.detectChanges();
    categoriasServiceMock.listar.mockClear();

    component.total.set(25);
    component.cambiarPagina(2);

    expect(component.pagina()).toBe(2);
    expect(categoriasServiceMock.listar).toHaveBeenCalledWith({
      nombre: undefined,
      page: 2,
      page_size: 10,
    });
  });

  it('no debe cambiar de página si el número es inválido, igual al actual o si está cargando', () => {
    fixture.detectChanges();
    categoriasServiceMock.listar.mockClear();

    component.cambiarPagina(1); // Mismo número
    component.cambiarPagina(0); // Menor a 1
    component.cambiarPagina(999); // Mayor a totalPaginas
    component.cargando.set(true);
    component.cambiarPagina(2); // Bloqueado mientras carga

    expect(categoriasServiceMock.listar).not.toHaveBeenCalled();
  });

  // ---------------------------------------------------------------------------
  // 4. Estados visuales: carga, error y lista vacía
  // ---------------------------------------------------------------------------

  it('debe mostrar mensaje de carga mientras cargando() sea true', () => {
    fixture.detectChanges();
    component.cargando.set(true);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.state-message')?.textContent).toContain('Cargando categorías...');
  });

  it('debe mostrar error con botón de reintento si la consulta falla', () => {
    categoriasServiceMock.listar.mockReturnValue(
      throwError(() => ({ status: 500 })),
    );

    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const errorMsg = compiled.querySelector('.state-message--error');
    expect(errorMsg).toBeTruthy();
    expect(errorMsg?.textContent).toContain('No se pudo cargar la lista');

    // Botón reintentar
    categoriasServiceMock.listar.mockReturnValue(of(mockRespuestaPaginada));
    const btnReintentar = errorMsg?.querySelector('button') as HTMLButtonElement;
    btnReintentar.click();

    expect(categoriasServiceMock.listar).toHaveBeenCalledTimes(2);
  });

  it('debe mostrar mensaje específico cuando no haya categorías en el catálogo', () => {
    categoriasServiceMock.listar.mockReturnValue(
      of({ count: 0, next: null, previous: null, results: [] }),
    );

    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.empty-title')?.textContent).toContain('Sin categorías registradas');
  });

  it('debe mostrar mensaje específico cuando una búsqueda no arroje resultados', () => {
    categoriasServiceMock.listar.mockReturnValue(
      of({ count: 0, next: null, previous: null, results: [] }),
    );

    fixture.detectChanges();
    component.busquedaNombre.set('Misterio');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.empty-title')?.textContent).toContain('Sin resultados para "Misterio"');
  });

  // ---------------------------------------------------------------------------
  // 5. Modal en modo Registro (POST)
  // ---------------------------------------------------------------------------

  it('abrirModalRegistro() debe abrir el modal en modo creación y resetear campos', () => {
    fixture.detectChanges();
    expect(component.modalAbierto()).toBe(false);

    component.abrirModalRegistro();
    fixture.detectChanges();

    expect(component.modalAbierto()).toBe(true);
    expect(component.modoEdicion()).toBe(false);
    expect(component.formCategoria.get('nombre_categoria')?.value).toBe('');

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('#modal-categoria-titulo')?.textContent?.trim()).toBe('Registrar nueva categoría');
  });

  it('cerrarModal() debe cerrar el modal y limpiar el estado cuando no se esté guardando', () => {
    fixture.detectChanges();
    component.abrirModalRegistro();
    expect(component.modalAbierto()).toBe(true);

    component.cerrarModal();
    expect(component.modalAbierto()).toBe(false);
    expect(component.modoEdicion()).toBe(false);
    expect(component.categoriaSeleccionada()).toBeNull();
  });

  it('no debe cerrar el modal si guardando() es true', () => {
    fixture.detectChanges();
    component.abrirModalRegistro();
    component.guardando.set(true);

    component.cerrarModal();
    expect(component.modalAbierto()).toBe(true);
  });

  it('onSubmit() en registro: debe rechazar nombre vacío o de solo espacios', () => {
    fixture.detectChanges();
    component.abrirModalRegistro();

    component.formCategoria.patchValue({ nombre_categoria: '     ' });
    component.onSubmit();

    expect(categoriasServiceMock.registrar).not.toHaveBeenCalled();
    expect(component.obtenerErrorNombre()).toBe('El nombre de la categoría es obligatorio.');
  });

  it('onSubmit() en registro: debe rechazar nombres mayores a 50 caracteres', () => {
    fixture.detectChanges();
    component.abrirModalRegistro();

    component.formCategoria.patchValue({ nombre_categoria: 'C'.repeat(51) });
    component.onSubmit();

    expect(categoriasServiceMock.registrar).not.toHaveBeenCalled();
    expect(component.obtenerErrorNombre()).toBe('El nombre no puede exceder 50 caracteres.');
  });

  it('onSubmit() en registro: debe enviar POST con nombre recortado, cerrar modal, notificar y recargar', () => {
    const nuevaCategoria: CategoriaAdministrativa = {
      categoria_id: 4,
      nombre_categoria: 'Realismo Mágico',
      cantidad_libros: 0,
    };
    categoriasServiceMock.registrar.mockReturnValue(of(nuevaCategoria));

    fixture.detectChanges();
    categoriasServiceMock.listar.mockClear();

    component.abrirModalRegistro();
    component.formCategoria.patchValue({ nombre_categoria: '   Realismo Mágico   ' });
    component.onSubmit();

    expect(categoriasServiceMock.registrar).toHaveBeenCalledWith({
      nombre_categoria: 'Realismo Mágico',
    });
    expect(component.modalAbierto()).toBe(false);
    expect(component.guardando()).toBe(false);
    expect(component.mensajeExito()).toContain('Realismo Mágico');
    expect(component.mensajeExito()).toContain('#4');
    expect(categoriasServiceMock.listar).toHaveBeenCalledTimes(1);
  });

  // ---------------------------------------------------------------------------
  // 6. Modal en modo Edición (PATCH)
  // ---------------------------------------------------------------------------

  it('abrirModalEdicion() debe abrir el modal, activar modoEdicion y precargar datos de solo lectura', () => {
    fixture.detectChanges();
    expect(component.modalAbierto()).toBe(false);

    component.abrirModalEdicion(mockCategorias[0]);
    fixture.detectChanges();

    expect(component.modalAbierto()).toBe(true);
    expect(component.modoEdicion()).toBe(true);
    expect(component.categoriaSeleccionada()?.categoria_id).toBe(1);
    expect(component.formCategoria.get('nombre_categoria')?.value).toBe('Novela Histórica');

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('#modal-categoria-titulo')?.textContent?.trim()).toBe('Editar categoría');
    expect(compiled.querySelector('.summary-id')?.textContent).toContain('#1');
    expect(compiled.querySelector('.summary-hint')?.textContent).toContain('5');
  });

  it('onSubmit() en edición: si el nombre no cambió, debe cerrar el modal sin hacer petición HTTP', () => {
    fixture.detectChanges();
    component.abrirModalEdicion(mockCategorias[0]); // 'Novela Histórica'

    // Mantener el mismo nombre (incluso con espacios circundantes)
    component.formCategoria.patchValue({ nombre_categoria: '  Novela Histórica  ' });
    component.onSubmit();

    expect(categoriasServiceMock.modificar).not.toHaveBeenCalled();
    expect(categoriasServiceMock.actualizar).not.toHaveBeenCalled();
    expect(component.modalAbierto()).toBe(false);
  });

  it('onSubmit() en edición: debe enviar PATCH con el nombre modificado, cerrar modal y recargar', () => {
    const categoriaActualizada: CategoriaAdministrativa = {
      ...mockCategorias[0],
      nombre_categoria: 'Ficción Histórica',
    };
    categoriasServiceMock.modificar.mockReturnValue(of(categoriaActualizada));

    fixture.detectChanges();
    categoriasServiceMock.listar.mockClear();

    component.abrirModalEdicion(mockCategorias[0]);
    component.formCategoria.patchValue({ nombre_categoria: '  Ficción Histórica  ' });
    component.onSubmit();

    expect(categoriasServiceMock.modificar).toHaveBeenCalledWith(1, {
      nombre_categoria: 'Ficción Histórica',
    });
    expect(categoriasServiceMock.actualizar).not.toHaveBeenCalled();
    expect(component.modalAbierto()).toBe(false);
    expect(component.guardando()).toBe(false);
    expect(component.mensajeExito()).toContain('Ficción Histórica');
    expect(component.mensajeExito()).toContain('#1');
    expect(categoriasServiceMock.listar).toHaveBeenCalledTimes(1);
  });

  // ---------------------------------------------------------------------------
  // 7. Manejo de duplicidad de nombres (HTTP 400 del backend) y otros errores
  // ---------------------------------------------------------------------------

  it('debe capturar error HTTP 400 por nombre duplicado del backend y mostrarlo bajo el campo sin borrar el texto', () => {
    const mensajeErrorBackend = 'Ya existe una categoría con el nombre "Ciencia Ficción".';
    categoriasServiceMock.registrar.mockReturnValue(
      throwError(() => ({
        status: 400,
        error: { nombre_categoria: [mensajeErrorBackend] },
      })),
    );

    fixture.detectChanges();
    component.abrirModalRegistro();
    component.formCategoria.patchValue({ nombre_categoria: 'Ciencia Ficción' });
    component.onSubmit();

    expect(component.guardando()).toBe(false);
    expect(component.modalAbierto()).toBe(true);
    // El texto ingresado se conserva en el formulario para facilitar corrección
    expect(component.formCategoria.get('nombre_categoria')?.value).toBe('Ciencia Ficción');
    // El error se muestra en el campo específico
    expect(component.errorCampoNombre()).toBe(mensajeErrorBackend);
    expect(component.obtenerErrorNombre()).toBe(mensajeErrorBackend);
    expect(component.errorGeneralModal()).toBeNull();
  });

  it('debe manejar errores HTTP generales (como 403 o 500) mostrándolos en el modal sin tratarlos como duplicidad', () => {
    categoriasServiceMock.registrar.mockReturnValue(
      throwError(() => ({
        status: 403,
        error: { detail: 'No tiene permisos para ejecutar esta acción.' },
      })),
    );

    fixture.detectChanges();
    component.abrirModalRegistro();
    component.formCategoria.patchValue({ nombre_categoria: 'Poesía' });
    component.onSubmit();

    expect(component.guardando()).toBe(false);
    expect(component.modalAbierto()).toBe(true);
    expect(component.errorCampoNombre()).toBeNull();
    expect(component.errorGeneralModal()).toBe('No tiene permisos para ejecutar esta acción.');
  });

  // ---------------------------------------------------------------------------
  // 8. Prevención de envíos dobles y bloqueo de interfaz
  // ---------------------------------------------------------------------------

  it('no debe procesar envíos si guardando() ya está activo', () => {
    fixture.detectChanges();
    component.abrirModalRegistro();
    component.guardando.set(true);

    component.formCategoria.patchValue({ nombre_categoria: 'Drama' });
    component.onSubmit();

    expect(categoriasServiceMock.registrar).not.toHaveBeenCalled();
  });

  it('el botón de guardar debe deshabilitarse y mostrar el texto "Guardando..." cuando guardando() es true', () => {
    fixture.detectChanges();
    component.abrirModalRegistro();
    component.guardando.set(true);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const btnGuardar = compiled.querySelector('#btn-guardar-categoria') as HTMLButtonElement;
    expect(btnGuardar.disabled).toBe(true);
    expect(btnGuardar.textContent).toContain('Guardando...');
  });

  // ---------------------------------------------------------------------------
  // 9. Accesibilidad y teclado
  // ---------------------------------------------------------------------------

  it('debe cerrar el modal al pulsar la tecla Escape si no se está guardando', () => {
    fixture.detectChanges();
    component.abrirModalRegistro();
    expect(component.modalAbierto()).toBe(true);

    const escapeEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    component.manejarTecladoModal(escapeEvent);

    expect(component.modalAbierto()).toBe(false);
  });

  it('no debe cerrar el modal al pulsar Escape si se está guardando', () => {
    fixture.detectChanges();
    component.abrirModalRegistro();
    component.guardando.set(true);

    const escapeEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    component.manejarTecladoModal(escapeEvent);

    expect(component.modalAbierto()).toBe(true);
  });

  // ---------------------------------------------------------------------------
  // 10. Restricciones de diseño (Sin botones DELETE)
  // ---------------------------------------------------------------------------

  it('la interfaz de categorías no debe contener botones de eliminación ni baja', () => {
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const todosLosBotones = Array.from(compiled.querySelectorAll('button')).map(
      (b) => b.textContent?.trim().toLowerCase() || '',
    );

    for (const texto of todosLosBotones) {
      expect(texto).not.toContain('eliminar');
      expect(texto).not.toContain('borrar');
      expect(texto).not.toContain('baja');
    }
  });

  it('cerrarMensajeExito() debe limpiar la notificación de éxito', () => {
    component.mensajeExito.set('Categoría guardada');
    expect(component.mensajeExito()).toBe('Categoría guardada');

    component.cerrarMensajeExito();
    expect(component.mensajeExito()).toBeNull();
  });
});
