# HoneyChat Architecture

High-level architecture of the HoneyChat AI companion platform. This document describes the public-facing technical design — the full application source is proprietary.

## Service Topology

```mermaid
graph TB
    subgraph "Clients"
        Web["Web Browser<br/>honeychat.bot"]
        TG["Telegram App<br/>@HoneyChatAIBot"]
        TGApp["Telegram Mini App<br/>app.honeychat.bot"]
    end

    subgraph "Edge"
        Nginx["nginx + Certbot<br/>Let's Encrypt"]
    end

    subgraph "Frontends"
        Astro["Astro SSG<br/>Landing + Blog<br/>17 locales"]
        NextJS["Next.js 15 App Router<br/>User area (feed/chat/pricing)"]
        Mini["Vite + React<br/>Telegram Mini App"]
        Bot["aiogram<br/>Telegram Bot"]
    end

    subgraph "Backend"
        API["FastAPI"]
        Worker["Celery<br/>named queues"]
        Beat["Celery Beat<br/>RedBeat"]
    end

    subgraph "Data"
        PG[("PostgreSQL<br/>SQLAlchemy async")]
        Redis[("Redis<br/>cache + FSM + broker")]
        Chroma[("ChromaDB<br/>vector memory")]
        S3[("Storj S3<br/>LoRA, voice, media")]
    end

    subgraph "External AI"
        OR["OpenRouter<br/>Multi-LLM routing"]
        Inworld["Inworld TTS-1.5 Max<br/>15 languages"]
        Kling["fal.ai Kling 2.6 Pro<br/>Video"]
        Comfy["ComfyUI<br/>SDXL + LoRA"]
    end

    subgraph "Payments"
        Paddle["Paddle<br/>Merchant of Record"]
        Stars["Telegram Stars"]
        Crypto["CryptoBot<br/>TON/BTC/ETH/USDT"]
    end

    Web --> Nginx
    TG --> Nginx
    TGApp --> Nginx

    Nginx --> Astro
    Nginx --> NextJS
    Nginx --> Mini
    Nginx --> API
    TG -.polling.-> Bot

    NextJS --> API
    Mini --> API
    Bot --> API

    API --> PG
    API --> Redis
    API --> Chroma
    API --> S3
    API --> OR
    API --> Inworld

    Worker --> OR
    Worker --> Kling
    Worker --> Comfy
    Worker --> S3
    Beat --> Worker

    NextJS --> Paddle
    Bot --> Stars
    Bot --> Crypto
```

## Key Flows

### 1. Chat Message (Telegram bot)

1. User sends message via `@HoneyChatAIBot`
2. aiogram dispatcher picks up update
3. Middleware chain: **Auth → Onboarding → Rate Limit → Plan Inject → Cost Guard**
4. Handler increments Redis daily counter (atomic `INCR`)
5. Memory retrieval: Redis recent (last 20) + ChromaDB semantic (top-K by embedding similarity)
6. System prompt constructed with character persona + memory + tier limits
7. LLM call via OpenRouter (model selected by plan tier)
8. Content escalation check — if intent over tier, spawn in-character refusal + upsell
9. Response stored in Redis + ChromaDB (for future semantic retrieval)
10. Message sent back via Telegram API

### 2. Web Login (Multi-provider)

Seven OAuth providers + email + guest. Example Google flow:

```mermaid
sequenceDiagram
    participant U as User
    participant N as Next.js
    participant G as Google OAuth
    participant A as FastAPI (/api/v1/auth)
    participant DB as PostgreSQL

    U->>N: Click "Sign in with Google"
    N->>N: Generate state, store in cookie
    N->>G: Redirect to accounts.google.com with state
    G->>U: Consent screen
    U->>G: Approve
    G->>N: Redirect to /auth/callback with code+state
    N->>N: Verify state == cookie (RFC 6749 §10.12)
    N->>A: POST /api/v1/auth/oauth/exchange {code, provider}
    A->>G: Exchange code for access_token
    G->>A: Return token + user info
    A->>DB: UPSERT user by provider_id
    A->>A: Issue JWT (15-min access) + refresh token
    A->>N: Return JWT cookies
    N->>U: Redirect to /feed
```

### 3. Crypto Payment (Telegram)

```mermaid
sequenceDiagram
    participant U as User
    participant B as @HoneyChatAIBot
    participant A as FastAPI
    participant C as CryptoBot
    participant DB as PostgreSQL

    U->>B: /buy premium
    B->>A: Request invoice
    A->>C: Create invoice (amount, asset=TON)
    C->>A: Return invoice_id + pay_url
    A->>B: Pass pay_url to user
    B->>U: Send inline button "Pay with TON"
    U->>C: Complete on-chain payment
    C->>A: Webhook POST /webhook/cryptobot (signed)
    A->>A: Verify HMAC signature
    A->>A: Idempotency check by invoice_id
    A->>DB: UPDATE subscriptions SET plan='premium', expires_at=...
    A->>B: Notify user
    B->>U: "Premium activated"
```

## Memory System (3-layer)

| Layer | Storage | TTL | Purpose |
|-------|---------|-----|---------|
| Recent | Redis sorted set `mem:recent:{user}:{char}` | 7 days | Last 20 messages, fast retrieval for every turn |
| Semantic | ChromaDB collection `mem:{user}:{char}` | Unbounded | Embeddings of key events/emotions, top-K similarity search |
| Summary | PostgreSQL `memory_summaries` | Persistent | Auto-generated rolling summary when recent + semantic exceeds tier token budget |

Summarization is triggered asynchronously via Celery `summarize` queue when token count exceeds plan's `PLAN_CONTEXT_TOKENS` threshold.

## LLM Routing by Tier

| Tier | Default model | Output tokens | Monthly price |
|------|--------------|---------------|---------------|
| Free | Qwen3-235B MoE (free tier) | 250 | $0 |
| Basic | Qwen3-235B MoE | 400 | $4.99 |
| Premium | Qwen3-235B MoE (more context) | 600 | $9.99 |
| VIP | Gemini 3.1 Flash Lite | 800 | $19.99 |
| Elite | Aion-2.0 (RP fine-tuned) | 800 | $39.99 |

Instant-mode users also have access to Grok 4.1 Fast for explicit-content turns (via `model_switcher.py` override).

## Infra Layout (Docker Compose)

| Service | Purpose |
|---------|---------|
| `bot` | Telegram aiogram bot (polling) |
| `api` | FastAPI (4 uvicorn workers) |
| `nextjs` | Next.js 15 standalone server |
| `celery_worker` | Async job processing (7 queues) |
| `celery_beat` | Periodic scheduler |
| `gen_worker` | Dedicated image/GIF generation queue |
| `postgres` | PostgreSQL 16 primary DB |
| `redis` | Cache + FSM + Celery broker |
| `chromadb` | Vector memory |
| `nginx` | HTTPS proxy + static files |
| `certbot` | Let's Encrypt SSL renewal |

Two Docker networks: `internal` (service-to-service) and `external` (nginx only, ports 80/443).

## Scaling Notes

- Async DB connection pool with health checks (`pool_pre_ping`)
- Cost tracking via Redis atomic counters, fail-closed on backend error
- Daily spend thresholds trigger admin alerts and hard stops on new generations
- Rate limits (API endpoints): per-user Redis counters with sliding window

## Related

- API reference: [api.md](api.md)
- Project overview: [../README.md](../README.md)
- Web: [honeychat.bot](https://honeychat.bot)
