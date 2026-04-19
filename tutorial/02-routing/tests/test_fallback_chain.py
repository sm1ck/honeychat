"""Tests for the fallback chain — mocks OpenRouter HTTP so the tests are offline."""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import httpx
import pytest

os.environ.setdefault("OPENROUTER_API_KEY", "test-key")

from app import router


def _response(content: str, finish_reason: str = "stop") -> dict:
    return {"choices": [{"message": {"content": content}, "finish_reason": finish_reason}]}


def _mock_call(side_effect):
    """Patch router._call with a sequence of responses / exceptions."""
    calls = iter(side_effect)

    async def fake_call(client, model, messages):
        item = next(calls)
        if isinstance(item, Exception):
            raise item
        return item

    return patch.object(router, "_call", side_effect=fake_call)


@pytest.mark.asyncio
async def test_primary_returns_content():
    with _mock_call([_response("hello from primary")]):
        result = await router.complete([{"role": "user", "content": "hi"}])
    assert result.content == "hello from primary"
    assert result.attempt == 0
    assert result.model == router.PRIMARY_MODEL


@pytest.mark.asyncio
async def test_content_filter_empty_triggers_fallback():
    """The whole point of the article: silent refusal must fall through."""
    with _mock_call([
        _response("", finish_reason="content_filter"),
        _response("from the fallback"),
    ]):
        result = await router.complete([{"role": "user", "content": "hi"}])
    assert result.content == "from the fallback"
    assert result.attempt == 1


@pytest.mark.asyncio
async def test_length_with_empty_also_retries():
    with _mock_call([
        _response("", finish_reason="length"),
        _response("saved by fallback"),
    ]):
        result = await router.complete([{"role": "user", "content": "hi"}])
    assert result.attempt == 1


@pytest.mark.asyncio
async def test_transient_5xx_retries():
    mock_resp = httpx.Response(503, text="service unavailable")
    err = httpx.HTTPStatusError("503", request=httpx.Request("POST", "x"), response=mock_resp)
    with _mock_call([err, _response("back online")]):
        result = await router.complete([{"role": "user", "content": "hi"}])
    assert result.content == "back online"
    assert result.attempt == 1


@pytest.mark.asyncio
async def test_non_transient_4xx_raises():
    mock_resp = httpx.Response(401, text="unauthorized")
    err = httpx.HTTPStatusError("401", request=httpx.Request("POST", "x"), response=mock_resp)
    with _mock_call([err]):
        with pytest.raises(httpx.HTTPStatusError):
            await router.complete([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_all_fail_raises_all_models_failed():
    bad = _response("", finish_reason="content_filter")
    with _mock_call([bad, bad, bad]):
        with pytest.raises(router.AllModelsFailedError):
            await router.complete([{"role": "user", "content": "hi"}])


@pytest.mark.asyncio
async def test_override_primary_in_chain():
    with _mock_call([_response("from override")]):
        result = await router.complete(
            [{"role": "user", "content": "hi"}],
            primary="anthropic/claude-3-haiku",
        )
    assert result.model == "anthropic/claude-3-haiku"
