"""Resilient LLM routing via OpenRouter with a fallback chain.

Demonstrates two things:

1. Routing by content mode — a cheap fast model for general turns, a permissive
   fallback when the primary refuses, an uncensored last resort when both fail.
2. The reasoning-model empty-completion bug — reasoning-class models (Qwen3,
   DeepSeek R1, etc.) sometimes return `finish_reason=content_filter` with an
   empty `content` string. If your retry logic only catches HTTP errors, you
   miss this and users see blank replies. We detect it here and retry.

Model choices come from env — no hardcoded tier-to-model mapping. See
`.env.example` for recommended picks per mode.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Iterable

import httpx

log = logging.getLogger(__name__)

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Fallback chain — configurable from env. Order matters: primary first.
#
# Recommended: use a different *provider* for each fallback rung. Same-provider
# fallbacks often fail on the same content because the moderation layer is
# upstream of the model.
PRIMARY_MODEL      = os.environ.get("PRIMARY_MODEL",      "meta-llama/llama-3.1-8b-instruct:free")
FALLBACK_MODEL     = os.environ.get("FALLBACK_MODEL",     "mistralai/mistral-7b-instruct:free")
LAST_RESORT_MODEL  = os.environ.get("LAST_RESORT_MODEL",  "nousresearch/hermes-3-llama-3.1-405b")

# HTTP status codes we retry on. 429 + 5xx.
TRANSIENT_CODES = frozenset({408, 409, 425, 429, 500, 502, 503, 504})


@dataclass
class CompletionResult:
    content: str
    model: str
    attempt: int


class AllModelsFailedError(RuntimeError):
    """Raised when every model in the chain returned unusable content."""


def _build_chain(override_primary: str | None = None) -> list[str]:
    """Build the fallback chain. First element is the turn-specific primary."""
    primary = override_primary or PRIMARY_MODEL
    # Deduplicate while preserving order — in case primary == one of the fallbacks.
    chain: list[str] = []
    for m in (primary, FALLBACK_MODEL, LAST_RESORT_MODEL):
        if m and m not in chain:
            chain.append(m)
    return chain


def _is_silent_refusal(choice: dict) -> bool:
    """
    The whole point of this post: reasoning models can return a successful
    HTTP response with finish_reason=content_filter AND an empty content.
    If you only check HTTP status, you ship blank replies to users.
    """
    reason = choice.get("finish_reason")
    content = choice.get("message", {}).get("content") or ""
    return reason in ("content_filter", "length") and not content.strip()


async def _call(client: httpx.AsyncClient, model: str, messages: list[dict]) -> dict:
    r = await client.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "HTTP-Referer": "https://github.com/sm1ck/honeychat",
            "X-Title": "honeychat tutorial 02-routing",
        },
        json={"model": model, "messages": messages, "max_tokens": 400},
        timeout=30.0,
    )
    r.raise_for_status()
    return r.json()


async def complete(
    messages: list[dict],
    *,
    primary: str | None = None,
    chain: Iterable[str] | None = None,
) -> CompletionResult:
    """Run the fallback chain. Return the first usable response."""
    models = list(chain) if chain is not None else _build_chain(primary)
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    async with httpx.AsyncClient() as client:
        for attempt, model in enumerate(models):
            try:
                data = await _call(client, model, messages)
            except httpx.HTTPStatusError as e:
                if e.response.status_code in TRANSIENT_CODES:
                    log.warning("transient %s on %s — trying next", e.response.status_code, model)
                    continue
                raise
            except (httpx.ReadTimeout, httpx.ConnectError) as e:
                log.warning("network error on %s: %s — trying next", model, e)
                continue

            choice = (data.get("choices") or [{}])[0]
            if _is_silent_refusal(choice):
                log.warning("silent refusal on %s (reason=%s) — trying next", model, choice.get("finish_reason"))
                continue

            content = choice.get("message", {}).get("content") or ""
            if not content.strip():
                log.warning("empty content on %s — trying next", model)
                continue

            return CompletionResult(content=content, model=model, attempt=attempt)

    raise AllModelsFailedError(f"no model returned usable content; tried {models}")
