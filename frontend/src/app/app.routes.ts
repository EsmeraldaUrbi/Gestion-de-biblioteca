import {
  Routes,
} from '@angular/router';

import { authGuard } from './core/auth/guards/auth.guard';
import { guestGuard } from './core/auth/guards/guest.guard';

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
    ],
  },
  {
    path: '**',
    redirectTo: 'inicio',
  },
];