# HAL Django Project

A Django project with PostgreSQL 14 database using Docker.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. Clone the repository

2. Build and start the application:

```bash
docker-compose down -v  # Remove previous containers and volumes if any
docker-compose up --build  # Build and start the containers
```

3. The application will be available at http://localhost
4. The admin interface will be available at http://localhost/admin
5. Nginx serves static files directly for improved performance
6. Celery workers process background tasks
7. Celery Beat schedules periodic tasks

## Creating an Admin User

```bash
docker-compose exec web python manage.py createsuperuser
```

## Troubleshooting

If you encounter issues with the Docker build or database connection:

1. Try rebuilding without cache:
```bash
docker-compose build --no-cache
docker-compose up
```

2. Check container logs:
```bash
docker-compose logs web
docker-compose logs db
```

3. Make sure PostgreSQL is running properly:
```bash
docker-compose exec db psql -U postgres -c "SELECT 1"
```

## Development

To run Django management commands:

```bash
docker-compose exec web python manage.py [command]
```

Example commands:
- `makemigrations` - Create new database migrations
- `migrate` - Apply database migrations
- `shell` - Open Django shell
- `createsuperuser` - Create a superuser

## Project Structure

- `hal/` - Django project settings
- `core/` - Main application
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, etc.)
- `nginx/` - Nginx configuration

## Asynchronous Tasks with Celery

The project includes Celery for handling asynchronous and scheduled tasks:

1. **Celery Worker**:
   - Processes asynchronous tasks
   - View logs: `docker-compose logs celery`
   - Test task execution: `docker-compose exec web python -c "from core.tasks import sample_task; sample_task.delay('test')"`

2. **Celery Beat**:
   - Manages periodic task scheduling
   - View logs: `docker-compose logs celery-beat`
   - Schedule tasks via Django admin: http://localhost/admin/django_celery_beat/

3. **Redis**:
   - Acts as the message broker for Celery
   - Handles task queue management

## Environment Variables

The application uses the following environment variables:

- `DEBUG` - Set to 1 to enable debug mode
- `SECRET_KEY` - Django secret key
- `POSTGRES_DB` - PostgreSQL database name
- `POSTGRES_USER` - PostgreSQL username
- `POSTGRES_PASSWORD` - PostgreSQL password
- `POSTGRES_HOST` - PostgreSQL host
- `POSTGRES_PORT` - PostgreSQL port
- `CELERY_BROKER_URL` - URL for the Celery broker (Redis)
- `CELERY_RESULT_BACKEND` - Backend for storing task results

These are configured in the docker-compose.yml file.