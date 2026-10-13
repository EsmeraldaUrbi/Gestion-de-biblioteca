import { inject } from '@angular/core';
import {
  CanActivateFn,
  Router,
} from '@angular/router';

import { AuthSessionService } from '../services/auth-session.service';

export const authGuard: CanActivateFn = () => {
  const session = inject(
    AuthSessionService,
  );

  const router = inject(Router);

  if (!session.hasSession()) {
    return router.createUrlTree(
      ['/login'],
    );
  }

  if (session.isExpired()) {
    session.clear();

    return router.createUrlTree(
      ['/login'],
      {
        queryParams: {
          reason: 'session-expired',
        },
      },
    );
  }

  return true;
};