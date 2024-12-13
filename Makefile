.PHONY: check
check: lint test

.PHONY: lint
lint:
	uv run ruff format src/
	uv run ruff check --fix --show-fixes src/
	uv run mypy src/

.PHONY: test
test:
	uv run pytest src/

.PHONY: migrate
migrate:
	docker run --platform=linux/amd64 --rm --env FLYWAY_URL=jdbc:sqlite:/data/usages.db -v ${PWD}/:/data/ ghcr.io/preparingforexams/rate-limiter-migrations-sqlite:VERSION migrate
