# BiblioTech — Sistema de gestión de biblioteca

Proyecto académico de Arquitectura de Software para administrar el catálogo de una biblioteca, sus usuarios y la circulación de ejemplares. Desarrollado con Angular, Django REST Framework y MySQL, con separación por capas y un entorno reproducible mediante Docker Compose.

## Funcionalidades

- Inicio y cierre de sesión mediante tokens Bearer y permisos por rol.
- Registro, consulta y modificación de usuarios.
- Administración de libros, autores, categorías y ejemplares físicos.
- Catálogo con filtros y disponibilidad calculada a partir de los ejemplares y préstamos activos.
- Registro de préstamos y consulta administrativa de su historial.
- Devoluciones con cálculo automático de multas por retraso.
- Aplicación periódica de bloqueos por préstamos vencidos.
- Consulta de sanciones y registro de pago total de multas.
- Consulta personal de préstamos, multas y bloqueos para estudiantes y docentes.

## Tecnologías

| Componente | Tecnología declarada en el proyecto |
|---|---|
| Interfaz | Angular 21.2 y TypeScript 5.9 |
| Runtime del frontend | Node.js 24, imagen Alpine |
| API | Python 3.12, Django 5.2 y Django REST Framework 3.16 |
| Persistencia | MySQL 8.4 y mysqlclient |
| Entorno | Docker y Docker Compose v2 |
| Pruebas | Django Test Runner y Vitest mediante Angular CLI |

Las dependencias de Python se declaran en `backend/requirements.txt`. Las de Angular se encuentran en `frontend/package.json` y `frontend/package-lock.json`.

## Roles

| Rol | Operaciones principales |
|---|---|
| Bibliotecario | Gestionar usuarios y catálogo; registrar préstamos, devoluciones y pagos; consultar préstamos y sanciones administrativos |
| Estudiante | Consultar catálogo, préstamos y sanciones propios |
| Docente | Consultar catálogo, préstamos y sanciones propios |

El backend comprueba los permisos aunque las solicitudes se envíen directamente a la API. El bibliotecario no es elegible para recibir préstamos.

## Requisitos

- Git.
- Docker Desktop en Windows/macOS, o Docker Engine con Compose v2 en Linux.
- Docker en ejecución y acceso a Internet para descargar imágenes y dependencias.
- Puertos locales `4200`, `8000` y `3306` disponibles.
- Opcional: VS Code y Postman.

No es necesario instalar Python, Node.js, Angular CLI o MySQL en el equipo si se utiliza Docker.

> En Windows se recomienda clonar fuera de carpetas sincronizadas con OneDrive, por ejemplo en `C:\Users\TU_USUARIO\source\Gestion-de-biblioteca`, para evitar problemas al leer archivos durante la construcción de imágenes.

## Instalación desde cero

Ejecuta los comandos desde la raíz del repositorio, donde se encuentra `compose.yaml`. Se utiliza el nombre de proyecto `gestion-de-biblioteca` de forma explícita para conservar la identidad de sus recursos.

### 1. Clonar la rama de trabajo

```bash
git clone --branch dev https://github.com/EsmeraldaUrbi/Gestion-de-biblioteca.git
cd Gestion-de-biblioteca
```

### 2. Crear la configuración local

En PowerShell:

```powershell
Copy-Item .env.example .env
```

En Git Bash, Linux o macOS:

```bash
cp .env.example .env
```

Edita `.env` y sustituye las contraseñas de ejemplo por valores locales:

```dotenv
MYSQL_DATABASE=db_biblioteca
MYSQL_USER=biblioteca_user
MYSQL_PASSWORD=CAMBIA_ESTA_CLAVE_LOCAL
MYSQL_ROOT_PASSWORD=CAMBIA_ESTA_CLAVE_ROOT_LOCAL
AUTH_TOKEN_TTL_HOURS=8
DJANGO_TIME_ZONE=America/Mexico_City
```

`DJANGO_TIME_ZONE` es opcional: Compose utiliza `America/Mexico_City` por defecto. `AUTH_TOKEN_TTL_HOURS` controla la vigencia de los tokens. Dentro de Docker, Django se conecta al servicio `db` en el puerto `3306`.

