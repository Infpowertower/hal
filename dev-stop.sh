#!/bin/bash

# Stop Django development server and Celery processes
echo "Stopping Django development server and Celery processes..."
pkill -f "python manage.py runserver" || true
tmux kill-session -t celery 2>/dev/null || true
tmux kill-session -t celery-beat 2>/dev/null || true

# Stop Redis and PostgreSQL containers
echo "Stopping Redis and PostgreSQL containers..."
docker-compose -f docker-compose.dev.yml down

echo "Development environment stopped."