FROM python:3.10-slim

WORKDIR /app

ENV POETRY_PYPI_VERSION=1.2.0
RUN pip install poetry==$POETRY_PYPI_VERSION --no-cache
RUN poetry config virtualenvs.create false

COPY [ "poetry.toml", "poetry.lock", "pyproject.toml", "./" ]

# We don't want the tests
COPY src/horoscopebot ./src/horoscopebot

RUN poetry install --no-dev

ARG build
ENV BUILD_SHA=$build

CMD [ "python", "-m", "horoscopebot" ]
