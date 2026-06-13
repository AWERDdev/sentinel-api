# Sentinel API — Design Decisions

This document explains the engineering rationale behind key choices in the Sentinel (CanaryBox) codebase. Each section ties a decision to the threat model, operational constraints, or implementation trade-offs visible in the current source.

---

## 1. FastAPI as the Application Framework

**Decision:** Use FastAPI with modular `APIRouter` instances rather than a monolithic route file or a heavier framework.

**Why:**

- **Pydantic-native validation** — `CanaryTokenCreate` enforces structure at the HTTP boundary. Invalid `token_type` values and missing fields are rejected before Redis is touched.
- **Dependency injection for cross-cutting policy** — Rate limiting is a `Depends(ratelimiter)` declaration on every route, not duplicated guard code in each handler.
- **Async-ready trigger handler** — The honeypot endpoint is `async` and integrates `BackgroundTasks` without introducing Celery, Redis queues, or a separate worker process.
- **Low operational footprint** — A single Uvicorn process is sufficient for a developer-focused honeypot tool.

**Trade-off:** No built-in admin UI or multi-tenant auth. The API assumes trusted operators control token generation and deletion endpoints.

---

## 2. Redis as the Sole Datastore

**Decision:** Store all token documents, name indexes, and rate-limit counters in Redis with simple string keys.

**Why:**

- **Access pattern fit** — Every operation is a point lookup (`GET`/`SET`/`DEL`/`INCR`) by known key. No relational joins or ad-hoc queries.
- **Speed** — Trigger interception must be fast; Redis keeps read/write latency low so the deceptive response returns quickly.
- **Dual use for rate limiting** — The same client connection performs `INCR` + `EXPIRE` on `rate_limit:{ip}` keys, avoiding a second infrastructure component.
- **Schema flexibility** — Token JSON can accumulate breach `logs` without migrations. The document shape evolves in place.

**Key design:**

```text
canary:token:{uuid}     → full token JSON (primary record)
canary:name:{normalized} → uuid string (secondary index)
rate_limit:{ip}         → integer counter with TTL
```

**Trade-off:** No durable audit trail beyond what is stored on each token's `logs` array. Redis persistence configuration (RDB/AOF) is an deployment concern, not enforced in code.

---

## 3. Secondary Name Index

**Decision:** Maintain a separate Redis key `canary:name:{normalized_name}` mapping to `token_id`, rather than scanning all token keys.

**Why:**

- **O(1) lookup by name** — Operators think in terms of labels like "Production Database Honey Key", not UUIDs.
- **Normalized keys** — Names are lowercased and spaces replaced with underscores (`name.replace(' ', '_').lower()`), reducing accidental duplicate-index issues from casing differences.

**Trade-off:** Name uniqueness is not enforced atomically. Creating two tokens with names that normalize to the same key would overwrite the index (last write wins). The API treats `name` as a convenience index, not a strict unique constraint.

---

## 4. `token_type` Sanitization and Validation

**Decision:** Apply `data.token_type.strip().lower()` and whitelist only `["http", "https", "aws"]`.

**Why:**

- **Input normalization** — Clients may send `"HTTP"`, `" Http "`, etc. Stripping and lowercasing makes validation predictable and prevents duplicate logic branches for casing variants.
- **Explicit allowlist** — Only supported honeypot formats receive generated payloads. Unknown types fail fast with `400 Bad Request` and a clear message listing allowed values.
- **Branching safety** — Generation logic uses clean `if/elif` on known types. Without sanitization, typos could fall through and produce empty `auth_string` values.

**Relevant code path:**

```python
token_type_clean = data.token_type.strip().lower()
allowed_types = ["http", "https", "aws"]
if token_type_clean not in allowed_types:
    raise HTTPException(status_code=400, ...)
```

**Trade-off:** No extensibility plugin system. Adding a new token type (e.g., `dns` or `slack_webhook`) requires a code change to the allowlist and generation branch.

---

## 5. Type-Specific Decoy Payloads

**Decision:** Generate different `auth_string` formats per `token_type`.

| Type | Payload shape | Rationale |
|------|---------------|-----------|
| `http` / `https` | Full URL to `/canary/trigger/{id}` | Mimics a leaked admin link or webhook; any HTTP client triggers the tripwire |
| `aws` | Fake `aws_access_key_id` / `aws_secret_access_key` block | Mimics credentials in `.env`, CI secrets, or config dumps; key embeds trackable ID prefix |

**Why:** High-fidelity decoys match real secret formats attackers already scan for, increasing the chance of interaction compared to generic placeholder strings.

**`DOMAIN` dependency:** HTTP/HTTPS URLs use `os.getenv('DOMAIN', 'http://127.0.0.1:8000')` so the same codebase works locally and in production without hardcoding hostnames.

---

## 6. BackgroundTasks for Email Processing

**Decision:** Queue `send_security_alert` via FastAPI `BackgroundTasks` instead of sending email synchronously in the trigger handler.

**Why:**

- **Response latency** — The honeypot must return quickly. Waiting on Resend's HTTP API would add hundreds of milliseconds to seconds of delay and could timeout under load.
- **Failure isolation** — Email errors are caught and logged inside `send_security_alert`. A Resend outage does not prevent Redis state updates or the deceptive HTTP response (though the operator may not receive the alert).
- **Simplicity** — No message broker, no worker fleet. For low-to-moderate trigger volume, in-process background tasks are sufficient.

