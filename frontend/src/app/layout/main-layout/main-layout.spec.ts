import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { of } from 'rxjs';
import { signal } from '@angular/core';

import { MainLayoutComponent } from './main-layout';
import { AuthService } from '../../core/auth/services/auth.service';
import { AuthSessionService } from '../../core/auth/services/auth-session.service';
import { UserRole, UsuarioSesion } from '../../core/auth/models/auth.models';

describe('MainLayoutComponent', () => {
  let component: MainLayoutComponent;
  let fixture: ComponentFixture<MainLayoutComponent>;
  let authServiceMock: Partial<AuthService>;
  let sessionServiceMock: {
    rol: ReturnType<typeof signal<UserRole | null>>;
    usuario: ReturnType<typeof signal<UsuarioSesion | null>>;
    estaAutenticado: ReturnType<typeof signal<boolean>>;
  };
  let router: Router;

  const mockUsuario: UsuarioSesion = {
    usuario_id: 10,
    nombre: 'Ana García',
    email: 'ana.garcia@universidad.edu',
    rol: {
      rol_id: 1,
      nombre: 'estudiante',
      limite_prestamos_activos: 3,
    },
  };

  beforeEach(async () => {
    sessionServiceMock = {
      rol: signal<UserRole | null>('estudiante'),
      usuario: signal<UsuarioSesion | null>(mockUsuario),
      estaAutenticado: signal<boolean>(true),
    };

    authServiceMock = {
      restoreSession: vi.fn().mockReturnValue(of(null)),
      logout: vi.fn().mockReturnValue(of(void 0)),
    };

    await TestBed.configureTestingModule({
      imports: [MainLayoutComponent],
      providers: [
        provideRouter([]),
        { provide: AuthService, useValue: authServiceMock },
        { provide: AuthSessionService, useValue: sessionServiceMock },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);

    fixture = TestBed.createComponent(MainLayoutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
    expect(authServiceMock.restoreSession).toHaveBeenCalled();
  });

  describe('Navegación según rol del usuario', () => {
    it('para estudiante debe mostrar exactamente: Inicio, Catálogo, Mis préstamos y Mis sanciones', () => {
      sessionServiceMock.rol.set('estudiante');
      fixture.detectChanges();

      const items = component.visibleNavigation();
      const labels = items.map((i) => i.label);

      expect(labels).toEqual([
        'Inicio',
        'Catálogo',
        'Mis préstamos',
        'Mis sanciones',
      ]);

      // Mis préstamos está disponible cuando el módulo de consulta personal existe.
      expect(items.find((i) => i.label === 'Inicio')?.route).toBe('/inicio');
      expect(items.find((i) => i.label === 'Catálogo')?.route).toBe('/catalogo');
      expect(items.find((i) => i.label === 'Mis préstamos')?.route).toBe('/mis-prestamos');
      expect(items.find((i) => i.label === 'Mis sanciones')?.route).toBeUndefined();

      // No debe contener módulos administrativos
      expect(labels).not.toContain('Gestión de libros');
      expect(labels).not.toContain('Usuarios');
      expect(labels).not.toContain('Préstamos');
      expect(labels).not.toContain('Devoluciones');
    });

    it('para docente debe mostrar la misma navegación de lector que estudiante', () => {
      sessionServiceMock.rol.set('docente');
      fixture.detectChanges();

      const items = component.visibleNavigation();
      const labels = items.map((i) => i.label);

      expect(labels).toEqual([
        'Inicio',
        'Catálogo',
        'Mis préstamos',
        'Mis sanciones',
      ]);
    });

    it('para bibliotecario debe mostrar módulos administrativos y no módulos de lector', () => {
      sessionServiceMock.rol.set('bibliotecario');
      fixture.detectChanges();

      const items = component.visibleNavigation();
      const labels = items.map((i) => i.label);

      expect(labels).toEqual([
        'Inicio',
        'Catálogo',
        'Gestión de libros',
        'Usuarios',
        'Préstamos',
        'Devoluciones',
      ]);

      expect(labels).not.toContain('Mis préstamos');
      expect(labels).not.toContain('Mis sanciones');
    });

    it('retorna arreglo vacío si no hay rol de sesión', () => {
      sessionServiceMock.rol.set(null);
      fixture.detectChanges();

      expect(component.visibleNavigation()).toEqual([]);
    });
  });

  describe('Menú de perfil y drawer lateral', () => {
    it('debe alternar y cerrar el menú de perfil', () => {
      expect(component.menuPerfilAbierto()).toBe(false);

      component.toggleMenuPerfil();
      expect(component.menuPerfilAbierto()).toBe(true);

      component.cerrarMenuPerfil();
      expect(component.menuPerfilAbierto()).toBe(false);
    });

    it('debe alternar y cerrar el drawer de la barra lateral móvil', () => {
      expect(component.sidebarAbierto()).toBe(false);

      component.toggleSidebar();
      expect(component.sidebarAbierto()).toBe(true);

      component.cerrarSidebar();
      expect(component.sidebarAbierto()).toBe(false);
    });

    it('debe cerrar menús al presionar la tecla Escape', () => {
      component.menuPerfilAbierto.set(true);
      component.sidebarAbierto.set(true);

      component.onEscape();

      expect(component.menuPerfilAbierto()).toBe(false);
      expect(component.sidebarAbierto()).toBe(false);
    });

    it('calcula las iniciales del usuario correctamente', () => {
      expect(component.userInitials()).toBe('AG');

      sessionServiceMock.usuario.set({
        ...mockUsuario,
        nombre: 'Carlos',
      });
      expect(component.userInitials()).toBe('CA');
    });
  });

  describe('Cierre de sesión', () => {
    it('debe invocar auth.logout y redirigir a /login', () => {
      component.logout();

      expect(authServiceMock.logout).toHaveBeenCalled();
      expect(router.navigateByUrl).toHaveBeenCalledWith('/login');
      expect(component.menuPerfilAbierto()).toBe(false);
    });
  });
});
