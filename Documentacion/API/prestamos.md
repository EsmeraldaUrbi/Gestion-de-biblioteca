
# Contrato de API — Préstamos

## Información general

- Módulo: 3.5 — Préstamos.
- Documentación: 2.4 — Contratos de API.
- Backend: Django REST Framework.
- URL base: `/api/`.
- Autenticación: `Authorization: Bearer <token>`.
- Formato: JSON.
- Fechas: `YYYY-MM-DD`.
- Reglas relacionadas: RN-02, RN-03, RN-08 a RN-12, RN-18, P-01, P-02, P-04 y P-05.

Todas las operaciones administrativas requieren el rol
`bibliotecario`.

El registro y la consulta administrativa comparten la
ruta `/api/prestamos/`, utilizando métodos HTTP distintos.

La consulta no modifica registros, fechas ni sanciones.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/prestamos/` | Consultar todos los préstamos |
| POST | `/api/prestamos/` | Registrar un préstamo |
| GET | `/api/prestamos/seleccion/usuarios/` | Buscar lectores |
| GET | `/api/prestamos/elegibilidad/` | Consultar elegibilidad |

La consulta personal de estudiantes y docentes se
documenta por separado en `mis_prestamos.md`.

---

## 1. GET /api/prestamos/

### Propósito

Permite al bibliotecario consultar los préstamos
registrados de todos los estudiantes y docentes.

La consulta admite búsqueda, filtrado por estado
y paginación.

Es una operación exclusivamente de lectura.

### Autenticación

Requiere token Bearer vigente y rol `bibliotecario`.

### Parámetros

| Parámetro | Tipo | Descripción |
|---|---|---|
| `q` | Texto opcional | Busca por nombre, correo, libro, ISBN, código de ejemplar o folio exacto |
| `estado` | Texto opcional | `todos`, `en_prestamo`, `vencidos`, `devueltos` |
| `page` | Entero positivo | Número de página; predeterminado 1 |
| `page_size` | Entero de 1 a 50 | Registros por página; predeterminado 10 |

El parámetro `q` admite hasta 100 caracteres.
La búsqueda no distingue mayúsculas y minúsculas.

No se admiten parámetros desconocidos.

### Estados calculados

- `EN_PRESTAMO`: `fecha_devolucion` es nula y
  `fecha_limite` es mayor o igual que hoy.
- `VENCIDO`: `fecha_devolucion` es nula y
  `fecha_limite` es anterior a hoy.
- `DEVUELTO`: `fecha_devolucion` contiene una fecha.

Un préstamo vencido sigue siendo activo hasta que
se registre su devolución.

El estado no se guarda en una columna adicional;
se calcula al consultar.

### Ejemplo de solicitud

GET `/api/prestamos/?estado=vencidos&page=1&page_size=10`

### Ejemplo HTTP 200

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "prestamo_id": 15,
      "usuario": {
        "usuario_id": 5,
        "nombre": "Ana Pérez",
        "email": "ana@example.com",
        "rol": "estudiante"
      },
      "libro": {
        "libro_id": 3,
        "titulo": "Ingeniería de Software",
        "isbn": "9780000000456"
      },
      "ejemplar": {
        "ejemplar_id": 12,
        "codigo_inventario": "EJ-012"
      },
      "fecha_prestamo": "2026-09-01",
      "fecha_limite": "2026-10-01",
      "fecha_devolucion": null,
      "estado": "VENCIDO",
      "dias_restantes": 0
    }
  ],
  "resumen": {
    "total": 20,
    "en_prestamo": 8,
    "vencidos": 3,
    "devueltos": 9
  }
}
```

Los identificadores, fechas y cantidades son ilustrativos.

### Interpretación del resultado

- `count`: número de registros que coinciden con los filtros.
- `next`: URL de la página siguiente, o `null`.
- `previous`: URL de la página anterior, o `null`.
- `results`: préstamos de la página solicitada.
- `resumen`: conteos generales de toda la biblioteca.

El resumen no depende del filtro ni de la página.

Los registros se ordenan por fecha de préstamo
descendente y, después, por identificador descendente.