```python
background_tasks.add_task(
    send_security_alert,
    user_email,
    token_data.get("name", "Unknown Token"),
    attacker_ip,
    user_agent,
)
```

**Trade-off:** Background tasks run in the same process as the API. If the Uvicorn worker is killed immediately after responding, an in-flight email task could be lost. For production hardening at scale, a durable queue would be the next step.

---

## 7. Honeytoken Deception Strategy

**Decision:** On successful trigger, return HTTP `200 OK` with a JSON body that **mimics a generic server error**, rather than confirming the honeypot fired.

**Deceptive response body:**

```json
{
  "status": "error",
  "code": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred while processing your request."
}
```

**Why:**

- **Attacker psychology** — Automated scanners and opportunistic actors often abandon paths that return obvious "access logged" or "honeypot" messages. A bland internal error suggests a dead end, not active monitoring.
- **Status code choice** — Using `200` with an error-shaped body avoids some tools flagging `4xx`/`5xx` as "broken" and deprioritizing the URL. Real `500` responses are reserved for genuine handler failures (`HTTPException` with `500` and `detail: "failed to trigger canary token"`).
- **Contrast with operator endpoints** — Management routes (`generate-token`, `fetch`, `delete`) return honest, descriptive messages because they are called by trusted operators, not adversaries.

**What still happens server-side (invisible to attacker):**

1. Token `status` → `COMPROMISED`
2. `breach_count` incremented
3. Attacker IP and `User-Agent` appended to `logs`
4. Email alert dispatched in the background

**Trade-off:** A sophisticated attacker inspecting response timing, headers, or correlating behavior across requests might infer monitoring. Deception raises the bar; it does not guarantee invisibility.

---

## 8. Client IP Attribution

**Decision:** Prefer `X-Forwarded-For` (first hop) when present; otherwise use `request.client.host`.

**Why:**

- Deployments behind reverse proxies (nginx, Cloudflare, load balancers) see the proxy IP without `X-Forwarded-For`.
- Taking the first comma-separated value follows common convention for original client IP.

**Trade-off:** Spoofed `X-Forwarded-For` headers can poison logs if the API is exposed directly without a trusted proxy stripping client-supplied values. Production deployments should only trust forwarded headers from known proxies.

---

## 9. IP-Based Rate Limiting on All Routes

**Decision:** Apply `ratelimiter` to root, generation, fetch, trigger, and delete endpoints.

**Why:**

- **Abuse prevention** — Attackers could spam `generate-token` or `trigger` to flood Redis, logs, or Resend quotas.
- **Redis-backed sliding window** — `INCR` on first request sets `EXPIRE`; subsequent requests increment atomically. Simple and consistent with existing infrastructure.
- **Configurable thresholds** — `REDIS_MAX_REQUESTS` and `REDIS_WINDOW_SECONDS` tune strictness per environment.

**Trade-off:** Shared NAT IPs (corporate networks) share one bucket. Trigger endpoint rate limiting could theoretically slow repeated legitimate breach attempts from the same egress IP — usually acceptable for a honeypot.

---

## 10. Pydantic Models: Input vs. Storage

**Decision:** Separate `CanaryTokenCreate` (API input) from `CanaryToken` (Redis document).

**Why:**

- **Least privilege on input** — Clients cannot set `token_ID`, `breach_count`, `status`, or `logs` at creation time. The server owns those fields.
- **Defaults on storage** — `created_at`, `is_active`, `status`, `breach_count`, and `logs` are initialized server-side with safe defaults.
- **Serialization** — `model_dump_json()` produces consistent JSON for Redis storage on create.

**Trade-off:** Fetch endpoints return the full internal document including `alert_email`. Operators must treat fetch responses as sensitive.

---

## 11. Logging Strategy

**Decision:** Three dedicated loggers (`app`, `app.redis`, `app.rate_limiter`) with separate log files plus console output.

**Why:**

- **Operational separation** — Redis connection issues and rate-limit events can be diagnosed without sifting through all application logs.
- **Security auditing** — Token generation, triggers, deletions, and email dispatch are logged at INFO; failures at WARNING/ERROR.

**Trade-off:** Log files grow unbounded; no rotation is configured in code.

---

## 12. Error Handling Philosophy by Endpoint Class

| Endpoint class | Error style | Rationale |
|----------------|-------------|-----------|
| Operator (generate, fetch, delete) | Honest HTTP status + `detail` string | Operators need actionable feedback |
| Honeypot (trigger) | Deceptive `200` on success; honest `404` only if token missing | Balance attribution with deception |
| Infrastructure failures | `500` with generic detail | Avoid leaking stack traces to clients |

Delete handlers wrap unexpected exceptions in `500` with a generic message while logging the real error server-side — a standard pattern to avoid information disclosure.

---

## Summary

Sentinel API optimizes for **simplicity, speed, and deception**:

- FastAPI + Pydantic keep the HTTP layer strict and thin.
- Redis provides fast key-value storage and rate limiting in one service.
- Background email delivery protects trigger response time.
- Sanitized `token_type` validation prevents ambiguous decoy generation.
- The honeypot returns fake errors so attackers stay unaware while operators receive real alerts.

These choices reflect a developer-tool threat model: trusted operators provision tokens; untrusted parties trigger them. Hardening for untrusted operator access (authentication, authorization) is intentionally out of scope in the current codebase.
