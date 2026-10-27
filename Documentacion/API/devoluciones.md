# Contrato de API — Registro de devoluciones y cálculo de multas

## Información general

- Ticket: 3.6 (3.6.1, 3.6.2, 3.6.3)
- Responsable: Kaltum Abdala Viveros Gómez (`Kaltum-Viveros`)
- Estado: Implementado e integrado con frontend; escenarios principales verificados.
- Fecha de actualización: 2026-10-15
- Corrección documental de solicitud HTTP: 2026-10-26
- Reglas de negocio: RN-05, RN-06, RN-15, RN-20, RN-03, RN-08 y RN-13 a RN-18

## Endpoints

| Método | Ruta | Descripción | Roles |
|---|---|---|---|
| POST | `/api/prestamos/{prestamo_id}/devolucion/` | Registrar devolución física y calcular multa por retraso | bibliotecario |
| GET | `/api/devoluciones/prestamos-activos/` | Consultar préstamos activos y estimar multa | bibliotecario |

## Detalle de operaciones

### POST `/api/prestamos/{prestamo_id}/devolucion/`

**Propósito:**

Registrar la fecha real de devolución de un ejemplar prestado y generar automáticamente una sanción ECONOMICA cuando exista retraso. El estado operativo del ejemplar se conserva; vuelve a estar disponible si permanece ACTIVO y ya no tiene un préstamo activo.

**Autenticación y autorización:**

- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación mediante token Bearer y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros:**

| Parámetro | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `prestamo_id` | Entero positivo | Sí | Identificador numérico único del préstamo a devolver |

**Solicitud JSON:**

No requiere datos en el cuerpo; el cliente puede enviar `{}`. La fecha real de devolución se obtiene del servidor utilizando la zona horaria configurada. **No se permite enviar `fecha_devolucion` ni otros campos.** Las pruebas automatizadas controlan las fechas directamente en el servicio, no mediante el cuerpo HTTP.

```json
{}
```

**Respuesta exitosa:**

- Código HTTP: 200 OK
- Estructura JSON (devolución a tiempo):

```json
{
  "mensaje": "Devolución registrada correctamente.",
  "prestamo_id": 15,
  "fecha_devolucion": "2026-10-15",
  "dias_retraso": 0,
  "monto_multa": "0.00",
  "sancion_generada": false,
  "ejemplar_estado": "ACTIVO"
}
```

- Estructura JSON (devolución con retraso):

```json
{
  "mensaje": "Devolución registrada con retraso. Multa generada.",
  "prestamo_id": 15,
  "fecha_devolucion": "2026-10-15",
  "dias_retraso": 5,
  "monto_multa": "25.00",
  "sancion_generada": true,
  "sancion_id": 4,
  "ejemplar_estado": "ACTIVO"
}
```

**Errores esperados:**

| HTTP | Condición |
|---|---|
| 400 | Préstamo ya devuelto (evita duplicación), campos de solicitud no permitidos o fecha de devolución incompatible con la fecha del préstamo |
| 401 | Petición anónima, cabecera `Authorization` ausente o token inválido |
| 403 | Usuario autenticado cuyo rol no es `bibliotecario` |
| 404 | No existe ningún préstamo con el `prestamo_id` indicado |

### GET `/api/devoluciones/prestamos-activos/`

**Propósito:**

Consultar préstamos activos y estimar la multa, sin modificar registros.

- Rol permitido: bibliotecario.
- Autenticación: Bearer token.
- Parámetro obligatorio: `q`, texto de 1 a 100 caracteres.
- Busca por código de inventario, nombre, correo o ID de préstamo.
- Paginación: `page` (predeterminado 1) y `page_size` (predeterminado 10, máximo 100).
- Respuesta HTTP 200: `count`, `next`, `previous` y `results`.
- Cada resultado incluye `prestamo`, `fecha_referencia`, `dias_retraso` y `monto_multa`.
- Sin coincidencias: respuesta HTTP 200 con `results: []`.
- Errores: 400 por parámetros inválidos, 401 sin autenticación, 403 sin rol bibliotecario y 404 por página inexistente.
- La estimación se recalcula al confirmar la devolución.

## Reglas de negocio

1. **Cálculo de multas (RN-15):** Se cobran $5.00 MXN por cada día transcurrido después de la `fecha_limite`. Si la devolución se realiza dentro del plazo, el monto generado es de $0.00 MXN y no se crea registro de sanción.
2. **Garantía de idempotencia:** Reintentar la devolución sobre un préstamo que ya posee `fecha_devolucion` rechaza la operación con HTTP 400 Bad Request, garantizando que no se dupliquen sanciones ni se alteren las fechas originales.
3. **Liberación del ejemplar:** La devolución cierra el préstamo registrando `fecha_devolucion`, sin modificar `Ejemplar.estado`. La disponibilidad se calcula conforme a RN-03, RN-05 y RN-13.
4. **Bloqueos:** Los bloqueos existentes no impiden registrar devoluciones ni se eliminan o reinician al devolver. Antes de cerrar el préstamo se registran los bloqueos pendientes que correspondan mediante el servicio existente.

## Pruebas

- Archivo: `backend/biblioteca/tests/test_devoluciones.py`
- Comando:

```bash
docker compose -p gestion-de-biblioteca exec backend python manage.py test biblioteca.tests.test_devoluciones --verbosity 2
```

- Resultado verificado en el módulo: 17 pruebas correctas en MySQL, con las migraciones hasta `biblioteca.0008` aplicadas en la base de pruebas.

Se verificó:

- Devolución en fecha límite sin multa.
- Cinco días naturales de retraso generan $25.00 MXN.
- Repetir una devolución conserva la fecha y no duplica sanciones.
- Dos devoluciones simultáneas registran una sola devolución y multa.
- Si falla la creación de la multa, se revierte la devolución.
- Rechazo de fechas anteriores al préstamo o futuras.
- Restricciones de acceso para estudiantes.
- Búsqueda de préstamos activos y estimación sin modificar registros.
- Exclusión de préstamos devueltos en la búsqueda.
- Conservación de bloqueos existentes y registro de bloqueos pendientes.

### Integración manual con Angular

- Búsqueda y selección de un préstamo activo: verificada.
- Visualización de fechas, retraso e importe estimado: verificada.
- Devolución sin multa y resumen de confirmación: verificados.
- Exclusión del préstamo devuelto al repetir la búsqueda: verificada.
- Rechazo de devolución repetida mediante Postman: verificado.
- Devolución con cinco días de retraso y multa de $25.00: confirmada por la responsable durante la prueba manual; sin captura del resumen final.

### Compilación del frontend

Comando:

```bash
docker compose -p gestion-de-biblioteca exec frontend npm run build
```

Resultado: compilación de producción correcta. Se mantiene una advertencia de tamaño de CSS en `registro-prestamo`, sin impedir la compilación.

### Alcance de la verificación

La prueba concurrente cubre dos operaciones del servicio de devoluciones con conexiones independientes a MySQL. No equivale a una prueba de carga ni a una prueba simultánea entre devoluciones, nuevos préstamos y el worker.

## Dependencias y pendientes

NA
