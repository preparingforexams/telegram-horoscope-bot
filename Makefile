.PHONY: check
check: lint test

.PHONY: lint
lint:
	poetry run ruff format src/
	poetry run ruff check --fix --show-fixes src/
	poetry run mypy src/

.PHONY: test
test:
	poetry run pytest src/

.PHONY: migrate
migrate:
	docker run --platform=linux/amd64 --rm --env FLYWAY_URL=jdbc:sqlite:/data/usages.db -v ${PWD}/:/data/ ghcr.io/preparingforexams/rate-limiter-migrations-sqlite:VERSION migrate
