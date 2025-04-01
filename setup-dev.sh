#!/bin/bash

# Create a new netmap app
echo "Creating netmap app..."
pipenv run python manage.py startapp netmap

# Install required packages
echo "Installing additional packages..."
pipenv install ipaddress django-rest-framework ipython pytest-django

# Install all deps in case we missed any
pipenv install
pipenv install --dev

echo "Development environment has been set up."
echo "To start the environment, run: ./dev.sh"