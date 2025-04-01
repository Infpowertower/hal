#!/bin/bash

# Start Redis and PostgreSQL in docker
echo "Starting Redis and PostgreSQL..."
docker-compose -f docker-compose.dev.yml up -d

# Load environment variables
export $(grep -v '^#' .env.dev | xargs)

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Run database migrations
echo "Running database migrations..."
pipenv run python manage.py migrate

# Create a new terminal for Celery worker
echo "Starting Celery worker..."
tmux new-session -d -s celery "pipenv run celery -A hal worker -l INFO"

# Create a new terminal for Celery beat
echo "Starting Celery beat..."
tmux new-session -d -s celery-beat "pipenv run celery -A hal beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler"

# Start Django development server
echo "Starting Django development server..."
pipenv run python manage.py runserver 0.0.0.0:8000