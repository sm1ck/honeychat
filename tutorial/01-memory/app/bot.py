"""Minimal Telegram bot showing the dual-layer memory pattern end-to-end.

- Every user message is saved to Redis (hot layer).
- Every N turns, a summary of the recent window is written to ChromaDB (cold layer).
- On each new turn, all three retrieval paths fire in parallel via asyncio.gather.
- The LLM reply is generated via OpenRouter using the assembled prompt.

No tiers, no paywalls, no content escalation — just the memory pattern.
Set TELEGRAM_BOT_TOKEN and OPENROUTER_API_KEY in your .env.
"""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import suppress

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from app import memory

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
SUMMARIZER_MODEL = os.getenv("SUMMARIZER_MODEL", LLM_MODEL)

# Single demo character so the tutorial stays focused.
CHAR_ID = "demo"
CHAR_PROMPT = (
    "You are a helpful companion in a conversational demo. Remember what the user "
    "tells you and reference it naturally when relevant. Keep replies under 120 words."
)

dp = Dispatcher()


async def _chat_completion(model: str, messages: list[dict]) -> str:
    """Call OpenRouter chat/completions. Tiny wrapper; no retries here."""
    if not OPENROUTER_KEY:
        return "(OPENROUTER_API_KEY not set — set it in .env to enable replies.)"
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "HTTP-Referer": "https://github.com/sm1ck/honeychat",
                "X-Title": "honeychat tutorial 01-memory",
            },
            json={"model": model, "messages": messages, "max_tokens": 400},
        )
        r.raise_for_status()
        data = r.json()
        return (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""


def _assemble_prompt(ctx: dict, user_text: str) -> list[dict]:
    """Build the OpenRouter messages list from the retrieval context."""
    system_bits = [CHAR_PROMPT]
    if ctx.get("summary"):
        system_bits.append(f"Conversation summary so far: {ctx['summary']}")
    if ctx.get("memories"):
        system_bits.append(f"Related memories from this user: {ctx['memories']}")
    messages = [{"role": "system", "content": "\n\n".join(system_bits)}]
    for m in ctx.get("recent", []):
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_text})
    return messages


async def _maybe_summarize(user_id: int) -> None:
    """Every SUMMARIZE_EVERY_TURNS turns, compress the window into a summary."""
    recent = await memory.get_recent(user_id, CHAR_ID)
    if len(recent) < memory.SUMMARIZE_EVERY_TURNS * 2:
        return
    # Only summarize when we cross a multiple of SUMMARIZE_EVERY_TURNS
    if len(recent) % (memory.SUMMARIZE_EVERY_TURNS * 2) != 0:
        return
    text = "\n".join(f"{m['role']}: {m['content']}" for m in recent)
    prompt = [
        {"role": "system", "content": "Summarize this conversation chunk in 2-3 sentences, preserving key facts and emotional arc."},
        {"role": "user", "content": text},
    ]
    try:
        summary = await _chat_completion(SUMMARIZER_MODEL, prompt)
        await memory.save_summary(user_id, CHAR_ID, summary)
        log.info("summarized window for uid=%s", user_id)
    except Exception as e:
        log.warning("summarize failed for uid=%s: %s", user_id, e)


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Hi! I'm a demo bot for the persistent-memory architecture tutorial.\n\n"
        "Just chat with me. I save your recent messages in Redis and semantic summaries in "
        "ChromaDB. Every few turns I compress what you've said into a summary that sticks around.\n\n"
        "Commands: /reset — wipe our memory."
    )


@dp.message(Command("reset"))
async def cmd_reset(message: Message) -> None:
    uid = message.from_user.id if message.from_user else 0
    await memory.clear_conversation(uid, CHAR_ID)
    await message.answer("Memory cleared. Fresh start.")


@dp.message(F.text)
async def handle_text(message: Message) -> None:
    if not message.text or not message.from_user:
        return
    uid = message.from_user.id
    user_text = message.text.strip()

    # 1. Retrieve all three context pieces in parallel
    ctx = await memory.build_prompt_context(uid, CHAR_ID, user_text)

    # 2. Call LLM
    messages = _assemble_prompt(ctx, user_text)
    try:
        reply = await _chat_completion(LLM_MODEL, messages)
    except Exception as e:
        log.exception("LLM call failed")
        await message.answer(f"LLM error: {e}")
        return

    if not reply.strip():
        reply = "(empty completion — try a different prompt)"

    # 3. Persist both sides of the turn
    await memory.save_message(uid, CHAR_ID, "user", user_text)
    await memory.save_message(uid, CHAR_ID, "assistant", reply)

    # 4. Ship reply
    await message.answer(reply)

    # 5. Maybe summarize in the background
    with suppress(Exception):
        asyncio.create_task(_maybe_summarize(uid))


async def main() -> None:
    if not TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    bot = Bot(token=TOKEN)
    log.info("bot starting with model=%s", LLM_MODEL)
    try:
        await dp.start_polling(bot, handle_signals=False)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
