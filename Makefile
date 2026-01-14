.PHONY: help install dev-install test lint format type-check security-check clean

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -e .

dev-install:  ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

test:  ## Run tests
	pytest tests/ -v --cov=turbo --cov-report=term-missing

test-unit:  ## Run unit tests only
	pytest tests/unit/ -v

test-integration:  ## Run integration tests only
	pytest tests/integration/ -v

test-e2e:  ## Run end-to-end tests only
	pytest tests/e2e/ -v

lint:  ## Run linting
	ruff check .

format:  ## Format code
	black .
	ruff check --fix .

type-check:  ## Run type checking
	mypy turbo/

security-check:  ## Run security checks
	bandit -r turbo/ -c pyproject.toml

check: format lint type-check security-check test  ## Run all quality checks

clean:  ## Clean cache files
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .mypy_cache .pytest_cache .coverage htmlcov dist build

dev-server:  ## Start development server
	uvicorn turbo.main:app --reload --host 127.0.0.1 --port 8000

web-server:  ## Start web UI
	streamlit run turbo/web/app/main.py --server.port 8501

db-reset:  ## Reset development database
	turbo db reset --confirm

db-migrate:  ## Run database migrations
	turbo db migrate

watch-tests:  ## Run tests in watch mode
	pytest-watch -- tests/ -v