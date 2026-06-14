# Code Quality & Architecture Audit

## Strengths

### Modular FastAPI layout

The project follows a conventional, review-friendly structure:

```text
main.py              → app bootstrap, router registration
config.py            → shared Redis client + rate limiter dependency
models/              → Pydantic input/storage schemas + Redis settings
routes/              → one module per concern (generate, fetch, trigger, delete)
utils/               → auth verification helpers
logger_config/       → centralized logging factory
DOCS/                → architecture, API reference, setup, design decisions
```

Routers are registered cleanly in `main.py` with no monolithic handler file.

### Separation of input vs storage models

`CanaryTokenCreate` (HTTP boundary) is distinct from `CanaryToken` (Redis document). Server-owned fields (`token_ID`, `status`, `breach_count`, `logs`) cannot be injected at creation time — correct least-privilege pattern.

### Cross-cutting policy via dependencies

Rate limiting is applied uniformly with `Depends(ratelimiter)` on every route including `/` and `/canary/docs`. This avoids copy-pasted guard logic.

### Redis data model is intentional

Three key namespaces are used with clear purpose:

| Key pattern | Purpose |
|-------------|---------|
| `canary:token:{uuid}` | Primary JSON document |
| `canary:name:{normalized}` | Secondary index for O(1) name lookup |
| `rate_limit:{ip}` | Windowed abuse counter |

Trigger flow performs read → mutate (`status`, `breach_count`, `logs`) → write — genuine stateful persistence, not a stub.

### Honeypot deception layer

The trigger endpoint returns a humorous fake error payload while updating Redis and queueing email alerts via `BackgroundTasks`. Email failure is isolated in `send_security_alert` so Resend outages do not block the tripwire response.

### Logging architecture

`setupLogger()` configures three named loggers (`app`, `app.redis`, `app.rate_limiter`) with separate file handlers plus console output. Vercel-aware `/tmp/` path selection shows deployment awareness.

### Documentation depth (unusually strong for YSWS)

Beyond auto-generated OpenAPI at `/docs`, the repo ships handwritten `DOCS/` covering architecture diagrams, API reference, setup, and design rationale. Postman fixtures and manual test cases exist under `test-fixtures/`.

---

## Room for Improvement

### 1. Unauthenticated token generation

`POST /canary/generate-token` has no ownership secret or API key. Any client can flood Redis with tokens. Fetch/delete require `auth_string`, but generation does not — asymmetric security model.

**Fix:** Require an operator API key header on mutating admin routes, or return the secret only once and document demo keys.

### 2. Naming and schema confusion

The `CanaryToken` model uses:

- `auth_string` → UUID secret for fetch/delete auth
- `CanaryToken` → deployable decoy payload (URL or AWS block)

This inverts intuitive naming (`auth_string` sounds like the decoy). README and API docs describe `auth_string` as the deployable payload — **documentation drift from code**.

**Fix:** Rename fields to `owner_secret` and `decoy_payload`; align README.

### 3. Inconsistent formatting in `canary_trigger.py`

Mixed indentation (2-space body inside 4-space function) and a broad `except Exception` that masks JSON parse errors as 500s reduce maintainability.

### 4. Redis failure is non-fatal at startup

```13:21:config.py
try:
    redis_connect = redis.from_url(...)
    redis_logger.info(...)
except Exception as e:
    redis_logger.error(f"Connecting to Redis failed {e}")
```

If connection fails, `redis_connect` may be undefined and all routes crash at first Redis call. No health check or fail-fast.

### 5. Sync Redis in async handler

`trigger_canary` is `async` but uses blocking `redis_connect.get/set`. Under load this blocks the event loop. Acceptable at small scale; use `redis.asyncio` or run in thread pool for production.

### 6. Name index collisions

Generating two tokens with the same `name` overwrites `canary:name:{name}` without conflict detection. Deletes may orphan or mis-associate records.

### 7. `verify_token_owner` not used as FastAPI `Depends`

Auth checks are manual function calls in route bodies instead of reusable dependencies — works, but misses automatic OpenAPI documentation of auth requirements.

### 8. Incomplete `requirements.txt`

Missing `uvicorn`, `python-dotenv`, and `email-validator` (required for `EmailStr`). Fresh installs may fail until manual `pip install`.

### 9. No automated test suite

Fixtures exist for manual/Postman testing but there are no pytest tests or CI. Regressions in auth matching or token generation would not be caught automatically.

---

## Exceptional patterns worth credit

| Pattern | Location | Why it matters |
|---------|----------|----------------|
| Type-specific decoy payloads | `canary_generation.py` | HTTP URL vs AWS credential block increases honeypot fidelity |
| Background email dispatch | `canary_trigger.py` | Keeps tripwire response fast; failures logged not raised |
| Dual lookup (ID + name) | fetch/delete routes | Practical operator UX without Redis SCAN |
| Content-negotiated root | `main.py` | HTML welcome page for browsers, JSON for API clients |
