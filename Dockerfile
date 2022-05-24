FROM python:3.10-slim

WORKDIR /app

RUN pip install poetry --no-cache
RUN poetry config virtualenvs.create false

COPY [ "poetry.toml", "poetry.lock", "pyproject.toml", "./" ]

RUN poetry install --no-dev

COPY src .

ARG build
ENV BUILD_SHA=$build

CMD [ "python", "-m", "horoscopebot" ]
