.PHONY: install run migrate revision test lint up down

install:
	pip install -e ".[dev]"

run:
	uvicorn app.main:app --reload

revision:
	alembic revision --autogenerate -m "$(m)"

migrate:
	alembic upgrade head

test:
	pytest -v

lint:
	ruff check app tests && ruff format --check app tests && mypy app

up:
	docker compose up --build -d

down:
	docker compose down -v
