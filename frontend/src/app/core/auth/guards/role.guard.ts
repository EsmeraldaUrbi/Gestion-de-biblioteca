import { inject } from '@angular/core';
import {
  ActivatedRouteSnapshot,
  CanActivateFn,
  Router,
} from '@angular/router';

import { UserRole } from '../models/auth.models';
import { AuthSessionService } from '../services/auth-session.service';

export const roleGuard: CanActivateFn = (
  route: ActivatedRouteSnapshot,
) => {
  const session = inject(
    AuthSessionService,
  );

  const router = inject(Router);

  const allowedRoles =
    route.data['roles'] as
      | UserRole[]
      | undefined;

  if (
    !allowedRoles ||
    allowedRoles.length === 0
  ) {
    return true;
  }

  const currentRole = session.rol();

  if (
    currentRole &&
    allowedRoles.includes(currentRole)
  ) {
    return true;
  }

  return router.createUrlTree(
    ['/acceso-denegado'],
  );
};