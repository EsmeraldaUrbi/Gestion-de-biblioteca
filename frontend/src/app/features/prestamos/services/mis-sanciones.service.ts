import {
  HttpClient,
  HttpParams,
} from '@angular/common/http';
import {
  inject,
  Injectable,
} from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from '../../../core/config/api.config';
import type {
  FiltrosMisSanciones,
  RespuestaMisSanciones,
} from '../models/mis-sanciones.models';

@Injectable({
  providedIn: 'root',
})
export class MisSancionesService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_BASE_URL}/sanciones/mias/`;

  listar(filtros?: FiltrosMisSanciones): Observable<RespuestaMisSanciones> {
    let params = new HttpParams();

    if (filtros) {
      if (filtros.tipo !== undefined && filtros.tipo !== null) {
        params = params.set('tipo', filtros.tipo);
      }
      if (filtros.estado !== undefined && filtros.estado !== null) {
        params = params.set('estado', filtros.estado);
      }
      if (filtros.page !== undefined && filtros.page !== null) {
        params = params.set('page', filtros.page.toString());
      }
      if (filtros.page_size !== undefined && filtros.page_size !== null) {
        params = params.set('page_size', filtros.page_size.toString());
      }
    }

    return this.http.get<RespuestaMisSanciones>(this.url, { params });
  }
}
