.PHONY: infra api web test lint format
infra:
	docker compose up -d postgres redis
api:
	cd apps/api && uvicorn app.main:app --reload --port 8000
web:
	cd apps/web && npm run dev
test:
	cd apps/api && pytest
lint:
	cd apps/api && python -m ruff check .
format:
	cd apps/api && python -m ruff format .
