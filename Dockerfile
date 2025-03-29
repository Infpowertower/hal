FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=hal.settings

# Set work directory
WORKDIR /app

# Install system dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --upgrade pip

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install pipenv, generate requirements.txt, and install dependencies
RUN pip install pipenv && \
    pipenv lock && \
    pipenv install --deploy --system

# Copy project
COPY . .

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/media /app/static

# Expose the port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "hal.wsgi:application", "--bind", "0.0.0.0:8000"]