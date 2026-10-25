# Contrato de API — Gestión de libros, autores, categorías y ejemplares

## Información general

- **Ticket:** 3.3 — Gestión de libros y ejemplares (incluye administración de autores y categorías)
- **Módulo:** Gestión de libros, autores, categorías y ejemplares
- **Responsables:** Diego Alberto Nava Rivera (`inava404`)
- **Estado:** Verificado (204 pruebas automatizadas aprobadas)
- **Fecha de actualización:** 2026-10-19
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
| `GET` | `/api/autores/` | Listado administrativo de autores con filtros y paginación | `bibliotecario` |
| `POST` | `/api/autores/` | Registro de un nuevo autor bibliográfico | `bibliotecario` |
| `GET` | `/api/autores/{autor_id}/` | Consulta de detalle de autor por identificador | `bibliotecario` |
| `PATCH` | `/api/autores/{autor_id}/` | Modificación parcial de datos de un autor (conserva omitidos) | `bibliotecario` |
| `PUT` | `/api/autores/{autor_id}/` | Actualización completa de autor (restablece omitidos a `null`) | `bibliotecario` |
| `GET` | `/api/categorias/` | Listado administrativo de categorías con búsqueda y paginación | `bibliotecario` |
| `POST` | `/api/categorias/` | Registro de una nueva categoría de clasificación | `bibliotecario` |
| `GET` | `/api/categorias/{categoria_id}/` | Consulta de detalle de categoría por identificador | `bibliotecario` |
| `PATCH` | `/api/categorias/{categoria_id}/` | Modificación parcial del nombre de una categoría | `bibliotecario` |
| `PUT` | `/api/categorias/{categoria_id}/` | Actualización completa del nombre de una categoría | `bibliotecario` |

---\n\n## Detalle de operaciones

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

---\n\n---\n\n### 10. GET `/api/autores/`

**Propósito:**
Permite al personal bibliotecario consultar la lista de autores registrados en el sistema, con soporte de paginación, filtros de búsqueda por nombre y nacionalidad, e indicación del número de libros asociados.

**Autenticación y autorización:**
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de consulta (Query Parameters):**

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| `nombre` | String | No | Ninguno | Coincidencia parcial insensible a mayúsculas/minúsculas |
| `nacionalidad` | String | No | Ninguno | Coincidencia parcial insensible a mayúsculas/minúsculas |
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
      "autor_id": 1,
      "nombre": "Gabriel García Márquez",
      "nacionalidad": "Colombiana",
      "fecha_nacimiento": "1927-03-06",
      "cantidad_libros": 2
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

### 11. POST `/api/autores/`

**Propósito:**
Registra un nuevo autor bibliográfico en el sistema.

**Autenticación y autorización:**
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:** Ninguno.

**Ejemplo 1 — Registro con datos completos:**

*Solicitud JSON:*
```json
{
  "nombre": "Gabriel García Márquez",
  "nacionalidad": "Colombiana",
  "fecha_nacimiento": "1927-03-06"
}
```

**Ejemplo 2 — Registro con únicamente campos obligatorios:**

*Solicitud JSON:*
```json
{
  "nombre": "Isabel Allende"
}
```

*Detalles de validación de campos:*
- `nombre`: String no vacío (longitud 1 a 100 caracteres tras normalización). Obligatorio.
- `nacionalidad`: String opcional (máximo 50 caracteres) o `null`.
- `fecha_nacimiento`: String en formato `YYYY-MM-DD` menor o igual a la fecha actual (`date.today()`) o `null`. Opcional.
- `autor_id` y `cantidad_libros`: Campos de solo lectura. Cualquier inyección en la solicitud es descartada o rechazada.
- **Normalización de espacios:** Se eliminan espacios en blanco al inicio, final y secuencias redundantes intermedias.
- **Homónimos permitidos:** Se permite el registro de autores con nombres idénticos por decisión de diseño funcional, ya que personas distintas pueden compartir el mismo nombre.
- **Rechazo de campos desconocidos:** Cualquier clave adicional ajena al contrato genera un error de validación `400 Bad Request`.

**Respuesta exitosa:**
- **Código HTTP:** 201 Created
- **Estructura JSON:**

