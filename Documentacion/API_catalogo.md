# API de catálogo — issue 3.4.2

Consultas de solo lectura para estudiante, docente y bibliotecario autenticados.
Usar el token obtenido en `/api/auth/login/` con la cabecera de autenticación
establecida por el backend (`Authorization: Bearer <token>`).

## Rutas

- `GET /api/catalogo/`: listado paginado ordenado por título e ID.
- `GET /api/catalogo/<libro_id>/`: detalle bibliográfico y existencias.
- `GET /api/catalogo/filtros/`: autores y categorías para los selectores.

## Parámetros del listado

| Parámetro | Significado |
| --- | --- |
| titulo | Coincidencia parcial de título, sin distinguir mayúsculas. |
| autor | ID positivo de autor. |
| categoria | ID positivo de categoría. |
| disponible | `true`: al menos una copia disponible; `false`: ninguna. Omitir para ambos. |
| page | Página, desde 1. |
| page_size | Tamaño de página, de 1 a 100; predeterminado 10. |

Todos los filtros se combinan mediante AND. Un ID de autor o categoría inexistente
produce un listado vacío. Los parámetros inválidos producen HTTP 400.

Ejemplo: `/api/catalogo/?titulo=software&autor=1&categoria=2&disponible=true`

El listado devuelve `count`, `next`, `previous` y `results`. Cada libro incluye
`libro_id`, `titulo`, `isbn`, `fecha_publicacion`, `autores`, `categorias`,
`stock_total` y `stock_disponible`. El detalle devuelve el mismo objeto de libro.
Autores: `autor_id`, `nombre`. Categorías: `categoria_id`, `nombre_categoria`.

## Existencias (RN-03, RN-05 y RN-06)

- Total: copias cuyo estado no sea BAJA; incluye MANTENIMIENTO.
- Disponible: copias ACTIVO sin ningún préstamo con fecha_devolucion vacía.
- Un préstamo vencido sin devolver sigue activo.
- Libros sin ejemplares tienen ambas cantidades en cero.
- Las asociaciones y el historial de préstamos no multiplican las cantidades.
- Las cantidades se calculan al consultar; no autorizan ni reservan un préstamo.

HTTP 401: sin sesión válida. HTTP 403: rol no autorizado. HTTP 404: libro o
página inexistente. Las operaciones de escritura no están disponibles.

No requiere migraciones nuevas del catálogo. Antes de probar, aplicar las
migraciones de dev, incluida 0004_tokenacceso. Las pruebas están en
`biblioteca.tests.test_catalogo` y crean sus propios datos en una base de pruebas.

## Cobertura e integración (issue 3.4.3)

La integración y cálculo de disponibilidad fue validada mediante:
- Suite de pruebas en `backend/biblioteca/tests/test_catalogo.py` cubriendo:
  - Filtros individuales y combinados (título, autor, categoría, disponibilidad).
  - Verificación de que múltiples relaciones (autores y categorías) no duplican filas ni alteran stock.
  - Exclusión de copias en `MANTENIMIENTO` y `BAJA` de `stock_disponible`, e inclusión de `MANTENIMIENTO` en `stock_total`.
  - Préstamos activos (incluso vencidos) mantienen la copia como no disponible; las devoluciones restauran disponibilidad inmediatamente.
  - El historial acumulado de préstamos devueltos no multiplica las existencias.
- Pruebas de contrato y códigos HTTP en Postman (`Biblioteca_Catalogo.postman_collection.json`).

> **Nota:** La validación visual de la interfaz de usuario queda pendiente de la autorización explícita para la implementación del frontend (issue 3.4.1).

