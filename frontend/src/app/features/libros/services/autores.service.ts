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
  ActualizarAutorRequest,
  AutorAdministrativo,
  AutoresFiltros,
  AutoresPaginados,
  ModificarAutorRequest,
  RegistrarAutorRequest,
} from '../models/autores.models';

@Injectable({
  providedIn: 'root',
})
export class AutoresService {
  private readonly http = inject(HttpClient);

  private readonly autoresUrl = `${API_BASE_URL}/autores/`;

  /**
   * GET /api/autores/
   * Listado paginado con filtros opcionales de nombre y nacionalidad.
   * Requiere rol bibliotecario (gestionado por el interceptor y guards).
   */
  listar(filtros?: AutoresFiltros): Observable<AutoresPaginados> {
    let params = new HttpParams();

    if (filtros) {
      const nombreFiltro = (filtros.nombre ?? filtros.search)?.trim();
      if (nombreFiltro && nombreFiltro.length > 0) {
        params = params.set('nombre', nombreFiltro);
      }
      if (filtros.nacionalidad && filtros.nacionalidad.trim().length > 0) {
        params = params.set('nacionalidad', filtros.nacionalidad.trim());
      }
      if (filtros.page !== undefined && filtros.page !== null) {
        params = params.set('page', filtros.page.toString());
      }
      if (filtros.page_size !== undefined && filtros.page_size !== null) {
        params = params.set('page_size', filtros.page_size.toString());
      }
    }

    return this.http.get<AutoresPaginados>(this.autoresUrl, { params });
  }

  /**
   * GET /api/autores/{autor_id}/
   * Detalle completo de un autor por su identificador primario.
   */
  obtenerPorId(autorId: number): Observable<AutorAdministrativo> {
    return this.http.get<AutorAdministrativo>(`${this.autoresUrl}${autorId}/`);
  }

  /**
   * Alias de conveniencia para obtenerPorId.
   */
  obtener(autorId: number): Observable<AutorAdministrativo> {
    return this.obtenerPorId(autorId);
  }

  /**
   * POST /api/autores/
   * Registra un nuevo autor bibliográfico.
   * Respuesta: 201 Created con los datos del autor registrado.
   */
  registrar(datos: RegistrarAutorRequest): Observable<AutorAdministrativo> {
    return this.http.post<AutorAdministrativo>(this.autoresUrl, datos);
  }

  /**
   * PATCH /api/autores/{autor_id}/
   * Modificación parcial. Conserva los campos omitidos en backend.
   * Respuesta: 200 OK con el autor actualizado.
   */
  modificar(
    autorId: number,
    datos: ModificarAutorRequest,
  ): Observable<AutorAdministrativo> {
    return this.http.patch<AutorAdministrativo>(
      `${this.autoresUrl}${autorId}/`,
      datos,
    );
  }

  /**
   * PUT /api/autores/{autor_id}/
   * Actualización completa. Los campos opcionales omitidos se restablecen a null.
   * Respuesta: 200 OK con el autor actualizado.
   */
  actualizar(
    autorId: number,
    datos: ActualizarAutorRequest,
  ): Observable<AutorAdministrativo> {
    return this.http.put<AutorAdministrativo>(
      `${this.autoresUrl}${autorId}/`,
      datos,
    );
  }
}
