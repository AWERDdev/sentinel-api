# Technical Findings — Validation, Safety & Bugs

## Input validation & error architecture

### What works

| Mechanism | Evidence |
|-----------|----------|
| Pydantic request body | `CanaryTokenCreate` with `EmailStr`, required fields |
| Token type allowlist | `allowed_types` check with `HTTP 400` |
| Granular HTTP errors | 400, 403, 404, 429, 500 used appropriately across routes |
| Auth mismatch → 403 | `utils/canary_verify.py` compares path `auth_string` to stored secret |
| Structured logging | INFO/WARNING/ERROR at decision points |

```46:52:routes/canary_generation.py
    allowed_types = ["http", "https", "aws", "web", "url"]
    if token_type_clean not in allowed_types:
        logger.warning(f"Invalid token type attempted: {token_type_clean}")
        raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid token type. Choose from: {', '.join(allowed_types)}"
        )
```

**Verdict:** Earns the **+0.05 validation bonus**. Not exhaustive (no UUID format validation on path params, no request size limits), but meets RaspAPI "proper error handling & input validation" bar.

---

## Persistence layer

### Operations verified

| Operation | File | Redis commands |
|-----------|------|----------------|
| Create token | `canary_generation.py` | `SET` primary + name index |
| Read token | `canary_fetching.py`, `canary_trigger.py` | `GET` |
| Update on trigger | `canary_trigger.py` | `GET` → mutate JSON → `SET` |
| Delete token | `canary_delete.py` | `DEL` primary + index |
| Rate limit | `config.py` | `INCR`, `EXPIRE` |

Trigger mutations include `status`, `breach_count`, and append-only `logs` with IP, user-agent, timestamp — **complex state mutation**, not read-only caching.

**Verdict:** **+0.10 persistence** justified.

---

## External API integration (Resend)

```49:54:routes/canary_trigger.py
         resend.Emails.send({
            "from": "CanaryBox <onboarding@resend.dev>",
            "to": user_email,
            "subject": f"🚨 BREACH DETECTED: {token_name}",
            "html": html_content
         })
```

- Active outbound HTTP to Resend infrastructure
- HTML template with breach metadata
- Async via `BackgroundTasks`
- Errors caught and logged

**Caveat:** Free-tier sender domain (`onboarding@resend.dev`) restricts recipients — documented in `routes/localEmail_testing.md`.

**Verdict:** **+0.10 external API** justified (non-trivial transactional email).

---

## Rate limiting / abuse prevention

```25:47:config.py
def ratelimiter(request: Request):
    ...
    redis_key = f"rate_limit:{client_IP}"
    current_requests = redis_connect.incr(redis_key)
    if current_requests == 1:
        redis_connect.expire(redis_key, WINDOW_SECONDS)
    if current_requests > MAX_REQUESTS:
        raise HTTPException(status_code=429, ...)
```

- Windowed counter stored in Redis (not in-memory)
- Configurable via `REDIS_MAX_REQUESTS` / `REDIS_WINDOW_SECONDS`
- Applied to all 9 route handlers

**Verdict:** **+0.10 rate limiting** justified.

---

## Potential bugs & security notes

| Severity | Issue | Detail |
|----------|-------|--------|
| Medium | Redis startup failure | App starts without valid client; runtime crashes |
| Medium | Open token generation | No auth on `POST /generate-token` |
| Medium | Name collision | Duplicate names overwrite index key |
| Low | X-Forwarded-For trust | Client can spoof IP in logs if not behind trusted proxy |
| Low | Field naming | `CanaryToken` Pydantic field vs model class name collision risk |
| Low | Race on trigger | Concurrent triggers can lose log entries (last-write-wins JSON) |
| Info | Typo in errors | `"Cannary token not found"` in verify helper |
| Info | README drift | Fetch/delete URLs omit required `{auth_string}` path segment |

---

## Endpoint inventory

| Method | Path | Rate limited | Auth |
|--------|------|--------------|------|
| GET | `/` | Yes | No |
| GET | `/canary/docs` | Yes | No |
| POST | `/canary/generate-token` | Yes | No |
| GET | `/canary/fetch/id/{token_id}/{auth_string}` | Yes | Per-token secret |
| GET | `/canary/fetch/name/{name}/{auth_string}` | Yes | Per-token secret |
| GET | `/canary/trigger/{token_id}` | Yes | No (intentional — honeypot) |
| DELETE | `/canary/delete/id/{token_id}/{auth_string}` | Yes | Per-token secret |
| DELETE | `/canary/delete/name/{name}/{auth_string}` | Yes | Per-token secret |

**RaspAPI minimum:** 3 GET + 1 POST — **exceeded** (5+ GET, 1 POST, 2 DELETE).
