import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import {
  ComponentFixture,
  TestBed,
} from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';

import { CatalogoService } from '../../services/catalogo.service';
import { CatalogoListComponent } from './catalogo-list';

describe('CatalogoListComponent', () => {
  let component: CatalogoListComponent;
  let fixture: ComponentFixture<CatalogoListComponent>;
  let catalogoServiceMock: Partial<CatalogoService>;

  const mockLibros = [
    {
      libro_id: 1,
      titulo: 'Sistemas Operativos',
      isbn: '9780000000001',
      fecha_publicacion: '2020-01-01',
      autores: [{ autor_id: 1, nombre: 'Andrew S. Tanenbaum' }],
      categorias: [{ categoria_id: 1, nombre_categoria: 'Computación' }],
      stock_total: 4,
      stock_disponible: 2,
    },
    {
      libro_id: 2,
      titulo: 'Cálculo Avanzado',
      isbn: '9780000000002',
      fecha_publicacion: '2019-05-10',
      autores: [{ autor_id: 2, nombre: 'James Stewart' }],
      categorias: [{ categoria_id: 2, nombre_categoria: 'Matemáticas' }],
      stock_total: 1,
      stock_disponible: 0,
    },
  ];

  const mockOpciones = {
    autores: [
      { autor_id: 1, nombre: 'Andrew S. Tanenbaum' },
      { autor_id: 2, nombre: 'James Stewart' },
    ],
    categorias: [
      { categoria_id: 1, nombre_categoria: 'Computación' },
      { categoria_id: 2, nombre_categoria: 'Matemáticas' },
    ],
  };

  beforeEach(async () => {
    catalogoServiceMock = {
      listar: vi.fn().mockReturnValue(
        of({
          count: 2,
          next: null,
          previous: null,
          results: mockLibros,
        }),
      ),
      obtenerFiltros: vi.fn().mockReturnValue(of(mockOpciones)),
      obtenerDetalle: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [CatalogoListComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: CatalogoService, useValue: catalogoServiceMock },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CatalogoListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse e inicializar datos de libros y filtros', () => {
    expect(component).toBeTruthy();
    expect(catalogoServiceMock.obtenerFiltros).toHaveBeenCalled();
    expect(catalogoServiceMock.listar).toHaveBeenCalled();
    expect(component.libros().length).toBe(2);
    expect(component.totalRegistros()).toBe(2);
    expect(component.autores().length).toBe(2);
    expect(component.categorias().length).toBe(2);
  });

  it('debe calcular el total de copias disponibles correctamente', () => {
    // 2 disponibles del libro 1 + 0 disponibles del libro 2 = 2
    expect(component.totalDisponibles()).toBe(2);
  });

  it('debe buscar y reiniciar la página al ejecutar onBuscar', () => {
    component.paginaActual.set(3);
    component.busqueda.set('Sistemas');
    component.onBuscar();

    expect(component.paginaActual()).toBe(1);
    expect(catalogoServiceMock.listar).toHaveBeenCalledWith(
      expect.objectContaining({
        titulo: 'Sistemas',
        page: 1,
      }),
    );
  });

  it('debe limpiar filtros y recargar el catálogo', () => {
    component.busqueda.set('algo');
    component.autorSeleccionado.set(1);
    component.categoriaSeleccionada.set(2);
    component.soloDisponibles.set(true);

    component.limpiarFiltros();

    expect(component.busqueda()).toBe('');
    expect(component.autorSeleccionado()).toBeNull();
    expect(component.categoriaSeleccionada()).toBeNull();
    expect(component.soloDisponibles()).toBe(false);
    expect(component.paginaActual()).toBe(1);
  });

  it('debe cambiar de página correctamente', () => {
    component.totalRegistros.set(20);
    component.tamanioPagina.set(10);
    expect(component.totalPaginas()).toBe(2);

    component.paginaSiguiente();
    expect(component.paginaActual()).toBe(2);

    component.paginaAnterior();
    expect(component.paginaActual()).toBe(1);
  });

  it('debe manejar error al consultar catálogo', () => {
    (catalogoServiceMock.listar as any).mockReturnValueOnce(
      throwError(() => ({ status: 500 })),
    );

    component.cargarCatalogo();

    expect(component.cargando()).toBe(false);
    expect(component.error()).toContain('Error al cargar');
  });

  it('debe formatear los autores adecuadamente', () => {
    expect(component.formatearAutores(mockLibros[0])).toBe('Andrew S. Tanenbaum');
    expect(
      component.formatearAutores({
        ...mockLibros[0],
        autores: [],
      }),
    ).toBe('Autor no registrado');
  });

  it('debe determinar el estado visual de disponibilidad', () => {
    // 2 copias disponibles -> Disponible
    expect(component.obtenerEstadoDisponibilidad(mockLibros[0])).toEqual({
      clase: 'status-pill--available',
      etiqueta: 'Disponible',
    });

    // 1 copia disponible -> 1 disponible (Último)
    expect(
      component.obtenerEstadoDisponibilidad({
        ...mockLibros[0],
        stock_disponible: 1,
      }),
    ).toEqual({
      clase: 'status-pill--last-unit',
      etiqueta: '1 disponible (Último)',
    });

    // 0 copias disponibles -> No disponible
    expect(component.obtenerEstadoDisponibilidad(mockLibros[1])).toEqual({
      clase: 'status-pill--unavailable',
      etiqueta: 'No disponible',
    });
  });

  it('debe detectar correctamente si hay filtros activos', () => {
    expect(component.hayFiltrosActivos()).toBe(false);

    component.busqueda.set('Sistemas');
    expect(component.hayFiltrosActivos()).toBe(true);

    component.busqueda.set('');
    component.soloDisponibles.set(true);
    expect(component.hayFiltrosActivos()).toBe(true);
  });

  describe('Búsqueda incremental reactiva con debounce', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('no hay llamada antes de 300 ms al escribir en el campo de búsqueda', () => {
      vi.clearAllMocks();
      component.onBusquedaChange('Algoritmos');

      // Avanzamos 299 ms (justo antes del umbral de debounce)
      vi.advanceTimersByTime(299);
      expect(catalogoServiceMock.listar).not.toHaveBeenCalled();
    });

    it('hay una sola llamada después del debounce de 300 ms', () => {
      vi.clearAllMocks();
      component.onBusquedaChange('Algoritmos');

      vi.advanceTimersByTime(300);
      expect(catalogoServiceMock.listar).toHaveBeenCalledTimes(1);
    });

    it('el filtro enviado contiene el texto actualizado y reinicia a la página 1', () => {
      vi.clearAllMocks();
      component.paginaActual.set(3);
      component.onBusquedaChange('Estructuras de Datos');

      vi.advanceTimersByTime(300);

      expect(component.paginaActual()).toBe(1);
      expect(catalogoServiceMock.listar).toHaveBeenCalledWith(
        expect.objectContaining({
          titulo: 'Estructuras de Datos',
          page: 1,
        }),
      );
    });

    it('borrar el texto elimina el filtro de título y recarga el catálogo', () => {
      // Primero simulamos una búsqueda previa con texto
      component.onBusquedaChange('Redes');
      vi.advanceTimersByTime(300);
      expect(catalogoServiceMock.listar).toHaveBeenCalledWith(
        expect.objectContaining({ titulo: 'Redes' }),
      );

      vi.clearAllMocks();
      // Ahora borramos el texto
      component.onBusquedaChange('');
      vi.advanceTimersByTime(300);

      expect(catalogoServiceMock.listar).toHaveBeenCalledTimes(1);
      expect(catalogoServiceMock.listar).toHaveBeenCalledWith(
        expect.objectContaining({
          titulo: undefined,
          page: 1,
        }),
      );
    });

    it('Enter fuerza la consulta inmediata sin esperar 300 ms y no duplica la llamada tras el debounce', () => {
      vi.clearAllMocks();
      component.onBusquedaChange('Compiladores');

      // Presionar Enter inmediatamente (0 ms transcurridos)
      component.onBuscar();

      // Debe haberse ejecutado de inmediato
      expect(catalogoServiceMock.listar).toHaveBeenCalledTimes(1);
      expect(catalogoServiceMock.listar).toHaveBeenCalledWith(
        expect.objectContaining({
          titulo: 'Compiladores',
          page: 1,
        }),
      );

      // Al cumplirse los 300 ms del debounce, NO debe ejecutarse una segunda llamada duplicada
      vi.advanceTimersByTime(300);
      expect(catalogoServiceMock.listar).toHaveBeenCalledTimes(1);
    });
  });
});
