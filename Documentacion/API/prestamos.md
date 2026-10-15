# Contrato de API — Registro de préstamos

## Información general

- Ticket: 3.5.2 y 3.5.3
- Módulo: Registro de préstamos
- Backend: Django REST Framework
- Base: `/api/`
- Autenticación: Token Bearer personalizado
- Rol autorizado: `bibliotecario`
- Formato: JSON
- Fechas: `YYYY-MM-DD`

El módulo reutiliza las entidades Usuario, Rol, Libro,
Ejemplar, Prestamo y Sancion existentes en MySQL.

No administra usuarios ni ejemplares y no implementa
devoluciones o pagos.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/prestamos/seleccion/usuarios/` | Buscar lectores |
| GET | `/api/prestamos/elegibilidad/` | Consultar elegibilidad |
| POST | `/api/prestamos/` | Registrar préstamo |

Todos requieren:

Authorization: Bearer <token>

El usuario autenticado debe tener rol bibliotecario.

## 1. Buscar lectores

GET `/api/prestamos/seleccion/usuarios/?q=Esmeralda&limite=10`

Parámetros:

- `q`: Texto obligatorio, máximo 100 caracteres.
- `limite`: Entero opcional entre 1 y 20. Predeterminado: 10.

Busca por nombre o correo, sin distinguir mayúsculas.

Solo devuelve estudiantes y docentes.

Respuesta HTTP 200:

```json
{
  "count": 1,
  "results": [
    {
      "usuario_id": 1,
      "nombre": "Esmeralda Urbina Cinto",
      "email": "esme@bibliotech.com",
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