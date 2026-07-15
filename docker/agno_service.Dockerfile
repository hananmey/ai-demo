FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY agno_service/pyproject.toml agno_service/pyproject.toml
COPY agno_service/src agno_service/src
RUN uv sync --frozen --no-dev --package agno-service

EXPOSE 8080
CMD ["uv", "run", "--frozen", "--no-dev", "--package", "agno-service", "uvicorn", "agno_service.main:app", "--host", "0.0.0.0", "--port", "8080"]
