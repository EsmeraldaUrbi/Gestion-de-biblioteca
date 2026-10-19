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
  RespuestaPaginada,
} from '../models/prestamo.models';

import type {
  DevolucionRegistrada,
  PrestamoActivoDevolucion,
} from '../models/devolucion.models';


@Injectable({
  providedIn: 'root',
})
export class DevolucionesService {
  private readonly http = inject(HttpClient);

  buscarPrestamosActivos(
    termino: string,
    pagina: number = 1,
  ): Observable<RespuestaPaginada<PrestamoActivoDevolucion>> {
    const params = new HttpParams()
      .set('q', termino.trim())
      .set('page', pagina)
      .set('page_size', 10);

    return this.http.get<
      RespuestaPaginada<PrestamoActivoDevolucion>
    >(
      `${API_BASE_URL}/devoluciones/prestamos-activos/`,
      { params },
    );
  }

  registrarDevolucion(
    prestamoId: number,
  ): Observable<DevolucionRegistrada> {
    return this.http.post<DevolucionRegistrada>(
      `${API_BASE_URL}/prestamos/${prestamoId}/devolucion/`,
      {},
    );
  }
}