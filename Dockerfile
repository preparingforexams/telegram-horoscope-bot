FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry==1.4.1 --no-cache
RUN poetry config virtualenvs.create false

COPY [ "poetry.toml", "poetry.lock", "pyproject.toml", "./" ]

# We don't want the tests
COPY src/horoscopebot ./src/horoscopebot

RUN poetry install --no-dev

ARG build
ENV BUILD_SHA=$build

CMD [ "python", "-m", "horoscopebot" ]
