# Sanciones y pagos — API 3.8

Base: `/api/`. Las operaciones requieren token de sesión.

## Consulta administrativa

`GET /sanciones/` — Solo `bibliotecario`.

Parámetros opcionales: `q`, `tipo` (`todos`, `ECONOMICA`, `BLOQUEO`),
`estado` (`todos`, `pendiente`, `pagada`, `vigente`, `finalizada`), `page` y
`page_size` (máximo 50).

La respuesta es paginada e incluye `results` y `resumen`:

```json
{
  "count": 1,
  "results": [{
    "sancion_id": 12,
    "tipo": "ECONOMICA",
    "monto": "25.00",
    "fecha_pago": null,
    "estado": "PENDIENTE",
    "prestamo": {
      "prestamo_id": 8,
      "usuario": { "usuario_id": 4, "nombre": "Ana Pérez" },
      "ejemplar": { "codigo_inventario": "EJ-008", "libro": { "titulo": "Algoritmos" } }
    }
  }],
  "resumen": {
    "multas_pendientes": 1,
    "monto_pendiente": "25.00",
    "bloqueos_vigentes": 0
  }
}
```

`GET /sanciones/{sancion_id}/` obtiene el detalle administrativo.

## Registrar pago

`POST /sanciones/{sancion_id}/pago/` — Solo `bibliotecario`.

El cuerpo debe ser `{}`: el pago siempre liquida el importe completo y la fecha
se toma del servidor. Solo se admite una sanción `ECONOMICA` pendiente.

- `200`: devuelve la sanción con `fecha_pago` y estado `PAGADA`.
- `400 SANCION_YA_PAGADA`: evita pagos duplicados.
- `400 SANCION_PAGO_NO_PERMITIDO`: rechaza bloqueos y sanciones no cobrables.
- `404 SANCION_NO_ENCONTRADA`: el identificador no existe.

Pagar una multa no liquida otras multas ni altera bloqueos temporales.

## Consulta personal

`GET /sanciones/mias/` — Solo `estudiante` o `docente`.

La identidad siempre se obtiene del token: no acepta `usuario_id`. Devuelve las
sanciones del lector autenticado, paginadas y con un resumen de importes
pendientes, pagados y bloqueos vigentes.
