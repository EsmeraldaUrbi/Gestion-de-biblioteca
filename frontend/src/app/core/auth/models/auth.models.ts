export type UserRole = 'estudiante' | 'docente' | 'bibliotecario';

export interface RolSesion {
  rol_id: number;
  nombre: UserRole;
  limite_prestamos_activos: number;
}

export interface UsuarioSesion {
  usuario_id: number;
  nombre: string;
  email: string;
  rol: RolSesion;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  tipo_token: string;
  expira_en: string;
  usuario: UsuarioSesion;
}

export interface AuthSession {
  token: string;
  expiraEn: string;
  usuario: UsuarioSesion;
  recordar: boolean;
}