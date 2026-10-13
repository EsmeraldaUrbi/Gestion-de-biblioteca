import { Injectable } from '@angular/core';

import { AuthSession } from '../models/auth.models';

@Injectable({
  providedIn: 'root',
})
export class AuthStorageService {
  private readonly storageKey = 'bibliotech.auth.session';

  load(): AuthSession | null {
    if (typeof window === 'undefined') {
      return null;
    }

    const rawSession =
      window.sessionStorage.getItem(this.storageKey) ??
      window.localStorage.getItem(this.storageKey);

    if (!rawSession) {
      return null;
    }

    try {
      const session = JSON.parse(rawSession) as AuthSession;

      if (
        !session.token ||
        !session.expiraEn ||
        !session.usuario ||
        !session.usuario.rol ||
        !session.usuario.rol.nombre
      ) {
        this.clear();
        return null;
      }

      return session;
    } catch {
      this.clear();
      return null;
    }
  }

  save(session: AuthSession): void {
    if (typeof window === 'undefined') {
      return;
    }

    this.clear();

    const storage = session.recordar
      ? window.localStorage
      : window.sessionStorage;

    storage.setItem(
      this.storageKey,
      JSON.stringify(session),
    );
  }

  clear(): void {
    if (typeof window === 'undefined') {
      return;
    }

    window.sessionStorage.removeItem(
      this.storageKey,
    );

    window.localStorage.removeItem(
      this.storageKey,
    );
  }
}