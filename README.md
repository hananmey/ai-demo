# Project Context & Coding Guidelines

Guidance for Claude Code when working in this repository.

## Project Overview

A natural-language analytics app over ClickHouse, built as a set of services on Kubernetes:

UI → FastAPI → Agno agent middleware (K8s deployment) → ClickHouse MCP server → ClickHouse (NYC taxi rides)

- Data store: ClickHouse (columnar OLAP DB) on GKE — already installed and running, single-node demo deployment (StatefulSet, no operator, namespace `clickhouse`). Do not re-deploy or re-create it; treat it as an existing dependency the other services connect to.
- Datasource: NYC taxi trip data (`nyc_taxi.trips_small` — loaded directly from the public GCS dataset via ClickHouse's `gcs()` table function, no local CSV/ETL step needed)
- Tool access layer: ClickHouse MCP server (`mcp-clickhouse`) — Agno's tool calls go through MCP rather than a direct `clickhouse-driver` connection. It runs as a stdio subprocess spawned in-process by `agno_service` (via Agno's `MCPTools`), not as a separate deployment — see Service Architecture.
- Agent layer: Agno — Python agent framework, deployed as its own middleware service inside the cluster (not run locally)
- API layer: FastAPI — sits between the UI and the Agno service, exposes the chat/query endpoints the UI calls
- UI: calls FastAPI only; never talks to Agno, MCP, or ClickHouse directly
- Containerization: Agno middleware, FastAPI gateway, and UI are each built as separate Docker images and deployed to the cluster as their own Deployments/Services. ClickHouse is the one component that is not rebuilt/redeployed by this repo — it's a pre-existing dependency. See `docker/` for Dockerfiles and `k8s/` for manifests.

## Tech Stack

- Python 3.11+
- ClickHouse (queried exclusively via ClickHouse MCP from Agno — no direct `clickhouse-driver` calls from agent tools)
- Agno (agent orchestration, tool calling) — packaged as a standalone K8s deployment
- FastAPI (UI-facing API, wraps the Agno service)
- Kubernetes (GKE) — runtime for ClickHouse, MCP server, Agno middleware, and FastAPI
- kubectl alias: `k`

## Service Architecture

| Service | Runs where | Talks to | Notes |
|---|---|---|---|
| UI | browser / frontend host | FastAPI only | no direct backend/data access |
| FastAPI | K8s deployment | Agno middleware | thin layer: auth, request shaping, streaming responses back to UI |
| Agno middleware | K8s deployment | ClickHouse MCP server | holds agent/tool definitions, prompt logic |
| ClickHouse MCP server | stdio subprocess inside the agno-service pod (`mcp-clickhouse`, spawned via `uv run --frozen --package agno-service mcp-clickhouse`) | ClickHouse (HTTP interface, port 8123) | not its own Deployment/Service — no `clickhouse-mcp` manifest exists; exposes query/schema tools over MCP to the Agno process that spawned it |
| ClickHouse | K8s StatefulSet | — | data store, namespace `clickhouse` |

Each hop should use in-cluster DNS service names (`*.namespace.svc.cluster.local`), not hardcoded IPs or `localhost` — `localhost` only applies during local dev via `kubectl port-forward`.

## Running Locally (uv)

`agno_service/`, `api_service/`, and `ui_app/` are members of a single `uv` workspace rooted at the repo root (`[tool.uv.workspace]` in the root `pyproject.toml`). There is one shared `.venv` and one `uv.lock` at the repo root — this is also why a single IDE interpreter (the root `.venv`) covers all three services. Each service still has its own `pyproject.toml` declaring its own dependencies.

- Install/sync everything (all three services + root): `uv sync --all-packages` (run from the repo root)
- Sync just one service: `uv sync --package agno-service` (package names use hyphens: `agno-service`, `api-service`, `ui-app`)
- Add a dependency to a service: `cd <service> && uv add <package>` — this updates that service's `pyproject.toml` and re-locks the shared root `uv.lock`. Always run `uv add`/`uv remove` from inside the target service's directory, not the repo root, or it'll modify the wrong project.
- Run agno_service (port 8080): `cd agno_service && uv run uvicorn agno_service.main:app --reload --port 8080`
- Run api_service (port 8000): `cd api_service && uv run uvicorn api_service.main:app --reload --port 8000`
- Run ui_app (port 8501): `cd ui_app && uv run streamlit run src/ui_app/app.py`

`uv run` auto-detects which workspace member you're in from the cwd, so the commands above work unchanged whether run from a service directory or (with `--package <name>`) from the repo root — the latter is how the Dockerfiles invoke it, since the MCP server is not its own deployment.

For local end-to-end runs, `kubectl port-forward -n clickhouse svc/clickhouse 8123:8123` for ClickHouse and point `AGNO_SERVICE_URL`/`API_SERVICE_URL` env vars at `localhost` instead of the in-cluster DNS names. Port 8123 (not 9000) because `mcp-clickhouse` connects over ClickHouse's HTTP interface via `clickhouse-connect`, not the native protocol.

Dockerfiles (`docker/*.Dockerfile`) build from the workspace root: they `COPY` the root `pyproject.toml`/`uv.lock` plus only that one service's `pyproject.toml`/`src`, then run `uv sync --frozen --no-dev --package <name>`. This keeps each image lean (e.g. the ui_app image never pulls in agno/fastapi) without needing the other services' source present in the build context.

## ClickHouse MCP

- Agno tools call the ClickHouse MCP server, not `clickhouse_driver` directly. Do not reintroduce direct driver calls into Agno tool code — MCP is the single access path from the agent layer.
- The MCP server is `mcp-clickhouse` (a dependency of `agno_service`), spawned as a stdio subprocess by `agno_service/src/agno_service/agent.py` via `MCPTools(command="uv run --frozen --package agno-service mcp-clickhouse", ...)`. It is not a separate Deployment/Service — there is no `clickhouse-mcp` k8s manifest.
- `mcp-clickhouse` connects to ClickHouse over the HTTP interface (`clickhouse-connect`), configured via `CLICKHOUSE_HOST`/`CLICKHOUSE_PORT`/`CLICKHOUSE_USER`/`CLICKHOUSE_PASSWORD`/`CLICKHOUSE_SECURE` env vars (see `agent.py`) — port 8123, not the native protocol port 9000.
- In-cluster: `CLICKHOUSE_HOST=clickhouse.clickhouse.svc.cluster.local`, `CLICKHOUSE_PORT=8123` (set in `k8s/agno-service.yaml`).
- Local dev: port-forward ClickHouse's HTTP port (`kubectl port-forward -n clickhouse svc/clickhouse 8123:8123`) and set `CLICKHOUSE_HOST=localhost` `CLICKHOUSE_PORT=8123` when running `agno_service`.
- Auth: default user, no password (demo only — do not carry this into anything internet-facing).

## UI Requirements

- A single prompt input where the user types a natural-language question.
- A submit action that sends the question to the FastAPI gateway (not to Agno, MCP, or ClickHouse directly — see Service Architecture).
- A textbox that displays the returned answer once the backend responds.
- No direct data access, query building, or ClickHouse/Agno logic in the UI layer — it is purely input (question) → output (answer) via FastAPI.