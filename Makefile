.PHONY: help setup up down logs contracts generate lint typecheck test-unit test-integration test-web migrate e2e check

help:
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  %-18s %s\n", $$1, $$2}'

setup: ## Install Python and Node dependencies
	uv sync --all-packages
	cd apps/web && npm ci
	cd tests/e2e && npm ci

up: ## Build and start the full local stack
	docker compose up --build --detach --wait

down: ## Stop the stack (data volumes are kept)
	docker compose down

logs: ## Follow stack logs
	docker compose logs -f

contracts: ## Validate Research Core contracts and generated bindings
	uv run python scripts/contracts/check_contracts.py
	uv run python scripts/contracts/generate_bindings.py --check

generate: ## Regenerate Python/TypeScript bindings from the contracts
	uv run python scripts/contracts/generate_bindings.py

lint: ## Lint backend and frontend
	uv run ruff format --check .
	uv run ruff check .
	cd apps/web && npm run lint

typecheck: ## Type-check backend and frontend
	uv run mypy services/api/research_api services/worker/research_worker scripts/contracts
	cd apps/web && npm run typecheck

test-unit: ## Backend unit tests (no services needed)
	uv run pytest services/api/tests/unit

test-integration: ## Backend + worker integration tests (needs DATABASE_URL, e.g. after `make up`)
	cd services/api && uv run pytest tests/integration
	cd services/worker && uv run pytest

test-web: ## Frontend unit tests
	cd apps/web && npm test

migrate: ## Apply migrations to DATABASE_URL
	cd services/api && uv run alembic upgrade head

e2e: ## Playwright smoke tests against the running stack
	cd tests/e2e && npx playwright test

check: contracts lint typecheck test-unit test-web ## Fast checks to run before pushing
