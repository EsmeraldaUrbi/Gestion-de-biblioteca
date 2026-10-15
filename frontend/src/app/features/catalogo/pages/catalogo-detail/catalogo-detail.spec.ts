import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import {
  ComponentFixture,
  TestBed,
} from '@angular/core/testing';
import {
  ActivatedRoute,
  provideRouter,
  Router,
} from '@angular/router';
import { of, throwError } from 'rxjs';

import { CatalogoService } from '../../services/catalogo.service';
import { CatalogoDetailComponent } from './catalogo-detail';

describe('CatalogoDetailComponent', () => {
  let component: CatalogoDetailComponent;
  let fixture: ComponentFixture<CatalogoDetailComponent>;
  let catalogoServiceMock: Partial<CatalogoService>;
  let router: Router;

  const mockLibro = {
    libro_id: 42,
    titulo: 'Estructuras de Datos',
    isbn: '9781234567890',
    fecha_publicacion: '2021-03-15',
    autores: [{ autor_id: 1, nombre: 'Clifford A. Shaffer' }],
    categorias: [{ categoria_id: 1, nombre_categoria: 'Algoritmos' }],
    stock_total: 6,
    stock_disponible: 4,
  };

  const setupTest = async (paramId: string | null) => {
    catalogoServiceMock = {
      obtenerDetalle: vi.fn().mockReturnValue(of(mockLibro)),
    };

    await TestBed.configureTestingModule({
      imports: [CatalogoDetailComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: {
                get: (key: string) => (key === 'id' ? paramId : null),
              },
            },
          },
        },
        { provide: CatalogoService, useValue: catalogoServiceMock },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);

    fixture = TestBed.createComponent(CatalogoDetailComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  };

  it('debe crearse y cargar el detalle del libro para un ID válido', async () => {
    await setupTest('42');

    expect(component).toBeTruthy();
    expect(catalogoServiceMock.obtenerDetalle).toHaveBeenCalledWith(42);
    expect(component.libro()?.titulo).toBe('Estructuras de Datos');
    expect(component.libro()?.stock_total).toBe(6);
    expect(component.libro()?.stock_disponible).toBe(4);
    expect(component.cargando()).toBe(false);
    expect(component.error()).toBeNull();
  });

  it('debe manejar un ID no numérico o inválido', async () => {
    await setupTest('invalido');

    expect(component.cargando()).toBe(false);
    expect(component.error()).toBe('Identificador de libro inválido.');
    expect(catalogoServiceMock.obtenerDetalle).not.toHaveBeenCalled();
  });

  it('debe manejar error 404 de libro no encontrado', async () => {
    await setupTest('999');
    (catalogoServiceMock.obtenerDetalle as any).mockReturnValueOnce(
      throwError(() => ({ status: 404 })),
    );

    component.cargarDetalle(999);

    expect(component.cargando()).toBe(false);
    expect(component.error()).toBe('El libro solicitado no existe.');
  });

  it('debe permitir volver al catálogo', async () => {
    await setupTest('42');
    component.volver();

    expect(router.navigate).toHaveBeenCalledWith(['/catalogo']);
  });
});
