# Sentinel API — System Architecture

Sentinel API (also referred to as **CanaryBox** in project notes) is a lightweight honeypot canary token service. Operators provision decoy credentials or URLs, embed them in real environments, and receive alerts when an unauthorized party interacts with those tripwires.

The system is intentionally small: a single FastAPI application, an in-memory-speed Redis datastore, and asynchronous email delivery via Resend. There is no separate worker tier, message queue, or relational database.

---

## High-Level Overview

```text
┌─────────────────┐     HTTP      ┌──────────────────┐     Redis      ┌─────────────┐
│  Client /       │ ────────────► │  FastAPI App     │ ◄────────────► │  Redis      │
│  Attacker       │               │  (main.py)       │                │  (state)    │
└─────────────────┘               └────────┬─────────┘                └─────────────┘
                                           │
                                           │ BackgroundTasks
                                           ▼
                                  ┌──────────────────┐
                                  │  Resend API      │
                                  │  (email alerts)  │
                                  └──────────────────┘
```

| Layer | Responsibility |
|-------|----------------|
| **FastAPI** | HTTP routing, request validation (Pydantic), dependency injection (rate limiter), background task scheduling |
| **Redis** | Token persistence, name-to-ID indexing, per-IP rate limiting |
| **Resend** | Outbound breach notification emails |
| **Pydantic models** | Input schemas (`CanaryTokenCreate`) and stored token shape (`CanaryToken`) |

---

## Project Structure

```text
sentinel-api/
├── main.py                      # App entry point; registers routers and root routes
├── config.py                    # Redis client + IP rate limiter dependency
├── requirements.txt             # Python dependencies
├── models/
│   ├── canary_model.py          # Pydantic models for create input and stored tokens
│   └── redis_settings_model.py  # Redis connection and rate-limit settings (env-driven)
├── routes/
│   ├── canary_generation.py     # POST /canary/generate-token
│   ├── canary_fetching.py       # GET  /canary/fetch/id|name/...
│   ├── canary_trigger.py        # GET  /canary/trigger/{token_id}
│   └── canary_delete.py         # DELETE /canary/delete/id|name/...
└── logger_config/
    └── logs_handler.py          # File + console logging for app, Redis, rate limiter
```

Routers are modular: each route file defines an `APIRouter` with `prefix="/canary"` and is mounted in `main.py`. Shared infrastructure (`redis_connect`, `ratelimiter`) lives in `config.py` and is imported by route modules.

---

## Role of FastAPI

FastAPI serves three architectural purposes in this project:

1. **API surface and validation** — Endpoints accept JSON bodies validated against `CanaryTokenCreate`. Invalid payloads are rejected by Pydantic before business logic runs.

2. **Composable middleware via dependencies** — Every protected route declares `dependencies=[Depends(ratelimiter)]`. The rate limiter runs before the handler and can short-circuit with `429 Too Many Requests`.

3. **Non-blocking alert delivery** — The trigger endpoint uses `BackgroundTasks` to send email alerts after the HTTP response is prepared, so slow or failing email infrastructure does not block the deceptive response to the attacker.

The application is started with Uvicorn (`uvicorn main:app --reload` per `main.py`). FastAPI also exposes auto-generated OpenAPI docs at `/docs` and `/redoc` by default.

---

## Role of Redis

Redis is the sole persistence layer. It holds three categories of data:

### 1. Primary token records

- **Key pattern:** `canary:token:{token_id}`
- **Value:** JSON-serialized `CanaryToken` (ID, type, name, alert email, auth string, status, breach count, logs, timestamps)

### 2. Secondary name index

- **Key pattern:** `canary:name:{normalized_name}` where spaces become underscores and the name is lowercased
- **Value:** The token UUID string
- **Purpose:** O(1) lookup by human-readable name for fetch and delete operations without scanning all tokens

### 3. Rate-limit counters

- **Key pattern:** `rate_limit:{client_ip}`
- **Value:** Integer request count, with TTL set on first request in a window (`REDIS_WINDOW_SECONDS`, default 60s)
- **Purpose:** Enforce `REDIS_MAX_REQUESTS` (default 5) per IP per window

Redis was chosen because token state is small, ephemeral, and accessed by simple key lookups. No migrations, joins, or complex queries are required. The same Redis instance also backs the sliding-window rate limiter with atomic `INCR` and `EXPIRE`.

