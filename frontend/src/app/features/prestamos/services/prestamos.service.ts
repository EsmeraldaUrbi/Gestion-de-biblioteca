import {
  HttpClient,
  HttpParams,
} from '@angular/common/http';

import {
  inject,
  Injectable,
} from '@angular/core';

import {
  EMPTY,
  expand,
  map,
  Observable,
  reduce,
} from 'rxjs';

import {
  API_BASE_URL,
} from '../../../core/config/api.config';

import {
  BusquedaLectores,
  EjemplarPrestamo,
  ElegibilidadPrestamo,
  LibroPrestamo,
  PrestamoRegistrado,
  RespuestaPaginada,
  SolicitudPrestamo,
} from '../models/prestamo.models';


@Injectable({
  providedIn: 'root',
})
export class PrestamosService {
  private readonly http = inject(HttpClient);

  private readonly prestamosUrl =
    `${API_BASE_URL}/prestamos/`;

  private readonly librosUrl =
    `${API_BASE_URL}/libros/`;

  private readonly ejemplaresUrl =
    `${API_BASE_URL}/ejemplares/`;

  buscarLectores(
    termino: string,
  ): Observable<BusquedaLectores> {
    const params = new HttpParams()
      .set('q', termino.trim())
      .set('limite', 10);

    return this.http.get<BusquedaLectores>(
      `${this.prestamosUrl}seleccion/usuarios/`,
      { params },
    );
  }

  buscarLibros(
    termino: string,
  ): Observable<RespuestaPaginada<LibroPrestamo>> {
    const busqueda = termino.trim();

    let params = new HttpParams()
      .set('page', 1)
      .set('page_size', 20);

    // La API administrativa 3.3 admite filtros
    // independientes por título e ISBN.
    if (/^\d{3,13}$/.test(busqueda)) {
      params = params.set('isbn', busqueda);
    } else {
      params = params.set('titulo', busqueda);
    }

    return this.http.get<
      RespuestaPaginada<LibroPrestamo>
    >(
      this.librosUrl,
      { params },
    );
  }

  obtenerEjemplares(
    libroId: number,
  ): Observable<EjemplarPrestamo[]> {
    const params = new HttpParams()
      .set('libro_id', libroId)
      .set('page_size', 100);

    // Recorremos la paginación de Django
    // sin asumir que un libro tiene 100 copias o menos.
    return this.http.get<
      RespuestaPaginada<EjemplarPrestamo>
    >(
      this.ejemplaresUrl,
      { params },
    ).pipe(
      expand((respuesta) =>
        respuesta.next
          ? this.http.get<
              RespuestaPaginada<EjemplarPrestamo>
            >(respuesta.next)
          : EMPTY,
      ),
      reduce(
        (acumulados, respuesta) => [
          ...acumulados,
          ...respuesta.results,
        ],
        [] as EjemplarPrestamo[],
      ),
      map((ejemplares) =>
        ejemplares.sort((a, b) => {
          if (a.estado === 'ACTIVO' &&
              b.estado !== 'ACTIVO') {
            return -1;
          }

          if (a.estado !== 'ACTIVO' &&
              b.estado === 'ACTIVO') {
            return 1;
          }

          return a.ejemplar_id - b.ejemplar_id;
        }),
      ),
    );
  }

  evaluarElegibilidad(
    solicitud: SolicitudPrestamo,
  ): Observable<ElegibilidadPrestamo> {
    const params = new HttpParams()
      .set('usuario_id', solicitud.usuario_id)
      .set('ejemplar_id', solicitud.ejemplar_id);

    return this.http.get<ElegibilidadPrestamo>(
      `${this.prestamosUrl}elegibilidad/`,
      { params },
    );
  }

  registrarPrestamo(
    solicitud: SolicitudPrestamo,
  ): Observable<PrestamoRegistrado> {
    return this.http.post<PrestamoRegistrado>(
      this.prestamosUrl,
      solicitud,
    );
  }
}