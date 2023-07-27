.PHONY: check
check: lint test

.PHONY: lint
lint:
	poetry run black src/
	poetry run isort src/
	poetry run mypy src/

.PHONY: test
test:
	poetry run pytest src/

.PHONY: migrate
migrate:
	docker run --platform=linux/amd64 --rm --env FLYWAY_URL=jdbc:sqlite:/data/usages.db -v ${PWD}/:/data/ ghcr.io/preparingforexams/rate-limiter-migrations:VERSION migrate
