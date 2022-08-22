.PHONY: check coding_standards test

check: coding_standards test

coding_standards:
	poetry run black src/
	poetry run flake8 --exit-zero src/
	poetry run mypy src/

test:
	poetry run pytest src/

migrate:
	docker run --platform=linux/amd64 --rm --env FLYWAY_URL=jdbc:sqlite:/data/usages.db -v ${PWD}/:/data/ ghcr.io/preparingforexams/rate-limiter-migrations:1.0.2 migrate