No subas tu `.env` ni tokens activos al repositorio. Cambiar las variables de contraseña no cambia automáticamente las credenciales de un volumen MySQL ya inicializado.

### 3. Construir las imágenes e iniciar MySQL

```bash
docker compose -p gestion-de-biblioteca build
docker compose -p gestion-de-biblioteca up -d db
docker compose -p gestion-de-biblioteca logs --tail=50 db
```

Espera a que MySQL indique que está listo para aceptar conexiones. Compose no tiene configurada una comprobación de salud que espere automáticamente a esa condición.

### 4. Aplicar las migraciones

```bash
docker compose -p gestion-de-biblioteca run --rm backend python manage.py migrate
```

Si MySQL todavía está inicializándose y aparece un error de conexión, revisa sus logs y repite el comando cuando esté disponible. No es necesario ejecutar `makemigrations` al clonar: los archivos de migración ya forman parte del repositorio.

### 5. Preparar usuarios y libros de demostración

```bash
docker compose -p gestion-de-biblioteca run --rm backend python manage.py seed_auth_demo
docker compose -p gestion-de-biblioteca run --rm backend python manage.py seed_libros_prestamos_demo
```

- `seed_auth_demo` crea o actualiza los tres roles y sus cuentas de prueba. Al repetirlo restablece sus contraseñas y revoca sus tokens anteriores.
- `seed_libros_prestamos_demo` prepara diez libros y sus ejemplares, incluyendo estados y libros sin copias para demostrar disponibilidad. Conserva los registros existentes. A pesar de su nombre, no crea préstamos: estos se registran desde la interfaz.

Opcionalmente, puede ampliarse el catálogo con:

```bash
docker compose -p gestion-de-biblioteca run --rm backend python manage.py seed_catalogo_demo
```

Este último comando agrega hasta quince libros ficticios y escenarios de disponibilidad, incluyendo préstamos de prueba. No es necesario para el recorrido básico.

### 6. Iniciar todo el sistema

```bash
docker compose -p gestion-de-biblioteca up -d
docker compose -p gestion-de-biblioteca ps
```

Deben aparecer cuatro servicios: `db`, `backend`, `frontend` y `bloqueos_worker`. El frontend puede tardar un momento en completar su compilación inicial.

## Accesos locales

| Recurso | Dirección |
|---|---|
| Aplicación Angular | http://localhost:4200 |
| Inicio de sesión | http://localhost:4200/login |
| API | http://localhost:8000/api/ |
| Administración de Django | http://localhost:8000/admin/ |
| MySQL desde una herramienta local | Host `127.0.0.1`, puerto `3306`, credenciales del `.env` |

La raíz `http://localhost:8000/` no tiene una página configurada y puede responder 404. El prefijo `/api/` también necesita una ruta concreta; no es una pantalla de inicio.

Las cuentas de demostración pertenecen al modelo de usuarios de la aplicación; no son cuentas del administrador de Django.

### Credenciales de demostración

Disponibles después de ejecutar `seed_auth_demo`:

| Correo | Rol |
|---|---|
| `kalt@bibliotech.com` | Bibliotecario |
| `esme@bibliotech.com` | Estudiante |
| `saul@bibliotech.com` | Docente |

Contraseña común: **`Biblioteca123*`**. Son credenciales públicas para demostración local.

## Guía breve de uso

### Bibliotecario

1. Inicia sesión con `kalt@bibliotech.com`.
2. En Usuarios, registra o consulta estudiantes y docentes.
3. En la gestión bibliográfica, administra libros, autores, categorías y ejemplares.
4. En Préstamos, selecciona al lector y un ejemplar disponible; revisa la elegibilidad y confirma.
5. En el historial de préstamos, consulta los registros y sus estados.
6. En Devoluciones, busca por código de inventario, ID de préstamo, nombre o correo del lector; selecciona el registro y confirma la recepción física.
7. En Sanciones, consulta multas y bloqueos y registra el pago total de una multa pendiente.

### Estudiante y docente

