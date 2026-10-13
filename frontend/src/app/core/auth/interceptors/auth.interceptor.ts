import {
  HttpErrorResponse,
  HttpInterceptorFn,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import {
  catchError,
  throwError,
} from 'rxjs';

import { API_BASE_URL } from '../../config/api.config';
import { AuthSessionService } from '../services/auth-session.service';

export const authInterceptor: HttpInterceptorFn = (
  request,
  next,
) => {
  const session = inject(
    AuthSessionService,
  );

  const router = inject(Router);

  const isApiRequest =
    request.url.startsWith(API_BASE_URL);

  const isLoginRequest =
    request.url ===
    `${API_BASE_URL}/auth/login/`;

  const isLogoutRequest =
    request.url ===
    `${API_BASE_URL}/auth/logout/`;

  const token = session.token();

  let outgoingRequest = request;

  if (
    isApiRequest &&
    !isLoginRequest &&
    token
  ) {
    outgoingRequest = request.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  return next(outgoingRequest).pipe(
    catchError(
      (error: HttpErrorResponse) => {
        if (
          isApiRequest &&
          error.status === 401 &&
          !isLoginRequest &&
          !isLogoutRequest &&
          session.hasSession()
        ) {
          session.clear();

          void router.navigate(
            ['/login'],
            {
              queryParams: {
                reason: 'session-expired',
              },
            },
          );
        }

        if (
          isApiRequest &&
          error.status === 403 &&
          session.hasSession()
        ) {
          void router.navigate(
            ['/acceso-denegado'],
          );
        }

        return throwError(
          () => error,
        );
      },
    ),
  );
};