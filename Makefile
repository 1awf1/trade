.PHONY: help install dev test clean docker-build docker-up docker-down logs migrate startup check-deps

help:
	@echo "Kripto Para Analiz Sistemi - Makefile Commands"
	@echo ""
	@echo "install       - Install dependencies"
	@echo "dev           - Run development server"
	@echo "startup       - Run startup checks and migrations"
	@echo "migrate       - Run database migrations"
	@echo "check-deps    - Check system dependencies"
	@echo "test          - Run tests"
	@echo "test-cov      - Run tests with coverage"
	@echo "test-pbt      - Run property-based tests only"
	@echo "clean         - Clean up generated files"
	@echo "docker-build  - Build Docker images"
	@echo "docker-up     - Start Docker containers (production)"
	@echo "docker-up-dev - Start Docker containers (development)"
	@echo "docker-down   - Stop Docker containers"
	@echo "docker-restart- Restart Docker containers"
	@echo "logs          - Show Docker logs"
	@echo "celery-worker - Start Celery worker"
	@echo "celery-beat   - Start Celery beat"
	@echo "lint          - Run code linting"
	@echo "format        - Format code with black"

install:
	pip install -r requirements.txt

dev:
	python startup.py && uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

startup:
	python startup.py

migrate:
	python migrate.py

check-deps:
	python -c "from utils.dependencies import startup_checks; startup_checks()"

test:
	pytest

test-cov:
	pytest --cov=. --cov-report=html --cov-report=term

test-pbt:
	pytest tests/ -v -k "property"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".hypothesis" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-up-dev:
	docker-compose -f docker-compose.dev.yml up -d

docker-down:
	docker-compose down

docker-down-dev:
	docker-compose -f docker-compose.dev.yml down

docker-restart:
	docker-compose restart

logs:
	docker-compose logs -f

celery-worker:
	celery -A utils.celery_app worker --loglevel=info

celery-beat:
	celery -A utils.celery_app beat --loglevel=info

lint:
	@echo "Running flake8..."
	@flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
	@flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics || true

format:
	@echo "Formatting code with black..."
	@black . --line-length=120 || echo "black not installed, skipping"

shell:
	python -i -c "from utils.config import settings; from models.database import engine; print('Settings and engine loaded')"
