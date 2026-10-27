# Contratos de API — Sistema de Gestión de Biblioteca

## Objetivo

Este directorio centraliza los contratos HTTP de comunicación entre Angular y Django REST Framework. Corresponde al **entregable 2.4** del proyecto.

La documentación describe las rutas implementadas en `backend/biblioteca/urls.py` en la rama `dev`. Los ejemplos de datos y tokens son ilustrativos, nunca credenciales reales.

## Convenciones generales

- **URL base local:** `http://localhost:8000/api/`.
- **Formato:** solicitudes y respuestas JSON; fechas `YYYY-MM-DD`; fechas-hora ISO 8601 cuando aplican.
- **Autenticación:** `Authorization: Bearer <token>`, excepto `POST /api/auth/login/`.
- **Roles y permisos:** se verifican en Django; los controles de Angular no sustituyen esta validación.
- **Identificadores:** son asignados por MySQL; no se deben fijar valores de IDs en el cliente.
- **Códigos comunes:** `200` consulta/actualización, `201` creación, `204` operación sin cuerpo, `400` validación, `401` autenticación, `403` permisos, `404` recurso inexistente, `409` conflicto de negocio cuando la operación lo define, `405` método no permitido.

## Índice de contratos implementados

| Módulo | Operaciones | Contrato |
|---|---|---|
| Autenticación y permisos (3.1) | Login, logout, sesión y verificaciones de rol | [auth.md](auth.md) |
| Gestión de usuarios y roles (3.2) | Registro, consulta y edición de usuarios; listado de roles | [usuarios.md](usuarios.md) |
| Gestión de libros, ejemplares, autores y categorías (3.3) | Operaciones administrativas del acervo | [libros_ejemplares.md](libros_ejemplares.md) |
| Catálogo (3.4) | Listado, detalle y filtros de catálogo | [API_catalogo.md](../API_catalogo.md) |
| Registro de préstamos y elegibilidad (3.5) | Búsqueda de lectores, elegibilidad, registro | [prestamos.md](prestamos.md) |
| Bloqueos temporales (3.7) | Información en elegibilidad y estado de cuenta; sin ruta HTTP independiente | [prestamos.md](prestamos.md), [mis_prestamos.md](mis_prestamos.md) |
| Devoluciones y multas (3.6) | Registro de devolución y búsqueda de préstamos activos | [devoluciones.md](devoluciones.md) |
| Sanciones y pagos (3.8) | Consulta administrativa, detalle y registro de pago | [sanciones.md](sanciones.md) |
| Consulta personal de préstamos (3.9) | Historial y estado de cuenta del lector | [mis_prestamos.md](mis_prestamos.md) |
| Consulta personal de sanciones (3.9) | Historial, importes y bloqueos registrados | [mis_sanciones.md](mis_sanciones.md) |

**Operación auxiliar:** `GET /api/estado/` se utiliza para diagnóstico del servicio; no es un endpoint funcional de Angular.

## Contenido mínimo por contrato

1. Nombre de módulo y tickets relacionados.
2. Ruta y método HTTP implementados.
3. Autenticación y roles autorizados.
4. Parámetros de ruta y consulta.
5. Campos de entrada y sus validaciones.
6. Ejemplos JSON de solicitudes y respuestas.
7. Códigos HTTP y estructuras de errores.
8. Reglas de negocio relacionadas.
9. Pruebas, dependencias y limitaciones conocidas.

## Mantenimiento y responsabilidades

- No documentar rutas propuestas como si ya estuvieran implementadas.
- Actualizar el contrato en el mismo cambio que modifique una ruta, campo o respuesta.
- Confirmar la especificación en vistas, serializers y servicios reales; el contrato no sustituye esas validaciones.
- No incluir contraseñas, tokens activos ni datos personales reales.
- Coordinar modificaciones de contratos de otros módulos con sus responsables.
- Utilizar [plantilla_contrato.md](plantilla_contrato.md) para módulos nuevos.

## Colecciones Postman

Las colecciones y entornos locales se encuentran en `Documentacion/Postman/`. Postman complementa los contratos escritos; no los sustituye.
