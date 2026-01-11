# Makefile for common development tasks

.PHONY: help install dev lint format check test docker-build docker-up docker-down clean

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv pip install -e .

dev: ## Install dev dependencies
	uv pip install -e ".[dev]"
	pre-commit install

lint: ## Run ruff linter
	ruff check .

format: ## Format code with ruff
	ruff format .

check: ## Run linter and formatter checks
	ruff check .
	ruff format --check .

fix: ## Auto-fix linting issues and format code
	ruff check --fix .
	ruff format .

sync: ## Sync calendars
	python sync.py

server: ## Start the server
	python run_server.py

docker-build: ## Build Docker image
	docker build -t scouting-agenda:latest .

docker-up: ## Start Docker containers
	docker-compose up -d

docker-down: ## Stop Docker containers
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

clean: ## Clean generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.tmp" -delete
	rm -rf .ruff_cache

test-build: ## Test Docker build
	docker build -t scouting-agenda:test .
