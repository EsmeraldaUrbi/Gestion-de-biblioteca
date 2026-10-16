# Contrato de API — Registro de devoluciones y cálculo de multas



## Información general



- Ticket: 3.6 (3.6.1, 3.6.2, 3.6.3)

- Responsable: Kaltum Abdala Viveros Gómez (`Kaltum-Viveros`)

- Estado: Propuesto

- Fecha de actualización: 2026-10-15

- Reglas de negocio: RN-05, RN-06, RN-15, RN-20



## Endpoints



| Método | Ruta | Descripción | Roles |

|---|---|---|---|

| POST | `/api/prestamos/{prestamo_id}/devolucion/` | Registrar devolución física y calcular multa por retraso | bibliotecario |



## Detalle de operaciones



### POST `/api/prestamos/{prestamo_id}/devolucion/`



**Propósito:**



Registrar la fecha real de devolución de un ejemplar prestado, actualizar el estado operativo del ejemplar a `ACTIVO` y generar automáticamente una sanción económica si el préstamo superó la fecha límite acordada.



**Autenticación y autorización:**



- Cabecera: `Authorization: Bearer <token>`

- Requiere autenticación mediante token Bearer y rol `bibliotecario` (`IsBibliotecario`).



**Parámetros:**



| Parámetro | Tipo | Obligatorio | Descripción |

|---|---|---|---|

| `prestamo_id` | Entero positivo | Sí | Identificador numérico único del préstamo a devolver |



**Solicitud JSON:**



No requiere cuerpo de solicitud para la operación regular en producción (asume la fecha actual del servidor). Para pruebas de aceptación permite enviar opcionalmente la fecha de devolución:



{

  "fecha_devolucion": "2026-10-15"

}



**Respuesta exitosa:**



- Código HTTP: 200 OK

- Estructura JSON (Devolución a tiempo):



{

  "mensaje": "Devolución registrada correctamente.",

  "prestamo_id": 15,

  "fecha_devolucion": "2026-10-15",

  "dias_retraso": 0,

  "monto_multa": "0.00",

  "sancion_generada": false,

  "ejemplar_estado": "ACTIVO"

}



- Estructura JSON (Devolución con retraso):



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



**Errores esperados:**



| HTTP | Condición |

|---|---|

| 400 | El préstamo ya cuenta con una `fecha_devolucion` registrada (Intento de duplicación / Idempotencia) |

| 401 | Petición anónima, cabecera `Authorization` ausente o token inválido |

| 403 | Usuario autenticado cuyo rol no es `bibliotecario` |

| 404 | No existe ningún préstamo con el `prestamo_id` indicado |



## Reglas de negocio



1. **Cálculo de multas (RN-15):** Se cobran $5.00 MXN por cada día transcurrido después de la `fecha_limite`. Si la devolución se realiza dentro del plazo, el monto generado es de $0.00 MXN y no se crea registro de sanción.

2. **Garantía de idempotencia:** Reintentar la devolución sobre un préstamo que ya posee `fecha_devolucion` rechaza la operación con `HTTP 400 Bad Request`, garantizando que no se dupliquen sanciones ni se alteren las fechas originales.

3. **Liberación del ejemplar:** Al procesar exitosamente la devolución, el estado del `Ejemplar` asociado al préstamo cambia automáticamente a `ACTIVO` para permitir su disponibilidad en el catálogo.



## Pruebas



- Archivo: `backend/biblioteca/tests/test_devoluciones.py`

- Comando:

  docker compose exec backend python manage.py test biblioteca.tests.test_devoluciones

- Resultado verificado: Pendiente de ejecución tras implementación del backend (3.6.2).



## Dependencias y pendientes



1. **Módulo de Préstamos (Ticket 3.5):** Reutiliza los registros de préstamos existentes creados por la API de registro de préstamos.

2. **Frontend de Devoluciones (Ticket 3.6.1):** Integración del endpoint con el componente de Angular en `features/prestamos/pages/registro-devolucion`.