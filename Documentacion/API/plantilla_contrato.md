# Plantilla — Contrato de API [nombre del módulo]

> **Instrucciones:** copia este archivo con el nombre del módulo (por ejemplo, `auth.md`) y sustituye los marcadores entre corchetes. No publiques rutas, parámetros, códigos ni datos que no estén implementados. Confirma la información en `backend/biblioteca/urls.py`, en las vistas y en los serializers correspondientes. Elimina las instrucciones antes de aprobar el contrato.

## Información general

- **Módulo y ticket:** [3.x / issue].
- **Responsable:** [persona o equipo].
- **Estado y fecha de actualización:** [implementado/verificado; AAAA-MM-DD].
- **URL base:** `/api/`.
- **Autenticación:** [Bearer obligatorio / endpoint público].
- **Roles autorizados:** [roles exactos].
- **Formato:** JSON; fechas `YYYY-MM-DD` y fechas-hora ISO 8601 si aplican.
- **Reglas de negocio:** [RN-XX, P-XX].

## Endpoints implementados

| Método | Ruta | Descripción | Roles |
|---|---|---|---|
| [GET/POST/PATCH/PUT] | `/api/[recurso]/` | [operación] | [rol] |

## 1. [MÉTODO] `/api/[recurso]/`

**Propósito:** [qué resuelve la operación y si modifica datos].

**Autenticación y autorización:** [cabecera / roles / permiso Django].

**Parámetros:** [ruta, query y valores predeterminados; indicar cuando no aplica].

| Nombre | Ubicación | Tipo | Obligatorio | Validación |
|---|---|---|---|---|
| `[campo]` | [path/query/body] | [tipo] | [sí/no] | [regla] |

**Solicitud:** [sin cuerpo / objeto JSON exacto].

```json
{
  "campo_de_ejemplo": "valor_ilustrativo"
}
```

**Respuesta exitosa:** HTTP `[200/201/204]` — [explicación]. Si es `204`, indicar que **no devuelve cuerpo**.

```json
{
  "campo_de_respuesta": "valor_ilustrativo"
}
```

**Errores:**

| HTTP | Condición | Ejemplo de estructura |
|---|---|---|
| `400` | [campo o formato inválido] | `{ "campo": ["Mensaje de validación."] }` |
| `401` | [sin autenticación válida] | `{ "detail": "..." }` |
| `403` | [rol no permitido] | `{ "detail": "..." }` |
| `404` | [recurso inexistente] | `{ "detail": "..." }` |
| `409` | [conflicto de negocio, solo cuando corresponda] | `{ "codigo": "...", "detail": "..." }` |

Eliminar los códigos que no apliquen; mantener los mensajes literales solo cuando coincidan con el backend. Para campos opcionales, documentar explícitamente sus valores por defecto y el comportamiento de campos desconocidos.

## Reglas de negocio y consistencia

- [Políticas aplicables, validaciones, transacciones o idempotencia].
- [Distinguir consultas GET de operaciones que modifican registros].
- [No documentar datos enviados por el cliente cuando el servidor los calcula o prohíbe; por ejemplo, la fecha real de devolución].

## Pruebas e integración

- **Backend:** `[ruta del archivo de pruebas]`.
- **Frontend:** `[servicio Angular que utiliza la ruta]`.
- **Pruebas ejecutadas:** [comandos y resultado real; no inventar verificaciones].
- **Dependencias y pendientes:** [módulos y decisiones de integración].

## Lista de revisión antes de publicar

- [ ] Todas las rutas y métodos existen en `urls.py` y la vista correspondiente.
- [ ] Parámetros y validaciones coinciden con serializers y servicios.
- [ ] Ejemplos JSON tienen sintaxis válida y campos reales.
- [ ] Respuestas HTTP y roles coinciden con el backend.
- [ ] No hay contraseñas, tokens válidos ni datos personales reales.
- [ ] El contrato está enlazado desde `Documentacion/API/README.md`.
