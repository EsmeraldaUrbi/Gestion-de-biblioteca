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

import {
  FiltroMisPrestamos,
  MisPrestamosResponse,
} from '../models/mis-prestamos.models';


@Injectable({
  providedIn: 'root',
})
export class MisPrestamosService {
  private readonly http = inject(HttpClient);

  private readonly url =
    `${API_BASE_URL}/prestamos/mios/`;

  obtenerMisPrestamos(
    filtro: FiltroMisPrestamos = 'todos',
    pagina = 1,
    pageSize = 8,
  ): Observable<MisPrestamosResponse> {
    const params = new HttpParams()
      .set('filtro', filtro)
      .set('page', pagina)
      .set('page_size', pageSize);

    return this.http.get<MisPrestamosResponse>(
      this.url,
      { params },
    );
  }
}