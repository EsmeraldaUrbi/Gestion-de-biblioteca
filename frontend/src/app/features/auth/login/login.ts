import { CommonModule } from '@angular/common';
import {
  HttpErrorResponse,
} from '@angular/common/http';
import {
  Component,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import {
  ActivatedRoute,
  Router,
} from '@angular/router';
import { finalize } from 'rxjs';

import {
  UserRole,
} from '../../../core/auth/models/auth.models';
import { AuthService } from '../../../core/auth/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
  ],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class LoginComponent
  implements OnInit
{
  private readonly formBuilder =
    inject(FormBuilder);

  private readonly auth =
    inject(AuthService);

  private readonly router =
    inject(Router);

  private readonly route =
    inject(ActivatedRoute);

  readonly selectedRole =
    signal<UserRole>('estudiante');

  readonly passwordVisible =
    signal(false);

  readonly loading =
    signal(false);

  readonly message =
    signal<string | null>(null);

  readonly messageType =
    signal<'error' | 'info'>('error');

  readonly roles: {
    value: UserRole;
    label: string;
  }[] = [
    {
      value: 'estudiante',
      label: 'Estudiante',
    },
    {
      value: 'docente',
      label: 'Docente',
    },
    {
      value: 'bibliotecario',
      label: 'Bibliotecario',
    },
  ];

  private readonly roleLabels:
    Record<UserRole, string> = {
      estudiante: 'Estudiante',
      docente: 'Docente',
      bibliotecario: 'Bibliotecario',
    };

  readonly loginForm =
    this.formBuilder.nonNullable.group({
      email: [
        '',
        [
          Validators.required,
          Validators.email,
        ],
      ],
      password: [
        '',
        [
          Validators.required,
        ],
      ],
      recordar: [false],
    });

  ngOnInit(): void {
    const reason =
      this.route.snapshot.queryParamMap.get(
        'reason',
      );

    if (
      reason === 'session-expired'
    ) {
      this.setMessage(
        'Tu sesión ha vencido. Inicia sesión nuevamente.',
        'info',
      );
    }
  }

  selectRole(role: UserRole): void {
    this.selectedRole.set(role);
    this.message.set(null);
  }

  togglePassword(): void {
    this.passwordVisible.update(
      (visible) => !visible,
    );
  }

  submit(): void {
    this.message.set(null);

    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();

      this.setMessage(
        'Ingresa un correo válido y tu contraseña.',
        'error',
      );

      return;
    }

    const {
      email,
      password,
      recordar,
    } = this.loginForm.getRawValue();

    this.loading.set(true);

    this.auth
      .login(
        {
          email: email.trim(),
          password,
        },
        recordar,
      )
      .subscribe({
        next: (response) => {
          const actualRole =
            response.usuario.rol.nombre;

          if (
            actualRole !==
            this.selectedRole()
          ) {
            this.handleRoleMismatch(
              actualRole,
            );

            return;
          }

          this.loading.set(false);

          void this.router.navigateByUrl(
            '/inicio',
          );
        },
        error: (
          error: HttpErrorResponse,
        ) => {
          this.loading.set(false);

          if (error.status === 401) {
            this.setMessage(
              'Correo o contraseña incorrectos.',
              'error',
            );

            return;
          }

          if (error.status === 400) {
            this.setMessage(
              'Revisa los datos ingresados.',
              'error',
            );

            return;
          }

          if (error.status === 0) {
            this.setMessage(
              'No fue posible conectar con el servidor. Verifica que el backend esté disponible.',
              'error',
            );

            return;
          }

          this.setMessage(
            'Ocurrió un error al iniciar sesión. Inténtalo nuevamente.',
            'error',
          );
        },
      });
  }

  showRecoveryMessage(): void {
    this.setMessage(
      'Para recuperar o reponer tus credenciales, acude al mostrador de servicios bibliotecarios.',
      'info',
    );
  }

  private handleRoleMismatch(
    actualRole: UserRole,
  ): void {
    this.auth
      .logout()
      .pipe(
        finalize(() => {
          this.loading.set(false);

          this.setMessage(
            `Estas credenciales pertenecen al perfil ${this.roleLabels[actualRole]}. Selecciona ese perfil para iniciar sesión.`,
            'error',
          );
        }),
      )
      .subscribe({
        error: () => {
          // La sesión local se limpia
          // igualmente desde AuthService.
        },
      });
  }

  private setMessage(
    message: string,
    type: 'error' | 'info',
  ): void {
    this.message.set(message);
    this.messageType.set(type);
  }
}