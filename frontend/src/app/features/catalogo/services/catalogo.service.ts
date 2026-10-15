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
import {
  CatalogoFiltros,
  CatalogoOpciones,
  CatalogoResponse,
  LibroCatalogo,
} from '../models/catalogo.models';

@Injectable({
  providedIn: 'root',
})
export class CatalogoService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${API_BASE_URL}/catalogo`;

  listar(filtros?: CatalogoFiltros): Observable<CatalogoResponse> {
    let params = new HttpParams();

    if (filtros) {
      if (filtros.titulo && filtros.titulo.trim().length > 0) {
        params = params.set('titulo', filtros.titulo.trim());
      }
      if (filtros.autor !== undefined && filtros.autor !== null) {
        params = params.set('autor', filtros.autor.toString());
      }
      if (filtros.categoria !== undefined && filtros.categoria !== null) {
        params = params.set('categoria', filtros.categoria.toString());
      }
      if (filtros.disponible !== undefined && filtros.disponible !== null) {
        params = params.set('disponible', filtros.disponible.toString());
      }
      if (filtros.page !== undefined && filtros.page !== null) {
        params = params.set('page', filtros.page.toString());
      }
      if (filtros.page_size !== undefined && filtros.page_size !== null) {
        params = params.set('page_size', filtros.page_size.toString());
      }
    }

    return this.http.get<CatalogoResponse>(`${this.baseUrl}/`, { params });
  }

  obtenerFiltros(): Observable<CatalogoOpciones> {
    return this.http.get<CatalogoOpciones>(`${this.baseUrl}/filtros/`);
  }

  obtenerDetalle(libroId: number): Observable<LibroCatalogo> {
    return this.http.get<LibroCatalogo>(`${this.baseUrl}/${libroId}/`);
  }
}
