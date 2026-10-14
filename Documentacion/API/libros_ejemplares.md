# Contrato de API — Gestión de libros y ejemplares

## Información general

- **Ticket:** 3.3.2 — Issue #27
- **Módulo:** Gestión de libros y ejemplares
- **Responsable:** `inava404`
- **Estado:** Verificado
- **Fecha de actualización:** 2026-10-13
- **Reglas de negocio asociadas:** RN-01, RN-02, RN-03, RN-04, RN-19, RN-20
- **URL base:** `/api/`
- **Esquema de autenticación:** Autenticación obligatoria mediante token Bearer personalizado (`BibliotecaTokenAuthentication`). El cliente debe enviar la cabecera:
  ```http
  Authorization: Bearer bt_sample_token_xyz123
  ```
  No se utiliza autenticación por sesiones web ni cookies para estas operaciones.
- **Rol autorizado:** Exclusivo para usuarios con rol `bibliotecario` ([IsBibliotecario](../../backend/biblioteca/permissions.py))

---

## Endpoints

| Método | Ruta | Descripción | Roles autorizados |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/libros/` | Listado administrativo de libros con filtros y paginación | `bibliotecario` |
| `POST` | `/api/libros/` | Registro de un nuevo libro bibliográfico y sus asociaciones | `bibliotecario` |
| `GET` | `/api/libros/{libro_id}/` | Consulta de detalle bibliográfico por identificador | `bibliotecario` |
| `PATCH` | `/api/libros/{libro_id}/` | Modificación parcial de libro (conserva asociaciones omitidas) | `bibliotecario` |
| `PUT` | `/api/libros/{libro_id}/` | Actualización completa de libro y sincronización de asociaciones | `bibliotecario` |
| `GET` | `/api/ejemplares/` | Listado administrativo de ejemplares físicos con filtros y paginación | `bibliotecario` |
| `POST` | `/api/ejemplares/` | Registro de un nuevo ejemplar físico asociado a un libro | `bibliotecario` |
| `GET` | `/api/ejemplares/{ejemplar_id}/` | Consulta individual de un ejemplar por identificador | `bibliotecario` |
| `PATCH` | `/api/ejemplares/{ejemplar_id}/` | Modificación exclusiva del estado operativo del ejemplar | `bibliotecario` |

---

## Detalle de operaciones

### 1. GET `/api/libros/`

**Propósito:**  
Permite al personal bibliotecario consultar el catálogo de libros con paginación y filtros opcionales de búsqueda.

**Autenticación y autorización:**  
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de consulta (Query Parameters):**

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| `titulo` | String | No | Ninguno | Coincidencia parcial insensible a mayúsculas/minúsculas |
| `isbn` | String | No | Ninguno | Coincidencia parcial en el código ISBN |
| `autor_id` | Integer | No | Ninguno | Identificador entero del autor asociado |
| `categoria_id` | Integer | No | Ninguno | Identificador entero de la categoría asociada |
| `page` | Integer | No | `1` | Número de página solicitada (inicia en 1) |
| `page_size` | Integer | No | `10` | Registros por página (máximo `100`) |

**Solicitud JSON:**  
No requiere cuerpo de solicitud.

**Respuesta exitosa:**  
- **Código HTTP:** 200 OK
- **Estructura JSON:**

```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "libro_id": 1,
      "titulo": "Cien Años de Soledad",
      "isbn": "9780307474728",
      "fecha_publicacion": "1967-05-30",
      "autores": [
        {
          "autor_id": 1,
          "nombre": "Gabriel García Márquez"
        }
      ],
      "categorias": [
        {
          "categoria_id": 1,
          "nombre_categoria": "Realismo Mágico"
        }
      ]
    }
  ]
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 401 | Petición anónima, cabecera `Authorization` ausente o token inválido/expirado |
| 403 | Usuario autenticado cuyo rol no es `bibliotecario` (ej. estudiante o docente) |

---

### 2. POST `/api/libros/`

**Propósito:**  
Registra un nuevo título bibliográfico en el sistema junto con sus autores y categorías correspondientes.

**Autenticación y autorización:**  
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:** Ninguno.

**Solicitud JSON:**

```json
{
  "titulo": "Don Quijote de la Mancha",
  "isbn": "9788424116286",
  "fecha_publicacion": "1605-01-16",
  "autor_ids": [1],
  "categoria_ids": [2]
}
```