Connection settings are loaded from environment variables via `redis_Settings` (`REDIS_HOST`, `REDIS_PORT`, etc.) in `models/redis_settings_model.py`.

---

## Request Flow: Token Generation → Trigger Interception

The canary lifecycle has four phases: **provision**, **deploy**, **intercept**, and **alert**.

```mermaid
sequenceDiagram
    participant Op as Operator
    participant API as FastAPI
    participant R as Redis
    participant Atk as Attacker
    participant Email as Resend

    Note over Op,R: Phase 1 — Token Generation
    Op->>API: POST /canary/generate-token
    API->>API: Validate token_type, sanitize input
    API->>API: Generate UUID, build auth_string (URL or AWS block)
    API->>R: SET canary:token:{id}
    API->>R: SET canary:name:{name} → id
    API-->>Op: 201 + Canary_Token payload

    Note over Op,Atk: Phase 2 — Deploy (external)
    Op->>Op: Embed URL/credentials in env, repo, config, etc.

    Note over Atk,Email: Phase 3 & 4 — Trigger Interception
    Atk->>API: GET /canary/trigger/{token_id}
    API->>R: GET canary:token:{id}
    API->>API: Extract IP, User-Agent
    API->>API: status=COMPROMISED, breach_count++, append log
    API->>R: SET canary:token:{id} (updated)
    API->>Email: BackgroundTasks → send_security_alert
    API-->>Atk: 200 + deceptive error JSON
    Email-->>Op: Breach notification email
```

### Phase 1: Token generation

1. Operator sends `POST /canary/generate-token` with `token_type`, `name`, and `alert_email`.
2. `token_type` is stripped and lowercased; only `http`, `https`, and `aws` are accepted.
3. A UUID becomes `token_id`.
4. Depending on type:
   - **http/https:** `auth_string` is a tracking URL: `{DOMAIN}/canary/trigger/{token_id}`
   - **aws:** `auth_string` is a fake credential block embedding the token ID
5. A `CanaryToken` document is written to Redis; a name index key is created.
6. The operator receives the decoy payload to deploy.

### Phase 2: Deployment (outside the API)

The operator places the generated string in a `.env` file, password manager export, S3 bucket policy snippet, or similar. This step is not implemented in code but is essential to the threat model.

### Phase 3: Trigger interception

1. An unauthorized client requests `GET /canary/trigger/{token_id}` (e.g., by following the embedded URL or invoking a fake AWS key).
2. The handler loads the token from Redis. Missing tokens return `404`.
3. Client identity is derived from `X-Forwarded-For` (first hop) or `request.client.host`, plus `User-Agent`.
4. Token state is mutated: `status` → `COMPROMISED`, `breach_count` incremented, a log entry appended.
5. Updated JSON is written back to Redis.

### Phase 4: Alert and deception

1. If `alert_email` is present, `send_security_alert` is queued on `BackgroundTasks`.
2. The HTTP response body mimics a generic server failure (`status: error`, `code: INTERNAL_SERVER_ERROR`) while typically returning HTTP `200 OK` — so automated scanners and casual attackers do not realize they tripped a honeypot.
3. The operator receives an HTML email with IP, user agent, and timestamp.

---

## Cross-Cutting Concerns

### Rate limiting

All documented canary routes and the root `/` endpoint use the shared `ratelimiter` dependency. Limits are per client IP, stored in Redis, and configurable via `REDIS_MAX_REQUESTS` and `REDIS_WINDOW_SECONDS`.

### Logging

`setupLogger()` configures three named loggers (`app`, `app.redis`, `app.rate_limiter`) writing to `app.log`, `redis.log`, `rate_limiter.log`, and the console.

### Data model evolution

Stored tokens accumulate breach telemetry (`logs`, `breach_count`, `status`) only after a trigger event. Fetch endpoints return the live Redis document, so post-trigger inspection shows full incident history.

---

## Deployment Considerations

- Set `DOMAIN` to the public base URL in production so generated HTTP/HTTPS tripwire links resolve correctly.
- Place Redis behind a managed service (e.g., Upstash) or run locally for development.
- Configure `RESEND_API_KEY` for alert delivery; without it, triggers still update Redis but emails will fail silently (logged as errors).
- When behind a reverse proxy, ensure `X-Forwarded-For` is set so attacker IP attribution is accurate.

For endpoint-level detail, see [api-reference.md](./api-reference.md). For local setup, see [setup-guide.md](./setup-guide.md).
