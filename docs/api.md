# HoneyChat API Reference

Public API endpoints exposed at `https://api.honeychat.bot`. This is a documentation-level reference — authenticated endpoints require a valid JWT obtained via login.

**Base URL**: `https://api.honeychat.bot/api/v1`

## Authentication

All user endpoints require a Bearer JWT in the `Authorization` header, or the `_at` cookie (set by `/auth/*` flows on honeychat.bot).

Token lifetime: 15 minutes (access). Refresh token is stored in `web_sessions` (hashed SHA-256).

### Auth endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/email/register` | Email + password registration |
| `POST` | `/auth/email/login` | Email + password login |
| `POST` | `/auth/oauth/exchange` | Exchange OAuth code for JWT. Body: `{code, provider}`. Providers: `google`, `discord`, `twitter`, `yandex`, `line`, `kakao`, `telegram` |
| `POST` | `/auth/guest` | Create guest session (Redis, 24h TTL) |
| `POST` | `/auth/refresh` | Refresh JWT using refresh token cookie |
| `POST` | `/auth/logout` | Invalidate current session |

### Example: guest session

```bash
curl -X POST https://api.honeychat.bot/api/v1/auth/guest
# Response: { "access_token": "...", "user_id": "...", "tier": "guest" }
```

## User

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/user/me` | Current user profile (plan, coins, language) |
| `PATCH` | `/user/me` | Update language or preferences |
| `GET` | `/user/stats` | Usage stats (messages, images, remaining quota) |
| `DELETE` | `/user/me` | GDPR-compliant account deletion |

## Characters

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/characters` | List public + user's created characters |
| `GET` | `/characters/{id}` | Character details (bio, scenario, avatar, voice) |
| `POST` | `/characters` | Create custom character (requires 100 coins + paid plan) |
| `DELETE` | `/characters/{id}` | Delete user's character |
| `GET` | `/characters/{id}/voice-preview` | Pre-generated TTS sample (cached in Storj S3) |

## Chat

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat/{char_id}/message` | Send message, get response. Body: `{content, session_id?, mode?}` |
| `GET` | `/chat/{char_id}/history?limit=50` | Recent messages |
| `POST` | `/chat/{char_id}/regenerate` | Regenerate last assistant response |
| `POST` | `/chat/{char_id}/session` | Create new isolated session (premium+) |
| `GET` | `/chat/{char_id}/sessions` | List user's sessions with this character |

## Generation

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/gen/image` | Queue image generation. Body: `{char_id, prompt, style?}` |
| `POST` | `/gen/voice` | Queue TTS. Body: `{char_id, text, voice_id?}` |
| `POST` | `/gen/video` | Queue video generation. Body: `{char_id, prompt, duration?}` |
| `GET` | `/gen/{job_id}` | Poll job status. Response: `{status, result_url?, error?}` |

All generation endpoints are async — returns `job_id`, result polled or pushed via WebSocket.

## Payments

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/pricing/tiers` | List subscription tiers with prices |
| `POST` | `/pay/paddle/checkout` | Create Paddle checkout URL |
| `POST` | `/pay/cryptobot/invoice` | Create CryptoBot invoice (TON/BTC/ETH/USDT). Body: `{tier, asset}` |
| `POST` | `/pay/stars/invoice` | Create Telegram Stars invoice (Telegram Mini App only) |
| `GET` | `/pay/history` | User's payment history |

### Payment webhooks (server-to-server)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhook/paddle` | Paddle webhook (signed) |
| `POST` | `/webhook/cryptobot` | CryptoBot webhook (HMAC signed) |
| `POST` | `/webhook/stars` | Telegram Stars webhook (via Telegram Bot API) |

## Rate Limits

- Rate limits apply per IP (anonymous) and per user (authenticated), with tier-dependent quotas
- Specific thresholds are not published and may change without notice
- When a limit is reached the response is `429 Too Many Requests` with a `Retry-After` header

Rate limit headers on every response:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

## CORS

Allowed origins (production):
- `https://honeychat.bot`
- `https://app.honeychat.bot`
- `https://www.honeychat.bot`

Credentials required (`withCredentials: true` on client).

## Error Format

```json
{
  "error": {
    "code": "insufficient_credits",
    "message": "You have no generation credits left. Upgrade to Premium.",
    "details": { "plan": "free", "quota_reset_at": "2026-04-19T00:00:00Z" }
  }
}
```

Common error codes:
- `401 unauthorized` — missing/invalid JWT
- `403 forbidden` — tier doesn't allow this action
- `409 content_level_exceeded` — requested content exceeds tier max level
- `429 rate_limited` — too many requests
- `503 generation_disabled` — daily cost hard-stop reached

## Related

- Architecture: [architecture.md](architecture.md)
- Main site: [honeychat.bot](https://honeychat.bot)
