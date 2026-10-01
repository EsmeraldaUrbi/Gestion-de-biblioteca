# Gestión-de-biblioteca
Sistema de gestión de biblioteca con arquitectura en capas (N-Tier) para administrar ejemplares, usuarios, préstamos, devoluciones, sanciones y catálogo.

## Requisitos
- Docker y Docker Compose instalados.

## Configuración inicial
1. Duplica el archivo `.env.example`, renómbralo a `.env` y configura tus contraseñas locales.
2. Levanta el entorno con el comando:
   `docker compose up -d --build`
3. Ejecuta las migraciones de la base de datos:
   `docker compose exec backend python manage.py migrate`

## Accesos
- **Frontend (Angular):** http://localhost:4200
- **Backend (Django):** http://localhost:8000
