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
  ActualizarLibroRequest,
  Libro,
  LibrosFiltros,
  LibrosPaginados,
  ModificarLibroRequest,
  RegistrarLibroRequest,
} from '../models/libros.models';

@Injectable({
  providedIn: 'root',
})
export class LibrosService {
  private readonly http = inject(HttpClient);

  private readonly librosUrl = `${API_BASE_URL}/libros/`;

  /**
   * GET /api/libros/
   * Listado paginado con filtros opcionales.
   * Requiere rol bibliotecario (gestionado por el interceptor y el guard).
   */
  listar(filtros?: LibrosFiltros): Observable<LibrosPaginados> {
    let params = new HttpParams();

    if (filtros) {
      if (filtros.titulo && filtros.titulo.trim().length > 0) {
        params = params.set('titulo', filtros.titulo.trim());
      }
      if (filtros.isbn && filtros.isbn.trim().length > 0) {
        params = params.set('isbn', filtros.isbn.trim());
      }
      if (filtros.autor_id !== undefined && filtros.autor_id !== null) {
        params = params.set('autor_id', filtros.autor_id.toString());
      }
      if (filtros.categoria_id !== undefined && filtros.categoria_id !== null) {
        params = params.set('categoria_id', filtros.categoria_id.toString());
      }
      if (filtros.page !== undefined && filtros.page !== null) {
        params = params.set('page', filtros.page.toString());
      }
      if (filtros.page_size !== undefined && filtros.page_size !== null) {
        params = params.set('page_size', filtros.page_size.toString());
      }
    }

    return this.http.get<LibrosPaginados>(this.librosUrl, { params });
  }

  /**
   * GET /api/libros/{libro_id}/
   * Detalle completo de un libro.
   */
  obtener(libroId: number): Observable<Libro> {
    return this.http.get<Libro>(`${this.librosUrl}${libroId}/`);
  }

  /**
   * POST /api/libros/
   * Registra un nuevo libro junto con sus autores y categorías.
   * Respuesta: 201 Created con el libro creado.
   */
  registrar(datos: RegistrarLibroRequest): Observable<Libro> {
    return this.http.post<Libro>(this.librosUrl, datos);
  }

  /**
   * PATCH /api/libros/{libro_id}/
   * Actualización parcial. Las asociaciones omitidas se conservan.
   * Respuesta: 200 OK con el libro actualizado.
   */
  modificarParcial(
    libroId: number,
    datos: ModificarLibroRequest,
  ): Observable<Libro> {
    return this.http.patch<Libro>(`${this.librosUrl}${libroId}/`, datos);
  }

  /**
   * PUT /api/libros/{libro_id}/
   * Actualización completa. La omisión de autor_ids o categoria_ids
   * vacía las asociaciones correspondientes.
   * Respuesta: 200 OK con el libro actualizado.
   */
  actualizarCompleto(
    libroId: number,
    datos: ActualizarLibroRequest,
  ): Observable<Libro> {
    return this.http.put<Libro>(`${this.librosUrl}${libroId}/`, datos);
  }
}
