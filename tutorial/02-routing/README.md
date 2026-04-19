# Tutorial 02 · LLM routing with fallback chain

Minimal runnable demo of the LLM-routing pattern used in HoneyChat: a primary
model per tier/content-mode, plus a multi-provider fallback chain that handles
the reasoning-model **silent content_filter empty completion** failure mode.

Companion article: [honeychat.bot/en/blog/llm-routing-per-tier-openrouter](https://honeychat.bot/en/blog/llm-routing-per-tier-openrouter/)

## What's inside

```
02-routing/
├── app/
│   ├── router.py   ← fallback chain + empty-completion guard
│   └── main.py     ← FastAPI POST /complete + GET /health
├── tests/
│   └── test_fallback_chain.py
├── docker-compose.yml
└── pyproject.toml
```

## Running

```bash
cp .env.example .env
# Fill in OPENROUTER_API_KEY

docker compose up --build -d
curl http://localhost:8000/health

# Try a turn
curl -X POST http://localhost:8000/complete \
  -H 'content-type: application/json' \
  -d '{"messages":[{"role":"user","content":"Say hi in under 10 words"}]}' \
  | jq
# → {"content": "...", "model": "...", "attempt": 0, "used_fallback": false}
```

The response includes which model actually answered. `attempt > 0` means the
primary failed and a fallback kicked in — log this in production to spot
routing regressions.

## Testing

```bash
pip install -e ".[dev]"
pytest -v
```

Tests mock OpenRouter so they run offline. They cover:

- Primary returns content → no fallback
- `finish_reason=content_filter` with empty content → fallback fires
- Transient 5xx → retry on next model
- Non-transient 4xx (e.g. 401) → raise, don't retry
- All models fail → `AllModelsFailedError`
- Override the primary per-request

## Model picks

Default configuration picks free-tier OpenRouter models so you can run the
tutorial without spending money. For a production setup, pick:

- **Primary**: fast + cheap for your common turns
- **Fallback**: different provider, looser moderation (good for when the
  primary returns `content_filter`)
- **Last resort**: uncensored-leaning, e.g. `hermes-3` — only reached when
  both above fail. In practice this is rare.

See OpenRouter's model list: https://openrouter.ai/models

## License

MIT.
