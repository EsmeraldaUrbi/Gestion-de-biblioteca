import {
  Routes,
} from '@angular/router';

import {
  authGuard,
} from './core/auth/guards/auth.guard';
import {
  guestGuard,
} from './core/auth/guards/guest.guard';
import {
  roleGuard,
} from './core/auth/guards/role.guard';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [guestGuard],
    loadComponent: () =>
      import('./features/auth/login/login').then((module) => module.LoginComponent),
  },
  {
    path: '',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./layout/main-layout/main-layout').then((module) => module.MainLayoutComponent),
    children: [
      {
        path: 'inicio',
        loadComponent: () =>
          import('./features/inicio/inicio').then((module) => module.InicioComponent),
      },
      {
        path: 'catalogo',
        canActivate: [roleGuard],
        data: { roles: ['estudiante', 'docente', 'bibliotecario'] },
        loadComponent: () =>
          import('./features/catalogo/pages/catalogo-list/catalogo-list').then(
            (module) => module.CatalogoListComponent,
          ),
      },
      {
        path: 'catalogo/:id',
        canActivate: [roleGuard],
        data: { roles: ['estudiante', 'docente', 'bibliotecario'] },
        loadComponent: () =>
          import('./features/catalogo/pages/catalogo-detail/catalogo-detail').then(
            (module) => module.CatalogoDetailComponent,
          ),
      },
      {
        path: 'acceso-denegado',
        loadComponent: () =>
          import('./features/acceso-denegado/acceso-denegado').then(
            (module) => module.AccesoDenegadoComponent,
          ),
      },
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'inicio',
      },
      {
        path: 'mis-prestamos',
        canActivate: [roleGuard],
        data: { roles: ['estudiante', 'docente'] },
        loadComponent: () =>
          import('./features/prestamos/pages/mis-prestamos/mis-prestamos').then(
            (module) => module.MisPrestamosComponent,
          ),
      },
      {
        path: 'sanciones/mias',
        canActivate: [roleGuard],
        data: { roles: ['estudiante', 'docente'] },
        loadComponent: () =>
          import('./features/sanciones/pages/mis-sanciones/mis-sanciones').then(
            (module) => module.MisSancionesComponent,
          ),
      },
      {
        path: 'prestamos',
        canActivate: [roleGuard],
        data: { roles: ['bibliotecario'] },
        loadComponent: () =>
          import('./features/prestamos/pages/registro-prestamo/registro-prestamo').then(
            (module) => module.RegistroPrestamoComponent,
          ),
      },
      {
        path: 'devoluciones',
        canActivate: [roleGuard],
        data: { roles: ['bibliotecario'] },
        loadComponent: () =>
          import('./features/prestamos/pages/registro-devolucion/registro-devolucion').then(
            (module) => module.RegistroDevolucionComponent,
          ),
      },
      {
        path: 'sanciones',
        canActivate: [roleGuard],
        data: { roles: ['bibliotecario'] },
        loadComponent: () =>
          import('./features/sanciones/pages/gestion-sanciones/gestion-sanciones').then(
            (module) => module.GestionSancionesComponent,
          ),
      },
      {
        path: 'usuarios/nuevo',
        canActivate: [roleGuard],
        data: { roles: ['bibliotecario'] },
        loadComponent: () =>
          import('./features/usuarios/pages/usuario-nuevo/usuario-nuevo').then(
            (module) => module.UsuarioNuevoComponent,
          ),
      },
      {
        path: 'usuarios/:id/editar',
        canActivate: [roleGuard],
        data: { roles: ['bibliotecario'] },
        loadComponent: () =>
          import('./features/usuarios/pages/usuario-editar/usuario-editar').then(
            (module) => module.UsuarioEditarComponent,
          ),
      },
      {
        path: 'usuarios/:id',
        canActivate: [roleGuard],
        data: { roles: ['bibliotecario'] },
        loadComponent: () =>
          import('./features/usuarios/pages/usuario-detalle/usuario-detalle').then(
            (module) => module.UsuarioDetalleComponent,
          ),
      },
      {
        path: 'usuarios',
        canActivate: [roleGuard],
        data: { roles: ['bibliotecario'] },
        loadComponent: () =>
          import('./features/usuarios/pages/usuarios-lista/usuarios-lista').then(
            (module) => module.UsuariosListaComponent,
          ),
      },
      {
        path: 'libros/nuevo',
        canActivate: [roleGuard],
        data: { roles: ['bibliotecario'] },
        loadComponent: () =>
          import('./features/libros/pages/libro-nuevo/libro-nuevo').then(
            (module) => module.LibroNuevoComponent,
          ),
      },
      {
        path: 'libros/:id/editar',
        canActivate: [roleGuard],
        data: { roles: ['bibliotecario'] },
        loadComponent: () =>
          import('./features/libros/pages/libro-editar/libro-editar').then(
            (module) => module.LibroEditarComponent,
          ),
      },
      {
        path: 'libros/:id',
        canActivate: [roleGuard],
        data: { roles: ['bibliotecario'] },
        loadComponent: () =>
          import('./features/libros/pages/libro-detalle/libro-detalle').then(
            (module) => module.LibroDetalleComponent,
          ),
      },
      {
        path: 'libros',
        canActivate: [roleGuard],
        data: { roles: ['bibliotecario'] },
        loadComponent: () =>
          import('./features/libros/pages/libros-lista/libros-lista').then(
            (module) => module.LibrosListaComponent,
          ),
      },
      {
        path: 'autores',
        canActivate: [roleGuard],
        data: { roles: ['bibliotecario'] },
        loadComponent: () =>
          import('./features/libros/pages/autores-lista/autores-lista').then(
            (module) => module.AutoresListaComponent,
          ),
      },
      {
        path: 'categorias',
        canActivate: [roleGuard],
        data: { roles: ['bibliotecario'] },
        loadComponent: () =>
          import('./features/libros/pages/categorias-lista/categorias-lista').then(
            (module) => module.CategoriasListaComponent,
          ),
      },
    ],
  },
  {
    path: '**',
    redirectTo: 'inicio',
  },
];
