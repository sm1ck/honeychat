"""Unit tests for the memory layer. Uses fakeredis + a ChromaDB stub.

Run: pytest -v tests/
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app import memory


@pytest.fixture(autouse=True)
def _mock_redis(monkeypatch):
    """Replace get_redis() with a minimal async fake for every test."""
    store: dict[str, list] = {}
    kv: dict[str, str] = {}

    class FakePipe:
        def __init__(self):
            self.ops = []
        def rpush(self, k, v):   self.ops.append(("rpush", k, v)); return self
        def ltrim(self, k, s, e): self.ops.append(("ltrim", k, s, e)); return self
        def expire(self, k, ttl): self.ops.append(("expire", k, ttl)); return self
        async def execute(self):
            for op in self.ops:
                if op[0] == "rpush":
                    store.setdefault(op[1], []).append(op[2])
                elif op[0] == "ltrim":
                    _, k, s, e = op
                    data = store.get(k, [])
                    if s < 0 and e == -1:
                        data = data[s:]
                    store[k] = data
                elif op[0] == "expire":
                    pass

    class FakeRedis:
        def pipeline(self):      return FakePipe()
        async def lrange(self, k, s, e):
            data = store.get(k, [])
            if s < 0:
                return data[s:] if e == -1 else data[s:e + 1]
            return data[s:e + 1]
        async def get(self, k):  return kv.get(k)
        async def setex(self, k, _ttl, v): kv[k] = v
        async def delete(self, *keys):
            for k in keys:
                store.pop(k, None); kv.pop(k, None)

    fake = FakeRedis()
    monkeypatch.setattr(memory, "get_redis", lambda: fake)
    return fake


@pytest.fixture(autouse=True)
def _mock_chroma(monkeypatch):
    """Replace get_chroma() with a stub that tracks collections + docs."""
    class FakeCollection:
        def __init__(self):
            self.docs: list[str] = []
        def add(self, documents, ids):
            self.docs.extend(documents)
        def query(self, query_texts, n_results):
            return {"documents": [[d for d in self.docs[-n_results:]]]}

    class FakeChroma:
        def __init__(self):
            self.collections: dict[str, FakeCollection] = {}
        def get_or_create_collection(self, name):
            return self.collections.setdefault(name, FakeCollection())
        def get_collection(self, name):
            if name not in self.collections:
                raise ValueError("missing")
            return self.collections[name]
        def delete_collection(self, name):
            self.collections.pop(name, None)

    fake = FakeChroma()
    monkeypatch.setattr(memory, "get_chroma", lambda: fake)
    return fake


@pytest.mark.asyncio
async def test_save_and_get_recent():
    await memory.save_message(1, "demo", "user", "hello")
    await memory.save_message(1, "demo", "assistant", "hi there")
    recent = await memory.get_recent(1, "demo")
    assert len(recent) == 2
    assert recent[0]["role"] == "user"
    assert recent[1]["content"] == "hi there"


@pytest.mark.asyncio
async def test_ltrim_caps_buffer(monkeypatch):
    """Hot buffer is bounded — writing more than HOT_BUFFER_SIZE must not grow past cap."""
    monkeypatch.setattr(memory, "HOT_BUFFER_SIZE", 3)
    for i in range(8):
        await memory.save_message(2, "demo", "user", f"msg {i}")
    recent = await memory.get_recent(2, "demo", limit=100)
    assert len(recent) == 3
    assert recent[-1]["content"] == "msg 7"


@pytest.mark.asyncio
async def test_summary_roundtrip():
    await memory.save_summary(3, "demo", "User mentioned they have a cat named Luna.")
    s = await memory.get_latest_summary(3, "demo")
    assert "Luna" in s


@pytest.mark.asyncio
async def test_semantic_retrieval_empty_for_new_user():
    # No collection yet → empty string, not an exception
    result = await memory.get_relevant_memories(999, "demo", "what about the cat?")
    assert result == ""


@pytest.mark.asyncio
async def test_clear_wipes_both_layers():
    await memory.save_message(4, "demo", "user", "remember X")
    await memory.save_summary(4, "demo", "Mentioned X.")
    await memory.clear_conversation(4, "demo")
    recent = await memory.get_recent(4, "demo")
    summary = await memory.get_latest_summary(4, "demo")
    assert recent == []
    assert summary == ""


@pytest.mark.asyncio
async def test_build_prompt_context_fires_three_reads():
    await memory.save_message(5, "demo", "user", "I love skiing")
    await memory.save_summary(5, "demo", "User is into winter sports.")
    ctx = await memory.build_prompt_context(5, "demo", "do you remember my hobby?")
    assert "recent" in ctx and "summary" in ctx and "memories" in ctx
    assert len(ctx["recent"]) == 1