1. Inicia sesión con la cuenta correspondiente.
2. Consulta el catálogo y la disponibilidad de cada libro.
3. En Mis préstamos, revisa los préstamos activos e históricos.
4. En Mis sanciones, consulta multas, pagos y bloqueos propios.

### Recorrido de demostración

Con los usuarios y libros de demostración cargados, registra un préstamo para `esme@bibliotech.com` sobre una copia ACTIVA y libre. Después busca ese ejemplar en Devoluciones y confirma su recepción. Una devolución el mismo día no genera multa y deja de aparecer entre los préstamos activos. Para demostrar retrasos sin alterar datos reales, utiliza las pruebas automatizadas de devoluciones.

## Reglas principales

- Estudiantes y docentes tienen un límite inicial de cinco préstamos activos, configurado mediante los roles de demostración.
- Cada préstamo tiene un plazo de 30 días naturales.
- Un préstamo está activo mientras `fecha_devolucion` esté vacía, aunque esté vencido.
- Solo puede prestarse un ejemplar ACTIVO y sin préstamo activo.
- El stock total excluye ejemplares en BAJA; el disponible cuenta ejemplares ACTIVO sin préstamo activo.
- No se permite enviar a mantenimiento o dar de baja una copia con un préstamo activo.
- La multa es de **$5.00 MXN por día natural de retraso y por ejemplar**. Devolver el día límite no genera multa.
- Repetir una devolución no modifica su fecha ni duplica sanciones.
- La devolución conserva el estado operativo del ejemplar; no existe un estado operativo PRESTADO.
- Al cumplirse un mes calendario desde la fecha límite de un préstamo sin devolver, corresponde un bloqueo de 30 días naturales, con inicio y fin inclusivos.
- Las multas pendientes y los bloqueos vigentes impiden nuevos préstamos, pero permiten devoluciones.
- Pagar una multa no cancela otras deudas ni elimina bloqueos temporales.
- Una sanción ECONOMICA tiene monto positivo y fechas de bloqueo vacías. Una sanción BLOQUEO tiene monto y fecha de pago vacíos, y fechas de inicio y fin válidas.

## Arquitectura y organización

| Ubicación | Responsabilidad |
|---|---|
| `frontend/src/app/core/` | Autenticación, configuración y servicios comunes |
| `frontend/src/app/features/` | Pantallas, modelos y servicios HTTP por módulo |
| `frontend/src/app/layout/` | Estructura común y navegación por rol |
| `backend/biblioteca/presentation/` | Vistas HTTP, serializers y validación de entrada |
| `backend/biblioteca/services/` | Reglas y operaciones de negocio |
| `backend/biblioteca/repositories/` | Interfaces y acceso a datos mediante el ORM |
| `backend/biblioteca/models.py` | Entidades, relaciones y restricciones |
| `backend/biblioteca/migrations/` | Evolución reproducible del esquema y datos |
| `backend/biblioteca/management/commands/` | Datos de demostración y procesos de bloqueos |
| `backend/biblioteca/tests/` | Pruebas del backend |
| `backend/config/` | Configuración y rutas principales de Django |
| `Documentacion/` | Contratos, diagramas, reglas, prototipos y colecciones Postman |

Las peticiones recorren la presentación, los servicios de negocio y los repositorios. Las operaciones que requieren consistencia utilizan transacciones y bloqueos de registros en el backend.

## API y Postman

Los contratos detallados se encuentran en [Documentacion/API/README.md](Documentacion/API/README.md). El catálogo se documenta también en [Documentacion/API_catalogo.md](Documentacion/API_catalogo.md).

Formato JSON, fechas `YYYY-MM-DD` y autenticación:

```http
Authorization: Bearer <token>
```

Ejemplo de login en Postman, sin autenticación previa:

```http
POST http://localhost:8000/api/auth/login/
Content-Type: application/json
```

```json
{
  "email": "kalt@bibliotech.com",
  "password": "Biblioteca123*"
}
```

Utiliza el token devuelto para las operaciones protegidas. Las colecciones y el entorno local disponibles se encuentran en [Documentacion/Postman/](Documentacion/Postman/). Al configurar Postman, usa la URL completa del servidor, no solo `/api/...`.

