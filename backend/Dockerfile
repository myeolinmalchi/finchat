#FROM python:3.12.3 AS build
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS build

WORKDIR /app

COPY . /app

RUN apk add --no-cache cargo rust
RUN uv sync --frozen --no-cache

EXPOSE 8899

CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--port", "8899", "--host", "0.0.0.0"]
