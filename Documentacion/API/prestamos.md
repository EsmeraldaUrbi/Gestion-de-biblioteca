# Contrato de API — Registro de préstamos y elegibilidad

## Información general

- **Módulos:** 3.5 (registro de préstamos), 3.7 (bloqueo temporal por retraso).
- **Entregable:** 2.4 — Contratos de API.
- **Backend:** Django REST Framework; **URL base:** `/api/`.
- **Autenticación:** `Authorization: Bearer <token>`.
- **Rol autorizado para las tres operaciones:** `bibliotecario`.
- **Formato:** JSON; fechas `YYYY-MM-DD`.
- **Reglas relacionadas:** RN-02, RN-03, RN-08 a RN-12, RN-18, P-01, P-02, P-04 y P-05.

No modifica el catálogo ni las devoluciones. La evaluación GET es informativa; la creación POST vuelve a validar las condiciones.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/prestamos/seleccion/usuarios/` | Buscar estudiantes y docentes por nombre o correo |
| GET | `/api/prestamos/elegibilidad/` | Validar lector y ejemplar sin registrar un préstamo |
| POST | `/api/prestamos/` | Registrar un préstamo si todas las condiciones se cumplen |

## 1. GET `/api/prestamos/seleccion/usuarios/`

Ejemplo: `/api/prestamos/seleccion/usuarios/?q=Ana&limite=10`.

| Parámetro | Tipo | Regla |
|---|---|---|
| `q` | Texto, obligatorio | No vacío; entre 1 y 100 caracteres, después de recortar espacios |
| `limite` | Entero, opcional | Entre 1 y 20; predeterminado `10` |

Busca por nombre o correo (sin distinguir mayúsculas/minúsculas); únicamente incluye `estudiante` y `docente`.

**HTTP 200:**

```json
{
  "count": 1,
  "results": [
    {
      "usuario_id": 5,
      "nombre": "Lector de ejemplo",
      "email": "lector@example.com",
      "direccion": null,
      "telefono": null,
      "rol": {
        "rol_id": 1,
        "nombre": "estudiante",
        "limite_prestamos_activos": 5
      }
    }
  ]
}
```

Sin coincidencias: `{"count":0,"results":[]}`. Errores de parámetros: `400`.

## 2. GET `/api/prestamos/elegibilidad/`

Ejemplo: `/api/prestamos/elegibilidad/?usuario_id=5&ejemplar_id=2`.

| Parámetro | Tipo | Regla |
|---|---|---|
| `usuario_id` | Entero | Obligatorio, mayor que cero |
| `ejemplar_id` | Entero | Obligatorio, mayor que cero |

La respuesta es de **solo lectura**: no crea préstamos ni sanciones. Comprueba el rol, el estado operativo del ejemplar, si ya tiene un préstamo activo, el cupo del lector, multas pendientes y bloqueos vigentes. Las fechas de un préstamo potencial se calculan en el servidor para 30 días naturales.

**HTTP 200, ejemplo de préstamo rechazado por bloqueo:**

```json
{
  "elegible": false,
  "motivos": [
    {
      "codigo": "BLOQUEO_VIGENTE",
      "mensaje": "El usuario tiene un bloqueo temporal vigente."
    }
  ],
  "bloqueos_vigentes": [
    {
      "prestamo_id": 1,
      "motivo": "Retraso en la devolución de un préstamo.",
      "fecha_inicio": "2026-10-04",
      "fecha_fin": "2026-11-02"
    }
  ],
  "usuario": {
    "usuario_id": 5,
    "nombre": "Lector de ejemplo",
    "email": "lector@example.com",
    "direccion": null,
    "telefono": null,
    "rol": {
      "rol_id": 1,
      "nombre": "estudiante",
      "limite_prestamos_activos": 5
    }
  },
  "ejemplar": {
    "ejemplar_id": 2,
    "libro_id": 1,
    "libro": {
      "libro_id": 1,
      "titulo": "Libro de ejemplo",
      "isbn": "9780000000001"
    },
    "codigo_inventario": "EJ-002",
    "estado": "ACTIVO"
  },
  "prestamos_activos": 1,
  "limite_prestamos_activos": 5,
  "fecha_prestamo": "2026-10-19",
  "fecha_limite": "2026-11-18"
}
```

Todos los valores son ilustrativos; las fechas del bloqueo corresponden al préstamo que lo originó. Una solicitud elegible tiene `elegible: true`, `motivos: []` y `bloqueos_vigentes: []` cuando no existen bloqueos vigentes. La respuesta incluye **como máximo un motivo principal de rechazo**, según el orden de validación, pero puede incluir el listado de bloqueos aunque el motivo principal sea otro (por ejemplo, ejemplar ocupado).

`bloqueos_vigentes` muestra tanto sanciones `BLOQUEO` existentes como restricciones que ya corresponden por retraso pero todavía no han sido registradas por el worker. Por ello, **una lista no vacía no implica necesariamente que ya exista una fila en `Sancion`**.

**Errores:** `400` si los parámetros son inválidos o hay campos desconocidos; `404` si el usuario o ejemplar no existe; `401` sin token válido y `403` sin permiso de bibliotecario.

## 3. POST `/api/prestamos/`

**Solicitud JSON:**

```json
{
  "usuario_id": 5,
  "ejemplar_id": 2
}
```

Ambos campos son enteros positivos obligatorios. No se admiten campos extra, fechas, estados ni datos de multa: los calcula el servidor.

**HTTP 201 Created (ejemplo abreviado con estructura real):**

```json
{
  "prestamo_id": 15,
  "usuario_id": 5,
  "usuario": {
    "usuario_id": 5,
    "nombre": "Lector de ejemplo",
    "email": "lector@example.com",
    "direccion": null,
    "telefono": null,
    "rol": {
      "rol_id": 1,
      "nombre": "estudiante",
      "limite_prestamos_activos": 5
    }
  },
  "ejemplar_id": 2,
  "ejemplar": {
    "ejemplar_id": 2,
    "libro_id": 1,
    "libro": {
      "libro_id": 1,
      "titulo": "Libro de ejemplo",
      "isbn": "9780000000001"
    },
    "codigo_inventario": "EJ-002",
    "estado": "ACTIVO"
  },
  "fecha_prestamo": "2026-10-19",
  "fecha_limite": "2026-11-18",
  "fecha_devolucion": null
}
```

El registro es transaccional: se bloquean las filas del usuario y del ejemplar, se repiten las comprobaciones y solamente entonces se guarda el préstamo. Si alguna condición falla, **no se crea el nuevo préstamo**. Antes de iniciar esa transacción el servicio puede registrar bloqueos automáticos que ya correspondan al usuario; esas sanciones no se revierten si el préstamo nuevo es rechazado.

**HTTP 409 Conflict, ejemplo:**

```json
{
  "codigo": "BLOQUEO_VIGENTE",
  "detail": "El usuario tiene un bloqueo temporal vigente."
}
```

Los rechazos de negocio usan `{ "codigo": "...", "detail": "..." }`.

## Códigos HTTP y restricciones

| HTTP | Casos principales |
|---|---|
| `200` | Consulta GET válida, incluso si el lector no es elegible |
| `201` | Préstamo creado |
| `400` | Identificadores inválidos, campos faltantes o desconocidos |
| `401` | Sin sesión Bearer válida |
| `403` | Sesión válida de rol distinto a `bibliotecario` |
| `404` | Lector o ejemplar no encontrado |
| `409` | `ROL_NO_HABILITADO`, `EJEMPLAR_NO_DISPONIBLE`, `EJEMPLAR_OCUPADO`, `LIMITE_PRESTAMOS`, `ADEUDO_PENDIENTE`, `BLOQUEO_VIGENTE` en el registro POST |
| `405` | Método HTTP no permitido por la vista |

La elegibilidad GET devuelve `200` con `elegible: false` en conflictos de negocio; **no utiliza `409` para esos casos**. Los errores conocidos de recurso inexistente sí producen `404`.

## Reglas de bloqueos (3.7)

- P-04: si el préstamo sigue sin devolver al cumplirse **un mes calendario** desde `fecha_limite`, se aplica un bloqueo de 30 días naturales, con inicio y fin **inclusivos**.
- RN-18: una sanción `BLOQUEO` tiene fechas de inicio y fin y `monto` y `fecha_pago` nulos.
- La consulta GET no registra sanciones; el worker realiza revisiones automáticas y el POST de préstamos aplica bloqueos pendientes antes de intentar registrar un préstamo.
- Repetir la revisión o el intento POST no debe duplicar la sanción ni reiniciar el intervalo.

## Código relacionado, integración y pruebas

- Rutas: `backend/biblioteca/urls.py`.
- Vistas y serializers: `presentation/prestamos_views.py` y `presentation/prestamos_serializers.py`.
- Reglas: `services/prestamos_service.py` y `services/bloqueos_service.py`.
- Frontend: `frontend/src/app/features/prestamos/services/prestamos.service.ts`.
- Pruebas: `backend/biblioteca/tests/` (módulos de préstamos y bloqueos).

```bash
docker compose exec -T backend python manage.py test biblioteca.tests --verbosity 1
```

**Dependencias:** usuarios con roles válidos, ejemplares registrados, disponibilidad calculada desde préstamos activos y sanciones económicas o bloqueos vigentes.
