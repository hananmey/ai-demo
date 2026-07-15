FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY ui_app/pyproject.toml ui_app/pyproject.toml
COPY ui_app/src ui_app/src
RUN uv sync --frozen --no-dev --package ui-app

EXPOSE 8501
CMD ["uv", "run", "--frozen", "--no-dev", "--package", "ui-app", "streamlit", "run", "ui_app/src/ui_app/app.py", "--server.address=0.0.0.0", "--server.port=8501"]
