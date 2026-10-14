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
  ModificarUsuarioRequest,
  RegistrarUsuarioRequest,
  Rol,
  Usuario,
  UsuariosPaginados,
} from '../models/usuario.models';

@Injectable({
  providedIn: 'root',
})
export class UsuariosService {
  private readonly http = inject(HttpClient);

  private readonly usuariosUrl =
    `${API_BASE_URL}/usuarios/`;

  private readonly rolesUrl =
    `${API_BASE_URL}/roles/`;

  // Obtener una página del listado de usuarios.
  listarUsuarios(
    page = 1,
    pageSize = 10,
  ): Observable<UsuariosPaginados> {
    const params = new HttpParams()
      .set('page', page)
      .set('page_size', pageSize);

    return this.http.get<UsuariosPaginados>(
      this.usuariosUrl,
      { params },
    );
  }

  // Consultar los datos de un usuario.
  obtenerUsuario(
    usuarioId: number,
  ): Observable<Usuario> {
    return this.http.get<Usuario>(
      `${this.usuariosUrl}${usuarioId}/`,
    );
  }

  // Registrar un nuevo usuario.
  registrarUsuario(
    datos: RegistrarUsuarioRequest,
  ): Observable<Usuario> {
    return this.http.post<Usuario>(
      this.usuariosUrl,
      datos,
    );
  }

  // Modificar los campos permitidos.
  modificarUsuario(
    usuarioId: number,
    datos: ModificarUsuarioRequest,
  ): Observable<Usuario> {
    return this.http.patch<Usuario>(
      `${this.usuariosUrl}${usuarioId}/`,
      datos,
    );
  }

  // Obtener los roles disponibles.
  listarRoles(): Observable<Rol[]> {
    return this.http.get<Rol[]>(
      this.rolesUrl,
    );
  }
}
