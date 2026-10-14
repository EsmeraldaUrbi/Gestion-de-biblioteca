import type { UserRole } from '../../../core/auth/models/auth.models';

// Rol registrado en la base de datos.
export interface Rol {
  rol_id: number;
  nombre: UserRole;
  limite_prestamos_activos: number;
}

// Datos que devuelve la API de usuarios.
export interface Usuario {
  usuario_id: number;
  nombre: string;
  email: string;
  direccion: string | null;
  telefono: string | null;
  rol: Rol;
}

// Estructura de una respuesta paginada de Django.
export interface UsuariosPaginados {
  count: number;
  next: string | null;
  previous: string | null;
  results: Usuario[];
}

// Datos necesarios para registrar un usuario.
export interface RegistrarUsuarioRequest {
  nombre: string;
  email: string;
  direccion?: string | null;
  telefono?: string | null;
  rol_id: number;
  password: string;
}

// En edición se permite modificar solo algunos campos.
// La contraseña no forma parte de esta operación.
export type ModificarUsuarioRequest = Partial<
  Omit<RegistrarUsuarioRequest, 'password'>
>;
