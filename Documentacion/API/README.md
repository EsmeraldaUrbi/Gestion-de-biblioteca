# Contratos de API — Sistema de Gestión de Biblioteca

## Objetivo

Este directorio centraliza los contratos HTTP utilizados
para la comunicación entre Angular y Django REST Framework.

Corresponde al entregable 2.4 del proyecto.

## Convenciones generales

- URL base local: `http://localhost:8000/api/`
- Formato de solicitudes y respuestas: JSON.
- Autenticación: `Authorization: Bearer <token>`.
- Los permisos se validan en el backend.
- Los identificadores de los recursos son asignados
  por la base de datos.
- Cada módulo mantiene su propio contrato.

## Índice de contratos

| Módulo | Implementación en dev | Contrato |
|---|---|---|
| Autenticación (3.1) | Backend y frontend implementados | Pendiente de documentar |
| Gestión de usuarios (3.2) | Backend implementado | [usuarios.md](usuarios.md) |
| Gestión de libros, autores, categorías y ejemplares (3.3) | Backend implementado (Frontend en desarrollo) | [libros_ejemplares.md](libros_ejemplares.md) |
| Catálogo (3.4.2) | Backend implementado | [API_catalogo.md](../API_catalogo.md) |
| Otros módulos | En desarrollo o pendientes de integración | Pendientes de definir o documentar |

La tabla deberá actualizarse conforme se integren
nuevas funcionalidades.

## Contenido mínimo por contrato

Cada contrato debe especificar:

1. Nombre del módulo y ticket.
2. Rutas y métodos HTTP.
3. Roles autorizados.
4. Parámetros de ruta y consulta.
5. Campos de entrada y sus validaciones.
6. Ejemplos JSON de solicitudes y respuestas.
7. Códigos y estructuras de error.
8. Reglas de negocio relacionadas.
9. Pruebas y dependencias conocidas.

## Reglas de mantenimiento

- No documentar rutas propuestas como si estuvieran
  implementadas.
- Si una ruta cambia, actualizar su contrato en el
  mismo cambio de código.
- No incluir contraseñas reales ni tokens válidos.
- Cada responsable documenta los endpoints de su módulo.
- No modificar los contratos ajenos sin coordinarlo
  con el responsable.
- Usar [plantilla_contrato.md](plantilla_contrato.md)
  para los módulos nuevos.

## Colecciones Postman

Las colecciones y entornos de prueba permanecen en:

`Documentacion/Postman/`

Postman complementa los contratos escritos,
pero no los sustituye.
