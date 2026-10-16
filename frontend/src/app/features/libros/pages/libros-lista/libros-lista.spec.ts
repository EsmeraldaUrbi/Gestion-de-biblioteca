import {
  ComponentFixture,
  TestBed,
} from '@angular/core/testing';
import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';
import { provideRouter } from '@angular/router';

import { CatalogoOpciones } from '../../../catalogo/models/catalogo.models';
import { CatalogoService } from '../../../catalogo/services/catalogo.service';
import {
  Libro,
  LibrosPaginados,
} from '../../models/libros.models';
import { LibrosService } from '../../services/libros.service';
import { LibrosListaComponent } from './libros-lista';

describe('LibrosListaComponent', () => {
  let component: LibrosListaComponent;
  let fixture: ComponentFixture<LibrosListaComponent>;
  let librosServiceMock: {
    listar: ReturnType<typeof vi.fn>;
  };
  let catalogoServiceMock: {
    obtenerFiltros: ReturnType<typeof vi.fn>;
  };

  const mockLibros: Libro[] = [
    {
      libro_id: 1,
      titulo: 'Cien Años de Soledad',
      isbn: '9780307474728',
      fecha_publicacion: '1967-05-30',
      autores: [{ autor_id: 1, nombre: 'Gabriel García Márquez' }],
      categorias: [{ categoria_id: 1, nombre_categoria: 'Realismo Mágico' }],
    },
    {
      libro_id: 2,
      titulo: 'Don Quijote de la Mancha',
      isbn: '9788424116286',
      fecha_publicacion: '1605-01-16',
      autores: [{ autor_id: 2, nombre: 'Miguel de Cervantes' }],
      categorias: [{ categoria_id: 2, nombre_categoria: 'Novela Clásica' }],
    },
  ];

  const mockRespuestaPaginada: LibrosPaginados = {
    count: 2,
    next: null,
    previous: null,
    results: mockLibros,
  };

  const mockOpcionesFiltros: CatalogoOpciones = {
    autores: [
      { autor_id: 1, nombre: 'Gabriel García Márquez' },
      { autor_id: 2, nombre: 'Miguel de Cervantes' },
    ],
    categorias: [
      { categoria_id: 1, nombre_categoria: 'Realismo Mágico' },
      { categoria_id: 2, nombre_categoria: 'Novela Clásica' },
    ],
  };

  beforeEach(async () => {
    librosServiceMock = {
      listar: vi.fn().mockReturnValue(of(mockRespuestaPaginada)),
    };

    catalogoServiceMock = {
      obtenerFiltros: vi.fn().mockReturnValue(of(mockOpcionesFiltros)),
    };

    await TestBed.configureTestingModule({
      imports: [LibrosListaComponent],
      providers: [
        provideRouter([{ path: '**', component: class {} }]),
        { provide: LibrosService, useValue: librosServiceMock },
        { provide: CatalogoService, useValue: catalogoServiceMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(LibrosListaComponent);
    component = fixture.componentInstance;
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('debe crearse e inicializarse correctamente', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  describe('Carga inicial y renderizado', () => {
    it('debe consultar filtros y listado de libros al iniciar', () => {
      fixture.detectChanges();

      expect(catalogoServiceMock.obtenerFiltros).toHaveBeenCalledTimes(1);
      expect(librosServiceMock.listar).toHaveBeenCalledWith({
        page: 1,
        page_size: 10,
      });
      expect(component.libros().length).toBe(2);
      expect(component.total()).toBe(2);
      expect(component.autoresOpciones().length).toBe(2);
      expect(component.categoriasOpciones().length).toBe(2);
    });

    it('debe renderizar los libros en la tabla', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;

      const filas = compiled.querySelectorAll('tbody tr');
      expect(filas.length).toBe(2);

      const primerTitulo = filas[0].querySelector('.book-title')?.textContent;
      expect(primerTitulo).toContain('Cien Años de Soledad');

      const primerIsbn = filas[0].querySelector('.isbn-badge')?.textContent;
      expect(primerIsbn).toContain('9780307474728');

      const primerAutor = filas[0].querySelector('.book-authors')?.textContent;
      expect(primerAutor).toContain('Gabriel García Márquez');

      const primeraCategoria = filas[0].querySelector('.category-chip')?.textContent;
      expect(primeraCategoria).toContain('Realismo Mágico');
    });

    it('debe mostrar el total en la tarjeta de resumen', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      const totalText = compiled.querySelector('.summary-card strong')?.textContent;
      expect(totalText).toBe('2');
    });
  });

  describe('Búsqueda reactiva con debounce', () => {
    it('debe enviar el filtro de título tras el debounce', () => {
      vi.useFakeTimers();
      fixture.detectChanges();
      librosServiceMock.listar.mockClear();

      component.actualizarBusquedaTitulo('quijote');
      expect(librosServiceMock.listar).not.toHaveBeenCalled();

      vi.advanceTimersByTime(300);

      expect(librosServiceMock.listar).toHaveBeenCalledWith({
        page: 1,
        page_size: 10,
        titulo: 'quijote',
      });
    });

    it('debe enviar el filtro de ISBN tras el debounce', () => {
      vi.useFakeTimers();
      fixture.detectChanges();
      librosServiceMock.listar.mockClear();

      component.actualizarBusquedaIsbn('9788424116286');
      expect(librosServiceMock.listar).not.toHaveBeenCalled();

      vi.advanceTimersByTime(300);

      expect(librosServiceMock.listar).toHaveBeenCalledWith({
        page: 1,
        page_size: 10,
        isbn: '9788424116286',
      });
    });

    it('debe combinar título e ISBN si ambos están presentes', () => {
      vi.useFakeTimers();
      fixture.detectChanges();
      librosServiceMock.listar.mockClear();

      component.busquedaTitulo.set('soledad');
      component.actualizarBusquedaIsbn('9780307474728');
      vi.advanceTimersByTime(300);

      expect(librosServiceMock.listar).toHaveBeenCalledWith({
        page: 1,
        page_size: 10,
        titulo: 'soledad',
        isbn: '9780307474728',
      });
    });
  });

  describe('Filtros de autor y categoría', () => {
    it('debe filtrar inmediatamente al seleccionar un autor', () => {
      fixture.detectChanges();
      librosServiceMock.listar.mockClear();

      component.cambiarAutor(1);

      expect(component.pagina()).toBe(1);
      expect(librosServiceMock.listar).toHaveBeenCalledWith({
        page: 1,
        page_size: 10,
        autor_id: 1,
      });
    });

    it('debe filtrar inmediatamente al seleccionar una categoría', () => {
      fixture.detectChanges();
      librosServiceMock.listar.mockClear();

      component.cambiarCategoria(2);

      expect(component.pagina()).toBe(1);
      expect(librosServiceMock.listar).toHaveBeenCalledWith({
        page: 1,
        page_size: 10,
        categoria_id: 2,
      });
    });

    it('limpiarFiltros() debe restablecer todos los filtros y recargar desde página 1', () => {
      fixture.detectChanges();

      component.busquedaTitulo.set('prueba');
      component.busquedaIsbn.set('1234');
      component.autorSeleccionado.set(1);
      component.categoriaSeleccionada.set(2);
      component.pagina.set(3);

      librosServiceMock.listar.mockClear();
      component.limpiarFiltros();

      expect(component.busquedaTitulo()).toBe('');
      expect(component.busquedaIsbn()).toBe('');
      expect(component.autorSeleccionado()).toBeNull();
      expect(component.categoriaSeleccionada()).toBeNull();
      expect(component.pagina()).toBe(1);
      expect(librosServiceMock.listar).toHaveBeenCalledWith({
        page: 1,
        page_size: 10,
      });
    });
  });

  describe('Paginación', () => {
    beforeEach(() => {
      librosServiceMock.listar.mockReturnValue(
        of({
          count: 25,
          next: 'http://localhost:8000/api/libros/?page=2',
          previous: null,
          results: mockLibros,
        }),
      );
      fixture.detectChanges();
    });

    it('debe calcular correctamente totalPaginas, primerRegistro y ultimoRegistro', () => {
      expect(component.totalPaginas()).toBe(3);
      expect(component.primerRegistro()).toBe(1);
      expect(component.ultimoRegistro()).toBe(10);
    });

    it('cambiarPagina() debe cargar la página solicitada', () => {
      librosServiceMock.listar.mockClear();

      component.cambiarPagina(2);

      expect(component.pagina()).toBe(2);
      expect(librosServiceMock.listar).toHaveBeenCalledWith({
        page: 2,
        page_size: 10,
      });
    });

    it('cambiarPagina() no debe hacer nada si la página es menor a 1 o mayor al total', () => {
      librosServiceMock.listar.mockClear();

      component.cambiarPagina(0);
      expect(librosServiceMock.listar).not.toHaveBeenCalled();

      component.cambiarPagina(5);
      expect(librosServiceMock.listar).not.toHaveBeenCalled();
    });

    it('los botones de paginación deben reflejar el estado deshabilitado en los extremos', () => {
      const compiled = fixture.nativeElement as HTMLElement;
      const botones = compiled.querySelectorAll('.pagination-controls button');
      const btnAnterior = botones[0] as HTMLButtonElement;
      const btnSiguiente = botones[1] as HTMLButtonElement;

      // En página 1, el botón anterior debe estar deshabilitado
      expect(btnAnterior.disabled).toBe(true);
      expect(btnSiguiente.disabled).toBe(false);

      // Si nos movemos a la última página (3)
      component.pagina.set(3);
      fixture.detectChanges();
      expect(btnAnterior.disabled).toBe(false);
      expect(btnSiguiente.disabled).toBe(true);
    });
  });

  describe('Estados vacíos y de carga', () => {
    it('debe mostrar mensaje de carga mientras cargando() sea true', () => {
      fixture.detectChanges();
      component.cargando.set(true);
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      const mensajeCarga = compiled.querySelector('[role="status"]');
      expect(mensajeCarga?.textContent).toContain('Cargando libros');
    });

    it('debe mostrar mensaje cuando la lista esté vacía sin filtros', () => {
      librosServiceMock.listar.mockReturnValue(
        of({ count: 0, next: null, previous: null, results: [] }),
      );
      component.cargarLibros();
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('Aún no hay libros registrados');
    });

    it('debe mostrar mensaje específico cuando no haya resultados con filtros activos', () => {
      librosServiceMock.listar.mockReturnValue(
        of({ count: 0, next: null, previous: null, results: [] }),
      );
      component.busquedaTitulo.set('no-existe');
      component.cargarLibros();
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('No se encontraron libros con los filtros');
    });
  });

  describe('Manejo de errores HTTP', () => {
    it('debe manejar error de conexión (status 0)', () => {
      librosServiceMock.listar.mockReturnValue(
        throwError(() => new HttpErrorResponse({ status: 0 })),
      );
      component.cargarLibros();
      fixture.detectChanges();

      expect(component.error()).toBe('No fue posible conectar con el servidor.');
    });

    it('debe manejar error de sesión expirada (status 401)', () => {
      librosServiceMock.listar.mockReturnValue(
        throwError(() => new HttpErrorResponse({ status: 401 })),
      );
      component.cargarLibros();
      fixture.detectChanges();

      expect(component.error()).toBe('Tu sesión ha vencido.');
    });

    it('debe manejar error de permisos (status 403)', () => {
      librosServiceMock.listar.mockReturnValue(
        throwError(() => new HttpErrorResponse({ status: 403 })),
      );
      component.cargarLibros();
      fixture.detectChanges();

      expect(component.error()).toBe('No tienes permiso para consultar libros.');
    });

    it('debe manejar otros errores de servidor (status 500)', () => {
      librosServiceMock.listar.mockReturnValue(
        throwError(() => new HttpErrorResponse({ status: 500 })),
      );
      component.cargarLibros();
      fixture.detectChanges();

      expect(component.error()).toBe(
        'No fue posible cargar los libros. Inténtalo nuevamente.',
      );
    });

    it('el botón de reintentar debe volver a llamar a cargarLibros()', () => {
      librosServiceMock.listar.mockReturnValue(
        throwError(() => new HttpErrorResponse({ status: 500 })),
      );
      component.cargarLibros();
      fixture.detectChanges();

      librosServiceMock.listar.mockReturnValue(of(mockRespuestaPaginada));
      const compiled = fixture.nativeElement as HTMLElement;
      const btnReintentar = compiled.querySelector('.state-message--error button') as HTMLButtonElement;
      btnReintentar.click();

      expect(component.error()).toBeNull();
      expect(component.libros().length).toBe(2);
    });
  });

  describe('Acciones visuales — Etapa 4 habilitada', () => {
    it('el enlace + Nuevo libro debe estar activo y apuntar a /libros/nuevo', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      const enlaceNuevo = compiled.querySelector('#btn-nuevo-libro') as HTMLAnchorElement | null;

      expect(enlaceNuevo).toBeTruthy();
      expect(enlaceNuevo?.hasAttribute('disabled')).toBe(false);
    });

    it('el enlace Ver debe estar activo y apuntar a /libros/:id (Etapa 4)', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      const fila = compiled.querySelector('tbody tr');
      const enlaceVer = fila?.querySelector('.table-action-btn--view') as HTMLAnchorElement | null;

      expect(enlaceVer).toBeTruthy();
      expect(enlaceVer?.tagName.toLowerCase()).toBe('a');
      expect(enlaceVer?.hasAttribute('disabled')).toBe(false);
    });

    it('el enlace Editar debe estar activo y apuntar a /libros/:id/editar', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      const fila = compiled.querySelector('tbody tr');
      const enlaceEditar = fila?.querySelector('.table-action-btn--edit') as HTMLAnchorElement | null;

      expect(enlaceEditar).toBeTruthy();
      expect(enlaceEditar?.hasAttribute('disabled')).toBe(false);
    });

    it('el enlace Ejemplares debe estar activo y apuntar a /libros/:id con fragmento ejemplares (Etapa 4)', () => {
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      const fila = compiled.querySelector('tbody tr');
      const enlaceEjemplares = fila?.querySelector('.table-action-btn--secondary') as HTMLAnchorElement | null;

      expect(enlaceEjemplares).toBeTruthy();
      expect(enlaceEjemplares?.tagName.toLowerCase()).toBe('a');
      expect(enlaceEjemplares?.hasAttribute('disabled')).toBe(false);
    });
  });

  describe('Pruebas de regresión — Corrección de búsqueda, concurrencia y filtros', () => {
    it('debe permitir búsquedas consecutivas modificando el texto varias veces', () => {
      vi.useFakeTimers();
      fixture.detectChanges();
      librosServiceMock.listar.mockClear();

      // Primera búsqueda: "don"
      component.actualizarBusquedaTitulo('don');
      vi.advanceTimersByTime(300);
      expect(librosServiceMock.listar).toHaveBeenCalledTimes(1);
      expect(librosServiceMock.listar).toHaveBeenLastCalledWith(
        expect.objectContaining({ titulo: 'don', page: 1 }),
      );

      // Segunda búsqueda consecutiva: "don quijote"
      component.actualizarBusquedaTitulo('don quijote');
      vi.advanceTimersByTime(300);
      expect(librosServiceMock.listar).toHaveBeenCalledTimes(2);
      expect(librosServiceMock.listar).toHaveBeenLastCalledWith(
        expect.objectContaining({ titulo: 'don quijote', page: 1 }),
      );

      // Tercera búsqueda consecutiva: borrar texto a vacío
      component.actualizarBusquedaTitulo('');
      vi.advanceTimersByTime(300);
      expect(librosServiceMock.listar).toHaveBeenCalledTimes(3);
      expect(librosServiceMock.listar).toHaveBeenLastCalledWith(
        expect.not.objectContaining({ titulo: expect.anything() }),
      );
    });

    it('debe alternar de búsqueda por título a búsqueda por ISBN correctamente', () => {
      vi.useFakeTimers();
      fixture.detectChanges();
      librosServiceMock.listar.mockClear();

      // Búsqueda por título
      component.actualizarBusquedaTitulo('Cien Años');
      vi.advanceTimersByTime(300);
      expect(librosServiceMock.listar).toHaveBeenLastCalledWith(
        expect.objectContaining({ titulo: 'Cien Años' }),
      );

      // Cambiar a búsqueda por ISBN (limpiando título o manteniendo)
      component.actualizarBusquedaTitulo('');
      component.actualizarBusquedaIsbn('9780307474728');
      vi.advanceTimersByTime(300);

      expect(librosServiceMock.listar).toHaveBeenLastCalledWith(
        expect.objectContaining({ isbn: '9780307474728' }),
      );
    });

    it('debe recuperarse tras un error HTTP y permitir búsquedas posteriores sin recargar', () => {
      vi.useFakeTimers();
      fixture.detectChanges();
      librosServiceMock.listar.mockClear();

      // Provocar error HTTP en la búsqueda
      librosServiceMock.listar.mockReturnValue(
        throwError(() => new HttpErrorResponse({ status: 500 })),
      );

      component.actualizarBusquedaTitulo('error_trigger');
      vi.advanceTimersByTime(300);

      expect(component.error()).toBe('No fue posible cargar los libros. Inténtalo nuevamente.');
      expect(component.cargando()).toBe(false);

      // Siguiente búsqueda con servidor recuperado
      librosServiceMock.listar.mockReturnValue(of(mockRespuestaPaginada));
      component.actualizarBusquedaTitulo('recuperado');
      vi.advanceTimersByTime(300);

      expect(component.error()).toBeNull();
      expect(component.libros().length).toBe(2);
    });

    it('debe manejar solicitudes superpuestas y evitar que respuestas fuera de orden sobrescriban la búsqueda reciente (switchMap)', () => {
      vi.useFakeTimers();
      fixture.detectChanges();
      librosServiceMock.listar.mockClear();

      const respuestaVieja: LibrosPaginados = {
        count: 1,
        next: null,
        previous: null,
        results: [mockLibros[0]],
      };
      const respuestaNueva: LibrosPaginados = {
        count: 1,
        next: null,
        previous: null,
        results: [mockLibros[1]],
      };

      // Mock que devuelve un observable según el término
      librosServiceMock.listar.mockImplementation((filtros) => {
        if (filtros.titulo === 'antigua') {
          return of(respuestaVieja);
        }
        return of(respuestaNueva);
      });

      component.actualizarBusquedaTitulo('antigua');
      component.actualizarBusquedaTitulo('nueva');
      vi.advanceTimersByTime(300);

      expect(librosServiceMock.listar).toHaveBeenLastCalledWith(
        expect.objectContaining({ titulo: 'nueva' }),
      );
      expect(component.libros()[0].titulo).toBe('Don Quijote de la Mancha');
    });

    it('debe mostrar opciones disabled con mensaje informativo si los filtros de catálogo están vacíos', () => {
      catalogoServiceMock.obtenerFiltros.mockReturnValue(of({ autores: [], categorias: [] }));
      const fixtureVacio = TestBed.createComponent(LibrosListaComponent);
      fixtureVacio.detectChanges();

      const compiled = fixtureVacio.nativeElement as HTMLElement;
      const selectCategoria = compiled.querySelector('#filtro-categoria') as HTMLSelectElement;
      const selectAutor = compiled.querySelector('#filtro-autor') as HTMLSelectElement;

      expect(selectCategoria.textContent).toContain('No hay categorías registradas');
      expect(selectAutor.textContent).toContain('No hay autores registrados');
    });
  });
});
