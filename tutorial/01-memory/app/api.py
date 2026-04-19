"""Minimal FastAPI inspector for the memory demo.

Exposes a few read-only endpoints so you can watch what the memory layers hold
without having to poke at Redis or ChromaDB directly.

    GET  /health                              → {"ok": true}
    GET  /memory/{user_id}/{char_id}/recent   → last N raw messages from Redis
    GET  /memory/{user_id}/{char_id}/summary  → latest summary (Redis fast-path → Chroma)
    POST /memory/{user_id}/{char_id}/clear    → wipe both layers for that conversation

No auth, no rate limits — this is a tutorial. Don't expose it publicly.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import memory

app = FastAPI(title="HoneyChat tutorial 01-memory", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/memory/{user_id}/{char_id}/recent")
async def recent(user_id: int, char_id: str, limit: int = 20) -> dict:
    items = await memory.get_recent(user_id, char_id, limit=limit)
    return {"count": len(items), "items": items}


@app.get("/memory/{user_id}/{char_id}/summary")
async def summary(user_id: int, char_id: str) -> dict:
    s = await memory.get_latest_summary(user_id, char_id)
    return {"summary": s}


@app.post("/memory/{user_id}/{char_id}/clear")
async def clear(user_id: int, char_id: str) -> dict:
    await memory.clear_conversation(user_id, char_id)
    return {"ok": True}
