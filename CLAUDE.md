# HAL Project Guidelines for Claude

## Setup and Environment
- Python 3.10 required
- Use `pipenv install` to set up environment
- Use `pipenv shell` to activate environment
- Use `docker-compose up` to run the application with PostgreSQL, Nginx, Redis, Celery and Celery Beat
- Access the application at http://localhost
- Background tasks are processed with Celery
- Scheduled tasks are managed with Celery Beat

## Development Commands
- Start development server: `python manage.py runserver`
- Run tests: `python -m pytest`
- Run single test: `python -m pytest path/to/test_file.py::test_function`
- Lint code: `python -m flake8`
- Type check: `python -m mypy .`
- Create migrations: `python manage.py makemigrations`
- Apply migrations: `python manage.py migrate`
- Create superuser: `python manage.py createsuperuser`

## Code Style Guidelines
- Follow PEP 8 for formatting
- Organize imports: standard library > third-party > local
- Use type hints for all function parameters and return values
- Use snake_case for functions/variables, CamelCase for classes
- Document functions with docstrings (Google style)
- Handle errors explicitly with try/except blocks
- Log errors rather than printing
- Models should have descriptive string representations
- Use Django's built-in tools for security (never store secrets in code)
- Keep views simple, move complex logic to services or managers