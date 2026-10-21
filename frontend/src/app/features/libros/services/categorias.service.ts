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
  ActualizarCategoriaRequest,
  CategoriaAdministrativa,
  CategoriasFiltros,
  CategoriasPaginadas,
  ModificarCategoriaRequest,
  RegistrarCategoriaRequest,
} from '../models/categorias.models';

@Injectable({
  providedIn: 'root',
})
export class CategoriasService {
  private readonly http = inject(HttpClient);

  private readonly categoriasUrl = `${API_BASE_URL}/categorias/`;

  /**
   * GET /api/categorias/
   * Listado paginado con búsqueda por nombre.
   * Requiere rol bibliotecario (gestionado por el interceptor y guards).
   */
  listar(filtros?: CategoriasFiltros): Observable<CategoriasPaginadas> {
    let params = new HttpParams();

    if (filtros) {
      const nombreFiltro = (filtros.nombre ?? filtros.search)?.trim();
      if (nombreFiltro && nombreFiltro.length > 0) {
        params = params.set('nombre', nombreFiltro);
      }
      if (filtros.page !== undefined && filtros.page !== null) {
        params = params.set('page', filtros.page.toString());
      }
      if (filtros.page_size !== undefined && filtros.page_size !== null) {
        params = params.set('page_size', filtros.page_size.toString());
      }
    }

    return this.http.get<CategoriasPaginadas>(this.categoriasUrl, { params });
  }

  /**
   * GET /api/categorias/{categoria_id}/
   * Detalle completo de una categoría por su identificador primario.
   */
  obtenerPorId(categoriaId: number): Observable<CategoriaAdministrativa> {
    return this.http.get<CategoriaAdministrativa>(
      `${this.categoriasUrl}${categoriaId}/`,
    );
  }

  /**
   * Alias de conveniencia para obtenerPorId.
   */
  obtener(categoriaId: number): Observable<CategoriaAdministrativa> {
    return this.obtenerPorId(categoriaId);
  }

  /**
   * POST /api/categorias/
   * Registra una nueva categoría temática.
   * Respuesta: 201 Created. Errores de validación y duplicidad (HTTP 400) se propagan
   * de forma transparente hacia los componentes para su tratamiento visual.
   */
  registrar(
    datos: RegistrarCategoriaRequest,
  ): Observable<CategoriaAdministrativa> {
    return this.http.post<CategoriaAdministrativa>(this.categoriasUrl, datos);
  }

  /**
   * PATCH /api/categorias/{categoria_id}/
   * Modificación parcial del nombre de la categoría.
   * Respuesta: 200 OK con la categoría actualizada.
   */
  modificar(
    categoriaId: number,
    datos: ModificarCategoriaRequest,
  ): Observable<CategoriaAdministrativa> {
    return this.http.patch<CategoriaAdministrativa>(
      `${this.categoriasUrl}${categoriaId}/`,
      datos,
    );
  }

  /**
   * PUT /api/categorias/{categoria_id}/
   * Actualización completa de la categoría.
   * Respuesta: 200 OK con la categoría actualizada.
   */
  actualizar(
    categoriaId: number,
    datos: ActualizarCategoriaRequest,
  ): Observable<CategoriaAdministrativa> {
    return this.http.put<CategoriaAdministrativa>(
      `${this.categoriasUrl}${categoriaId}/`,
      datos,
    );
  }
}
