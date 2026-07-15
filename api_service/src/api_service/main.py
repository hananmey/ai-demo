import os

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

AGNO_SERVICE_URL = os.environ.get(
    "AGNO_SERVICE_URL",
    "http://agno-service.ai-demo.svc.cluster.local:8080",
)

app = FastAPI(title="api-service")


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(f"{AGNO_SERVICE_URL}/query", json={"question": request.question})
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"agno-service error: {exc}") from exc
    return ChatResponse(answer=resp.json()["answer"])


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


def run() -> None:
    import uvicorn

    uvicorn.run("api_service.main:app", host="0.0.0.0", port=8000)