El campo `dias_restantes` es:

- Un entero positivo o cero para préstamos sin devolver.
- Cero si el préstamo ya está vencido.
- `null` cuando el préstamo fue devuelto.

### Búsqueda sin resultados

Devuelve HTTP 200 con `count: 0` y `results: []`.
El resumen general continúa mostrando las cantidades
de toda la biblioteca.

### Errores

| HTTP | Causa |
|---|---|
| 400 | Filtro, página, tamaño o parámetro desconocido |
| 401 | Usuario sin token válido |
| 403 | Estudiante o docente intenta consultar |
| 404 | Página de resultados inexistente |
| 405 | Método HTTP no permitido |

---

## 2. GET /api/prestamos/seleccion/usuarios/

Busca estudiantes y docentes por nombre o correo.

### Parámetros

| Parámetro | Regla |
|---|---|
| `q` | Obligatorio, de 1 a 100 caracteres y no vacío |
| `limite` | Opcional, entero de 1 a 20; predeterminado 10 |

### Ejemplo

GET `/api/prestamos/seleccion/usuarios/?q=Ana&limite=10`

### Respuesta HTTP 200

```json
{
  "count": 1,
  "results": [
    {
      "usuario_id": 5,
      "nombre": "Ana Pérez",
      "email": "ana@example.com",
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

Sin coincidencias devuelve `results: []`.

Los parámetros inválidos producen HTTP 400.

---

## 3. GET /api/prestamos/elegibilidad/

Evalúa las condiciones para registrar un préstamo.
No crea ni modifica préstamos ni sanciones.

### Parámetros obligatorios

- `usuario_id`: entero positivo.
- `ejemplar_id`: entero positivo.

### Ejemplo

GET `/api/prestamos/elegibilidad/?usuario_id=5&ejemplar_id=12`

### Ejemplo HTTP 200

```json
{
  "elegible": true,
  "motivos": [],
  "bloqueos_vigentes": [],
  "usuario": {
    "usuario_id": 5,
    "nombre": "Ana Pérez",
    "email": "ana@example.com",
    "direccion": null,
    "telefono": null,
    "rol": {
      "rol_id": 1,
      "nombre": "estudiante",
      "limite_prestamos_activos": 5
    }
  },
  "ejemplar": {
    "ejemplar_id": 12,
    "libro_id": 3,
    "libro": {
      "libro_id": 3,
      "titulo": "Ingeniería de Software",
      "isbn": "9780000000456"
    },
    "codigo_inventario": "EJ-012",
    "estado": "ACTIVO"
  },
  "prestamos_activos": 2,
  "limite_prestamos_activos": 5,
  "fecha_prestamo": "2026-10-27",
  "fecha_limite": "2026-11-26"
}
```

Los valores son ilustrativos.

### Reglas comprobadas

1. El usuario debe ser estudiante o docente.
2. El ejemplar debe existir y estar `ACTIVO`.
3. El ejemplar no puede tener un préstamo activo.
4. El usuario no debe haber alcanzado su límite.
5. El usuario no debe tener multas pendientes de pago.
6. El usuario no debe tener bloqueos temporales vigentes,
   incluidos los que ya corresponden por retraso.

Cuando falla alguna condición de negocio, responde
HTTP 200 con `elegible: false` y un motivo de rechazo.

Los identificadores inválidos producen 400 y los
recursos inexistentes producen 404.

`bloqueos_vigentes` puede incluir bloqueos ya registrados
o bloqueos derivados de un retraso que todavía no han
sido materializados por el worker.

---

## 4. POST /api/prestamos/

Registra un préstamo de un ejemplar físico a un
estudiante o docente.

### Solicitud

```json
{
  "usuario_id": 5,
  "ejemplar_id": 12
}
```

Ambos campos son obligatorios y deben ser enteros positivos.

No se admiten campos extra, fechas ni estados.

### Respuesta HTTP 201

```json
{
  "prestamo_id": 15,
  "usuario_id": 5,
  "usuario": {
    "usuario_id": 5,
    "nombre": "Ana Pérez",
    "email": "ana@example.com",
    "direccion": null,
    "telefono": null,
    "rol": {
      "rol_id": 1,
      "nombre": "estudiante",
      "limite_prestamos_activos": 5
    }
  },
  "ejemplar_id": 12,
  "ejemplar": {
    "ejemplar_id": 12,
    "libro_id": 3,
    "libro": {
      "libro_id": 3,
      "titulo": "Ingeniería de Software",
      "isbn": "9780000000456"
    },
    "codigo_inventario": "EJ-012",
    "estado": "ACTIVO"
  },
  "fecha_prestamo": "2026-10-27",
  "fecha_limite": "2026-11-26",
  "fecha_devolucion": null
}
```

Los identificadores y fechas son ejemplos.

### Reglas de registro

El servicio aplica bloqueos pendientes del lector
cuando corresponda y después inicia una transacción.

Dentro de la transacción bloquea las filas del usuario
y del ejemplar, vuelve a comprobar la elegibilidad
y registra el préstamo únicamente si las condiciones
continúan siendo válidas.

La fecha límite es la fecha del servidor más
30 días naturales.

Si la operación es rechazada, no crea el nuevo préstamo.

### Errores

| HTTP | Situación |
|---|---|
| 400 | Datos incompletos, inválidos o no autorizados |
| 401 | Sesión no válida |
| 403 | Rol no autorizado |
| 404 | Usuario o ejemplar inexistente |
| 409 | Conflicto de negocio |

Los errores de conflicto incluyen `codigo` y `detail`.

Los códigos de rechazo de negocio son:

- `ROL_NO_HABILITADO`
- `EJEMPLAR_NO_DISPONIBLE`
- `EJEMPLAR_OCUPADO`
- `LIMITE_PRESTAMOS`
- `ADEUDO_PENDIENTE`
- `BLOQUEO_VIGENTE`

---

## 5. Relación con otros módulos

### Catálogo

Los ejemplares con préstamo activo no se cuentan
como disponibles.

Un préstamo vencido sigue ocupando el ejemplar.

### Devoluciones (3.6)

La devolución registra `fecha_devolucion` y cierra
el préstamo. El listado administrativo refleja
automáticamente el estado `DEVUELTO`.

La devolución se realiza mediante su endpoint propio.

### Bloqueos (3.7)

Cuando un préstamo permanece sin devolver durante
un mes calendario después de su fecha límite, puede
generarse un bloqueo de 30 días naturales.

La consulta administrativa no genera bloqueos ni
modifica sanciones.

### Sanciones y pagos (3.8)

Las multas se calculan y registran desde los procesos
correspondientes de devolución y sanciones.

El listado administrativo de préstamos no permite
registrar pagos.

### Consultas personales (3.9)

Estudiantes y docentes utilizan
`GET /api/prestamos/mios/`.

No pueden consultar los préstamos de otros usuarios.

---

## 6. Implementación

### Backend

- `repositories/prestamos_repository.py`
- `repositories/prestamos_admin_repository.py`
- `services/prestamos_service.py`
- `services/prestamos_admin_service.py`
- `presentation/prestamos_serializers.py`
- `presentation/prestamos_admin_serializers.py`
- `presentation/prestamos_views.py`
- `urls.py`

### Frontend

- `features/prestamos/pages/registro-prestamo/`
- `features/prestamos/pages/historial-prestamos/`
- `features/prestamos/services/prestamos.service.ts`
- `features/prestamos/services/prestamos-admin.service.ts`

### Pruebas

- `biblioteca.tests.test_prestamos_base`
- `biblioteca.tests.test_prestamos_reglas`
- `biblioteca.tests.test_prestamos_api`
- `biblioteca.tests.test_prestamos_admin`

### Postman

Colección única:

`Documentacion/Postman/BiblioTech_Prestamos_Completo.postman_collection.json`

Incluye autenticación, listado administrativo,
filtros, errores, permisos y operaciones existentes.

## 7. Alcance de la ampliación

El listado administrativo es exclusivamente de lectura.

No incorpora renovaciones, devoluciones, generación
de multas, pagos ni cambios de estado manuales.

No requiere nuevas migraciones ni modificaciones
del modelo de datos.
