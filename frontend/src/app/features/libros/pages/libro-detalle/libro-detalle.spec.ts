import { HttpErrorResponse } from '@angular/common/http';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { ActivatedRoute, convertToParamMap, provideRouter, Router, RouterLink } from '@angular/router';
import { of, throwError } from 'rxjs';

import {
  Ejemplar,
  EjemplaresPaginados,
  Libro,
} from '../../models/libros.models';
import { EjemplaresService } from '../../services/ejemplares.service';
import { LibrosService } from '../../services/libros.service';
import { LibroDetalleComponent } from './libro-detalle';

describe('LibroDetalleComponent', () => {
  let component: LibroDetalleComponent;
  let fixture: ComponentFixture<LibroDetalleComponent>;
  let librosServiceMock: {
    obtener: ReturnType<typeof vi.fn>;
  };
  let ejemplaresServiceMock: {
    listar: ReturnType<typeof vi.fn>;
    registrar: ReturnType<typeof vi.fn>;
  };
  let router: Router;

  const mockLibro: Libro = {
    libro_id: 1,
    titulo: 'Cien Años de Soledad',
    isbn: '9780307474728',
    fecha_publicacion: '1967-05-30',
    autores: [{ autor_id: 1, nombre: 'Gabriel García Márquez' }],
    categorias: [{ categoria_id: 1, nombre_categoria: 'Realismo Mágico' }],
  };

  const mockEjemplares: Ejemplar[] = [
    {
      ejemplar_id: 101,
      libro_id: 1,
      libro: { libro_id: 1, titulo: 'Cien Años de Soledad', isbn: '9780307474728' },
      codigo_inventario: 'CAS-001',
      estado: 'ACTIVO',
    },
    {
      ejemplar_id: 102,
      libro_id: 1,
      libro: { libro_id: 1, titulo: 'Cien Años de Soledad', isbn: '9780307474728' },
      codigo_inventario: 'CAS-002',
      estado: 'MANTENIMIENTO',
    },
    {
      ejemplar_id: 103,
      libro_id: 1,
      libro: { libro_id: 1, titulo: 'Cien Años de Soledad', isbn: '9780307474728' },
      codigo_inventario: 'CAS-003',
      estado: 'BAJA',
    },
  ];

  const mockEjemplaresPaginados: EjemplaresPaginados = {
    count: 3,
    next: null,
    previous: null,
    results: mockEjemplares,
  };

  async function configurarTestBed(idParam: string = '1', fragment: string | null = null) {
    librosServiceMock = {
      obtener: vi.fn().mockReturnValue(of(mockLibro)),
    };
    ejemplaresServiceMock = {
      listar: vi.fn().mockReturnValue(of(mockEjemplaresPaginados)),
      registrar: vi.fn().mockReturnValue(
        of({
          ejemplar_id: 104,
          libro_id: 1,
          libro: { libro_id: 1, titulo: 'Cien Años de Soledad', isbn: '9780307474728' },
          codigo_inventario: 'CAS-004',
          estado: 'ACTIVO' as const,
        }),
      ),
    };

    await TestBed.configureTestingModule({
      imports: [LibroDetalleComponent],
      providers: [
        provideRouter([{ path: '**', component: class {} }]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: convertToParamMap({ id: idParam }) },
            fragment: of(fragment),
          },
        },
        { provide: LibrosService, useValue: librosServiceMock },
        { provide: EjemplaresService, useValue: ejemplaresServiceMock },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    fixture = TestBed.createComponent(LibroDetalleComponent);
    component = fixture.componentInstance;
  }

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Inicialización y carga de datos', () => {
    beforeEach(async () => {
      await configurarTestBed('1');
    });

    it('debe crearse correctamente e iniciar la carga del libro y sus ejemplares', () => {
      fixture.detectChanges();
      expect(component).toBeTruthy();
      expect(component.libroId).toBe(1);
      expect(librosServiceMock.obtener).toHaveBeenCalledWith(1);
      expect(ejemplaresServiceMock.listar).toHaveBeenCalledWith({
        libro_id: 1,
        page: 1,
        page_size: 10,
      });
    });

    it('debe renderizar la información bibliográfica del libro', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;

      expect(compiled.querySelector('h1')?.textContent).toContain('Cien Años de Soledad');
      expect(compiled.querySelector('.isbn-badge')?.textContent).toContain('9780307474728');
      expect(compiled.querySelector('.data-value')?.textContent).toContain('1967-05-30');
      expect(compiled.querySelector('.data-value--authors')?.textContent).toContain(
        'Gabriel García Márquez',
      );
      expect(compiled.querySelector('.category-chip')?.textContent).toContain(
        'Realismo Mágico',
      );
    });

    it('debe mostrar "Sin autores asignados" y "Sin categorías asignadas" cuando las listas estén vacías', () => {
      librosServiceMock.obtener.mockReturnValue(
        of({
          ...mockLibro,
          autores: [],
          categorias: [],
          fecha_publicacion: null,
        }),
      );
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;

      expect(compiled.querySelector('.data-value--authors')?.textContent).toContain(
        'Sin autores asignados',
      );
      expect(compiled.querySelector('.empty-badge')?.textContent).toContain(
        'Sin categorías asignadas',
      );
    });
  });

  describe('Parámetro de ruta inválido', () => {
    it('debe redirigir a /libros si el parámetro id es inválido o no numérico', async () => {
      TestBed.resetTestingModule();
      await configurarTestBed('invalido');
      const navigateSpy = vi.spyOn(router, 'navigateByUrl');
      fixture.detectChanges();

      expect(navigateSpy).toHaveBeenCalledWith('/libros');
    });
  });

  describe('Listado y estados operativos de ejemplares', () => {
    beforeEach(async () => {
      await configurarTestBed('1');
    });

    it('debe renderizar los ejemplares en la tabla con sus estados operativos correspondientes', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;

      const filas = compiled.querySelectorAll('tbody tr');
      expect(filas.length).toBe(3);

      // Ejemplar 1: ACTIVO
      expect(filas[0].textContent).toContain('CAS-001');
      expect(filas[0].textContent).toContain('Activo');
      expect(filas[0].querySelector('.badge--activo')).toBeTruthy();

      // Ejemplar 2: MANTENIMIENTO
      expect(filas[1].textContent).toContain('CAS-002');
      expect(filas[1].textContent).toContain('Mantenimiento');
      expect(filas[1].querySelector('.badge--mantenimiento')).toBeTruthy();

      // Ejemplar 3: BAJA
      expect(filas[2].textContent).toContain('CAS-003');
      expect(filas[2].textContent).toContain('Baja');
      expect(filas[2].querySelector('.badge--baja')).toBeTruthy();
    });

    it('el botón de registrar ejemplar debe estar activo y los botones de cambiar estado deben estar deshabilitados (Etapa 6)', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;

      const btnNuevo = compiled.querySelector('#btn-abrir-registro-ejemplar') as HTMLButtonElement;
      expect(btnNuevo).toBeTruthy();
      expect(btnNuevo.disabled).toBe(false);

      const btnAccion = compiled.querySelector('.table-action-btn') as HTMLButtonElement;
      expect(btnAccion.disabled).toBe(true);
      expect(btnAccion.getAttribute('title')).toContain('Etapa 5');
    });

    it('debe mostrar estado vacío cuando el libro no tenga ejemplares', () => {
      ejemplaresServiceMock.listar.mockReturnValue(
        of({
          count: 0,
          next: null,
          previous: null,
          results: [],
        }),
      );
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;

      expect(compiled.querySelector('.empty-title')?.textContent).toContain(
        'Sin ejemplares registrados',
      );
      expect(compiled.querySelector('table')).toBeNull();
    });
  });

  describe('Paginación de ejemplares', () => {
    beforeEach(async () => {
      await configurarTestBed('1');
    });

    it('debe paginar ejemplares y deshabilitar botones según la página actual', () => {
      ejemplaresServiceMock.listar.mockReturnValue(
        of({
          count: 25,
          next: 'http://localhost:8000/api/ejemplares/?page=2',
          previous: null,
          results: mockEjemplares,
        }),
      );
      fixture.detectChanges();

      expect(component.totalPaginasEjemplares()).toBe(3);
      expect(component.paginaEjemplares()).toBe(1);

      ejemplaresServiceMock.listar.mockClear();
      component.cambiarPaginaEjemplares(2);

      expect(component.paginaEjemplares()).toBe(2);
      expect(ejemplaresServiceMock.listar).toHaveBeenCalledWith({
        libro_id: 1,
        page: 2,
        page_size: 10,
      });
    });

    it('no debe cambiar de página si el número es inválido o igual a la actual', () => {
      fixture.detectChanges();
      ejemplaresServiceMock.listar.mockClear();

      component.cambiarPaginaEjemplares(1); // misma
      expect(ejemplaresServiceMock.listar).not.toHaveBeenCalled();

      component.cambiarPaginaEjemplares(0); // menor que 1
      expect(ejemplaresServiceMock.listar).not.toHaveBeenCalled();

      component.cambiarPaginaEjemplares(99); // mayor que totalPaginas
      expect(ejemplaresServiceMock.listar).not.toHaveBeenCalled();
    });
  });

  describe('Manejo de errores y resiliencia', () => {
    beforeEach(async () => {
      await configurarTestBed('1');
    });

    it('debe mostrar mensaje específico si el libro no existe (HTTP 404)', () => {
      librosServiceMock.obtener.mockReturnValue(
        throwError(() => new HttpErrorResponse({ status: 404 })),
      );
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;

      expect(component.errorLibro()).toBe('El libro solicitado no existe en el catálogo.');
      expect(compiled.querySelector('.state-card--error')?.textContent).toContain(
        'El libro solicitado no existe en el catálogo.',
      );
    });

    it('debe mostrar mensaje de fallo de conexión si el servidor no responde (HTTP 0)', () => {
      librosServiceMock.obtener.mockReturnValue(
        throwError(() => new HttpErrorResponse({ status: 0 })),
      );
      fixture.detectChanges();

      expect(component.errorLibro()).toBe('No fue posible conectar con el servidor.');
    });

    it('si falla la consulta de ejemplares, NO debe ocultar la ficha del libro que cargó correctamente', () => {
      librosServiceMock.obtener.mockReturnValue(of(mockLibro));
      ejemplaresServiceMock.listar.mockReturnValue(
        throwError(() => new HttpErrorResponse({ status: 500 })),
      );
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;

      // La ficha del libro se mantiene visible
      expect(compiled.querySelector('.detail-card')).toBeTruthy();
      expect(compiled.querySelector('.isbn-badge')?.textContent).toContain('9780307474728');

      // La sección de ejemplares muestra el error aislado con reintentar
      expect(component.errorEjemplares()).toBe(
        'No fue posible cargar los ejemplares. Inténtalo nuevamente.',
      );
      expect(compiled.querySelector('.state-message--error')?.textContent).toContain(
        'No fue posible cargar los ejemplares.',
      );
    });
  });

  describe('Navegación', () => {
    beforeEach(async () => {
      await configurarTestBed('1');
    });

    it('el enlace Volver a Gestión de Libros debe apuntar a /libros', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      const backLink = compiled.querySelector('.back-link') as HTMLAnchorElement;

      expect(backLink.getAttribute('routerLink')).toBe('/libros');
    });

    it('el botón Editar libro debe estar visible y apuntar a /libros/1/editar', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      const btnEditar = compiled.querySelector('#btn-editar-libro') as HTMLAnchorElement;

      expect(btnEditar).toBeTruthy();
      expect(btnEditar.getAttribute('href')).toContain('/libros/1/editar');
    });
  });

  describe('Registro de nuevos ejemplares físicos (Etapa 5)', () => {
    beforeEach(async () => {
      await configurarTestBed('1');
      fixture.detectChanges();
    });

    it('1. Apertura del formulario o modal: debe abrir el modal y mostrar los datos del libro asociado', () => {
      const btnAbrir = fixture.nativeElement.querySelector('#btn-abrir-registro-ejemplar') as HTMLButtonElement;
      expect(btnAbrir).toBeTruthy();

      btnAbrir.click();
      fixture.detectChanges();

      expect(component.modalRegistroAbierto()).toBe(true);

      const modal = fixture.nativeElement.querySelector('.modal-dialog');
      expect(modal).toBeTruthy();

      // Debe visualizar el libro al que se asociará el nuevo ejemplar
      expect(modal.querySelector('.summary-title')?.textContent).toContain('Cien Años de Soledad');
      expect(modal.querySelector('.summary-isbn')?.textContent).toContain('9780307474728');
      expect(modal.querySelector('.badge--activo')?.textContent).toContain('Activo');

      // El campo de código de inventario debe estar inicialmente vacío
      const inputCodigo = modal.querySelector('#codigo-inventario') as HTMLInputElement;
      expect(inputCodigo.value).toBe('');
    });

    it('2. Cancelación: debe cerrar el modal sin registrar al pulsar Cancelar o el botón de cierre', () => {
      component.abrirModalRegistro();
      fixture.detectChanges();
      expect(component.modalRegistroAbierto()).toBe(true);

      // Cancelar con el botón Cancelar
      const btnCancelar = fixture.nativeElement.querySelector('.modal-actions .secondary-button') as HTMLButtonElement;
      btnCancelar.click();
      fixture.detectChanges();

      expect(component.modalRegistroAbierto()).toBe(false);
      expect(ejemplaresServiceMock.registrar).not.toHaveBeenCalled();

      // Probar cierre mediante botón '✕'
      component.abrirModalRegistro();
      fixture.detectChanges();
      const btnCerrar = fixture.nativeElement.querySelector('.btn-cerrar-modal') as HTMLButtonElement;
      btnCerrar.click();
      fixture.detectChanges();

      expect(component.modalRegistroAbierto()).toBe(false);

      // Probar cierre mediante click en backdrop
      component.abrirModalRegistro();
      fixture.detectChanges();
      component.cerrarModalRegistro();
      expect(component.modalRegistroAbierto()).toBe(false);
    });

    it('3. Validaciones del código de inventario: debe exigir el campo obligatorio al enviar vacío', () => {
      component.abrirModalRegistro();
      fixture.detectChanges();

      component.onSubmitRegistroEjemplar();
      fixture.detectChanges();

      expect(component.errorDeCodigo()).toBe('Este campo es obligatorio.');
      expect(component.formRegistroEjemplar.invalid).toBe(true);
      expect(ejemplaresServiceMock.registrar).not.toHaveBeenCalled();
    });

    it('3b. Validaciones del código de inventario: debe rechazar más de 15 caracteres', () => {
      component.abrirModalRegistro();
      fixture.detectChanges();

      component.formRegistroEjemplar.get('codigo_inventario')?.setValue('1234567890123456');
      component.formRegistroEjemplar.get('codigo_inventario')?.markAsTouched();
      fixture.detectChanges();

      expect(component.errorDeCodigo()).toBe('Máximo 15 caracteres.');
      expect(component.formRegistroEjemplar.invalid).toBe(true);
    });

    it('3c. Validaciones del código de inventario: no debe permitir solo espacios en blanco', () => {
      component.abrirModalRegistro();
      fixture.detectChanges();

      component.formRegistroEjemplar.get('codigo_inventario')?.setValue('     ');
      component.formRegistroEjemplar.get('codigo_inventario')?.markAsTouched();
      fixture.detectChanges();

      expect(component.errorDeCodigo()).toBe('No puede contener solo espacios en blanco.');
      expect(component.formRegistroEjemplar.invalid).toBe(true);
    });

    it('4. Asociación correcta mediante libro_id: debe obtener libro_id de la ruta y enviarlo inmutablemente', () => {
      component.abrirModalRegistro();
      component.formRegistroEjemplar.get('codigo_inventario')?.setValue('CAS-004');

      component.onSubmitRegistroEjemplar();

      expect(ejemplaresServiceMock.registrar).toHaveBeenCalledWith(
        expect.objectContaining({
          libro_id: 1,
        }),
      );
    });

    it('5. Envío de POST /api/ejemplares/: debe registrar con estado predeterminado ACTIVO', () => {
      component.abrirModalRegistro();
      component.formRegistroEjemplar.get('codigo_inventario')?.setValue('CAS-004');

      component.onSubmitRegistroEjemplar();

      expect(ejemplaresServiceMock.registrar).toHaveBeenCalledWith({
        libro_id: 1,
        codigo_inventario: 'CAS-004',
        estado: 'ACTIVO',
      });
    });

    it('6. Registro exitoso: debe cerrar el modal y mostrar mensaje inequívoco de confirmación', () => {
      component.abrirModalRegistro();
      component.formRegistroEjemplar.get('codigo_inventario')?.setValue('CAS-004');

      component.onSubmitRegistroEjemplar();
      fixture.detectChanges();

      expect(component.modalRegistroAbierto()).toBe(false);
      expect(component.mensajeExito()).toBe(
        'Ejemplar con código «CAS-004» registrado con éxito.',
      );

      const banner = fixture.nativeElement.querySelector('.success-banner');
      expect(banner).toBeTruthy();
      expect(banner.textContent).toContain('Ejemplar con código «CAS-004» registrado con éxito.');

      // Descartar mensaje
      component.limpiarMensajeExito();
      fixture.detectChanges();
      expect(component.mensajeExito()).toBeNull();
      expect(fixture.nativeElement.querySelector('.success-banner')).toBeNull();
    });

    it('7. Actualización de la tabla y del contador: debe recargar la lista de ejemplares', () => {
      const nuevoEjemplar: Ejemplar = {
        ejemplar_id: 104,
        libro_id: 1,
        libro: { libro_id: 1, titulo: 'Cien Años de Soledad', isbn: '9780307474728' },
        codigo_inventario: 'CAS-004',
        estado: 'ACTIVO',
      };

      ejemplaresServiceMock.listar.mockReturnValue(
        of({
          count: 4,
          next: null,
          previous: null,
          results: [...mockEjemplares, nuevoEjemplar],
        }),
      );

      component.abrirModalRegistro();
      component.formRegistroEjemplar.get('codigo_inventario')?.setValue('CAS-004');

      ejemplaresServiceMock.listar.mockClear();
      component.onSubmitRegistroEjemplar();
      fixture.detectChanges();

      expect(ejemplaresServiceMock.listar).toHaveBeenCalledWith({
        libro_id: 1,
        page: 1,
        page_size: 10,
      });

      expect(component.totalEjemplares()).toBe(4);
      const filas = fixture.nativeElement.querySelectorAll('tbody tr');
      expect(filas.length).toBe(4);
      expect(fixture.nativeElement.querySelector('.count-badge')?.textContent).toContain('4');
    });

    it('8. Registro cuando el libro no tenía ejemplares: debe reemplazar el estado vacío por la tabla', () => {
      // Estado inicial vacío
      component.ejemplares.set([]);
      component.totalEjemplares.set(0);
      fixture.detectChanges();

      expect(fixture.nativeElement.querySelector('.empty-title')?.textContent).toContain(
        'Sin ejemplares registrados',
      );
      expect(fixture.nativeElement.querySelector('table')).toBeNull();

      // Tras registro, el servicio retorna 1 ejemplar
      const nuevoEjemplar: Ejemplar = {
        ejemplar_id: 101,
        libro_id: 1,
        libro: { libro_id: 1, titulo: 'Cien Años de Soledad', isbn: '9780307474728' },
        codigo_inventario: 'CAS-001',
        estado: 'ACTIVO',
      };
      ejemplaresServiceMock.listar.mockReturnValue(
        of({
          count: 1,
          next: null,
          previous: null,
          results: [nuevoEjemplar],
        }),
      );

      component.abrirModalRegistro();
      component.formRegistroEjemplar.get('codigo_inventario')?.setValue('CAS-001');
      component.onSubmitRegistroEjemplar();
      fixture.detectChanges();

      // El estado vacío desaparece y se muestra la tabla
      expect(fixture.nativeElement.querySelector('.empty-title')).toBeNull();
      expect(fixture.nativeElement.querySelector('table')).toBeTruthy();
      expect(component.totalEjemplares()).toBe(1);
    });

    it('9. Prevención de doble envío: no debe permitir envíos simultáneos ni registrar dos veces', () => {
      component.abrirModalRegistro();
      component.formRegistroEjemplar.get('codigo_inventario')?.setValue('CAS-004');

      component.guardandoEjemplar.set(true);
      fixture.detectChanges();

      const btnGuardar = fixture.nativeElement.querySelector('#btn-guardar-ejemplar') as HTMLButtonElement;
      expect(btnGuardar.disabled).toBe(true);
      expect(btnGuardar.textContent).toContain('Guardando...');

      // Intento de envío manual mientras guarda
      ejemplaresServiceMock.registrar.mockClear();
      component.onSubmitRegistroEjemplar();

      expect(ejemplaresServiceMock.registrar).not.toHaveBeenCalled();

      // Tampoco debe permitir cerrar el modal mientras se guarda
      component.cerrarModalRegistro();
      expect(component.modalRegistroAbierto()).toBe(true);
    });

    it('10. Error por código duplicado: debe mostrar mensaje de error junto al campo', () => {
      ejemplaresServiceMock.registrar.mockReturnValue(
        throwError(
          () =>
            new HttpErrorResponse({
              status: 400,
              error: {
                codigo_inventario: ['Ya existe un ejemplar con este código de inventario.'],
              },
            }),
        ),
      );

      component.abrirModalRegistro();
      component.formRegistroEjemplar.get('codigo_inventario')?.setValue('CAS-001');

      component.onSubmitRegistroEjemplar();
      fixture.detectChanges();

      expect(component.errorCampoCodigo()).toBe(
        'Ya existe un ejemplar con este código de inventario.',
      );
      expect(component.errorDeCodigo()).toBe(
        'Ya existe un ejemplar con este código de inventario.',
      );

      const errorElem = fixture.nativeElement.querySelector('#error-codigo-inventario');
      expect(errorElem).toBeTruthy();
      expect(errorElem.textContent).toContain('Ya existe un ejemplar con este código de inventario.');

      // El modal debe permanecer abierto
      expect(component.modalRegistroAbierto()).toBe(true);

      // La ficha bibliográfica del libro no se oculta
      expect(fixture.nativeElement.querySelector('.detail-card')).toBeTruthy();
    });

    it('11. Fallos de red: debe manejar error HTTP 0 sin ocultar la ficha del libro', () => {
      ejemplaresServiceMock.registrar.mockReturnValue(
        throwError(() => new HttpErrorResponse({ status: 0 })),
      );

      component.abrirModalRegistro();
      component.formRegistroEjemplar.get('codigo_inventario')?.setValue('CAS-004');

      component.onSubmitRegistroEjemplar();
      fixture.detectChanges();

      expect(component.errorRegistro()).toBe('No fue posible conectar con el servidor.');
      expect(component.modalRegistroAbierto()).toBe(true);

      const modalError = fixture.nativeElement.querySelector('.modal-error');
      expect(modalError).toBeTruthy();
      expect(modalError.textContent).toContain('No fue posible conectar con el servidor.');

      // La ficha bibliográfica se conserva visible
      expect(fixture.nativeElement.querySelector('.detail-card')).toBeTruthy();
    });

    it('12. Comportamiento con paginación activa: debe recargar respetando la página actual', () => {
      component.paginaEjemplares.set(2);
      component.totalEjemplares.set(25);

      component.abrirModalRegistro();
      component.formRegistroEjemplar.get('codigo_inventario')?.setValue('CAS-026');

      ejemplaresServiceMock.listar.mockClear();
      component.onSubmitRegistroEjemplar();

      // Debe consultar específicamente la página activa (2)
      expect(ejemplaresServiceMock.listar).toHaveBeenCalledWith({
        libro_id: 1,
        page: 2,
        page_size: 10,
      });
      expect(component.paginaEjemplares()).toBe(2);
    });
  });
});

