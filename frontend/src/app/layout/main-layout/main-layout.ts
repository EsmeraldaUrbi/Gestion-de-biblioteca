import {
  CommonModule,
} from '@angular/common';
import {
  Component,
  computed,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import {
  Router,
  RouterLink,
  RouterOutlet,
} from '@angular/router';
import { finalize } from 'rxjs';

import {
  UserRole,
} from '../../core/auth/models/auth.models';
import { AuthService } from '../../core/auth/services/auth.service';
import { AuthSessionService } from '../../core/auth/services/auth-session.service';

interface NavigationItem {
  label: string;
  route?: string;
  roles: UserRole[];
}

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    RouterOutlet,
  ],
  templateUrl: './main-layout.html',
  styleUrl: './main-layout.css',
})
export class MainLayoutComponent
  implements OnInit
{
  private readonly auth =
    inject(AuthService);

  private readonly router =
    inject(Router);

  readonly session =
    inject(AuthSessionService);

  readonly loggingOut =
    signal(false);

  private readonly navigation:
    NavigationItem[] = [
      {
        label: 'Inicio',
        route: '/inicio',
        roles: [
          'estudiante',
          'docente',
          'bibliotecario',
        ],
      },
      {
        label: 'Catálogo',
        roles: [
          'estudiante',
          'docente',
          'bibliotecario',
        ],
      },
      {
        label: 'Mis préstamos',
        roles: [
          'estudiante',
          'docente',
        ],
      },
      {
        label: 'Gestión de libros',
        roles: [
          'bibliotecario',
        ],
      },
      {
        label: 'Usuarios',
        roles: [
          'bibliotecario',
        ],
      },
      {
        label: 'Préstamos',
        roles: [
          'bibliotecario',
        ],
      },
      {
        label: 'Devoluciones',
        roles: [
          'bibliotecario',
        ],
      },
    ];

  readonly visibleNavigation =
    computed(() => {
      const role = this.session.rol();

      if (!role) {
        return [];
      }

      return this.navigation.filter(
        (item) =>
          item.roles.includes(role),
      );
    });

  readonly roleLabel =
    computed(() => {
      const role = this.session.rol();

      const labels:
        Record<UserRole, string> = {
          estudiante: 'Estudiante',
          docente: 'Docente',
          bibliotecario: 'Bibliotecario',
        };

      return role
        ? labels[role]
        : '';
    });

  ngOnInit(): void {
    this.auth
      .restoreSession()
      .subscribe();
  }

  logout(): void {
    if (this.loggingOut()) {
      return;
    }

    this.loggingOut.set(true);

    this.auth
      .logout()
      .pipe(
        finalize(() => {
          this.loggingOut.set(false);

          void this.router.navigateByUrl(
            '/login',
          );
        }),
      )
      .subscribe({
        error: () => {
          // AuthService limpia la sesión
          // local incluso si falla la petición.
        },
      });
  }
}