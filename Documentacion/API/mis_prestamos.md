# Contrato de API — Mis préstamos y estado de cuenta

## Información general

- **Módulos:** 3.9 (consulta personal de préstamos) y 3.7 (visualización de bloqueos vigentes).
- **Entregable:** 2.4 — Contratos de API.
- **Endpoint:** `GET /api/prestamos/mios/`.
- **Autenticación:** `Authorization: Bearer <token>`.
- **Roles autorizados:** `estudiante`, `docente` (`IsEstudianteODocente`).
- **Formato:** JSON; fechas `YYYY-MM-DD`.

El usuario consultado se obtiene exclusivamente del token (`request.user.usuario_id`): **no acepta `usuario_id`** ni permite consultar los préstamos de otros lectores. Es un endpoint de **solo lectura**: no crea préstamos, devoluciones, multas, bloqueos ni pagos.

## Parámetros GET

| Parámetro | Valores admitidos | Predeterminado |
|---|---|---|
| `filtro` | `todos`, `activos`, `vencidos`, `devueltos` | `todos` |
| `page` | Entero desde 1 | `1` |
| `page_size` | Entero entre 1 y 20 | `8` |

Ejemplo: `/api/prestamos/mios/?filtro=todos&page=1&page_size=8`.

`activos` comprende préstamos sin devolución registrada; `vencidos` es un subconjunto de estos. `devueltos` incluye préstamos con `fecha_devolucion`. El estado y los días restantes se calculan con la fecha local del servidor.

## Respuesta HTTP 200

Ejemplo de lector con un préstamo vencido y bloqueo vigente:

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "prestamo_id": 1,
      "libro": {
        "libro_id": 1,
        "titulo": "Libro de ejemplo",
        "isbn": "9780000000001"
      },
      "ejemplar": {
        "ejemplar_id": 1,
        "codigo_inventario": "EJ-001"
      },
      "fecha_prestamo": "2026-08-05",
      "fecha_limite": "2026-09-04",
      "fecha_devolucion": null,
      "estado": "VENCIDO",
      "dias_restantes": 0
    }
  ],
  "resumen": {
    "total": 1,
    "activos": 1,
    "vencidos": 1,
    "devueltos": 0
  },
  "estado_cuenta": {
    "limite_prestamos_activos": 5,
    "prestamos_activos": 1,
    "cupos_disponibles": 4,
    "adeudos_pendientes": false,
    "bloqueo_vigente": true,
    "bloqueos_vigentes": [
      {
        "prestamo_id": 1,
        "motivo": "Retraso en la devolución de un préstamo.",
        "fecha_inicio": "2026-10-04",
        "fecha_fin": "2026-11-02"
      }
    ],
    "puede_solicitar": false,
    "motivos": [
      {
        "codigo": "BLOQUEO_VIGENTE",
        "mensaje": "Tienes un bloqueo temporal vigente por retraso en la devolución."
      }
    ]
  }
}
```

Los IDs, fechas y datos personales son ilustrativos. `estado_cuenta` y `resumen` describen al lector completo, no únicamente los registros de la página o filtro actual.

## Definición de campos relevantes

- `estado` por préstamo: `EN_PRESTAMO` (sin devolver, en plazo), `VENCIDO` (sin devolver y después de la fecha límite), `DEVUELTO` (con fecha de devolución).
- `dias_restantes`: número de días no negativos hasta la fecha límite para préstamos sin devolver; `null` para préstamos devueltos.
- `cupos_disponibles`: `max(limite_prestamos_activos - prestamos_activos, 0)`.
- `adeudos_pendientes`: existe una sanción económica pendiente de pago.
- `bloqueo_vigente`: hay al menos un bloqueo temporal vigente, registrado o calculado por retraso.
- `bloqueos_vigentes`: arreglo **siempre presente** (vacío cuando no hay bloqueos); cada elemento contiene `prestamo_id`, `motivo`, `fecha_inicio` y `fecha_fin`.
- `motivos`: arreglo de objetos `{ "codigo": "...", "mensaje": "..." }`; posibles códigos: `LIMITE_PRESTAMOS`, `ADEUDO_PENDIENTE`, `BLOQUEO_VIGENTE`. Puede contener varios motivos si se cumplen varias restricciones.
- `puede_solicitar`: `false` si existe al menos uno de esos motivos. **No garantiza** disponibilidad de un ejemplar concreto: esa comprobación corresponde a la elegibilidad del préstamo.

## Bloqueos temporales y consultas de solo lectura (3.7)

El cálculo considera sanciones `BLOQUEO` almacenadas y préstamos todavía sin devolver que ya alcanzaron el umbral de un mes calendario (P-04). Un bloqueo dura 30 días naturales, con ambas fechas inclusivas. Por lo tanto, un bloqueo puede aparecer en `bloqueos_vigentes` **antes** de que el worker registre la sanción; este GET **nunca crea registros**.

Una multa económica pendiente no debe confundirse con un bloqueo temporal: los indicadores y motivos son independientes.

## Códigos HTTP y seguridad

| HTTP | Condición |
|---|---|
| `200` | Consulta correcta, incluso sin resultados; `results: []` si corresponde |
| `400` | `filtro`, `page`, `page_size` inválidos o parámetros no permitidos (incluido `usuario_id`) |
| `401` | Sin token Bearer válido |
| `403` | Usuario autenticado que no sea estudiante o docente |
| `404` | Página fuera del rango de paginación |
| `405` | Método distinto de GET |

## Código relacionado y pruebas

- Backend: `presentation/mis_prestamos_views.py`, `presentation/mis_prestamos_serializers.py` y `services/mis_prestamos_service.py`.
- Bloqueos: `services/bloqueos_service.py` y `presentation/prestamos_serializers.py` (`BloqueoVigenteSerializer`).
- Frontend: `frontend/src/app/features/prestamos/services/mis-prestamos.service.ts`.
- Pruebas: `backend/biblioteca/tests/` (consultas personales y bloqueos).

```bash
docker compose exec -T backend python manage.py test biblioteca.tests --verbosity 1
```
