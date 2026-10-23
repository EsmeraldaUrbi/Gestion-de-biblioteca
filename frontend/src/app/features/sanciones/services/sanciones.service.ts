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
  FiltroEstadoSancion,
  RespuestaPaginadaSanciones,
  ResumenMisSanciones,
  ResumenSancionesAdministrativo,
  Sancion,
  TipoSancion,
} from '../models/sanciones.models';


export interface ConsultaSanciones {
  q?: string;
  tipo?: TipoSancion | 'todos';
  estado?: FiltroEstadoSancion;
  page?: number;
  pageSize?: number;
}


@Injectable({
  providedIn: 'root',
})
export class SancionesService {
  private readonly http = inject(HttpClient);
  private readonly url = `${API_BASE_URL}/sanciones/`;

  obtenerAdministrativas(
    consulta: ConsultaSanciones = {},
  ): Observable<RespuestaPaginadaSanciones<ResumenSancionesAdministrativo>> {
    let params = new HttpParams()
      .set('page', consulta.page ?? 1)
      .set('page_size', consulta.pageSize ?? 10)
      .set('tipo', consulta.tipo ?? 'todos')
      .set('estado', consulta.estado ?? 'todos');

    if (consulta.q?.trim()) {
      params = params.set('q', consulta.q.trim());
    }

    return this.http.get<RespuestaPaginadaSanciones<ResumenSancionesAdministrativo>>(
      this.url,
      { params },
    );
  }

  obtenerMias(
    page = 1,
    pageSize = 10,
  ): Observable<RespuestaPaginadaSanciones<ResumenMisSanciones>> {
    return this.http.get<RespuestaPaginadaSanciones<ResumenMisSanciones>>(
      `${this.url}mias/`,
      {
        params: new HttpParams()
          .set('page', page)
          .set('page_size', pageSize),
      },
    );
  }

  registrarPago(sancionId: number): Observable<Sancion> {
    return this.http.post<Sancion>(
      `${this.url}${sancionId}/pago/`,
      {},
    );
  }
}
