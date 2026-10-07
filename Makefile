.PHONY: help install dev up down build test lint format migrate migration logs clean evaluate-ai

help: ## Show this help message
	@echo TaskMate AI - Developer Commands
	@echo ================================
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ---- Setup ----

install: ## Install all dependencies locally
	cd apps/api && pip install -e ".[dev]"
	cd apps/web && npm install

# ---- Docker ----

up: ## Start all services with Docker Compose
	docker compose up --build -d

down: ## Stop all services
	docker compose down

build: ## Build all Docker images
	docker compose build

dev: ## Start services in development mode (attached)
	docker compose up --build

logs: ## Tail service logs
	docker compose logs -f

clean: ## Remove all containers, volumes, and orphans
	docker compose down -v --remove-orphans

# ---- Database ----

migrate: ## Run database migrations to latest
	cd apps/api && alembic upgrade head

migration: ## Create a new migration (usage: make migration msg="description")
	cd apps/api && alembic revision --autogenerate -m "$(msg)"

# ---- Testing ----

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	cd apps/api && pytest -v

test-frontend: ## Run frontend tests
	cd apps/web && npm test -- --passWithNoTests

# ---- Linting ----

lint: lint-backend lint-frontend ## Run all linters

lint-backend: ## Lint backend code
	cd apps/api && ruff check .
	cd apps/api && ruff format --check .

lint-frontend: ## Lint frontend code
	cd apps/web && npm run lint
	cd apps/web && npx prettier --check .

# ---- Formatting ----

format: format-backend format-frontend ## Auto-format all code

format-backend: ## Format backend code
	cd apps/api && ruff format .
	cd apps/api && ruff check --fix .

format-frontend: ## Format frontend code
	cd apps/web && npx prettier --write .

# ---- AI Evaluation ----

evaluate-ai: ## Run AI evaluation suite (requires AI_API_KEY)
	cd apps/api && python -m evaluation.evaluate

evaluate-agent: ## Run Agent-specific tests/evaluation
	cd apps/api && pytest tests/test_agent/ -v