| Operación | Endpoint principal |
|---|---|
| Autenticación | `/api/auth/login/`, `/api/auth/logout/`, `/api/auth/me/` |
| Usuarios y roles | `/api/usuarios/`, `/api/roles/` |
| Libros y ejemplares | `/api/libros/`, `/api/ejemplares/` |
| Autores y categorías | `/api/autores/`, `/api/categorias/` |
| Catálogo | `/api/catalogo/` |
| Consulta y registro de préstamos | `/api/prestamos/` |
| Búsqueda para devolución | `/api/devoluciones/prestamos-activos/?q=CODIGO` |
| Registro de devolución | `/api/prestamos/{prestamo_id}/devolucion/` |
| Sanciones y pago | `/api/sanciones/`, `/api/sanciones/{sancion_id}/pago/` |
| Consultas personales | `/api/prestamos/mios/`, `/api/sanciones/mias/` |

Consulta cada contrato para conocer los métodos HTTP, filtros y permisos. Las operaciones administrativas requieren rol bibliotecario.

## Bloqueos automáticos

`bloqueos_worker` ejecuta `vigilar_bloqueos` como proceso separado. Realiza una revisión al iniciar y después cada 3600 segundos. Si ocurre un fallo, reintenta en un intervalo de hasta 60 segundos.

```bash
docker compose -p gestion-de-biblioteca logs --tail=50 bloqueos_worker
docker compose -p gestion-de-biblioteca exec backend python manage.py aplicar_bloqueos
```

El segundo comando permite ejecutar una revisión manual. Las revisiones no deben duplicar ni reiniciar un bloqueo ya registrado.

## Pruebas y compilación

### Permisos para la base de pruebas

Django crea una base separada, normalmente `test_db_biblioteca` si el nombre principal es `db_biblioteca`. Si aparece un error 1044 al crearla, entra a MySQL:

```bash
docker compose -p gestion-de-biblioteca exec db mysql -u root -p
```

Introduce la contraseña root del `.env` y ejecuta, ajustando usuario y nombre si cambiaste la configuración:

```sql
GRANT ALL PRIVILEGES ON `test_db_biblioteca`.* TO 'biblioteca_user'@'%';
EXIT;
```

El permiso se concede únicamente sobre la base de pruebas. No es necesario crearla manualmente.

### Backend

```bash
docker compose -p gestion-de-biblioteca exec backend python manage.py check
docker compose -p gestion-de-biblioteca exec backend python manage.py test biblioteca.tests --verbosity 1
```

Para ejecutar únicamente las pruebas de devoluciones:

```bash
docker compose -p gestion-de-biblioteca exec backend python manage.py test biblioteca.tests.test_devoluciones --verbosity 2
```

Las pruebas de concurrencia requieren MySQL y bloqueos reales; no deben considerarse verificadas si el ejecutor las omite.

### Frontend

```bash
docker compose -p gestion-de-biblioteca exec frontend npm run build
docker compose -p gestion-de-biblioteca exec frontend npm test -- --watch=false
```

La compilación se escribe en `/app/dist/frontend-app` dentro del contenedor, correspondiente a `frontend/dist/frontend-app` en el equipo. Compilar no equivale a desplegar una versión de producción: Compose continúa ejecutando el servidor de desarrollo.

Este README documenta los comandos disponibles; los resultados deben registrarse sobre la versión que se esté evaluando, sin asumir que ejecuciones anteriores validan cambios nuevos.

## Operación cotidiana

```bash
# Iniciar los servicios ya preparados
docker compose -p gestion-de-biblioteca up -d

# Ver estado
docker compose -p gestion-de-biblioteca ps

# Revisar logs
docker compose -p gestion-de-biblioteca logs --tail=80 backend frontend bloqueos_worker

# Detener sin eliminar contenedores
docker compose -p gestion-de-biblioteca stop

# Retirar contenedores y red, conservando el volumen MySQL
docker compose -p gestion-de-biblioteca down
```

**No uses `docker compose down -v` si necesitas conservar la BD:** elimina el volumen de datos. La persistencia depende de mantener el mismo nombre de proyecto y su volumen `mysql_data`.

