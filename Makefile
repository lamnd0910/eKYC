.PHONY: install lint format test api

install:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check . --fix
	uv run ruff format .

test:
	uv run pytest -q

api:
	uv run uvicorn ekyc.api.main:app --host 0.0.0.0 --port 8000 --reload
