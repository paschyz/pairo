.PHONY: dev test lint format migrate

dev:
	@if [ -f .env ]; then set -a && . ./.env && set +a; fi; \
	uv run uvicorn pairo.app:app --reload --host 0.0.0.0 --port 8000 & \
	npx smee-client --url "$${SMEE_URL}" --target http://localhost:8000/webhook & \
	wait

test:
	uv run --extra dev pytest --cov=pairo --cov-report=term-missing

lint:
	uv run --extra dev ruff check src tests
	uv run --extra dev ruff format --check src tests
	uv run --extra dev mypy src

format:
	uv run --extra dev ruff format src tests
	uv run --extra dev ruff check --fix src tests

migrate:
	uv run alembic upgrade head
