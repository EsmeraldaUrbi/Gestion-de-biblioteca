# Contrato de API — Gestión de usuarios

## Información general

- Ticket: 3.2.2
- Estado: Implementado y probado
- Backend: Django REST Framework
- URL base: `/api/`
- Autenticación: Bearer Token
- Rol autorizado: bibliotecario

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/usuarios/` | Listar usuarios |
| POST | `/api/usuarios/` | Registrar usuario |
| GET | `/api/usuarios/{usuario_id}/` | Consultar usuario |
| PATCH | `/api/usuarios/{usuario_id}/` | Modificar usuario |
| GET | `/api/roles/` | Consultar roles | (Solo devuelve estudiante, docente y bibliotecario)

Todos requieren autenticación y rol bibliotecario.

## Representación de usuario

```json
{
  "usuario_id": 1,
  "nombre": "Ana Martínez",
  "email": "ana@example.com",
  "direccion": "Puebla",
  "telefono": "2221234567",
  "rol": {
    "rol_id": 1,
    "nombre": "estudiante",
    "limite_prestamos_activos": 5
  }
}
```

El ID es ilustrativo. No debe asumirse que un rol
tenga siempre el mismo identificador.

Nunca se devuelve `password` ni `contrasena_hash`.

## GET /api/usuarios/

Devuelve un listado paginado de usuarios,
ordenado por `usuario_id`.

Parámetros opcionales:

| Parámetro | Descripción |
|---|---|
| `page` | Página solicitada, desde 1 |
| `page_size` | Tamaño de página, predeterminado 10 y máximo 100 |

Respuesta HTTP 200:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "usuario_id": 1,
      "nombre": "Ana Martínez",
      "email": "ana@example.com",
      "direccion": "Puebla",
      "telefono": "2221234567",
      "rol": {
        "rol_id": 1,
        "nombre": "estudiante",
        "limite_prestamos_activos": 5
      }
    }
  ]
}
```

Actualmente este endpoint no implementa búsqueda
por nombre, filtro por rol ni filtro por estado.

## POST /api/usuarios/

Registra un usuario y almacena su contraseña
mediante el hashing de Django.

Solicitud JSON:

```json
{
  "nombre": "Ana Martínez",
  "email": "ana@example.com",
  "direccion": "Puebla",
  "telefono": "2221234567",
  "rol_id": 1,
  "password": "ClaveSegura123!"
}
```

Campos obligatorios:

- `nombre`: texto no vacío, máximo 100 caracteres.
- `email`: correo válido, máximo 50 caracteres.
- `rol_id`: entero positivo correspondiente
  a un rol existente.
- `password`: contraseña inicial que debe superar
  los validadores de Django.

Campos opcionales:

- `direccion`: texto o null, máximo 255 caracteres.
- `telefono`: texto o null, máximo 15 caracteres.

El correo se normaliza a minúsculas.
No se permite registrar un correo duplicado.

Respuesta exitosa: HTTP 201.
El cuerpo contiene el usuario creado, sin contraseña.

Los campos desconocidos se rechazan.

## GET /api/usuarios/{usuario_id}/

Devuelve los datos del usuario solicitado.

Respuesta exitosa: HTTP 200.
Usuario inexistente: HTTP 404.

## PATCH /api/usuarios/{usuario_id}/

Permite modificar uno o varios de estos campos:

- `nombre`
- `email`
- `direccion`
- `telefono`
- `rol_id`

Solicitud de ejemplo:

```json
{
  "nombre": "Ana Martínez López",
  "telefono": "2229876543"
}
```

Respuesta exitosa: HTTP 200.
El cuerpo contiene el usuario actualizado.

El endpoint rechaza campos no definidos,
incluido `password`.

Si se intenta cambiar a bibliotecario a un usuario
con préstamos activos, se devuelve HTTP 400.

## GET /api/roles/

Devuelve una lista de roles registrados en MySQL,
con los campos:

- `rol_id`
- `nombre`
- `limite_prestamos_activos`

Respuesta exitosa: HTTP 200.

## Códigos HTTP

| Código | Significado |
|---|---|
| 200 | Consulta o modificación exitosa |
| 201 | Registro exitoso |
| 400 | Validación o regla de negocio incumplida |
| 401 | No autenticado |
| 403 | Rol sin autorización |
| 404 | Usuario inexistente |

Los errores de validación utilizan normalmente
el nombre del campo y una lista de mensajes.

Ejemplo de correo duplicado:

```json
{
  "email": [
    "Este correo ya está registrado."
  ]
}
```

## Reglas de negocio relacionadas

- RN-07: asociación del usuario con un rol.
- RN-08: autorización del bibliotecario.
- P-06: elegibilidad para recibir préstamos.

No se permite convertir en bibliotecario a un
usuario que mantenga préstamos activos.

## Seguridad

- Los endpoints son exclusivos de bibliotecarios.
- No se devuelven hashes ni contraseñas.
- No se admite cambio de contraseña mediante PATCH.
- No existe endpoint de eliminación de usuarios
  en este módulo.

## Pruebas

Archivo:
`backend/biblioteca/tests/test_usuarios.py`

Ejecutar:

```bash
docker compose exec -T backend python manage.py test biblioteca.tests.test_usuarios -v 2
```

Se han implementado 21 pruebas, incluida la integración con Bearer

## Pendientes antes del cierre
1. Coordinar con préstamos la prevención de
   condiciones de carrera en cambios de rol.
2. Confirmar los criterios de aceptación con el
   frontend de gestión de usuarios.
