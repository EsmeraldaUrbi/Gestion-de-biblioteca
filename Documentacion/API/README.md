
# Contratos de API — Sistema de Gestión de Biblioteca

## Objetivo

Este directorio centraliza los contratos HTTP de
comunicación entre Angular y Django REST Framework.

Corresponde al entregable 2.4 del proyecto.

Los contratos documentan los endpoints implementados
y sus restricciones de autenticación, permisos,
validaciones y respuestas.

## Convenciones generales

- URL base local: `http://localhost:8000/api/`.
- Formato: JSON.
- Fechas: `YYYY-MM-DD`.
- Autenticación: `Authorization: Bearer <token>`.
- Excepción: `POST /api/auth/login/`.
- Identificadores: generados por MySQL.
- Permisos: verificados en el backend.

## Códigos HTTP generales

| Código | Significado |
|---|---|
| 200 | Consulta u operación exitosa |
| 201 | Recurso creado |
| 204 | Operación exitosa sin cuerpo |
| 400 | Parámetros o datos inválidos |
| 401 | Autenticación requerida o inválida |
| 403 | Rol sin autorización |
| 404 | Recurso o página inexistente |
| 405 | Método no permitido |
| 409 | Conflicto con las reglas de negocio |

## Índice de contratos

| Módulo | Operaciones | Documento |
|---|---|---|
| 3.1 Autenticación | Login, logout y permisos | [auth.md](auth.md) |
| 3.2 Usuarios | Registro, consulta y edición | [usuarios.md](usuarios.md) |
| 3.3 Libros y ejemplares | Administración bibliográfica | [libros_ejemplares.md](libros_ejemplares.md) |
| 3.4 Catálogo | Búsqueda y disponibilidad | [API_catalogo.md](../API_catalogo.md) |
| 3.5 Préstamos | Registro, elegibilidad y listado administrativo | [prestamos.md](prestamos.md) |
| 3.6 Devoluciones | Registro y multas por retraso | [devoluciones.md](devoluciones.md) |
| 3.7 Bloqueos | Restricciones por atrasos prolongados | [prestamos.md](prestamos.md), [mis_prestamos.md](mis_prestamos.md) |
| 3.8 Sanciones y pagos | Consulta, detalle y registro de pagos | [sanciones.md](sanciones.md) |
| 3.9 Mis préstamos | Historial y estado de cuenta del lector | [mis_prestamos.md](mis_prestamos.md) |
| 3.9 Mis sanciones | Multas y bloqueos propios | [mis_sanciones.md](mis_sanciones.md) |

## Préstamos administrativos

La ruta `/api/prestamos/` tiene dos operaciones:

- `GET`: listado administrativo con búsqueda,
  filtros por estado y paginación.
- `POST`: registro de préstamos.

Ambas requieren rol `bibliotecario`.

La consulta personal permanece separada en
`GET /api/prestamos/mios/`, exclusiva para
estudiantes y docentes.

## Mantenimiento de los contratos

Cada contrato debe documentar:

1. Ruta y método HTTP.
2. Roles autorizados.
3. Parámetros de entrada.
4. Reglas de validación.
5. Respuestas de éxito.
6. Errores HTTP.
7. Reglas de negocio aplicadas.
8. Pruebas y dependencias.

Los contratos deben actualizarse cuando cambien
las rutas, las respuestas o las restricciones del backend.

No deben incluir tokens activos, contraseñas reales
ni información personal sensible.

## Postman

Las colecciones se encuentran en
`Documentacion/Postman/`.

La colección unificada de préstamos se denomina:

`BiblioTech_Prestamos_Completo.postman_collection.json`

Incluye pruebas de consulta administrativa, registro,
elegibilidad y permisos.

No requiere un archivo adicional de entorno.
Las variables locales se incluyen en la colección.
