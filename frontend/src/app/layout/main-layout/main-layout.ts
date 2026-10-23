import {
  CommonModule,
} from '@angular/common';
import {
  Component,
  computed,
  ElementRef,
  HostListener,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import {
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
} from '@angular/router';
import { finalize } from 'rxjs';

import {
  UserRole,
} from '../../core/auth/models/auth.models';
import { AuthService } from '../../core/auth/services/auth.service';
import { AuthSessionService } from '../../core/auth/services/auth-session.service';

export interface NavigationItem {
  label: string;
  route?: string;
  roles: UserRole[];
  icon: string;
}

@Component({
  selector: 'app-main-layout',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    RouterLinkActive,
    RouterOutlet,
  ],
  templateUrl: './main-layout.html',
  styleUrl: './main-layout.css',
})
export class MainLayoutComponent implements OnInit {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  private readonly elementRef = inject(ElementRef);

  readonly session = inject(AuthSessionService);
  readonly loggingOut = signal(false);
  readonly menuPerfilAbierto = signal(false);
  readonly sidebarAbierto = signal(false);

  readonly navigation: NavigationItem[] = [
    {
      label: 'Inicio',
      route: '/inicio',
      roles: ['estudiante', 'docente', 'bibliotecario'],
      icon: 'home',
    },
    {
      label: 'Catálogo',
      route: '/catalogo',
      roles: ['estudiante', 'docente', 'bibliotecario'],
      icon: 'catalog',
    },
    {
      label: 'Mis préstamos',
      route: '/mis-prestamos',
      roles: ['estudiante', 'docente'],
      icon: 'loans',
    },
    {
      label: 'Mis sanciones',
      route: '/sanciones/mias',
      roles: ['estudiante', 'docente'],
      icon: 'fines',
    },
    {
      label: 'Gestión de libros',
      route: '/libros',
      roles: ['bibliotecario'],
      icon: 'admin-books',
    },
    {
      label: 'Autores',
      route: '/autores',
      roles: ['bibliotecario'],
      icon: 'authors',
    },
    {
      label: 'Categorías',
      route: '/categorias',
      roles: ['bibliotecario'],
      icon: 'categories',
    },
    {
      label: 'Usuarios',
      route: '/usuarios',
      roles: ['bibliotecario'],
      icon: 'users',
    },
    {
      label: 'Préstamos',
      route: '/prestamos',
      roles: ['bibliotecario'],
      icon: 'admin-loans',
    },
    {
      label: 'Devoluciones',
      route: '/devoluciones',
      roles: ['bibliotecario'],
      icon: 'returns',
    },
    {
      label: 'Sanciones',
      route: '/sanciones',
      roles: ['bibliotecario'],
      icon: 'fines',
    },
  ];

  readonly visibleNavigation = computed(() => {
    const role = this.session.rol();
    if (!role) {
      return [];
    }
    return this.navigation.filter((item) => item.roles.includes(role));
  });

  readonly roleLabel = computed(() => {
    const role = this.session.rol();
    const labels: Record<UserRole, string> = {
      estudiante: 'Estudiante',
      docente: 'Docente',
      bibliotecario: 'Bibliotecario',
    };
    return role ? labels[role] : '';
  });

  readonly userInitials = computed(() => {
    const name = this.session.usuario()?.nombre?.trim();
    if (!name) return 'U';
    const parts = name.split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  });

  ngOnInit(): void {
    this.auth.restoreSession().subscribe();
  }

  toggleMenuPerfil(): void {
    this.menuPerfilAbierto.update((v) => !v);
  }

  cerrarMenuPerfil(): void {
    this.menuPerfilAbierto.set(false);
  }

  toggleSidebar(): void {
    this.sidebarAbierto.update((v) => !v);
  }

  cerrarSidebar(): void {
    this.sidebarAbierto.set(false);
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.menuPerfilAbierto()) {
      return;
    }
    const target = event.target as HTMLElement;
    const profileContainer = this.elementRef.nativeElement.querySelector('.profile-container');
    if (profileContainer && !profileContainer.contains(target)) {
      this.cerrarMenuPerfil();
    }
  }

  @HostListener('document:keydown.escape')
  onEscape(): void {
    if (this.menuPerfilAbierto()) {
      this.cerrarMenuPerfil();
    }
    if (this.sidebarAbierto()) {
      this.cerrarSidebar();
    }
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
          this.cerrarMenuPerfil();
          void this.router.navigateByUrl('/login');
        }),
      )
      .subscribe({
        error: () => {
          // AuthService limpia la sesión local incluso ante fallos HTTP.
        },
      });
  }
}
