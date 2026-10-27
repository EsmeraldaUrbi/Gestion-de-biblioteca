# Contrato de API — Autenticación y control de acceso

## Información general

- **Módulo:** 3.1 — Autenticación y permisos.
- **Entregable:** 2.4 — Contratos de API.
- **Backend:** Django REST Framework con `BibliotecaTokenAuthentication`.
- **Frontend:** `core/auth/services/auth.service.ts` y el interceptor de autenticación de Angular.
- **URL base:** `/api/` (`http://localhost:8000/api/` en desarrollo).
- **Formato:** JSON; las rutas terminan con `/`.
- **Referencia temporal:** el servidor define la expiración; las fechas y horas se entregan en formato ISO 8601.

## Endpoints implementados

| Método | Ruta | Requiere Bearer | Roles autorizados | Función |
|---|---|---|---|---|
| POST | `/api/auth/login/` | No | Cualquier cuenta con credenciales válidas | Obtener token de acceso |
| POST | `/api/auth/logout/` | Sí | Cualquier usuario autenticado | Revocar el token presentado |
| GET | `/api/auth/me/` | Sí | Cualquier usuario autenticado | Consultar la identidad de la sesión |
| GET | `/api/auth/access/bibliotecario/` | Sí | `bibliotecario` | Verificar acceso administrativo |
| GET | `/api/auth/access/lector/` | Sí | `estudiante`, `docente` | Verificar acceso de lector |

## 1. POST `/api/auth/login/`

**Solicitud JSON:**

```json
{
  "email": "lector@example.com",
  "password": "<contrasena_de_ejemplo>"
}
```

- `email`: obligatorio; correo válido de máximo 50 caracteres. Se normaliza a minúsculas y se eliminan espacios externos.
- `password`: obligatorio, cadena no vacía. No se recortan los espacios de la contraseña.
- El servidor compara la contraseña mediante el verificador de hash del usuario.
- Esta operación **no** requiere cabecera `Authorization`.

**HTTP 200:**

```json
{
  "token": "<token_opaco_de_ejemplo>",
  "tipo_token": "Bearer",
  "expira_en": "2026-10-26T23:00:00+00:00",
  "usuario": {
    "usuario_id": 5,
    "nombre": "Lector de ejemplo",
    "email": "lector@example.com",
    "rol": {
      "rol_id": 1,
      "nombre": "estudiante",
      "limite_prestamos_activos": 5
    }
  }
}
```

El token y la fecha de expiración anteriores son **ilustrativos**, no credenciales utilizables. `expira_en` indica un instante absoluto, no una hora local fija. La respuesta no incluye la contraseña ni su hash.

**Errores:** `400` para validaciones de campos (p. ej., correo con formato inválido o contraseña ausente) y `401` para usuario inexistente o contraseña incorrecta, ambos casos sin revelar cuál credencial falló:

```json
{
  "detail": "Credenciales incorrectas."
}
```

## 2. POST `/api/auth/logout/`

**Solicitud:** cabecera `Authorization: Bearer <token>`; el frontend envía `{}` como cuerpo, pero no se requieren campos de negocio.

**HTTP 204 No Content:** sin cuerpo de respuesta. Revoca únicamente el token de la solicitud. Reutilizarlo después produce `401`.

**Errores:** `401` si no se proporciona una sesión válida o si el token ya está revocado o expirado.

## 3. GET `/api/auth/me/`

No recibe cuerpo ni parámetros. Obtiene la identidad del token presentado, no de un `usuario_id` enviado por el cliente.

**HTTP 200:**

```json
{
  "usuario_id": 5,
  "nombre": "Lector de ejemplo",
  "email": "lector@example.com",
  "rol": {
    "rol_id": 1,
    "nombre": "estudiante",
    "limite_prestamos_activos": 5
  }
}
```

**Errores:** `401` si no hay token válido. El frontend utiliza este endpoint al restaurar una sesión guardada.

## 4. GET `/api/auth/access/bibliotecario/`

Requiere token Bearer y rol `bibliotecario` (`IsBibliotecario`). No recibe cuerpo ni parámetros.

**HTTP 200:**

```json
{
  "detail": "Acceso autorizado para bibliotecario."
}
```

**Errores:** `401` sin autenticación válida; `403` si el usuario autenticado no es bibliotecario.

## 5. GET `/api/auth/access/lector/`

Requiere token Bearer y rol `estudiante` o `docente` (`IsEstudianteODocente`). No recibe cuerpo ni parámetros.

**HTTP 200:**

```json
{
  "detail": "Acceso autorizado para estudiante o docente."
}
```

**Errores:** `401` sin autenticación válida; `403` si el usuario autenticado es bibliotecario u otro rol no permitido.

## Autenticación, expiración y seguridad

Las peticiones protegidas deben incluir:

```http
Authorization: Bearer <token>
```

- Se utiliza un **token opaco personalizado**, no JWT ni autenticación por cookies para estas API.
- El token se genera aleatoriamente; la base de datos conserva su **hash SHA-256**, no el valor plano.
- La expiración se calcula al iniciar sesión usando `AUTH_TOKEN_TTL_HOURS` (valor predeterminado de configuración: **8 horas**, modificable mediante variable de entorno).
- El token expirado o revocado no sirve para acceder a rutas protegidas. Al detectar uno expirado, el backend lo revoca.
- El control de acceso real corresponde al backend; los *guards* del frontend mejoran la navegación, pero no sustituyen los permisos de Django.
- No registrar tokens ni contraseñas reales en contratos, capturas, tickets o colecciones de ejemplo.

## Códigos HTTP y formato de errores

| Código | Cuándo aparece |
|---|---|
| `200` | Login, consulta de sesión o verificación de acceso exitosa |
| `204` | Cierre de sesión exitoso |
| `400` | Campos de login ausentes o inválidos; DRF devuelve errores asociados al campo |
| `401` | Credenciales incorrectas o token ausente, inválido, revocado o expirado |
| `403` | Token válido, pero rol no autorizado para el recurso |
| `405` | Método HTTP no implementado para una ruta |

Para errores de campos, DRF emplea normalmente listas de mensajes por campo. Las denegaciones de autenticación o permisos usan `detail`.

## Código relacionado y pruebas

- Rutas: `backend/biblioteca/urls.py`.
- Vistas y validaciones: `presentation/auth_views.py` y `presentation/auth_serializers.py`.
- Emisión y revocación: `services/auth_service.py` y `repositories/auth_repository.py`.
- Validación del Bearer: `backend/biblioteca/authentication.py`.
- Permisos: `backend/biblioteca/permissions.py`.
- Cliente Angular: `frontend/src/app/core/auth/services/auth.service.ts`.
- Pruebas: `backend/biblioteca/tests/test_auth.py`.

```bash
docker compose exec -T backend python manage.py test biblioteca.tests.test_auth --verbosity 1
```

**Dependencias:** los usuarios y sus roles deben existir en la base de datos; el resto de las API protegidas utiliza el mismo mecanismo de autenticación.
