# Tutorial 01 · Persistent memory (Redis + ChromaDB)

Minimal runnable demo of the dual-layer memory architecture used in HoneyChat:
**Redis** for the hot buffer of recent messages, **ChromaDB** for semantic
retrieval over summaries of older turns. Every user message triggers three
parallel reads (`asyncio.gather`) that get assembled into the LLM prompt.

Companion article: [honeychat.bot/en/blog/persistent-memory-ai-companion-architecture](https://honeychat.bot/en/blog/persistent-memory-ai-companion-architecture/)

## What's inside

```
01-memory/
├── app/
│   ├── memory.py      ← the core: save_message, get_recent, save_summary,
│   │                    get_latest_summary, get_relevant_memories,
│   │                    build_prompt_context (parallel fetch)
│   ├── bot.py         ← aiogram Telegram bot wiring the memory into a chat loop
│   └── api.py         ← FastAPI inspector for peeking at the memory layers
├── tests/
│   └── test_memory.py ← unit tests (fakeredis + ChromaDB stub)
├── docker-compose.yml ← redis + chromadb + api + bot
└── pyproject.toml
```

## Running locally

```bash
cp .env.example .env
# Fill in TELEGRAM_BOT_TOKEN (from @BotFather) and OPENROUTER_API_KEY

docker compose up --build -d
docker compose logs -f bot        # watch the bot come alive
curl http://localhost:8000/health # {"ok":true} from the inspector API
```

Open your bot on Telegram, hit `/start`, then chat for a while. After ~10 turns
the bot writes a summary to ChromaDB. Peek at what's stored:

```bash
# Replace 12345 with your own Telegram user ID
curl http://localhost:8000/memory/12345/demo/recent  | jq
curl http://localhost:8000/memory/12345/demo/summary | jq
```

Clear everything:
```bash
curl -X POST http://localhost:8000/memory/12345/demo/clear
```

## Running tests

```bash
pip install -e ".[dev]"
pytest -v
```

Tests use a fake Redis and a ChromaDB stub, so no containers required.

## Tuning knobs

Set these in `.env` if you want to experiment with different memory profiles:

- `HOT_BUFFER_SIZE` (default 20) — how many recent messages to keep verbatim
- `HOT_BUFFER_TTL_DAYS` (default 7) — how long inactive conversations live in Redis
- `SUMMARY_TOPK` (default 3) — how many summary docs to pull per semantic query
- `SUMMARIZE_EVERY_TURNS` (default 10) — how often to compress a window into a summary

## What this is NOT

This tutorial strips everything that isn't the memory pattern. No paywalls, no
tier-specific token budgets, no rate limits, no auto-summarize cancellation,
no guest-to-user merge, no content moderation. The production HoneyChat code
has all of that — this is the architectural core in isolation, safe to read
and learn from.

## License

MIT. See the repo root `LICENSE`.
