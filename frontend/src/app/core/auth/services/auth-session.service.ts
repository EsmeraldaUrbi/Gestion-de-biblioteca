import {
  computed,
  inject,
  Injectable,
  signal,
} from '@angular/core';

import {
  AuthSession,
  LoginResponse,
  UsuarioSesion,
} from '../models/auth.models';
import { AuthStorageService } from './auth-storage.service';

@Injectable({
  providedIn: 'root',
})
export class AuthSessionService {
  private readonly storage = inject(
    AuthStorageService,
  );

  private readonly sessionState =
    signal<AuthSession | null>(
      this.storage.load(),
    );

  readonly session =
    this.sessionState.asReadonly();

  readonly usuario = computed(
    () => this.sessionState()?.usuario ?? null,
  );

  readonly token = computed(
    () => this.sessionState()?.token ?? null,
  );

  readonly rol = computed(
    () =>
      this.sessionState()?.usuario.rol.nombre ??
      null,
  );

  readonly autenticado = computed(
    () =>
      this.sessionState() !== null &&
      !this.isExpired(),
  );

  hasSession(): boolean {
    return this.sessionState() !== null;
  }

  isExpired(): boolean {
    const session = this.sessionState();

    if (!session) {
      return false;
    }

    const expiration = Date.parse(
      session.expiraEn,
    );

    if (Number.isNaN(expiration)) {
      return true;
    }

    return expiration <= Date.now();
  }

  start(
    response: LoginResponse,
    recordar: boolean,
  ): void {
    const session: AuthSession = {
      token: response.token,
      expiraEn: response.expira_en,
      usuario: response.usuario,
      recordar,
    };

    this.storage.save(session);
    this.sessionState.set(session);
  }

  updateUser(usuario: UsuarioSesion): void {
    const current = this.sessionState();

    if (!current) {
      return;
    }

    const updated: AuthSession = {
      ...current,
      usuario,
    };

    this.storage.save(updated);
    this.sessionState.set(updated);
  }

  clear(): void {
    this.storage.clear();
    this.sessionState.set(null);
  }
}