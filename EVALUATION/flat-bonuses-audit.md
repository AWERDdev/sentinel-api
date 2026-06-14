# Flat Bonuses Audit — Evidence & Scoring

Each bonus requires **active, functional implementation**, not configuration stubs or commented-out code.

---

## 1. Persistence Layer — **+0.10 ✅ AWARDED**

**Requirement:** Complex state mutations or records in an external database/key-value store.

### Evidence

| Operation | Key Pattern | File |
|-----------|-------------|------|
| CREATE token | `canary:token:{uuid}` ← JSON | `routes/canary_generation.py:91-92` |
| CREATE name index | `canary:name:{normalized}` ← uuid | `routes/canary_generation.py:95-96` |
| READ by ID | `GET canary:token:{id}` | `routes/canary_fetching.py:43` |
| READ by name (2-hop) | name index → token key | `routes/canary_fetching.py:69-83` |
| UPDATE on trigger | status, breach_count, logs[] | `routes/canary_trigger.py:99-118` |
| DELETE token + index | `DEL` both keys | `routes/canary_delete.py:52-53, 93-94` |
| Rate limit counters | `rate_limit:{ip}` INCR/EXPIRE | `config.py:34-39` |

### Stored model shape (`CanaryToken`)

```python
token_ID, token_type, name, alert_email, created_at,
is_active, auth_string, status, breach_count, logs[]
```

**Verdict:** Meets rubric. Redis is the sole datastore with meaningful state mutation on trigger events, not just cache reads.

---

## 2. External API Integration — **+0.10 ✅ AWARDED**

**Requirement:** Active, out-of-band network calls to an external service provider.

### Evidence

```python
# routes/canary_trigger.py
resend.api_key = os.getenv("RESEND_API_KEY")
resend.Emails.send({
    "from": "CanaryBox <onboarding@resend.dev>",
    "to": user_email,
    "subject": f"🚨 BREACH DETECTED: {token_name}",
    "html": html_content
})
```

- Called from `send_security_alert()` via `BackgroundTasks.add_task()` on every successful trigger with a valid `alert_email`.
- Non-trivial: HTML template includes IP, User-Agent, timestamp.
- Failure path logged without crashing the request.

**Verdict:** Meets rubric. Resend is a real third-party transactional email API, not a mock.

**Deduction note:** Uses Resend sandbox sender `onboarding@resend.dev` — acceptable for dev/demo but production would need verified domain.

---

## 3. Abuse Prevention & Rate Limiting — **+0.10 ✅ AWARDED**

**Requirement:** Functional endpoint protection with windowed state checks.

### Evidence (`config.py`)

```python
def ratelimiter(request: Request):
    client_IP = ...  # X-Forwarded-For or request.client.host
    redis_key = f"rate_limit:{client_IP}"
    current_requests = redis_connect.incr(redis_key)
    if current_requests == 1:
        redis_connect.expire(redis_key, WINDOW_SECONDS)
    if current_requests > MAX_REQUESTS:
        raise HTTPException(status_code=429, ...)
```

### Coverage

Applied via `dependencies=[Depends(ratelimiter)]` on:

- All four route modules (generate, fetch, trigger, delete)
- Root `/` and `/canary/docs` in `main.py`

Configurable via `REDIS_MAX_REQUESTS` (default 5) and `REDIS_WINDOW_SECONDS` (default 60).

**Verdict:** Meets rubric. Custom implementation (not a library middleware wrapper only), Redis-backed, windowed.

**Minor flaw:** `INCR` + conditional `EXPIRE` is not a single atomic Lua script — race window exists under extreme concurrency but is acceptable at this scale.

---

## 4. Input Validation & Error Architecture — **+0.05 ✅ AWARDED**

**Requirement:** Pydantic schemas, type casting, HTTPException traps, system logs.

### Pydantic input boundary

```python
class CanaryTokenCreate(BaseModel):
    token_type: str = Field(...)
    name: str = Field(...)
    alert_email: str = Field(...)  # Note: not EmailStr
```

FastAPI auto-validates JSON body before handler runs.

### Application-level validation

- `token_type.strip().lower()` + allowlist check → `400`
- Missing token in Redis → `404`
- Rate limit exceeded → `429`
- Delete/trigger failures → `500` with logged context

### Logging

- Route-level `logger.info/warning/error` across all handlers
- Dedicated `app.rate_limiter` and `app.redis` loggers via `setupLogger()`

**Verdict:** Meets rubric. Not exemplary (no `EmailStr`, redundant manual empty-field check that Pydantic already prevents), but clearly qualifies.

---

## 5. Authorization — **+0.00 ❌ NOT AWARDED**

No JWT, API keys, or user-token gates on any endpoint. Explicitly documented as out of scope in `DOCS/design-decisions.md`.

---

## 6. Pagination — **+0.00 ❌ NOT AWARDED**

No list endpoints. Fetch is by ID or name only. No `limit`/`offset`/`cursor` parameters.

---

## 7. Additional Endpoints — **+0.12 ✅ AWARDED (4 × +0.03)**

Minimum viable RaspAPI projects typically require a small CRUD surface. Beyond core generate + fetch + trigger:

| Extra endpoint | Bonus |
|----------------|-------|
| `GET /canary/fetch/name/{name}` | +0.03 |
| `DELETE /canary/delete/id/{token_id}` | +0.03 |
| `DELETE /canary/delete/name/{token_name}` | +0.03 |
| `GET /canary/docs` (custom docs hub) | +0.03 |

Cap of 4 extra endpoints reached.

---

## Flat Bonus Totals

| Rubric scope | Sum | Base multiplier |
|--------------|-----|-----------------|
| Review brief (4 categories) | +0.35 | **1.35** |
| Full official RaspAPI | +0.47 | **1.47** (under 1.5 cap) |
