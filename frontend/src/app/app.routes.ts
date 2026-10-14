import {
  Routes,
} from '@angular/router';

import { authGuard } from './core/auth/guards/auth.guard';
import { guestGuard } from './core/auth/guards/guest.guard';

//3.2
import { roleGuard } from './core/auth/guards/role.guard';

export const routes: Routes = [
  {
    path: 'login',
    canActivate: [
      guestGuard,
    ],
    loadComponent: () =>
      import(
        './features/auth/login/login'
      ).then(
        (module) =>
          module.LoginComponent,
      ),
  },
  {
    path: '',
    canActivate: [
      authGuard,
    ],
    loadComponent: () =>
      import(
        './layout/main-layout/main-layout'
      ).then(
        (module) =>
          module.MainLayoutComponent,
      ),
    children: [
      {
        path: 'inicio',
        loadComponent: () =>
          import(
            './features/inicio/inicio'
          ).then(
            (module) =>
              module.InicioComponent,
          ),
      },
      {
        path: 'acceso-denegado',
        loadComponent: () =>
          import(
            './features/acceso-denegado/acceso-denegado'
          ).then(
            (module) =>
              module.AccesoDenegadoComponent,
          ),
      },
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'inicio',
      },
      {
        path: 'usuarios/nuevo',
        canActivate: [
          roleGuard,
        ],
        data: {
          roles: ['bibliotecario'],
        },
        loadComponent: () =>
          import(
            './features/usuarios/pages/usuario-nuevo/usuario-nuevo'
          ).then(
            (module) => module.UsuarioNuevoComponent,
          ),
      },
      {
        path: 'usuarios/:id/editar',
        canActivate: [
          roleGuard,
        ],
        data: {
          roles: ['bibliotecario'],
        },
        loadComponent: () =>
          import(
            './features/usuarios/pages/usuario-editar/usuario-editar'
          ).then(
            (module) => module.UsuarioEditarComponent,
          ),
      },
      {
        path: 'usuarios/:id',
        canActivate: [
          roleGuard,
        ],
        data: {
          roles: ['bibliotecario'],
        },
        loadComponent: () =>
          import(
            './features/usuarios/pages/usuario-detalle/usuario-detalle'
          ).then(
            (module) => module.UsuarioDetalleComponent,
          ),
      },
      {
        path: 'usuarios',
        canActivate: [
          roleGuard,
        ],
        data: {
          roles: ['bibliotecario'],
        },
        loadComponent: () =>
          import(
            './features/usuarios/pages/usuarios-lista/usuarios-lista'
          ).then(
            (module) => module.UsuariosListaComponent,
          ),
      },
    ],
  },
  {
    path: '**',
    redirectTo: 'inicio',
  },
];