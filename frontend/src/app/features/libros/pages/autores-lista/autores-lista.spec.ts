import {
  ComponentFixture,
  TestBed,
} from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import {
  AutorAdministrativo,
  AutoresPaginados,
} from '../../models/autores.models';
import { AutoresService } from '../../services/autores.service';
import { AutoresListaComponent } from './autores-lista';

describe('AutoresListaComponent (Ticket 3.3 Etapa 2)', () => {
  let component: AutoresListaComponent;
  let fixture: ComponentFixture<AutoresListaComponent>;
  let autoresServiceMock: {
    listar: ReturnType<typeof vi.fn>;
    registrar: ReturnType<typeof vi.fn>;
    modificar: ReturnType<typeof vi.fn>;
    obtenerPorId: ReturnType<typeof vi.fn>;
    obtener: ReturnType<typeof vi.fn>;
    actualizar: ReturnType<typeof vi.fn>;
  };

  const mockAutores: AutorAdministrativo[] = [
    {
      autor_id: 1,
      nombre: 'Gabriel García Márquez',
      nacionalidad: 'Colombiana',
      fecha_nacimiento: '1927-03-06',
      cantidad_libros: 3,
    },
    {
      autor_id: 2,
      nombre: 'Isabel Allende',
      nacionalidad: 'Chilena',
      fecha_nacimiento: '1942-08-02',
      cantidad_libros: 1,
    },
    {
      // Homónimo permitido
      autor_id: 3,
      nombre: 'Gabriel García Márquez',
      nacionalidad: null,
      fecha_nacimiento: null,
      cantidad_libros: 0,
    },
  ];

  const mockRespuestaPaginada: AutoresPaginados = {
    count: 3,
    next: null,
    previous: null,
    results: mockAutores,
  };

  beforeEach(async () => {
    autoresServiceMock = {
      listar: vi.fn().mockReturnValue(of(mockRespuestaPaginada)),
      registrar: vi.fn(),
      modificar: vi.fn(),
      obtenerPorId: vi.fn(),
      obtener: vi.fn(),
      actualizar: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [AutoresListaComponent],
      providers: [
        { provide: AutoresService, useValue: autoresServiceMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AutoresListaComponent);
    component = fixture.componentInstance;
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  // ---------------------------------------------------------------------------
  // 1. Inicialización y renderizado
  // ---------------------------------------------------------------------------

  it('debe crearse e inicializar listado de autores', () => {
    fixture.detectChanges();

    expect(component).toBeTruthy();
    expect(autoresServiceMock.listar).toHaveBeenCalledTimes(1);
    expect(component.autores().length).toBe(3);
    expect(component.total()).toBe(3);
  });

  it('debe renderizar los autores en la tabla mostrando ID, nombre y libros asociados', () => {
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const filas = compiled.querySelectorAll('tbody tr');
    expect(filas.length).toBe(3);

    // Primera fila
    const fila1 = filas[0];
    expect(fila1.querySelector('.id-badge')?.textContent?.trim()).toBe('#1');
    expect(fila1.querySelector('.autor-nombre')?.textContent?.trim()).toBe('Gabriel García Márquez');
    expect(fila1.querySelector('.count-badge')?.textContent).toContain('3');
    expect(fila1.querySelector('.count-badge')?.textContent).toContain('libros');

    // Botón de acción Editar presente
    const btnEditar = fila1.querySelector('.table-action-btn--edit');
    expect(btnEditar).toBeTruthy();
    expect(btnEditar?.textContent?.trim()).toBe('Editar');
  });

  it('debe mostrar el total en la tarjeta de resumen', () => {
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const totalEl = compiled.querySelector('.summary-card strong');
    expect(totalEl?.textContent?.trim()).toBe('3');
  });

  // ---------------------------------------------------------------------------
  // 2. Homónimos
  // ---------------------------------------------------------------------------

  it('debe permitir autores homónimos distinguiéndolos por su ID en la tabla', () => {
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const filas = compiled.querySelectorAll('tbody tr');

    const fila1 = filas[0];
    const fila3 = filas[2];

    // Mismo nombre
    expect(fila1.querySelector('.autor-nombre')?.textContent?.trim()).toBe('Gabriel García Márquez');
    expect(fila3.querySelector('.autor-nombre')?.textContent?.trim()).toBe('Gabriel García Márquez');

    // Diferente ID claramente visible
    expect(fila1.querySelector('.id-badge')?.textContent?.trim()).toBe('#1');
    expect(fila3.querySelector('.id-badge')?.textContent?.trim()).toBe('#3');
  });

  // ---------------------------------------------------------------------------
  // 3. Búsqueda con debounce
  // ---------------------------------------------------------------------------

  it('debe filtrar autores tras el debounce de 300 ms y reiniciar a página 1', () => {
    vi.useFakeTimers();
    fixture.detectChanges();
    autoresServiceMock.listar.mockClear();

    const resultadoBusqueda: AutoresPaginados = {
      count: 1,
      next: null,
      previous: null,
      results: [mockAutores[1]], // Isabel Allende
    };
    autoresServiceMock.listar.mockReturnValue(of(resultadoBusqueda));

    component.pagina.set(2);
    expect(component.pagina()).toBe(2);
    autoresServiceMock.listar.mockClear();

    component.actualizarBusqueda('isabel');

    // Antes de 300ms no debe haber llamado
    vi.advanceTimersByTime(150);
    expect(autoresServiceMock.listar).not.toHaveBeenCalled();

    // Tras 300ms se ejecuta
    vi.advanceTimersByTime(150);
    expect(autoresServiceMock.listar).toHaveBeenCalledWith({
      nombre: 'isabel',
      page: 1,
      page_size: 10,
    });
    expect(component.pagina()).toBe(1);
    expect(component.autores().length).toBe(1);
  });

  it('limpiarBusqueda() debe restablecer el filtro y recargar desde página 1', () => {
    fixture.detectChanges();
    autoresServiceMock.listar.mockClear();

    component.busquedaNombre.set('algo');
    component.pagina.set(3);

    component.limpiarBusqueda();

    expect(component.busquedaNombre()).toBe('');
    expect(component.pagina()).toBe(1);
    expect(autoresServiceMock.listar).toHaveBeenCalledWith({
      nombre: undefined,
      page: 1,
      page_size: 10,
    });
  });

  // ---------------------------------------------------------------------------
  // 4. Paginación
  // ---------------------------------------------------------------------------

  it('debe calcular totalPaginas, primerRegistro y ultimoRegistro correctamente', () => {
    fixture.detectChanges();

    // 3 autores, pageSize 10 -> 1 página
    expect(component.totalPaginas()).toBe(1);
    expect(component.primerRegistro()).toBe(1);
    expect(component.ultimoRegistro()).toBe(3);

    // Simular 25 registros en página 2
    component.total.set(25);
    component.pagina.set(2);
    expect(component.totalPaginas()).toBe(3);
    expect(component.primerRegistro()).toBe(11);
    expect(component.ultimoRegistro()).toBe(20);
  });

  it('cambiarPagina() debe cambiar de página y solicitar los registros correspondientes', () => {
    fixture.detectChanges();
    autoresServiceMock.listar.mockClear();

    component.total.set(25);
    component.cambiarPagina(2);

    expect(component.pagina()).toBe(2);
    expect(autoresServiceMock.listar).toHaveBeenCalledWith({
      nombre: undefined,
      page: 2,
      page_size: 10,
    });
  });

  it('no debe cambiar de página si el número es inválido o igual al actual', () => {
    fixture.detectChanges();
    autoresServiceMock.listar.mockClear();

    component.cambiarPagina(1); // Mismo
    component.cambiarPagina(0); // Menor a 1
    component.cambiarPagina(999); // Mayor a totalPaginas (1)

    expect(autoresServiceMock.listar).not.toHaveBeenCalled();
  });

  // ---------------------------------------------------------------------------
  // 5. Estados visuales (carga, error, vacío)
  // ---------------------------------------------------------------------------

  it('debe mostrar mensaje de carga mientras cargando() sea true', () => {
    fixture.detectChanges();
    component.cargando.set(true);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.state-message')?.textContent).toContain('Cargando autores...');
  });

  it('debe mostrar error con botón de reintento si la consulta falla', () => {
    autoresServiceMock.listar.mockReturnValue(
      throwError(() => ({ status: 500 })),
    );

    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const errorMsg = compiled.querySelector('.state-message--error');
    expect(errorMsg).toBeTruthy();
    expect(errorMsg?.textContent).toContain('No fue posible cargar el listado');

    // Botón reintentar
    autoresServiceMock.listar.mockReturnValue(of(mockRespuestaPaginada));
    const btnReintentar = errorMsg?.querySelector('button') as HTMLButtonElement;
    btnReintentar.click();

    expect(autoresServiceMock.listar).toHaveBeenCalledTimes(2);
  });

  it('debe mostrar mensaje específico cuando no haya autores en el catálogo', () => {
    autoresServiceMock.listar.mockReturnValue(
      of({ count: 0, next: null, previous: null, results: [] }),
    );

    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.empty-title')?.textContent).toContain('Sin autores registrados');
  });

  it('debe mostrar mensaje específico cuando una búsqueda no arroje resultados', () => {
    autoresServiceMock.listar.mockReturnValue(
      of({ count: 0, next: null, previous: null, results: [] }),
    );

    fixture.detectChanges();
    component.busquedaNombre.set('Borges');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.empty-title')?.textContent).toContain('Sin resultados para "Borges"');
  });

  // ---------------------------------------------------------------------------
  // 6. Modal de Registro (POST simplificado con solo 'nombre')
  // ---------------------------------------------------------------------------

  it('abrirModalRegistro() debe abrir el modal y limpiar el formulario', () => {
    fixture.detectChanges();
    expect(component.modalRegistroAbierto()).toBe(false);

    component.abrirModalRegistro();
    fixture.detectChanges();

    expect(component.modalRegistroAbierto()).toBe(true);
    expect(component.formRegistro.get('nombre')?.value).toBe('');

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('#modal-registro-titulo')?.textContent).toBe('Registrar nuevo autor');
  });

  it('cerrarModalRegistro() debe cerrar el modal y resetear errores', () => {
    fixture.detectChanges();
    component.abrirModalRegistro();
    expect(component.modalRegistroAbierto()).toBe(true);

    component.cerrarModalRegistro();
    expect(component.modalRegistroAbierto()).toBe(false);
  });

  it('onSubmitRegistro(): debe exigir nombre no vacío', () => {
    fixture.detectChanges();
    component.abrirModalRegistro();

    component.formRegistro.patchValue({ nombre: '   ' });
    component.onSubmitRegistro();

    expect(autoresServiceMock.registrar).not.toHaveBeenCalled();
    expect(component.obtenerErrorNombre('formRegistro')).toBe('El nombre del autor es obligatorio.');
  });

  it('onSubmitRegistro(): debe validar longitud máxima de 100 caracteres', () => {
    fixture.detectChanges();
    component.abrirModalRegistro();

    component.formRegistro.patchValue({ nombre: 'A'.repeat(101) });
    component.onSubmitRegistro();

    expect(autoresServiceMock.registrar).not.toHaveBeenCalled();
    expect(component.obtenerErrorNombre('formRegistro')).toBe('El nombre no puede exceder 100 caracteres.');
  });

  it('onSubmitRegistro(): debe enviar POST con solo { nombre } y recargar lista al tener éxito', () => {
    const nuevoAutor: AutorAdministrativo = {
      autor_id: 4,
      nombre: 'Julio Cortázar',
      nacionalidad: null,
      fecha_nacimiento: null,
      cantidad_libros: 0,
    };
    autoresServiceMock.registrar.mockReturnValue(of(nuevoAutor));

    fixture.detectChanges();
    autoresServiceMock.listar.mockClear();

    component.abrirModalRegistro();
    component.formRegistro.patchValue({ nombre: '  Julio Cortázar  ' });
    component.onSubmitRegistro();

    // Envía el nombre recortado sin nacionalidad ni fecha_nacimiento
    expect(autoresServiceMock.registrar).toHaveBeenCalledWith({
      nombre: 'Julio Cortázar',
    });
    expect(component.modalRegistroAbierto()).toBe(false);
    expect(component.mensajeExito()).toContain('Julio Cortázar');
    expect(component.mensajeExito()).toContain('#4');
    expect(autoresServiceMock.listar).toHaveBeenCalledTimes(1);
  });

  it('onSubmitRegistro(): debe permitir registrar un autor con nombre homónimo sin bloqueo', () => {
    const homonimo: AutorAdministrativo = {
      autor_id: 5,
      nombre: 'Gabriel García Márquez',
      nacionalidad: null,
      fecha_nacimiento: null,
      cantidad_libros: 0,
    };
    autoresServiceMock.registrar.mockReturnValue(of(homonimo));

    fixture.detectChanges();
    component.abrirModalRegistro();
    component.formRegistro.patchValue({ nombre: 'Gabriel García Márquez' });
    component.onSubmitRegistro();

    // No debe bloquearse del lado del cliente
    expect(autoresServiceMock.registrar).toHaveBeenCalledWith({
      nombre: 'Gabriel García Márquez',
    });
    expect(component.modalRegistroAbierto()).toBe(false);
  });

  it('onSubmitRegistro(): debe mostrar error HTTP 400 del backend dentro del modal', () => {
    autoresServiceMock.registrar.mockReturnValue(
      throwError(() => ({
        status: 400,
        error: { error: 'Nombre de autor inválido.' },
      })),
    );

    fixture.detectChanges();
    component.abrirModalRegistro();
    component.formRegistro.patchValue({ nombre: 'X' });
    component.onSubmitRegistro();

    expect(component.guardando()).toBe(false);
    expect(component.modalRegistroAbierto()).toBe(true);
    expect(component.errorRegistro()).toBe('Nombre de autor inválido.');
  });

  // ---------------------------------------------------------------------------
  // 7. Modal de Edición (PATCH simplificado con solo 'nombre')
  // ---------------------------------------------------------------------------

  it('abrirModalEdicion() debe abrir el modal y precargar el nombre e ID del autor', () => {
    fixture.detectChanges();
    expect(component.modalEdicionAbierto()).toBe(false);

    component.abrirModalEdicion(mockAutores[0]);
    fixture.detectChanges();

    expect(component.modalEdicionAbierto()).toBe(true);
    expect(component.autorSeleccionado()?.autor_id).toBe(1);
    expect(component.formEdicion.get('nombre')?.value).toBe('Gabriel García Márquez');

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('#modal-edicion-titulo')?.textContent).toBe('Editar nombre de autor');
    expect(compiled.querySelector('.summary-id')?.textContent).toContain('#1');
  });

  it('cerrarModalEdicion() debe cerrar el modal y limpiar el autor seleccionado', () => {
    fixture.detectChanges();
    component.abrirModalEdicion(mockAutores[0]);
    expect(component.modalEdicionAbierto()).toBe(true);

    component.cerrarModalEdicion();
    expect(component.modalEdicionAbierto()).toBe(false);
    expect(component.autorSeleccionado()).toBeNull();
  });

  it('onSubmitEdicion(): debe exigir nombre no vacío', () => {
    fixture.detectChanges();
    component.abrirModalEdicion(mockAutores[0]);

    component.formEdicion.patchValue({ nombre: '   ' });
    component.onSubmitEdicion();

    expect(autoresServiceMock.modificar).not.toHaveBeenCalled();
    expect(component.obtenerErrorNombre('formEdicion')).toBe('El nombre del autor es obligatorio.');
  });

  it('onSubmitEdicion(): debe enviar PATCH exclusivamente con { nombre } al ID del autor', () => {
    const autorActualizado: AutorAdministrativo = {
      ...mockAutores[0],
      nombre: 'Gabriel José García Márquez',
    };
    autoresServiceMock.modificar.mockReturnValue(of(autorActualizado));

    fixture.detectChanges();
    autoresServiceMock.listar.mockClear();

    component.abrirModalEdicion(mockAutores[0]);
    component.formEdicion.patchValue({ nombre: '  Gabriel José García Márquez  ' });
    component.onSubmitEdicion();

    // PATCH exclusivamente con el campo modificado
    expect(autoresServiceMock.modificar).toHaveBeenCalledWith(1, {
      nombre: 'Gabriel José García Márquez',
    });
    // Jamás debe invocar actualizar (PUT)
    expect(autoresServiceMock.actualizar).not.toHaveBeenCalled();

    expect(component.modalEdicionAbierto()).toBe(false);
    expect(component.mensajeExito()).toContain('actualizado exitosamente a "Gabriel José García Márquez"');
    expect(autoresServiceMock.listar).toHaveBeenCalledTimes(1);
  });

  it('onSubmitEdicion(): debe mostrar error HTTP 400 del servidor dentro del modal', () => {
    autoresServiceMock.modificar.mockReturnValue(
      throwError(() => ({
        status: 400,
        error: { error: 'Error al actualizar autor.' },
      })),
    );

    fixture.detectChanges();
    component.abrirModalEdicion(mockAutores[0]);
    component.formEdicion.patchValue({ nombre: 'Nuevo Nombre' });
    component.onSubmitEdicion();

    expect(component.guardando()).toBe(false);
    expect(component.modalEdicionAbierto()).toBe(true);
    expect(component.errorEdicion()).toBe('Error al actualizar autor.');
  });

  // ---------------------------------------------------------------------------
  // 8. Restricciones funcionales (No DELETE)
  // ---------------------------------------------------------------------------

  it('la interfaz no debe contener botones de eliminación ni baja de autores', () => {
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

  it('cerrarMensajeExito() debe limpiar el banner de éxito', () => {
    component.mensajeExito.set('Autor registrado');
    expect(component.mensajeExito()).toBe('Autor registrado');

    component.cerrarMensajeExito();
    expect(component.mensajeExito()).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // 9. Comportamiento asíncrono con switchMap
  // ---------------------------------------------------------------------------

  it('el flujo reactivo con switchMap debe manejar cambios de página sucesivos correctamente', () => {
    // Configurar mock para devolver 30 registros (3 páginas de 10)
    const respuesta30: AutoresPaginados = { count: 30, next: null, previous: null, results: mockAutores };
    autoresServiceMock.listar.mockReturnValue(of(respuesta30));
    fixture.detectChanges();
    autoresServiceMock.listar.mockClear();

    // Primera solicitud de cambio de página (totalPaginas = 3, ok)
    component.cambiarPagina(2);
    expect(component.pagina()).toBe(2);
    expect(autoresServiceMock.listar).toHaveBeenCalledWith(
      expect.objectContaining({ page: 2 }),
    );

    autoresServiceMock.listar.mockClear();

    // Segunda solicitud: totalPaginas sigue siendo 3 (count=30 del mock)
    component.cambiarPagina(3);
    expect(component.pagina()).toBe(3);
    expect(autoresServiceMock.listar).toHaveBeenCalledWith(
      expect.objectContaining({ page: 3 }),
    );
  });

  it('el flujo reactivo debe manejar errores HTTP sin romper el stream', () => {
    fixture.detectChanges();
    autoresServiceMock.listar.mockClear();

    // Simular error 500
    autoresServiceMock.listar.mockReturnValue(throwError(() => ({ status: 500 })));
    component.cargarAutores();

    expect(component.errorListado()).toContain('No fue posible cargar');
    expect(component.cargando()).toBe(false);

    // El stream debe continuar operativo después del error
    autoresServiceMock.listar.mockReturnValue(of(mockRespuestaPaginada));
    component.cargarAutores();

    expect(component.autores().length).toBe(3);
    expect(component.errorListado()).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // 10. Accesibilidad: tecla Escape en modales
  // ---------------------------------------------------------------------------

  it('Escape debe cerrar el modal de registro si no se está guardando', () => {
    fixture.detectChanges();
    component.abrirModalRegistro();
    expect(component.modalRegistroAbierto()).toBe(true);

    const event = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true });
    component.manejarTecladoModal(event);

    expect(component.modalRegistroAbierto()).toBe(false);
  });

  it('Escape no debe cerrar el modal de registro mientras se está guardando', () => {
    fixture.detectChanges();
    component.abrirModalRegistro();
    component.guardando.set(true);

    const event = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true });
    component.manejarTecladoModal(event);

    expect(component.modalRegistroAbierto()).toBe(true);
  });

  it('Escape debe cerrar el modal de edición si no se está guardando', () => {
    fixture.detectChanges();
    component.abrirModalEdicion(mockAutores[0]);
    expect(component.modalEdicionAbierto()).toBe(true);

    const event = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true });
    component.manejarTecladoModal(event);

    expect(component.modalEdicionAbierto()).toBe(false);
  });

  it('Escape no debe hacer nada si ningún modal está abierto', () => {
    fixture.detectChanges();
    expect(component.modalRegistroAbierto()).toBe(false);
    expect(component.modalEdicionAbierto()).toBe(false);

    const event = new KeyboardEvent('keydown', { key: 'Escape', bubbles: true });
    // No debe lanzar excepción
    expect(() => component.manejarTecladoModal(event)).not.toThrow();
  });
});

