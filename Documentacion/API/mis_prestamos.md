# Contrato de API — Mis préstamos

## Alcance

Consulta personal de préstamos para estudiantes y docentes.

No contempla registro, modificación, devolución ni sanciones.

## Endpoint

GET `/api/prestamos/mios/`

Autenticación:
`Authorization: Bearer <token>`

Roles permitidos:
- estudiante
- docente

El usuario se identifica mediante el token autenticado.
No se acepta `usuario_id` como parámetro.

## Parámetros

| Parámetro | Valores | Predeterminado |
|---|---|---|
| filtro | todos, activos, vencidos, devueltos | todos |
| page | Entero positivo | 1 |
| page_size | Entero de 1 a 20 | 8 |

El filtro `activos` incluye los préstamos todavía
sin devolver, incluso cuando están vencidos.

## Respuesta HTTP 200

La respuesta contiene:

- count: préstamos que coinciden con el filtro.
- next: URL de la página siguiente o null.
- previous: URL de la página anterior o null.
- results: registros de la página.
- resumen: estadísticas de todos los préstamos del usuario.

Cada préstamo incluye:

- prestamo_id
- libro: identificador, título e ISBN.
- ejemplar: identificador y código de inventario.
- fecha_prestamo
- fecha_limite
- fecha_devolucion
- estado
- dias_restantes

## Estados

- EN_PRESTAMO: sin devolución y plazo no vencido.
- VENCIDO: sin devolución y fecha límite anterior a hoy.
- DEVUELTO: fecha de devolución registrada.

Los estados se calculan a partir de los modelos existentes.

`dias_restantes` es null cuando el préstamo está devuelto,
cero cuando está vencido y un entero no negativo cuando
continúa abierto.

## Seguridad

El backend obtiene el identificador del usuario desde
request.user.usuario_id.

Las consultas filtran por ese identificador.

No es posible consultar préstamos ajenos mediante
parámetros de URL.

## Respuestas

- 200: Consulta correcta.
- 400: Filtro o parámetros inválidos.
- 401: Sin autenticación.
- 403: Rol no autorizado.
- 404: Página de resultados inexistente.
- 405: Método no permitido.

## Dependencias

Utiliza los modelos Prestamo, Ejemplar y Libro existentes.
Reutiliza la autenticación y permisos del ticket 3.1.

La consulta no modifica la información almacenada.