## Actualizar una copia existente

Primero confirma que no tienes cambios locales pendientes con `git status`. Guarda el trabajo propio antes de actualizar.

```bash
git switch dev
git pull --ff-only origin dev

docker compose -p gestion-de-biblioteca stop backend frontend bloqueos_worker
docker compose -p gestion-de-biblioteca up -d db
docker compose -p gestion-de-biblioteca build
docker compose -p gestion-de-biblioteca run --rm backend python manage.py migrate
```

Solo si la migración termina correctamente:

```bash
docker compose -p gestion-de-biblioteca up -d
docker compose -p gestion-de-biblioteca exec backend python manage.py showmigrations biblioteca
docker compose -p gestion-de-biblioteca ps
```

Si cambiaron `package.json` o `package-lock.json`, sincroniza también el volumen de dependencias del frontend y reinicia el servicio:

```bash
docker compose -p gestion-de-biblioteca exec frontend npm ci
docker compose -p gestion-de-biblioteca restart frontend
```

Reiniciar el worker es necesario para que cargue cambios de Python, ya que no utiliza recarga automática. Conserva tu `.env` y los datos existentes; no vuelvas a ejecutar los seeds de autenticación salvo que quieras restablecer las cuentas de prueba.

## Solución de problemas

| Síntoma | Comprobación |
|---|---|
| Credenciales incorrectas en una copia nueva | Ejecuta `seed_auth_demo` y usa una cuenta de demostración; las migraciones no crean esas cuentas automáticamente |
| No aparecen préstamos en Devoluciones | Registra primero un préstamo y busca el correo del lector o el código del ejemplar; solo se muestran préstamos activos |
| Error de conexión a MySQL al iniciar | Espera a que MySQL esté listo y consulta `docker compose -p gestion-de-biblioteca logs --tail=80 db` |
| Puerto ocupado | Revisa aplicaciones o contenedores que usen 3306, 8000 o 4200; si cambias puertos, ajusta también la URL de la API o CORS según corresponda |
| Sesión inválida después de repetir un seed | El seed de autenticación revoca tokens anteriores; vuelve a iniciar sesión |
| Error al leer un Dockerfile dentro de OneDrive | Clona en una carpeta local no sincronizada y copia únicamente la configuración local necesaria |
| Una migración rechaza datos existentes | Conserva los datos y revisa el error; no elimines el volumen para ocultar el problema |
| Error de CORS en Angular | Usa `http://localhost:4200`, que es el origen permitido por la configuración actual |

## Documentación del proyecto

- [Índice de contratos de API](Documentacion/API/README.md).
- [Contrato de devoluciones](Documentacion/API/devoluciones.md).
- [Contrato de préstamos](Documentacion/API/prestamos.md).
- [Contrato de sanciones y pagos](Documentacion/API/sanciones.md).
- [Consultas personales de préstamos](Documentacion/API/mis_prestamos.md).
- [Consultas personales de sanciones](Documentacion/API/mis_sanciones.md).
- [Colecciones Postman](Documentacion/Postman/).
- [Diagramas de flujo](Documentacion/DiagramasDeFlujo/).
- [Diagramas de secuencia](Documentacion/DiagramasDeSecuencia/).
- [Diagramas de navegación](Documentacion/DiagramasDeNavegacion/).
- [Prototipos de interfaz](Documentacion/PrototipoUI/).

Los diagramas de arquitectura, casos de uso, entidad-relación y las reglas de negocio también están disponibles en `Documentacion/`.

## Alcance del entorno

La configuración incluida está orientada al desarrollo local y la demostración académica: utiliza servidores de desarrollo, `DEBUG=True`, credenciales de prueba y una clave de Django fija. Un despliegue público requiere configurar secretos, hosts, HTTPS, CORS, servidores de producción y respaldos antes de exponer el sistema.

---

README preparado mediante revisión del código de la rama `dev`, referencia `bf84bd9ff2c651c9c19338c608868c9f26785bb8`, el 28 de octubre de 2026. Las rutas relativas de este documento están pensadas para un archivo `README.md` en la raíz del repositorio.