```json
{
  "autor_id": 1,
  "nombre": "Gabriel García Márquez",
  "nacionalidad": "Colombiana",
  "fecha_nacimiento": "1927-03-06",
  "cantidad_libros": 0
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 400 | Nombre vacío, compuesto solo de espacios en blanco o longitud mayor a 100 caracteres |
| 400 | Fecha de nacimiento posterior a la fecha actual o formato de fecha inválido |
| 400 | Presencia de campos desconocidos no permitidos en el cuerpo JSON |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |

---

### 12. GET `/api/autores/{autor_id}/`

**Propósito:**
Consulta la información completa de un autor por su identificador primario, incluyendo el contador de libros vinculados.

**Autenticación y autorización:**
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `autor_id` | Integer | Sí | Identificador numérico entero del autor |

**Solicitud JSON:**
No requiere cuerpo de solicitud.

**Respuesta exitosa:**
- **Código HTTP:** 200 OK
- **Estructura JSON:**

```json
{
  "autor_id": 1,
  "nombre": "Gabriel García Márquez",
  "nacionalidad": "Colombiana",
  "fecha_nacimiento": "1927-03-06",
  "cantidad_libros": 2
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |
| 404 | No existe ningún autor registrado con el `autor_id` indicado |

---

### 13. PATCH `/api/autores/{autor_id}/`

**Propósito:**
Modificación parcial de los datos de un autor.
**Semántica PATCH (conservación de campos):** Solo se modifican los campos incluidos explícitamente en el cuerpo JSON. Cualquier campo omitido conserva su valor previo en la base de datos sin alteración.

**Autenticación y autorización:**
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `autor_id` | Integer | Sí | Identificador numérico entero del autor |

**Ejemplo 1 — Modificación de nombre únicamente:**

*Solicitud JSON:*
```json
{
  "nombre": "Gabriel José García Márquez"
}
```

*Respuesta exitosa (HTTP 200 OK):*
```json
{
  "autor_id": 1,
  "nombre": "Gabriel José García Márquez",
  "nacionalidad": "Colombiana",
  "fecha_nacimiento": "1927-03-06",
  "cantidad_libros": 2
}
```

**Ejemplo 2 — Modificación exclusiva de nacionalidad:**

*Solicitud JSON:*
```json
{
  "nacionalidad": "Latinoamericana"
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 400 | Intento de enviar `nombre` vacío o con espacios en blanco |
| 400 | Fecha de nacimiento en formato inválido o fecha futura |
| 400 | Envío de campos desconocidos no permitidos |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |
| 404 | No existe ningún autor con el `autor_id` indicado |

---

### 14. PUT `/api/autores/{autor_id}/`

**Propósito:**
Actualización completa de la representación de un autor.
**Semántica PUT (reemplazo integral):** Requiere obligatoriamente el campo `nombre`. Los campos opcionales omitidos en la solicitud (`nacionalidad` y `fecha_nacimiento`) **se restablecen automáticamente a `null`** en la base de datos.

**Autenticación y autorización:**
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `autor_id` | Integer | Sí | Identificador numérico entero del autor |

**Ejemplo 1 — Actualización completa con todos los datos:**

*Solicitud JSON:*
```json
{
  "nombre": "Gabriel García Márquez",
  "nacionalidad": "Colombiana",
  "fecha_nacimiento": "1927-03-06"
}
```

*Respuesta exitosa (HTTP 200 OK):*
```json
{
  "autor_id": 1,
  "nombre": "Gabriel García Márquez",
  "nacionalidad": "Colombiana",
  "fecha_nacimiento": "1927-03-06",
  "cantidad_libros": 2
}
```

**Ejemplo 2 — Actualización omitiendo campos opcionales (restablecimiento a `null`):**

*Solicitud JSON:*
```json
{
  "nombre": "Gabriel García Márquez"
}
```

*Respuesta exitosa (HTTP 200 OK):*
```json
{
  "autor_id": 1,
  "nombre": "Gabriel García Márquez",
  "nacionalidad": null,
  "fecha_nacimiento": null,
  "cantidad_libros": 2
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 400 | Solicitud sin el campo obligatorio `nombre` o con `nombre` vacío |
| 400 | Fecha de nacimiento futura o formato inválido |
| 400 | Campos desconocidos no autorizados |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |
| 404 | No existe ningún autor con el `autor_id` indicado |

---

### 15. GET `/api/categorias/`

**Propósito:**
Permite al personal bibliotecario consultar la lista de categorías temáticas registradas en el sistema, con paginación, búsqueda por nombre e indicación de la cantidad de libros asociados.

**Autenticación y autorización:**
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de consulta (Query Parameters):**

| Parámetro | Tipo | Obligatorio | Valor predeterminado | Descripción |
| :--- | :--- | :--- | :--- | :--- |
| `nombre` | String | No | Ninguno | Coincidencia parcial insensible a mayúsculas/minúsculas sobre `nombre_categoria` |
| `page` | Integer | No | `1` | Número de página solicitada (inicia en 1) |
| `page_size` | Integer | No | `10` | Registros por página (máximo `100`) |

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
      "categoria_id": 1,
      "nombre_categoria": "Realismo Mágico",
      "cantidad_libros": 1
    },
    {
      "categoria_id": 2,
      "nombre_categoria": "Novela Clásica",
      "cantidad_libros": 3
    }
  ]
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 401 | Petición anónima, cabecera `Authorization` ausente o token inválido/expirado |
| 403 | Usuario autenticado cuyo rol no es `bibliotecario` |

