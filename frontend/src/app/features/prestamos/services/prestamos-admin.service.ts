import {
  HttpClient,
  HttpParams,
} from '@angular/common/http';

import {
  inject,
  Injectable,
} from '@angular/core';

import {
  Observable,
} from 'rxjs';

import {
  API_BASE_URL,
} from '../../../core/config/api.config';

import type {
  FiltrosPrestamosAdmin,
  PrestamosAdminResponse,
} from '../models/prestamos-admin.models';


@Injectable({
  providedIn: 'root',
})
export class PrestamosAdminService {
  private readonly http = inject(HttpClient);

  private readonly url =
    `${API_BASE_URL}/prestamos/`;

  listar(
    filtros: FiltrosPrestamosAdmin,
  ): Observable<PrestamosAdminResponse> {
    let params = new HttpParams()
      .set('estado', filtros.estado)
      .set('page', filtros.page)
      .set('page_size', filtros.pageSize);

    const termino = filtros.q.trim();

    if (termino) {
      params = params.set('q', termino);
    }

    return this.http.get<PrestamosAdminResponse>(
      this.url,
      { params },
    );
  }
}