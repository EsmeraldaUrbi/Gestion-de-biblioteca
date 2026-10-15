# Contrato de API — Mis préstamos

## Alcance

Consulta personal de préstamos para estudiantes y docentes.

Permite consultar historial, fechas, estados y restricciones
de cuenta registradas.

No contempla renovaciones, devoluciones, generación de multas,
registro de pagos ni creación de bloqueos.

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

## Respuesta HTTP 200

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "prestamo_id": 15,
      "libro": {
        "libro_id": 3,
        "titulo": "Fundamentos de redes modernas",
        "isbn": "9786000000016"
      },
      "ejemplar": {
        "ejemplar_id": 12,
        "codigo_inventario": "PDEM01-01"
      },
      "fecha_prestamo": "2026-10-15",
      "fecha_limite": "2026-11-14",
      "fecha_devolucion": null,
      "estado": "EN_PRESTAMO",
      "dias_restantes": 30
    }
  ],
  "resumen": {
    "total": 1,
    "activos": 1,
    "vencidos": 0,
    "devueltos": 0
  },
  "estado_cuenta": {
    "limite_prestamos_activos": 5,
    "prestamos_activos": 1,
    "cupos_disponibles": 4,
    "adeudos_pendientes": false,
    "bloqueo_vigente": false,
    "puede_solicitar": true,
    "motivos": []
  }
}