# Contrato de API — Mis Sanciones y Bloqueos

## Información general

- **Ticket:** 3.9 — Consulta personal de préstamos y sanciones
- **Subtickets:** 3.9.2 (Backend #51) y 3.9.3 (Seguridad e Integración #52)
- **Módulo:** Circulación, préstamos y estado de cuenta del lector
- **Responsable:** Diego Alberto Nava Rivera (`inava404`)
- **Estado:** Implementado y verificado con 25 pruebas automatizadas
- **Fecha de actualización:** 2026-10-25
- **Reglas de negocio asociadas:** RN-05, RN-14, RN-18, P-04
- **URL base:** `/api/`
- **Esquema de autenticación:** Autenticación obligatoria mediante token Bearer personalizado (`BibliotecaTokenAuthentication`). Cabecera HTTP requerida:
  ```http
  Authorization: Bearer <token_acceso>
  ```
- **Roles autorizados:** Exclusivo para usuarios con rol `estudiante` o `docente` ([IsEstudianteODocente](../../backend/biblioteca/permissions.py)). El rol `bibliotecario` no tiene acceso a este endpoint personal (recibe HTTP 403).

---

## 1. Objetivo del endpoint

Permitir que estudiantes y docentes autenticados consulten de manera personal, transparente y segura el historial y estado vigente de sus sanciones en el sistema de biblioteca:
- **Multas económicas:** generadas por devoluciones con retraso, mostrando el importe adeudado, el libro/ejemplar relacionado y el estado de pago.
- **Bloqueos temporales:** generados por retrasos severos (30 días de suspensión conforme a P-04 y RN-18), mostrando el periodo de restricción (inicio y fin) y su vigencia operativa.

El endpoint es de **estricta solo lectura** y **aislado por usuario**: jamás permite consultar sanciones de terceros ni realizar pagos o modificaciones.

---

## 2. Autenticación y roles autorizados

- **Autenticación:** Obligatoria (`IsAuthenticated`). La identidad del usuario se obtiene estrictamente de la sesión asociada al token (`request.user.usuario_id`). No se permite enviar `usuario_id` en query params ni en payloads para seleccionar a qué usuario consultar.
- **Roles permitidos:**
  - `estudiante`
  - `docente`
- **Respuestas de control de acceso:**
  - Sin cabecera `Authorization` o formato inválido: `401 Unauthorized`.
  - Token inválido, expirado (`expira_en <= now()`) o revocado (`revocado_en is not None`): `401 Unauthorized`.
  - Usuario con rol `bibliotecario`: `403 Forbidden` (`{"detail": "No tienes permiso para acceder a este recurso personal."}`).

---

## 3. Ruta y método HTTP

- **Ruta:** `/api/sanciones/mias/`
- **Método permitido:** `GET`
- **Métodos rechazados:** `POST`, `PUT`, `PATCH`, `DELETE` responden `405 Method Not Allowed`.

---

## 4. Parámetros de consulta admitidos

Los parámetros son procesados y validados por [MisSancionesConsultaSerializer](../../backend/biblioteca/presentation/mis_sanciones_serializers.py), el cual rechaza de inmediato cualquier campo desconocido mediante `CamposPermitidosSerializer`.

| Parámetro | Tipo | Obligatorio | Valor por defecto | Opciones válidas | Descripción |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tipo` | String | No | `'todas'` | `todas`, `economicas`, `bloqueos` | Filtra por la naturaleza de la sanción. |
| `estado` | String | No | `'todos'` | `todos`, `pendientes`, `pagadas`, `programados`, `vigentes`, `concluidos` | Filtra por el estado operativo o de pago de la sanción. |
| `page` | Integer | No | `1` | `>= 1` | Número de página solicitada. |
| `page_size` | Integer | No | `10` | `1` a `50` | Cantidad de registros por página (máximo 50). |

---

## 5. Combinaciones válidas e inválidas de filtros

Para garantizar la coherencia semántica entre el tipo de sanción y el estado solicitado:

### Combinaciones válidas
- `tipo=todas` con `estado=todos`: todas las sanciones registradas del usuario.
- `tipo=todas` con `estado=pendientes` o `estado=pagadas`: únicamente multas en ese estado.
- `tipo=todas` con `estado=programados`, `estado=vigentes` o `estado=concluidos`: únicamente bloqueos en ese estado.
- `tipo=economicas` con `estado=todos`, `estado=pendientes` o `estado=pagadas`.
- `tipo=bloqueos` con `estado=todos`, `estado=programados`, `estado=vigentes` o `estado=concluidos`.

### Combinaciones inválidas (HTTP 400 Bad Request)
- `tipo=economicas` combinado con `estado=programados`, `estado=vigentes` o `estado=concluidos`:
  ```json
  {
    "estado": [
      "El estado solicitado no es aplicable a multas económicas."
    ]
  }
  ```
- `tipo=bloqueos` combinado con `estado=pendientes` o `estado=pagadas`:
  ```json
  {
    "estado": [
      "El estado solicitado no es aplicable a bloqueos temporales."
    ]
  }
  ```
- Parámetros no autorizados (ej. `?usuario_id=5`, `?prestamo_id=12`):
  ```json
  {
    "detail": "Los siguientes campos no están permitidos: usuario_id."
  }
  ```

---

## 6. Ejemplo de respuesta `200 OK`

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "sancion_id": 14,
      "prestamo_id": 28,
      "libro": {
        "libro_id": 5,
        "titulo": "Estructuras de Datos en Python",
        "isbn": "9780000000010"
      },
      "ejemplar": {
        "ejemplar_id": 11,
        "codigo_inventario": "EDP-01"
      },
      "tipo": "ECONOMICA",
      "estado": "PENDIENTE",
      "monto": "25.00",
      "fecha_pago": null,
      "fecha_inicio_bloqueo": null,
      "fecha_fin_bloqueo": null
    },
    {
      "sancion_id": 9,
      "prestamo_id": 19,
      "libro": {
        "libro_id": 3,
        "titulo": "Ingeniería de Software Moderna",
        "isbn": "9780000000020"
      },
      "ejemplar": {
        "ejemplar_id": 8,
        "codigo_inventario": "ISM-01"
      },
      "tipo": "BLOQUEO",
      "estado": "VIGENTE",
      "monto": null,
      "fecha_pago": null,
      "fecha_inicio_bloqueo": "2026-10-15",
      "fecha_fin_bloqueo": "2026-11-13"
    }
  ],
  "resumen": {
    "total_sanciones": 2,
    "multas_pendientes": 1,
    "monto_total_adeudado": "25.00",
    "bloqueos_vigentes": 1
  }
}
```

---

## 7. Descripción detallada de campos

### Elementos del arreglo `results`:
- `sancion_id` (Integer): Identificador primario de la sanción en la tabla `biblioteca_sancion`.
- `prestamo_id` (Integer): Identificador del préstamo que originó la sanción.
- `libro` (Object | null): Ficha resumida del libro asociado al ejemplar prestado:
  - `libro_id` (Integer): Clave primaria del libro.
  - `titulo` (String): Título oficial de la obra.
  - `isbn` (String): Código ISBN normalizado.
- `ejemplar` (Object | null): Ficha del ejemplar físico prestado:
  - `ejemplar_id` (Integer): Clave primaria del ejemplar.
  - `codigo_inventario` (String): Código de barras / inventario del ejemplar.
- `tipo` (String): Tipo de sanción registrado en base de datos (`'ECONOMICA'` o `'BLOQUEO'`).
- `estado` (String): Estado operativo dinámico calculado según la fecha local actual (`'PENDIENTE'`, `'PAGADA'`, `'PROGRAMADO'`, `'VIGENTE'`, `'CONCLUIDO'`).
- `monto` (String | null): Cadena decimal con 2 decimales para multas (ej. `"25.00"`). Para bloqueos es siempre `null`.
- `fecha_pago` (String | null): Fecha en que se liquidó la multa (`"YYYY-MM-DD"`) o `null` si permanece pendiente.
- `fecha_inicio_bloqueo` (String | null): Fecha de inicio del periodo de suspensión (`"YYYY-MM-DD"`). Para multas es `null`.
- `fecha_fin_bloqueo` (String | null): Fecha de término del periodo de suspensión (`"YYYY-MM-DD"`). Para multas es `null`.

### Objeto `resumen`:
- `total_sanciones` (Integer): Total acumulado histórico de sanciones del usuario autenticado.
- `multas_pendientes` (Integer): Cantidad de multas económicas del usuario que no han sido pagadas (`fecha_pago is null`).
- `monto_total_adeudado` (String): Suma total de los montos adeudados pendientes de pago (`"0.00"` si no hay adeudo).
- `bloqueos_vigentes` (Integer): Cantidad de bloqueos temporales que se encuentran activos hoy (`inicio <= hoy <= fin`).

---

## 8. Reglas de cálculo de estados

El estado se calcula dinámicamente en cada petición a partir de la fecha local del servidor (`timezone.localdate()`):

### Sanciones económicas (`tipo == 'ECONOMICA'`)
- **`PENDIENTE`**: `fecha_pago is None`. El usuario mantiene un adeudo económico activo.
- **`PAGADA`**: `fecha_pago is not None`. La multa ya fue liquidada en ventanilla.

### Bloqueos temporales (`tipo == 'BLOQUEO'`)
- **`PROGRAMADO`**: `fecha_inicio_bloqueo > hoy`. El periodo de restricción comenzará en una fecha futura.
- **`VIGENTE`**: `fecha_inicio_bloqueo <= hoy <= fecha_fin_bloqueo`. El usuario está actualmente suspendido de solicitar préstamos.
- **`CONCLUIDO`**: `fecha_fin_bloqueo < hoy`. El periodo de 30 días de suspensión ya expiró.

---

## 9. Significado del resumen global

El objeto `resumen` incluido en la respuesta posee una propiedad fundamental de diseño:
> **El resumen se calcula siempre sobre la totalidad de sanciones del usuario autenticado, de forma estrictamente independiente de los filtros (`tipo`, `estado`) y de la página solicitada (`page`, `page_size`).**

Esto asegura que:
1. Si el lector filtra solo por `tipo=bloqueos`, el resumen le seguirá recordando si tiene multas pendientes de pago y el importe total que adeuda.
2. Si el lector navega a la página 2 de sus sanciones, los totales globales no se reducen ni se distorsionan.
3. El resumen contabiliza **exclusivamente** registros del usuario autenticado; jamás incluye multas ni bloqueos de otros lectores.

---

## 10. Códigos de estado HTTP

| Código | Condición | Estructura devuelta |
| :--- | :--- | :--- |
| `200 OK` | Consulta exitosa (incluso si no hay registros, devuelve lista vacía). | Objeto paginado con `count`, `results` y `resumen`. |
| `400 Bad Request` | Parámetros inválidos, páginas <= 0, tamaños > 50, combinaciones incompatibles o intento de enviar parámetros no autorizados (`usuario_id`). | `{"estado": [...]}` o `{"page": [...]}` o `{"detail": "..."}`. |
| `401 Unauthorized` | Petición sin token Bearer, formato de cabecera inválido, token expirado o token revocado. | `{"detail": "Las credenciales de autenticación no se proveyeron o son inválidas."}`. |
| `403 Forbidden` | Usuario autenticado con rol distinto a `estudiante` o `docente` (por ejemplo rol `bibliotecario`). | `{"detail": "No tienes permiso para acceder a este recurso personal."}`. |
| `404 Not Found` | Página fuera de rango (ej. solicitar `page=99` cuando solo hay 1 página). | `{"detail": "Página no válida."}`. |
| `405 Method Not Allowed` | Peticiones con método distinto a `GET` (`POST`, `PUT`, `PATCH`, `DELETE`). | `{"detail": "Method \"POST\" not allowed."}`. |

---

## 11. Garantías de aislamiento de datos

1. **Aislamiento a nivel de repositorio:** Todas las consultas SQL generadas por Django ORM incluyen forzosamente:
   ```sql
   WHERE biblioteca_prestamo.usuario_id = %s
   ```
   donde el valor inyectado proviene de `request.user.usuario_id`.
2. **Imposibilidad de suplantación:** El backend rechaza activamente parámetros como `?usuario_id=12` o `?prestamo__usuario_id=12` mediante [CamposPermitidosSerializer](../../backend/biblioteca/presentation/usuarios_serializers.py).
3. **Aislamiento horizontal y vertical:**
   - Un estudiante no puede ver las sanciones de otro estudiante.
   - Un estudiante no puede ver las sanciones de un docente.
   - Un docente no puede ver las sanciones de otro docente.
   - Los bibliotecarios deben utilizar sus herramientas administrativas específicas de circulación (Tickets 3.5, 3.6 y 3.7), no este endpoint personal.

---

## 12. Ejemplos de peticiones

### Consultar todas las sanciones personales
```http
GET /api/sanciones/mias/ HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token_estudiante>
```

### Consultar únicamente multas pendientes
```http
GET /api/sanciones/mias/?tipo=economicas&estado=pendientes HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token_estudiante>
```

### Consultar únicamente bloqueos vigentes con paginación
```http
GET /api/sanciones/mias/?tipo=bloqueos&estado=vigentes&page=1&page_size=5 HTTP/1.1
Host: localhost:8000
Authorization: Bearer <token_docente>
```

---

## 13. Limitaciones y operaciones no permitidas

- Este endpoint **no realiza cobros ni registros de pago**.
- Este endpoint **no levanta bloqueos ni modifica fechas**.
- Este endpoint **no crea sanciones**. Las sanciones se generan exclusivamente mediante la devolución física en ventanilla (Ticket 3.6) o mediante el comando de bloqueos automáticos por retraso severo (Ticket 3.7).
- La invocación repetida mediante `GET` es 100% idempotente y no genera escrituras en la base de datos.