---

### 16. POST `/api/categorias/`

**Propósito:**
Registra una nueva categoría de clasificación bibliográfica en el sistema.

**Autenticación y autorización:**
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:** Ninguno.

**Solicitud JSON:**

```json
{
  "nombre_categoria": "Ciencia Ficción"
}
```

*Detalles de validación de campos:*
- `nombre_categoria`: String no vacío (longitud 1 a 50 caracteres tras normalización). Obligatorio.
- **Unicidad e insensibilidad a mayúsculas:** El nombre de la categoría debe ser único de forma insensible a mayúsculas y minúsculas. Si ya existe una categoría `"Ciencia Ficción"`, se rechazarán variaciones como `"ciencia ficción"` o `"CIENCIA FICCIÓN"`.
- **Normalización de espacios:** Se eliminan espacios en blanco en los extremos y secuencias consecutivas internas.
- **Rechazo de campos desconocidos:** Se prohíbe el envío de campos no declarados.
- `categoria_id` y `cantidad_libros`: Campos protegidos de solo lectura.

**Respuesta exitosa:**
- **Código HTTP:** 201 Created
- **Estructura JSON:**

```json
{
  "categoria_id": 3,
  "nombre_categoria": "Ciencia Ficción",
  "cantidad_libros": 0
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 400 | Nombre vacío, compuesto solo de espacios en blanco o longitud mayor a 50 caracteres |
| 400 | Nombre de categoría duplicado (coincidencia exacta o por mayúsculas/minúsculas) |
| 400 | Presencia de campos desconocidos no permitidos en el cuerpo JSON |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |

---

### 17. GET `/api/categorias/{categoria_id}/`

**Propósito:**
Consulta la información completa de una categoría por su identificador primario, incluyendo el contador de libros asociados.

**Autenticación y autorización:**
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `categoria_id` | Integer | Sí | Identificador numérico entero de la categoría |

**Solicitud JSON:**
No requiere cuerpo de solicitud.

**Respuesta exitosa:**
- **Código HTTP:** 200 OK
- **Estructura JSON:**

```json
{
  "categoria_id": 1,
  "nombre_categoria": "Realismo Mágico",
  "cantidad_libros": 1
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |
| 404 | No existe ninguna categoría registrada con el `categoria_id` indicado |

---

### 18. PATCH `/api/categorias/{categoria_id}/`

**Propósito:**
Modificación parcial del nombre de una categoría existente.

**Autenticación y autorización:**
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `categoria_id` | Integer | Sí | Identificador numérico entero de la categoría |

**Solicitud JSON:**

```json
{
  "nombre_categoria": "Ficción Especulativa"
}
```

*Validaciones:*
- Se valida la unicidad de forma insensible a mayúsculas frente al resto del catálogo. Si se envía el mismo nombre que la categoría ya posee, se conserva sin conflicto.
- No se permiten nombres vacíos ni campos desconocidos.

**Respuesta exitosa:**
- **Código HTTP:** 200 OK
- **Estructura JSON:**

```json
{
  "categoria_id": 3,
  "nombre_categoria": "Ficción Especulativa",
  "cantidad_libros": 0
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 400 | Nombre vacío o compuesto solo de espacios |
| 400 | El nuevo nombre ya pertenece a otra categoría registrada |
| 400 | Presencia de campos desconocidos en la solicitud |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |
| 404 | No existe ninguna categoría con el `categoria_id` indicado |

---

### 19. PUT `/api/categorias/{categoria_id}/`

**Propósito:**
Actualización completa del recurso categoría.

**Autenticación y autorización:**
- Cabecera: `Authorization: Bearer <token>`
- Requiere autenticación (`IsAuthenticated`) y rol `bibliotecario` (`IsBibliotecario`).

**Parámetros de ruta:**

| Parámetro | Tipo | Obligatorio | Descripción |
| :--- | :--- | :--- | :--- |
| `categoria_id` | Integer | Sí | Identificador numérico entero de la categoría |

**Solicitud JSON:**

```json
{
  "nombre_categoria": "Literatura Clásica Universal"
}
```

*Validaciones:*
- Requiere obligatoriamente el campo `nombre_categoria`.
- Se valida la unicidad insensible a mayúsculas frente a otras categorías.

**Respuesta exitosa:**
- **Código HTTP:** 200 OK
- **Estructura JSON:**

```json
{
  "categoria_id": 2,
  "nombre_categoria": "Literatura Clásica Universal",
  "cantidad_libros": 3
}
```

**Errores esperados:**

| HTTP | Condición |
| :--- | :--- |
| 400 | Solicitud sin el campo obligatorio `nombre_categoria` o con valor vacío |
| 400 | El nombre indicado colisiona con otra categoría existente |
| 400 | Campos desconocidos no permitidos |
| 401 | Petición sin token de autenticación válido |
| 403 | Usuario autenticado con rol distinto a `bibliotecario` |
| 404 | No existe ninguna categoría con el `categoria_id` indicado |

---

## Operaciones no disponibles (Restricción DELETE — HTTP 405)

- **DELETE `/api/libros/{libro_id}/`:** No implementado. Devuelve **HTTP 405 Method Not Allowed**. La eliminación física de títulos está restringida para preservar la integridad del catálogo y existencias.
- **DELETE `/api/ejemplares/{ejemplar_id}/`:** No implementado. Devuelve **HTTP 405 Method Not Allowed**. Conforme a **RN-04** y **RN-20**, las bajas se gestionan de manera exclusivamente lógica mediante `PATCH /api/ejemplares/{ejemplar_id}/` con `{"estado": "BAJA"}`, conservando intacto el historial de préstamos vinculados.
- **DELETE `/api/autores/{autor_id}/`:** No implementado. Devuelve **HTTP 405 Method Not Allowed**. La eliminación física de autores está expresamente restringida para garantizar la integridad referencial histórica con los libros registrados. Si un cliente emite una petición DELETE, el servidor responde 405 y el registro del autor permanece inalterado en la base de datos.
- **DELETE `/api/categorias/{categoria_id}/`:** No implementado. Devuelve **HTTP 405 Method Not Allowed**. La eliminación física de categorías está expresamente restringida para evitar desclasificar libros y salvaguardar la clasificación bibliográfica. El registro de la categoría permanece intacto ante cualquier solicitud DELETE.

---

## Diferencias semánticas entre PUT y PATCH

| Aspecto | `PATCH` | `PUT` |
| :--- | :--- | :--- |
| **Alcance** | Modificación parcial de la entidad | Reemplazo completo de la entidad |
| **Campos obligatorios** | Ninguno por defecto; solo se validan los campos enviados | Los campos obligatorios (`nombre` en autores, `nombre_categoria` en categorías) deben enviarse obligatoriamente |
| **Campos opcionales omitidos** | **Se conservan** con su valor actual sin modificaciones | **Se restablecen a `null`** en la base de datos (aplica a `nacionalidad` y `fecha_nacimiento` en Autores) |
| **Asociaciones de libros (`autor_ids`, `categoria_ids`)** | Si se omiten, **se conservan** las relaciones preexistentes | Si se omiten o envían vacíos, se sincronizan/eliminan las relaciones preexistentes |

---

## Integración con libros y catálogo

1. **Uso de identificadores en la creación y edición de libros:**
   Los identificadores primarios generados al registrar autores (`autor_id`) y categorías (`categoria_id`) son consumidos directamente en los endpoints de libros:
   - `POST /api/libros/`: campos `autor_ids: [int]` y `categoria_ids: [int]`.
   - `PUT /api/libros/{id}/` y `PATCH /api/libros/{id}/`.
2. **Consultas de detalle y catálogo:**
   Al consultar un libro en `/api/libros/{id}/` o en el catálogo público `/api/catalogo/`, las relaciones se exponen como objetos anidados (`autores: [{"autor_id": ..., "nombre": ...}]` y `categorias: [{"categoria_id": ..., "nombre_categoria": ...}]`).
3. **Contador de libros asociados (`cantidad_libros`):**
   Tanto en el listado como en el detalle de autores y categorías, se calcula en tiempo real mediante agregación ORM (`Count('libroautor', distinct=True)` y `Count('categorialibro', distinct=True)`), evitando duplicidad de conteos si existen múltiples asociaciones.
4. **Resiliencia ante modificaciones:**
   Modificar el nombre o datos de un autor o de una categoría no altera las claves foráneas en las tablas intermedias (`biblioteca_libros_autores` y `biblioteca_categoria_libros`). La consulta posterior de cualquier libro asociado reflejará de inmediato los nuevos nombres sin romper las relaciones bibliográficas.

---

## Reglas de negocio oficiales aplicadas

1. **RN-01 — Identificación bibliográfica:** Cada libro posee un ISBN único. Validado a nivel de servicio mediante consulta previa, a nivel de base de datos con restricción `UNIQUE` y gestionado mediante captura de `IntegrityError` sin enmascarar errores ajenos.
2. **RN-02 — Identificación de cada copia:** Cada ejemplar posee un `codigo_inventario` único (máximo 15 caracteres) y pertenece a un único libro. Validado a nivel de serializador, servicio y restricción física `UNIQUE` en base de datos.
3. **RN-03 — Estado operativo del ejemplar:** Los únicos estados válidos son `ACTIVO`, `MANTENIMIENTO` y `BAJA`. Si se omite en el registro, el sistema asigna `ACTIVO` automáticamente.
4. **RN-04 — Baja con conservación del historial:** La baja se efectúa exclusivamente cambiando el estado a `BAJA`. Se bloquea cualquier transición a `MANTENIMIENTO` o `BAJA` si el ejemplar tiene préstamos activos (`fecha_devolucion` nula).
5. **RN-19 — Relaciones sin duplicados:** Las tablas intermedias `biblioteca_libros_autores` y `biblioteca_categoria_libros` aplican deduplicación en capa de servicio y restricciones físicas `unique_libro_autor` y `unique_libro_categoria`.
6. **RN-20 — Referencias e historial:** No se permite la eliminación física destructiva que deje préstamos sin referencia histórica. Toda baja es lógica.
7. **Control de concurrencia pesimista:** Las operaciones de actualización de ejemplares adquieren bloqueo de fila mediante `select_for_update()` dentro de un bloque atómico (`transaction.atomic()`), serializando operaciones simultáneas.

---

## Validaciones y criterios de integridad de autores y categorías

A diferencia de las reglas de negocio oficiales numeradas a nivel del sistema general, los siguientes puntos corresponden a validaciones de modelo y decisiones de diseño técnico específicas para la administración de autores y categorías:

- **Validación de autores y soporte de homónimos:** El nombre del autor es obligatorio (longitud máxima de 100 caracteres) y se normalizan espacios redundantes. Por decisión de diseño se permite el registro de homónimos, considerando que personas distintas pueden tener el mismo nombre. Las fechas de nacimiento no pueden ser posteriores a la fecha actual (`date.today()`).
- **Unicidad e integridad de categorías:** El nombre de categoría es obligatorio (longitud máxima de 50 caracteres) y debe ser único de manera insensible a mayúsculas/minúsculas (`iexact`). Se normalizan espacios antes de persistir.
- **Conteo y protección de recursos vinculados:** Autores y categorías calculan en tiempo real `cantidad_libros` y restringen la eliminación física respondiendo HTTP 405 Method Not Allowed para preservar la integridad de las fichas bibliográficas asociadas.

---

## Pruebas automatizadas

El ticket 3.3 cuenta con **204 pruebas específicas** implementadas y verificadas (100% aprobadas):

1. **Repositorio y servicio de libros:** [`backend/biblioteca/tests/test_libros.py`](../../backend/biblioteca/tests/test_libros.py) (16 pruebas).
2. **API REST de libros:** [`backend/biblioteca/tests/test_libros_api.py`](../../backend/biblioteca/tests/test_libros_api.py) (21 pruebas).
3. **Repositorio y servicio de ejemplares:** [`backend/biblioteca/tests/test_ejemplares.py`](../../backend/biblioteca/tests/test_ejemplares.py) (24 pruebas).
4. **API REST de ejemplares:** [`backend/biblioteca/tests/test_ejemplares_api.py`](../../backend/biblioteca/tests/test_ejemplares_api.py) (30 pruebas).
5. **Repositorio y servicio de autores:** [`backend/biblioteca/tests/test_autores.py`](../../backend/biblioteca/tests/test_autores.py) (27 pruebas).
6. **Repositorio y servicio de categorías:** [`backend/biblioteca/tests/test_categorias.py`](../../backend/biblioteca/tests/test_categorias.py) (25 pruebas).
7. **API REST de autores:** [`backend/biblioteca/tests/test_autores_api.py`](../../backend/biblioteca/tests/test_autores_api.py) (34 pruebas).
8. **API REST de categorías:** [`backend/biblioteca/tests/test_categorias_api.py`](../../backend/biblioteca/tests/test_categorias_api.py) (28 pruebas).

### Comando de ejecución de la suite completa del ticket

```bash
docker compose exec backend python manage.py test biblioteca.tests.test_libros biblioteca.tests.test_libros_api biblioteca.tests.test_ejemplares biblioteca.tests.test_ejemplares_api biblioteca.tests.test_autores biblioteca.tests.test_categorias biblioteca.tests.test_autores_api biblioteca.tests.test_categorias_api
```

### Resultado verificado

```text
Ran 204 tests in 78.505s

OK
Destroying test database for alias 'default'...
```
- **Código de salida real:** `0` (100% de pruebas del ticket 3.3 aprobadas).
- **Validación regresiva completa del backend:** `Ran 370 tests in 159.919s, OK` (0 errores en todo el sistema).

---

## Dependencias y pendientes

1. **Frontend de autores y categorías (Fase 2 del Ticket 3.3):**
   - El selector de categorías en los formularios de registro y edición de libros (`libro-nuevo.ts` / `libro-nuevo.html`) ya se encuentra implementado y operativo en Angular.
   - El alcance pendiente de la Fase 2 consiste en crear los servicios y componentes administrativos dedicados para la gestión de autores y categorías (listados, formularios reactivos y modales de registro/edición).
2. **Garantía física de unicidad concurrente de categorías en MySQL:**
   - Implementada y verificada mediante la migración `0008_alter_categoria_nombre_categoria.py`.
   - La tabla `biblioteca_categoria` cuenta con la restricción física `UNIQUE KEY (nombre_categoria)` bajo la colación `utf8mb4_0900_ai_ci`, garantizando que a nivel de motor de almacenamiento no se puedan registrar nombres equivalentes por mayúsculas, minúsculas o acentos.
   - En la capa de servicios (`CategoriaService`), las colisiones concurrentes se traducen limpiamente en `CategoriaDuplicadaError` (HTTP 400 Bad Request), validado mediante pruebas reales multihilo con `TransactionTestCase`.
3. **Coordinación con el módulo de préstamos (Ticket 3.5):** El servicio de registro de préstamos del ticket 3.5 deberá implementar `select_for_update()` sobre la fila del `Ejemplar` dentro de su transacción atómica para garantizar la exclusión mutua frente a cambios de estado concurrentes del ticket 3.3.
4. **Pruebas de concurrencia real (Ticket 3.3.3 — Issue #28):** Realizar pruebas multihilo integradas con MySQL entre préstamos y bajas de ejemplares durante la fase de integración.
