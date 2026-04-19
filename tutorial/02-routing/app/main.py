"""FastAPI wrapper exposing the fallback-chain completion as an HTTP endpoint.

    POST /complete   body: {"messages": [...], "primary": "optional-model-id"}
    GET  /health

Useful for integration testing and for sending ad-hoc turns through the chain
from curl / HTTPie while you explore different model choices.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.router import AllModelsFailedError, complete

app = FastAPI(title="HoneyChat tutorial 02-routing", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Turn(BaseModel):
    role: str
    content: str


class CompleteRequest(BaseModel):
    messages: list[Turn]
    primary: str | None = None


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.post("/complete")
async def do_complete(req: CompleteRequest) -> dict:
    msgs = [{"role": t.role, "content": t.content} for t in req.messages]
    try:
        result = await complete(msgs, primary=req.primary)
    except AllModelsFailedError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "content": result.content,
        "model": result.model,
        "attempt": result.attempt,
        "used_fallback": result.attempt > 0,
    }
