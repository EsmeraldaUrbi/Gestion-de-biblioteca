import {
  Component,
  computed,
  inject,
} from '@angular/core';

import {
  UserRole,
} from '../../core/auth/models/auth.models';
import { AuthSessionService } from '../../core/auth/services/auth-session.service';

@Component({
  selector: 'app-inicio',
  standalone: true,
  templateUrl: './inicio.html',
  styleUrl: './inicio.css',
})
export class InicioComponent {
  readonly session =
    inject(AuthSessionService);

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
}