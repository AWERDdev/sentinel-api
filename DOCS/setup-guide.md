# Sentinel API — Setup Guide

This guide walks through environment configuration, dependency installation, local execution, and Redis connectivity verification for the Sentinel (CanaryBox) API.

---

## Prerequisites

| Requirement | Version / notes |
|-------------|-----------------|
| Python | 3.10+ recommended (project uses Pydantic v2, FastAPI 0.136+) |
| Redis | Running instance reachable from the API host (local or remote) |
| Resend account | Optional for development; required for breach email alerts |

---

## 1. Clone and Install Dependencies

```bash
git clone https://github.com/AWERDdev/sentinel-api.git
cd sentinel-api
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

The route modules also import `python-dotenv`, `resend`, and `pydantic-settings`. If any import fails after installing `requirements.txt`, install the missing packages explicitly:

```bash
pip install python-dotenv resend pydantic-settings
```

---

## 2. Environment Variables

Create a `.env` file in the project root (same directory as `main.py`). The application loads it via `dotenv.load_dotenv()` in route modules and via Pydantic Settings for Redis configuration.

### Application variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DOMAIN` | No | `http://127.0.0.1:8000` | Base URL used when generating `http`/`https` tripwire links. **Set this in production** to your public API hostname. |
| `RESEND_API_KEY` | Yes (for alerts) | — | API key for [Resend](https://resend.com). Used by `routes/canary_trigger.py` to send breach notification emails. Without it, triggers still work but emails fail (errors are logged). |

### Redis variables (`REDIS_` prefix)

Loaded by `redis_Settings` in `models/redis_settings_model.py`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_HOST` | No | `localhost` | Redis server hostname |
| `REDIS_PORT` | No | `6379` | Redis server port |
| `REDIS_DECODE_RESPONSES` | No | `true` | Decode Redis byte responses to strings |
| `REDIS_ENCODING` | No | `utf-8` | String encoding for Redis client |
| `REDIS_MAX_REQUESTS` | No | `5` | Max requests per IP per rate-limit window |
| `REDIS_WINDOW_SECONDS` | No | `60` | Rate-limit window length in seconds |

### Example `.env`

```env
# Public base URL for generated tripwire links
DOMAIN=https://canary.example.com

# Resend email API key
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx

# Redis connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_MAX_REQUESTS=10
REDIS_WINDOW_SECONDS=60
```

> **Security:** Never commit `.env` to version control. The project's `.gitignore` should exclude it.

---

## 3. Start Redis

### Option A — Local Redis (Docker)

```bash
docker run -d --name sentinel-redis -p 6379:6379 redis:7-alpine
```

### Option B — Local Redis (native)

Install Redis for your OS and start the server on port `6379` (or update `REDIS_PORT` accordingly).

### Option C — Managed Redis (e.g., Upstash)

Set `REDIS_HOST` and `REDIS_PORT` to your provider's endpoint values.

---

## 4. Start the Application

From the project root with your virtual environment activated:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

| Flag | Purpose |
|------|---------|
| `--reload` | Auto-restart on code changes (development only) |
| `--host 127.0.0.1` | Bind to localhost |
| `--port 8000` | Default port referenced in `DOMAIN` fallback |

On startup:

- `setupLogger()` writes to `app.log`, `redis.log`, `rate_limiter.log`, and the console.
- `config.py` attempts a Redis connection and logs success or failure to `redis.log`.

---

## 5. Verify the API Is Running

### Health check

```bash
curl http://127.0.0.1:8000/
```

Expected:

```json
{"message": "welcome to canary token generator API"}
```

### Interactive API docs

Open in a browser:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## 6. Verify Redis Connectivity

### Method 1 — Application logs

After starting Uvicorn, check `redis.log` or console output for:

```text
Successfully connected to Redis on port 6379
```

If connection fails, you will see:

```text
Connecting to Redis failed <error details>
```

### Method 2 — End-to-end token round-trip

Generate a token (writes to Redis), then fetch it (reads from Redis):

```bash
# Create token
curl -X POST http://127.0.0.1:8000/canary/generate-token \
  -H "Content-Type: application/json" \
  -d '{
    "token_type": "http",
    "name": "redis connectivity test",
    "alert_email": "you@example.com"
  }'
```

Copy the `Token_ID` from the response, then:

```bash
curl http://127.0.0.1:8000/canary/fetch/id/{Token_ID}
```

A `200` response with the full token object confirms Redis read/write is working.

### Method 3 — Redis CLI inspection

```bash
redis-cli ping
# Expected: PONG

# After generating a token:
redis-cli KEYS "canary:*"
redis-cli GET "canary:token:<your-token-id>"
```

You should see keys matching:

- `canary:token:{uuid}`
- `canary:name:redis_connectivity_test`
- `rate_limit:127.0.0.1` (after API requests)

### Method 4 — Python one-liner

```bash
python -c "from config import redis_connect; print(redis_connect.ping())"
```

Expected output: `True`

---

## 7. Verify Email Alerts (Optional)

1. Set a valid `RESEND_API_KEY` in `.env`.
2. Generate a token with your Resend-verified recipient email as `alert_email`.
3. Trigger the tripwire:

```bash
curl http://127.0.0.1:8000/canary/trigger/{Token_ID}
```

4. Check your inbox for subject `🚨 BREACH DETECTED: {token_name}`.
5. Confirm `app.log` contains: `Security alert email successfully dispatched to ...`

> The default sender is `CanaryBox <onboarding@resend.dev>` (Resend sandbox). Production deployments should configure a verified domain in Resend.

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `Connecting to Redis failed` on startup | Redis not running or wrong host/port | Start Redis; verify `REDIS_HOST` / `REDIS_PORT` |
| `429 Too Many Requests` during testing | Rate limit hit (default 5/min) | Wait 60s or raise `REDIS_MAX_REQUESTS` |
| `404` on fetch after create | Redis write failed silently | Check Redis logs; verify `redis_connect.set` succeeded |
| No email received | Missing/invalid `RESEND_API_KEY` or unverified recipient | Check `app.log` for email errors; verify Resend dashboard |
| HTTP links point to localhost in production | `DOMAIN` not set | Set `DOMAIN` to your public API URL |

---

## 9. Log Files

| File | Contents |
|------|----------|
| `app.log` | General application events, token lifecycle, email dispatch |
| `redis.log` | Redis connection status |
| `rate_limiter.log` | Rate-limit violations by IP |

---

## Next Steps

- Review [architecture.md](./architecture.md) for system design and request flow.
- Review [api-reference.md](./api-reference.md) for full endpoint specifications.
- Review [design-decisions.md](./design-decisions.md) for engineering rationale.