*Detalles de validación de campos:*
- `titulo`: String no vacío, máximo 100 caracteres. Obligatorio.
- `isbn`: String no vacío, máximo 13 caracteres. Obligatorio y único (**RN-01**).
- `fecha_publicacion`: String en formato `YYYY-MM-DD` o `null`. Opcional.
- `autor_ids`: Lista de enteros (`Integer`). Opcional (si se omite, se registra sin autores).
- `categoria_ids`: Lista de enteros (`Integer`). Opcional (si se omite, se registra sin categorías).

**Respuesta exitosa:**  
- **Código HTTP:** 201 Created
- **Estructura JSON:**

```json
{
  "libro_id": 2,
  "titulo": "Don Quijote de la Mancha",
  "isbn": "9788424116286",
  "fecha_publicacion": "1605-01-16",
  "autores": [
    {
      "autor_id": 1,
      "nombre": "Miguel de Cervantes"
    }
  ],
  "categorias": [
    {
      "categoria_id": 2,
      "nombre_categoria": "Novela Clásica"
    }
  ]
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 400 | ISBN duplicado con otro libro registrado en el catálogo (`RN-01`) |
| 400 | Uno o más identificadores en `autor_ids` no existen en la base de datos |
| 400 | Uno o más identificadores en `categoria_ids` no existen en la base de datos |
| 400 | Título o ISBN vacíos, compuestos de solo espacios en blanco o longitud excedida |
| 400 | Presencia de campos desconocidos no permitidos en el cuerpo JSON |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |

---

### 3. GET `/api/libros/{libro_id}/`

**Propósito:**  
Obtiene los datos bibliográficos completos de un libro por su identificador primario.

**Autenticación y autorización:**  
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `libro_id` | Integer | Sí | Identificador numérico entero del libro |

**Solicitud JSON:**  
No requiere cuerpo de solicitud.

**Respuesta exitosa:**  
- **Código HTTP:** 200 OK
- **Estructura JSON:**

```json
{
  "libro_id": 2,
  "titulo": "Don Quijote de la Mancha",
  "isbn": "9788424116286",
  "fecha_publicacion": "1605-01-16",
  "autores": [
    {
      "autor_id": 1,
      "nombre": "Miguel de Cervantes"
    }
  ],
  "categorias": [
    {
      "categoria_id": 2,
      "nombre_categoria": "Novela Clásica"
    }
  ]
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |
| 404 | No existe ningún libro con el `libro_id` indicado |

---

### 4. PATCH `/api/libros/{libro_id}/`

**Propósito:**  
Actualización parcial de la información de un libro.  
**Comportamiento con asociaciones omitidas:** Si en la solicitud se omite `autor_ids` o `categoria_ids`, las relaciones previamente asignadas al libro **se conservan intactas**. Solo se modifican o reemplazan si dichos campos se envían explícitamente en el cuerpo JSON.

**Autenticación y autorización:**  
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `libro_id` | Integer | Sí | Identificador numérico entero del libro |

**Ejemplo 1 — Modificación de título conservando asociaciones:**

*Solicitud JSON:*
```json
{
  "titulo": "Don Quijote de la Mancha (Edición Centenario)"
}
```

*Respuesta exitosa (HTTP 200 OK):*
```json
{
  "libro_id": 2,
  "titulo": "Don Quijote de la Mancha (Edición Centenario)",
  "isbn": "9788424116286",
  "fecha_publicacion": "1605-01-16",
  "autores": [
    {
      "autor_id": 1,
      "nombre": "Miguel de Cervantes"
    }
  ],
  "categorias": [
    {
      "categoria_id": 2,
      "nombre_categoria": "Novela Clásica"
    }
  ]
}
```

**Ejemplo 2 — Reemplazo explícito de autores:**

*Solicitud JSON:*
```json
{
  "autor_ids": [2]
}
```

*Respuesta exitosa (HTTP 200 OK):*
```json
{
  "libro_id": 2,
  "titulo": "Don Quijote de la Mancha (Edición Centenario)",
  "isbn": "9788424116286",
  "fecha_publicacion": "1605-01-16",
  "autores": [
    {
      "autor_id": 2,
      "nombre": "Francisco de Quevedo"
    }
  ],
  "categorias": [
    {
      "categoria_id": 2,
      "nombre_categoria": "Novela Clásica"
    }
  ]
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 400 | El nuevo ISBN entra en colisión con otro libro registrado |
| 400 | Identificadores inexistentes en `autor_ids` o `categoria_ids` |
| 400 | Envío de campos no permitidos en el cuerpo JSON |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |
| 404 | Libro inexistente con el `libro_id` indicado |

---

### 5. PUT `/api/libros/{libro_id}/`

**Propósito:**  
Actualización completa de un registro bibliográfico. Exige proporcionar los campos base obligatorios (`titulo`, `isbn`).  
**Diferencia con PATCH:** A diferencia de PATCH, en una actualización completa PUT la omisión de `autor_ids` o `categoria_ids` se interpreta como una sustitución por una lista vacía, eliminando las relaciones que tuviera el libro.

**Autenticación y autorización:**  
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `libro_id` | Integer | Sí | Identificador numérico entero del libro |

**Solicitud JSON:**

```json
{
  "titulo": "Cien Años de Soledad (Edición Conmemorativa)",
  "isbn": "9780307474728",
  "fecha_publicacion": "2007-03-01",
  "autor_ids": [1],
  "categoria_ids": [1, 2]
}
```

**Respuesta exitosa:**  
- **Código HTTP:** 200 OK
- **Estructura JSON:**

```json
{
  "libro_id": 1,
  "titulo": "Cien Años de Soledad (Edición Conmemorativa)",
  "isbn": "9780307474728",
  "fecha_publicacion": "2007-03-01",
  "autores": [
    {
      "autor_id": 1,
      "nombre": "Gabriel García Márquez"
    }
  ],
  "categorias": [
    {
      "categoria_id": 1,
      "nombre_categoria": "Realismo Mágico"
    },
    {
      "categoria_id": 2,
      "nombre_categoria": "Novela Latinoamericana"
    }
  ]
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 400 | Campos requeridos faltantes (`titulo` o `isbn`) |
| 400 | Conflicto por ISBN duplicado |
| 400 | Identificadores de autores o categorías inexistentes |
| 400 | Presencia de campos desconocidos |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |
| 404 | Libro inexistente con el `libro_id` indicado |

---

### 6. GET `/api/ejemplares/`

**Propósito:**  
Listado paginado de ejemplares físicos para administración interna, con filtros por libro, estado y código de inventario.

**Autenticación y autorización:**  
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de consulta (Query Parameters):**

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| `libro_id` | Integer | No | Ninguno | Filtra las copias asociadas a un libro específico |
| `estado` | String | No | Ninguno | Filtra por estado operativo (`ACTIVO`, `MANTENIMIENTO`, `BAJA`) |
| `codigo_inventario` | String | No | Ninguno | Búsqueda por coincidencia en el código de inventario |
| `page` | Integer | No | `1` | Número de página solicitada |
| `page_size` | Integer | No | `10` | Cantidad de registros por página (máximo `100`) |

**Solicitud JSON:**  
No requiere cuerpo de solicitud.

**Respuesta exitosa:**  
- **Código HTTP:** 200 OK
- **Estructura JSON:**

```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "ejemplar_id": 1,
      "libro_id": 1,
      "libro": {
        "libro_id": 1,
        "titulo": "Cien Años de Soledad",
        "isbn": "9780307474728"
      },
      "codigo_inventario": "CAS-001",
      "estado": "ACTIVO"
    },
    {
      "ejemplar_id": 2,
      "libro_id": 1,
      "libro": {
        "libro_id": 1,
        "titulo": "Cien Años de Soledad",
        "isbn": "9780307474728"
      },
      "codigo_inventario": "CAS-002",
      "estado": "MANTENIMIENTO"
    }
  ]
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |

---

### 7. POST `/api/ejemplares/`

**Propósito:**  
Registra un nuevo ejemplar físico asociado a un libro existente en el catálogo.

**Autenticación y autorización:**  
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:** Ninguno.

**Solicitud JSON:**

```json
{
  "libro_id": 1,
  "codigo_inventario": "CAS-003"
}
```

*Detalles de validación:*
- `libro_id`: Entero (`Integer`) positivo correspondiente a un libro registrado. Obligatorio.
- `codigo_inventario`: String no vacío, máximo 15 caracteres. Obligatorio y único (**RN-02**).
- `estado`: String en `["ACTIVO", "MANTENIMIENTO", "BAJA"]`. Opcional. **Si se omite, se asigna automáticamente `ACTIVO` como estado predeterminado (RN-03).**

**Respuesta exitosa:**  
- **Código HTTP:** 201 Created
- **Estructura JSON:**

```json
{
  "ejemplar_id": 3,
  "libro_id": 1,
  "libro": {
    "libro_id": 1,
    "titulo": "Cien Años de Soledad",
    "isbn": "9780307474728"
  },
  "codigo_inventario": "CAS-003",
  "estado": "ACTIVO"
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 400 | El `codigo_inventario` ya se encuentra registrado en otro ejemplar (`RN-02`) |
| 400 | No existe un libro registrado con el `libro_id` indicado |
| 400 | El `codigo_inventario` está vacío, contiene solo espacios o supera los 15 caracteres |
| 400 | El valor de `estado` no pertenece a `ACTIVO`, `MANTENIMIENTO` ni `BAJA` (`RN-03`) |
| 400 | Presencia de campos desconocidos no permitidos |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |

---

### 8. GET `/api/ejemplares/{ejemplar_id}/`

**Propósito:**  
Consulta la información detallada de una copia física específica mediante su identificador numérico.

**Autenticación y autorización:**  
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `ejemplar_id` | Integer | Sí | Identificador numérico entero del ejemplar |

**Solicitud JSON:**  
No requiere cuerpo de solicitud.

**Respuesta exitosa:**  
- **Código HTTP:** 200 OK
- **Estructura JSON:**

```json
{
  "ejemplar_id": 1,
  "libro_id": 1,
  "libro": {
    "libro_id": 1,
    "titulo": "Cien Años de Soledad",
    "isbn": "9780307474728"
  },
  "codigo_inventario": "CAS-001",
  "estado": "ACTIVO"
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |
| 404 | No existe ningún ejemplar registrado con el `ejemplar_id` indicado |

---

### 9. PATCH `/api/ejemplares/{ejemplar_id}/`

**Propósito:**  
Modificación del estado operativo de un ejemplar físico (`ACTIVO`, `MANTENIMIENTO`, `BAJA`).  
**Restricción estricta de campos:** Este endpoint acepta **únicamente** el campo `estado`. Cualquier intento de alterar `codigo_inventario` o `libro_id` es rechazado con error de validación para evitar sustituciones arbitrarias de copias.

**Autenticación y autorización:**  
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `ejemplar_id` | Integer | Sí | Identificador numérico entero del ejemplar |

**Ejemplo 1 — Cambio de estado a MANTENIMIENTO:**

*Solicitud JSON:*
```json
{
  "estado": "MANTENIMIENTO"
}
```

*Respuesta exitosa (HTTP 200 OK):*
```json
{
  "ejemplar_id": 1,
  "libro_id": 1,
  "libro": {
    "libro_id": 1,
    "titulo": "Cien Años de Soledad",
    "isbn": "9780307474728"
  },
  "codigo_inventario": "CAS-001",
  "estado": "MANTENIMIENTO"
}
```

**Ejemplo 2 — Baja lógica de ejemplar:**

*Solicitud JSON:*
```json
{
  "estado": "BAJA"
}
```

*Respuesta exitosa (HTTP 200 OK):*
```json
{
  "ejemplar_id": 1,
  "libro_id": 1,
  "libro": {
    "libro_id": 1,
    "titulo": "Cien Años de Soledad",
    "isbn": "9780307474728"
  },
  "codigo_inventario": "CAS-001",
  "estado": "BAJA"
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 400 | El ejemplar tiene un préstamo activo en curso (`fecha_devolucion` nula), lo cual impide pasarlo a `MANTENIMIENTO` o `BAJA` (**RN-04**) |
| 400 | El valor de `estado` no es válido (**RN-03**) |
| 400 | Intento de enviar campos no autorizados (ej. `codigo_inventario`, `libro_id` u otros desconocidos) |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |
| 404 | Ejemplar inexistente con el `ejemplar_id` indicado |

---

## Operaciones no disponibles

- **DELETE `/api/libros/{libro_id}/`:** No implementado. Devuelve **HTTP 405 Method Not Allowed**. La eliminación física de títulos está restringida para preservar la integridad del catálogo y existencias.
- **DELETE `/api/ejemplares/{ejemplar_id}/`:** No implementado. Devuelve **HTTP 405 Method Not Allowed**. Conforme a **RN-04** y **RN-20**, las bajas se gestionan de manera exclusivamente lógica mediante `PATCH /api/ejemplares/{ejemplar_id}/` con `{"estado": "BAJA"}`, conservando intacto el historial de préstamos vinculados.

---

## Reglas de negocio aplicadas

1. **RN-01 — Identificación bibliográfica:** Cada libro posee un ISBN único. Validado a nivel de servicio mediante consulta previa, a nivel de base de datos con restricción `UNIQUE` y gestionado mediante captura de `IntegrityError` sin enmascarar errores ajenos.
2. **RN-02 — Identificación de cada copia:** Cada ejemplar posee un `codigo_inventario` único (máximo 15 caracteres) y pertenece a un único libro. Validado a nivel de serializador, servicio y restricción física `UNIQUE` en base de datos.
3. **RN-03 — Estado operativo del ejemplar:** Los únicos estados válidos son `ACTIVO`, `MANTENIMIENTO` y `BAJA`. Si se omite en el registro, el sistema asigna `ACTIVO` automáticamente.
4. **RN-04 — Baja con conservación del historial:** La baja se efectúa exclusivamente cambiando el estado a `BAJA`. Se bloquea cualquier transición a `MANTENIMIENTO` o `BAJA` si el ejemplar tiene préstamos activos (`fecha_devolucion` nula).
5. **RN-19 — Relaciones sin duplicados:** Las tablas intermedias `biblioteca_libros_autores` y `biblioteca_categoria_libros` aplican deduplicación en capa de servicio y restricciones físicas `unique_libro_autor` y `unique_libro_categoria`.
6. **RN-20 — Referencias e historial:** No se permite la eliminación física destructiva que deje préstamos sin referencia histórica. Toda baja es lógica.
7. **Control de concurrencia pesimista:** Las operaciones de actualización de ejemplares adquieren bloqueo de fila mediante `select_for_update()` dentro de un bloque atómico (`transaction.atomic()`), serializando operaciones simultáneas.

---

## Pruebas automatizadas

El módulo cuenta con **91 pruebas específicas** implementadas y verificadas:

1. **Repositorio y servicio de libros:** [`backend/biblioteca/tests/test_libros.py`](../../backend/biblioteca/tests/test_libros.py) (16 pruebas).
2. **API REST de libros:** [`backend/biblioteca/tests/test_libros_api.py`](../../backend/biblioteca/tests/test_libros_api.py) (21 pruebas).
3. **Repositorio y servicio de ejemplares:** [`backend/biblioteca/tests/test_ejemplares.py`](../../backend/biblioteca/tests/test_ejemplares.py) (24 pruebas).
4. **API REST de ejemplares:** [`backend/biblioteca/tests/test_ejemplares_api.py`](../../backend/biblioteca/tests/test_ejemplares_api.py) (30 pruebas).

### Comando de ejecución

```bash
docker compose exec backend python manage.py test biblioteca.tests.test_libros biblioteca.tests.test_libros_api biblioteca.tests.test_ejemplares biblioteca.tests.test_ejemplares_api
```

### Resultado verificado

```text
Ran 91 tests in 24.116s

OK
Destroying test database for alias 'default'...
```
- **Código de salida real:** `0` (100% de pruebas del ticket aprobadas).

---

## Dependencias y pendientes

1. **Frontend de libros y ejemplares (Ticket 3.3.1 — Issue #26):** Integración de estos contratos REST con los componentes de Angular 21 (servicios HTTP, formularios reactivos y componentes de catálogo administrativo).
2. **Coordinación con el módulo de préstamos (Ticket 3.5):** El servicio de registro de préstamos del ticket 3.5 deberá implementar `select_for_update()` sobre la fila del `Ejemplar` dentro de su transacción atómica para garantizar la exclusión mutua frente a cambios de estado concurrentes del ticket 3.3.
3. **Pruebas de concurrencia real (Ticket 3.3.3 — Issue #28):** Realizar pruebas multihilo integradas con MySQL entre préstamos y bajas de ejemplares durante la fase de integración.
4. **Actualización de prueba en Catálogo (Ticket 3.4):** Coordinar con el responsable del ticket 3.4 la actualización de `test_relaciones_duplicadas_no_duplican_libros_ni_stock` en `test_catalogo.py` para utilizar asociaciones válidas distintas conforme a la restricción física de RN-19.
5. **Decisión funcional sobre reversibilidad de BAJA:** La reactivación administrativa de ejemplares desde `BAJA` a `ACTIVO` permanece permitida provisionalmente al no estar prohibida expresamente por la documentación; queda pendiente confirmación formal por parte del equipo de análisis de negocio.
