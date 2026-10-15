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
  CambiarEstadoEjemplarRequest,
  Ejemplar,
  EjemplaresFiltros,
  EjemplaresPaginados,
  RegistrarEjemplarRequest,
} from '../models/libros.models';

@Injectable({
  providedIn: 'root',
})
export class EjemplaresService {
  private readonly http = inject(HttpClient);

  private readonly ejemplaresUrl = `${API_BASE_URL}/ejemplares/`;

  /**
   * GET /api/ejemplares/
   * Listado paginado con filtros opcionales.
   * Para obtener los ejemplares de un libro, usar filtros.libro_id.
   * La primera página no garantiza todos los ejemplares; implementar paginación.
   */
  listar(filtros?: EjemplaresFiltros): Observable<EjemplaresPaginados> {
    let params = new HttpParams();

    if (filtros) {
      if (filtros.libro_id !== undefined && filtros.libro_id !== null) {
        params = params.set('libro_id', filtros.libro_id.toString());
      }
      if (filtros.estado) {
        params = params.set('estado', filtros.estado);
      }
      if (
        filtros.codigo_inventario &&
        filtros.codigo_inventario.trim().length > 0
      ) {
        params = params.set(
          'codigo_inventario',
          filtros.codigo_inventario.trim(),
        );
      }
      if (filtros.page !== undefined && filtros.page !== null) {
        params = params.set('page', filtros.page.toString());
      }
      if (filtros.page_size !== undefined && filtros.page_size !== null) {
        params = params.set('page_size', filtros.page_size.toString());
      }
    }

    return this.http.get<EjemplaresPaginados>(this.ejemplaresUrl, { params });
  }

  /**
   * GET /api/ejemplares/{ejemplar_id}/
   * Consulta individual de un ejemplar.
   */
  obtener(ejemplarId: number): Observable<Ejemplar> {
    return this.http.get<Ejemplar>(`${this.ejemplaresUrl}${ejemplarId}/`);
  }

  /**
   * POST /api/ejemplares/
   * Registra un nuevo ejemplar físico asociado a un libro.
   * El estado es opcional (predeterminado: ACTIVO por el backend, RN-03).
   * Respuesta: 201 Created con el ejemplar creado.
   */
  registrar(datos: RegistrarEjemplarRequest): Observable<Ejemplar> {
    return this.http.post<Ejemplar>(this.ejemplaresUrl, datos);
  }

  /**
   * PATCH /api/ejemplares/{ejemplar_id}/
   * Cambia el estado operativo de un ejemplar.
   * RESTRICCIÓN: solo acepta el campo `estado`. Enviar cualquier otro
   * campo resulta en HTTP 400 del servidor.
   * El backend rechaza transiciones prohibidas por préstamos activos (RN-04)
   * con HTTP 400; el frontend debe mostrar ese error sin suponer disponibilidad.
   */
  cambiarEstado(
    ejemplarId: number,
    datos: CambiarEstadoEjemplarRequest,
  ): Observable<Ejemplar> {
    return this.http.patch<Ejemplar>(
      `${this.ejemplaresUrl}${ejemplarId}/`,
      datos,
    );
  }
}
