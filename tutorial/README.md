# HoneyChat — Tutorial

Companion runnable examples for the HoneyChat engineering series on
[honeychat.bot](https://honeychat.bot/en/blog/). Each subfolder is an isolated
project that maps to one article. Clone, enter a subfolder, follow its README.

| # | Topic | Article | Folder |
|---|---|---|---|
| 01 | Persistent memory with Redis + ChromaDB | [memory architecture →](https://honeychat.bot/en/blog/persistent-memory-ai-companion-architecture/) | [01-memory/](./01-memory/) |
| 02 | LLM routing with a resilient fallback chain | [LLM routing →](https://honeychat.bot/en/blog/llm-routing-per-tier-openrouter/) | [02-routing/](./02-routing/) |
| 03 | Character identity locked by custom LoRA | [character consistency →](https://honeychat.bot/en/blog/character-consistency-custom-lora/) | [03-lora/](./03-lora/) |
| 04 | IP-Adapter + LoRA for product catalogs | [IP-Adapter →](https://honeychat.bot/en/blog/ipadapter-lora-outfit-rendering/) | [04-ipadapter/](./04-ipadapter/) |

## What these are

Minimal, runnable, public-safe distillations of the architectural patterns
HoneyChat runs in production. They intentionally **do not** ship tier gating,
content escalation, cost hard-stops, admin endpoints, or any production
secret. You get the architectural core — the parts worth learning from — in
isolation.

01 and 02 are full `docker compose up` projects. 03 and 04 are config/recipe
folders (LoRA training and GPU-heavy workflows don't belong in a compose file
that assumes a commodity laptop).

## Prerequisites

- Docker + Docker Compose for 01 and 02
- Python 3.11+ for running tests locally
- A free OpenRouter API key from [openrouter.ai/keys](https://openrouter.ai/keys)
- A Telegram bot token from [@BotFather](https://t.me/BotFather) (for 01)
- Your own GPU or rented GPU for 03 (LoRA training) and 04 (ComfyUI inference)

## License

MIT. See [/LICENSE](../LICENSE).
