from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from pydantic import BaseModel

from agno_service.agent import build_agent

_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    _state["agent"] = await build_agent()
    yield


app = FastAPI(title="agno-service", lifespan=lifespan)


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    response = await _state["agent"].arun(request.question)
    return QueryResponse(answer=response.content)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


def run() -> None:
    import uvicorn

    uvicorn.run("agno_service.main:app", host="0.0.0.0", port=8080)
