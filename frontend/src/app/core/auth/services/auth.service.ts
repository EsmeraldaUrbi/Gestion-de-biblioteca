import {
  HttpClient,
  HttpErrorResponse,
} from '@angular/common/http';
import {
  inject,
  Injectable,
} from '@angular/core';
import {
  catchError,
  finalize,
  Observable,
  of,
  tap,
  throwError,
} from 'rxjs';

import { API_BASE_URL } from '../../config/api.config';
import {
  LoginRequest,
  LoginResponse,
  UsuarioSesion,
} from '../models/auth.models';
import { AuthSessionService } from './auth-session.service';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly http = inject(HttpClient);

  private readonly session =
    inject(AuthSessionService);

  login(
    credentials: LoginRequest,
    recordar: boolean,
  ): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(
        `${API_BASE_URL}/auth/login/`,
        credentials,
      )
      .pipe(
        tap((response) => {
          this.session.start(
            response,
            recordar,
          );
        }),
      );
  }

  restoreSession():
    Observable<UsuarioSesion | null> {
    if (!this.session.hasSession()) {
      return of(null);
    }

    if (this.session.isExpired()) {
      this.session.clear();
      return of(null);
    }

    return this.http
      .get<UsuarioSesion>(
        `${API_BASE_URL}/auth/me/`,
      )
      .pipe(
        tap((usuario) => {
          this.session.updateUser(usuario);
        }),
        catchError(
          (
            error: HttpErrorResponse,
          ) => {
            if (error.status === 401) {
              this.session.clear();
            }

            return of(null);
          },
        ),
      );
  }

  logout(): Observable<void> {
    if (!this.session.hasSession()) {
      this.session.clear();

      return of(undefined);
    }

    return this.http
      .post<void>(
        `${API_BASE_URL}/auth/logout/`,
        {},
      )
      .pipe(
        catchError(
          (
            error: HttpErrorResponse,
          ) => {
            if (error.status === 401) {
              return of(undefined);
            }

            return throwError(
              () => error,
            );
          },
        ),
        finalize(() => {
          this.session.clear();
        }),
      );
  }
}