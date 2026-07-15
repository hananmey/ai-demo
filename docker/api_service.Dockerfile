FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY api_service/pyproject.toml api_service/pyproject.toml
COPY api_service/src api_service/src
RUN uv sync --frozen --no-dev --package api-service

EXPOSE 8000
CMD ["uv", "run", "--frozen", "--no-dev", "--package", "api-service", "uvicorn", "api_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
