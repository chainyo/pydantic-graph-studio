.PHONY: fmt lint typecheck test check

fmt:
	uv run ruff format

lint:
	uv run ruff check --fix .

typecheck:
	uv run ty check .

test:
	uv run pytest tests

check: fmt lint typecheck test
