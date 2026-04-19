"""Dual-layer memory: Redis hot buffer + ChromaDB semantic summaries.

Minimal public-safe version. Shows the architectural pattern used in HoneyChat
without the tier-specific token budgeting, auto-summarization background task,
or web-session bridging from the production code.

Reader clones this repo, runs `docker compose up`, and chats with the bot via
Telegram. Recent messages stay in Redis; summaries of older chunks live in
ChromaDB. On every new turn, three reads happen in parallel.
"""
from __future__ import annotations

import asyncio
import json
import os
import threading
from datetime import datetime, timezone
from typing import Any

import chromadb
import redis.asyncio as aioredis
from chromadb.config import Settings as ChromaSettings

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CHROMA_HOST = os.getenv("CHROMA_HOST", "chromadb")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

# Knobs — intentionally simple. Tune per use case.
HOT_BUFFER_SIZE = int(os.getenv("HOT_BUFFER_SIZE", "20"))
HOT_BUFFER_TTL_DAYS = int(os.getenv("HOT_BUFFER_TTL_DAYS", "7"))
SUMMARY_TOPK = int(os.getenv("SUMMARY_TOPK", "3"))
SUMMARIZE_EVERY_TURNS = int(os.getenv("SUMMARIZE_EVERY_TURNS", "10"))

_redis: aioredis.Redis | None = None
_chroma: Any = None
_chroma_lock = threading.Lock()


def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis


def get_chroma() -> Any:
    global _chroma
    if _chroma is not None:
        return _chroma
    with _chroma_lock:
        if _chroma is not None:
            return _chroma
        _chroma = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _chroma


def _chat_key(user_id: int, char_id: str) -> str:
    return f"chat:{user_id}:{char_id}:messages"


def _summary_key(user_id: int, char_id: str) -> str:
    return f"summary:{user_id}:{char_id}"


def _collection_name(user_id: int, char_id: str) -> str:
    return f"mem_{user_id}_{char_id}"


# ─── Hot layer (Redis) ──────────────────────────────────────────────────────

async def save_message(user_id: int, char_id: str, role: str, content: str) -> None:
    """Push a message to the per-conversation Redis list, bounded + TTL'd."""
    r = get_redis()
    key = _chat_key(user_id, char_id)
    msg = json.dumps({
        "role": role,
        "content": content,
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    pipe = r.pipeline()
    pipe.rpush(key, msg)
    pipe.ltrim(key, -HOT_BUFFER_SIZE, -1)
    pipe.expire(key, 86400 * HOT_BUFFER_TTL_DAYS)
    await pipe.execute()


async def get_recent(user_id: int, char_id: str, limit: int | None = None) -> list[dict]:
    """Return the last N messages from Redis as dicts with role/content."""
    r = get_redis()
    key = _chat_key(user_id, char_id)
    take = limit or HOT_BUFFER_SIZE
    raw = await r.lrange(key, -take, -1)
    return [json.loads(m) for m in raw]


async def clear_conversation(user_id: int, char_id: str) -> None:
    """Wipe Redis + ChromaDB state for one conversation. Idempotent."""
    r = get_redis()
    await r.delete(_chat_key(user_id, char_id), _summary_key(user_id, char_id))
    try:
        chroma = get_chroma()
        await asyncio.to_thread(chroma.delete_collection, _collection_name(user_id, char_id))
    except Exception:
        pass  # collection may not exist — that's fine


# ─── Cold layer (ChromaDB) ──────────────────────────────────────────────────

async def save_summary(user_id: int, char_id: str, summary: str) -> None:
    """Append a summary document to the user+character ChromaDB collection."""
    if not summary:
        return
    chroma = get_chroma()
    col_name = _collection_name(user_id, char_id)
    col = await asyncio.to_thread(chroma.get_or_create_collection, col_name)
    ts = str(datetime.now(timezone.utc).timestamp())
    await asyncio.to_thread(col.add, documents=[summary], ids=[f"{col_name}_{ts}"])
    # Cache the latest summary on Redis so the fast path doesn't re-query Chroma.
    r = get_redis()
    await r.setex(_summary_key(user_id, char_id), 86400 * 3, summary)


async def get_latest_summary(user_id: int, char_id: str) -> str:
    """Return the most recent summary for this conversation. Redis fast-path."""
    r = get_redis()
    cached = await r.get(_summary_key(user_id, char_id))
    if cached:
        return cached
    try:
        chroma = get_chroma()
        col = await asyncio.to_thread(chroma.get_collection, _collection_name(user_id, char_id))
    except Exception:
        return ""
    results = await asyncio.to_thread(
        col.query,
        query_texts=["recent conversation events and emotions"],
        n_results=SUMMARY_TOPK,
    )
    docs = (results.get("documents") or [[]])[0]
    if not docs:
        return ""
    merged = " | ".join(docs)
    await r.setex(_summary_key(user_id, char_id), 86400 * 3, merged)
    return merged


async def get_relevant_memories(user_id: int, char_id: str, query: str) -> str:
    """Top-K semantic search over past summaries for the current user query."""
    try:
        chroma = get_chroma()
        col = await asyncio.to_thread(chroma.get_collection, _collection_name(user_id, char_id))
    except Exception:
        return ""
    results = await asyncio.to_thread(col.query, query_texts=[query], n_results=SUMMARY_TOPK)
    docs = (results.get("documents") or [[]])[0]
    return " | ".join(docs) if docs else ""


# ─── Assembled prompt context ──────────────────────────────────────────────

async def build_prompt_context(user_id: int, char_id: str, user_query: str) -> dict:
    """Parallel fire the three reads. Returns everything the handler needs."""
    recent, summary, memories = await asyncio.gather(
        get_recent(user_id, char_id),
        get_latest_summary(user_id, char_id),
        get_relevant_memories(user_id, char_id, user_query),
    )
    return {"recent": recent, "summary": summary, "memories": memories}
