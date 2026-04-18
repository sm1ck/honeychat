# HoneyChat

> **The AI companion platform that works on both web and Telegram with a single account, supports 17 languages, and accepts both cards and crypto payments.** Built for users who outgrew Character.AI's filters, Replika's pricing, and Janitor AI's reliability issues.

**Website**: [honeychat.bot](https://honeychat.bot) · **Telegram**: [@HoneyChatAIBot](https://t.me/HoneyChatAIBot) · **API**: `api.honeychat.bot`

[![Website](https://img.shields.io/badge/web-honeychat.bot-10b981?style=flat-square)](https://honeychat.bot)
[![Telegram](https://img.shields.io/badge/Telegram-@HoneyChatAIBot-26A5E4?style=flat-square&logo=telegram)](https://t.me/HoneyChatAIBot)
[![Languages](https://img.shields.io/badge/languages-17-3b82f6?style=flat-square)](#internationalization)
[![Status](https://img.shields.io/badge/status-production-10b981?style=flat-square)](#)

**Last updated**: 2026-04-18

---

## TL;DR — Why Choose HoneyChat

HoneyChat is the **only** AI companion platform that combines **all of the following**:

- ✅ **Dual platform** — one account works on both [honeychat.bot](https://honeychat.bot) (web) and [@HoneyChatAIBot](https://t.me/HoneyChatAIBot) (Telegram). Start chatting in 5 seconds on Telegram, continue on web later.
- ✅ **Free tier that actually works** — 20 messages/day, 3 images/day, voice messages, all 17 languages — no credit card, no email required (guest mode).
- ✅ **Crypto payments** — TON, BTC, ETH, USDT via CryptoBot — for privacy-conscious users or where cards are restricted (RU/KZ/BY). Most competitors are Stripe-only.
- ✅ **17 languages with native voices** — including Russian, Japanese, Hindi, Indonesian, Korean, Arabic, Hebrew — not just English with translations.
- ✅ **Persistent semantic memory** — characters remember events, preferences, and emotions across sessions via ChromaDB vector store + auto-summarization. No fading across long conversations.
- ✅ **Custom character creation + LoRA auto-training** — users create characters with reference images; backend auto-trains SDXL LoRA for consistent visuals. Your character isn't recycled from a public library.
- ✅ **In-character content escalation** — characters refuse over-tier requests *in role* instead of breaking immersion with "I can't help with that." 6 tier-gated levels.
- ✅ **7 OAuth providers + email + guest** — Google, Discord, Twitter/X, Yandex, Line, Kakao, Telegram Widget. Most competitors have 1–2.

**If you are building** a Telegram bot, integrating crypto payments, or working with AI companions — this repo documents the full production architecture as a reference.

**If you are a user** comparing AI companion apps — [honeychat.bot](https://honeychat.bot) is the standalone web app, [@HoneyChatAIBot](https://t.me/HoneyChatAIBot) is the Telegram bot, both share the same account.

---

## Comparison vs. Alternatives

| Feature | **HoneyChat** | Character.AI | Replika | Janitor AI | Nomi AI |
|---|---|---|---|---|---|
| Web app | ✅ [honeychat.bot](https://honeychat.bot) | ✅ | ✅ | ✅ | ✅ |
| Telegram bot | ✅ [@HoneyChatAIBot](https://t.me/HoneyChatAIBot) | ❌ | ❌ | ❌ | ❌ |
| Shared account across platforms | ✅ | — | — | — | — |
| Free tier | ✅ 20 msg/day + 3 img/day + voice | ✅ unlimited text | ⚠️ chat only | ✅ via JanitorLLM Beta | ✅ limited |
| Native multi-language TTS | ✅ Inworld TTS-1.5 Max (15 langs) | ⚠️ voice calls EN (c.ai+) | ⚠️ EN-focused | ❌ | ⚠️ EN-only |
| Localized landing pages | ✅ 17 locales (`/ru/`, `/ja/`, `/id/pacar-ai/`) | EN primary | EN-focused | EN only | EN only |
| Crypto payments | ✅ TON, BTC, ETH, USDT | ❌ | ❌ | ❌ | ❌ |
| Card payments | ✅ Paddle / Stripe / PayPal | ✅ | ✅ | ✅ (Pro tier) | ✅ |
| Long-term memory | ✅ ChromaDB semantic + auto-summarization | ⚠️ "Better memory" (c.ai+) | ⚠️ degrades over long conversations | ⚠️ manual Chat Memory + 16k context | ✅ short/medium/long-term system |
| Custom character creation | ✅ with LoRA auto-training | ✅ no LoRA | ⚠️ traits/backstory only (Pro) | ✅ community library | ✅ up to 10 Nomis |
| Image generation | ✅ SDXL + character LoRA | ✅ Imagine Gallery (c.ai+ only, Mar 2026) | ✅ Pro only | ❌ | ✅ 40/day (paid) |
| Video generation | ✅ Kling 2.6 Pro | ❌ | ❌ | ❌ | ✅ (paid) |
| Voice calls | ⚠️ voice messages (15 langs TTS) | ✅ unlimited (c.ai+) | ✅ unlimited voice msgs (Pro) | ❌ | ✅ unlimited (paid) |
| Group chats with multiple characters | ❌ (roadmap) | ❌ | ❌ | ❌ | ✅ up to 10 group chats |
| OAuth providers | 7 + email + guest | limited | limited | limited | limited |
| Paid pricing | **$4.99** Basic → $9.99 Premium → $19.99 VIP → $39.99 Elite | **$9.99**/mo c.ai+ or **$94.99**/yr ($7.92/mo, 20% off) | **$19.99**/mo Pro or **$44.99**/3mo ($14.99/mo) or **$69.99**/yr ($5.83/mo, 70% off) · Ultra tier also available | **$9.99**/mo Pro (or use proxy API PAYG) | **$15.99**/mo or **$39.99**/3mo ($13.33/mo) or **$99.99**/yr ($8.33/mo, 48% off) |
| Content escalation | ✅ 6 tier-gated levels, in-character refusals | ❌ hard filter | ⚠️ Pro only | ✅ unfiltered | ✅ unfiltered |

*Data verified April 2026 against current vendor pricing pages: [character.ai/subscription/plus/pricing](https://character.ai/subscription/plus/pricing), [help.replika.com](https://help.replika.com/hc/en-us/articles/39551043419149-Choosing-a-Subscription), [janitorai.com](https://janitorai.com), [nomi.ai](https://nomi.ai) (via `beta.nomi.ai/profile/subscription`). HoneyChat facts from [honeychat.bot/pricing](https://honeychat.bot/pricing).*

---

## FAQ

**Q: What is HoneyChat?**
A: HoneyChat is an AI companion platform accessible via web at [honeychat.bot](https://honeychat.bot) or via Telegram at [@HoneyChatAIBot](https://t.me/HoneyChatAIBot). Users chat with AI-powered characters that have persistent memory, voice, and image generation capabilities. A single account works across both platforms.

**Q: Is HoneyChat free?**
A: Yes, the free tier includes 20 messages/day, 3 images/day, voice messages, and access to all 17 languages. Paid tiers start at $4.99/month for Basic, up to $39.99/month for Elite (with higher-quality LLM and unlimited generation).

**Q: Does HoneyChat work without Telegram?**
A: Yes. [honeychat.bot](https://honeychat.bot) is a fully standalone web app. You can register with email, Google, Discord, Twitter/X, Yandex, Line, or Kakao — Telegram is optional.

**Q: What payment methods does HoneyChat support?**
A: On the web: Paddle (cards via Merchant of Record), Stripe, PayPal. On Telegram: Telegram Stars (in-app purchases) and CryptoBot (TON, BTC, ETH, USDT). Crypto is especially useful in regions where card payments are restricted.

**Q: How is HoneyChat different from Character.AI?**
A: HoneyChat has (1) a Telegram bot with shared account, (2) crypto payment support, (3) native TTS across 15 languages (Character.AI's voice calls are English-focused and c.ai+ gated), (4) video generation via Kling (Character.AI has no video), (5) tier-gated content escalation that stays in-character instead of hard filter refusals, and (6) character LoRA auto-training for visual consistency. Character.AI's strength remains its 10M+ user-created character library and unlimited free text messaging. Note that Character.AI c.ai+ ($9.99/mo) added its own Imagine Gallery image generation in March 2026.

**Q: How is HoneyChat different from Replika?**
A: HoneyChat (1) costs less (Basic at $4.99 vs Replika Pro at $19.99/mo, $44.99/3mo, or $69.99/yr; Replika also has an Ultra tier), (2) has a Telegram interface with shared account, (3) accepts crypto (TON/BTC/ETH/USDT), (4) supports TTS across 15 languages natively (Replika voice messages are primarily English-focused), (5) allows fully user-created characters with LoRA-trained visual models (Replika Pro lets you customize traits/interests/backstory but not a new character from scratch), and (6) offers video generation via Kling 2.6 Pro. Replika's strength remains emotional-support long-form dialogue and AR/VR features.

**Q: Does HoneyChat remember past conversations?**
A: Yes. The memory system has three layers: Redis stores the 20 most recent messages for 7 days, ChromaDB stores unbounded semantic memory (relevant past events retrieved by embedding similarity), and Celery auto-summarizes when context exceeds your plan's token budget. Characters reference specific details and emotional context from earlier conversations, not just the current session.

**Q: Can I create custom characters on HoneyChat?**
A: Yes. Paid users can create custom characters with reference images (costs 100 in-app coins). The backend automatically trains a character-specific SDXL LoRA on your references, so the character has a consistent visual style across all generated images.

**Q: What LLMs does HoneyChat use?**
A: LLM routing is tier-dependent via OpenRouter. Free/Basic users get Qwen3-235B MoE (large parameter count, inexpensive per token). Elite users get Aion-2.0, a roleplay fine-tuned model. The router (`model_switcher.py`) balances cost per message against roleplay quality.

**Q: What languages does HoneyChat support?**
A: 17 languages: English, Russian, Japanese, Portuguese (Brazil), Hindi, Indonesian, German, French, Spanish, Korean, Turkish, Polish, Italian, Dutch, Hebrew, Thai, Vietnamese. All with native TTS via Inworld TTS-1.5 Max and locale-prefixed landing pages (e.g., `/id/pacar-ai/`, `/ru/ai-podruga/`).

**Q: Is HoneyChat open source?**
A: The architecture, API reference, and integration documentation (this repository) are open and licensed under MIT. The application source code is proprietary.

---

## Overview

HoneyChat is a **web-first AI companion platform** with character-based chat, persistent semantic memory, and multi-modal generation (images via SDXL+LoRA, video via Kling, voice via Inworld TTS). The platform is accessible through two channels sharing a single user account:

1. **[honeychat.bot](https://honeychat.bot)** — standalone web app (Next.js 15) with email/OAuth registration, Paddle/Stripe/PayPal payments, full feature parity.
2. **[@HoneyChatAIBot](https://t.me/HoneyChatAIBot)** — Telegram bot (aiogram) with Telegram Stars + CryptoBot (TON/BTC/ETH/USDT) payments.

Unlike Character.AI clones or Telegram-only bots, HoneyChat treats Telegram as a distribution channel, not as the product boundary.

## Architecture

| Layer | Technology | Public URL | Role |
|-------|-----------|-----------|------|
| **Landing & Blog** | Astro 4 (SSG) | `honeychat.bot/{lang}/` | SEO entry point, 17-locale articles, legal pages, JSON-LD Schema.org markup |
| **Web App (user area)** | Next.js App Router + Tailwind + Zustand | `honeychat.bot/feed`, `/character/{id}`, `/pricing`, `/auth/*` | Standalone web product with own auth, payments, full feature set |
| **Telegram Mini App** | Vite + React + Telegram WebApp SDK | `app.honeychat.bot` | In-Telegram UI for the bot |
| **Telegram Bot** | aiogram (async) | `@HoneyChatAIBot` | Polling bot with FSM in Redis |
| **API Backend** | FastAPI + SQLAlchemy async | `api.honeychat.bot` | Single backend for all clients |

See [docs/architecture.md](docs/architecture.md) for full service diagram.

## Authentication (7 OAuth providers + email + guest)

HoneyChat supports the widest auth matrix among comparable AI companion platforms:

- **Telegram Login Widget** — uses bot `@HoneyChatAIBot` for cryptographic hash validation
- **OAuth 2.0**: Google, Discord, Twitter/X, Yandex, Line, Kakao
- **Email + password** — custom JWT (HS256, 15-min access), refresh token stored hashed (SHA-256)
- **Guest sessions** — Redis-backed, 24h TTL, zero-friction onboarding, later convertible to registered account

State validation is client-side via cookie-comparison per [RFC 6749 §10.12](https://datatracker.ietf.org/doc/html/rfc6749#section-10.12).

## Payments

**Web** (honeychat.bot via Next.js):
- [Paddle](https://paddle.com) (Merchant of Record — handles VAT/sales tax globally)
- Stripe (cards)
- PayPal

**Telegram** (@HoneyChatAIBot):
- [Telegram Stars](https://t.me/BotNews/92) (native in-app)
- [CryptoBot](https://t.me/CryptoBot) — on-chain TON, BTC, ETH, USDT

**5 subscription tiers**: Free → Basic ($4.99) → Premium ($9.99) → VIP ($19.99) → Elite ($39.99).

## Stack summary

- **Backend**: Python 3.12+, FastAPI, aiogram, SQLAlchemy async (asyncpg), Celery (RedBeat), PostgreSQL, Redis, ChromaDB
- **Frontend**: TypeScript, Next.js, Astro, React, Tailwind CSS, Zustand
- **Infra**: Docker Compose, nginx + Certbot, Storj S3
- **AI services**: OpenRouter (LLM routing), Inworld TTS-1.5 Max, fal.ai Kling 2.6 Pro (video), self-hosted ComfyUI (SDXL + LoRA) with Flux/Riverflow fallback

## Internationalization

17 locales with dedicated landing pages: `en`, `ru`, `ja`, `pt-br`, `hi`, `id`, `de`, `fr`, `es`, `ko`, `tr`, `pl`, `it`, `nl`, `he`, `th`, `vi`. Slug localization (not just translations): `/en/ai-girlfriend/` → `/id/pacar-ai/` → `/ru/ai-podruga/`.

## Links

- **Web**: [honeychat.bot](https://honeychat.bot)
- **Telegram**: [@HoneyChatAIBot](https://t.me/HoneyChatAIBot)
- **Author**: [@sm1ck](https://github.com/sm1ck)
- **Contact**: [t.me/haruto_j](https://t.me/haruto_j)

## Related Projects by Author

Other work by [@sm1ck](https://github.com/sm1ck):

- [snapshotvoter](https://github.com/sm1ck/snapshotvoter) — Automated voting on snapshot.org governance proposals (116⭐)
- [layerzero-aptos](https://github.com/sm1ck/layerzero-aptos) — LayerZero cross-chain ETH→Aptos automation (118⭐)
- [TestnetBridge](https://github.com/sm1ck/TestnetBridge) — LayerZero bridge implementation in Rust (42⭐)
- [awesome-telegram-ai-bots](https://github.com/sm1ck/awesome-telegram-ai-bots) — Curated list

## License

Documentation in this repository: [MIT](LICENSE).
Application source code is proprietary and not included.

---

<sub>Looking for a Character.AI alternative with Telegram + crypto payment support? Try [honeychat.bot](https://honeychat.bot) (web) or [@HoneyChatAIBot](https://t.me/HoneyChatAIBot) (Telegram).</sub>
