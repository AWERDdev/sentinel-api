# Technical Findings — Validation & Safety Review

Objective scan of database interactions, rate limiters, and background mail dispatch.

---

## Redis Interactions — **Functional with caveats**

### Safe patterns observed

- JSON serialization via `model_dump_json()` on create
- Explicit key namespaces prevent collision (`canary:`, `rate_limit:`)
- Delete removes both primary and index keys (no obvious orphan index on ID delete)
- Trigger append-only log mutation preserves prior entries

### Risks

| Risk | Detail |
|------|--------|
| Connection fail-open | App starts even if Redis unreachable |
| Name index overwrite | No uniqueness lock — duplicate normalized names overwrite index |
| No TTL on tokens | Tokens persist forever unless deleted |
| Sync client in async route | Blocks event loop under load |
| JSON manual dumps on trigger | Bypasses Pydantic re-validation after mutation |

---

## Rate Limiter — **Functional**

### Flow

1. Resolve client IP (`X-Forwarded-For` first hop or direct host)
2. `INCR rate_limit:{ip}`
3. Set `EXPIRE` on first request in window
4. Return 429 if count > `MAX_REQUESTS`

### Trust model

Behind reverse proxy, accuracy depends on proxy setting `X-Forwarded-For`. Documented in architecture guide.

### Edge cases

- Shared NAT IPs rate-limit together (expected for IP-based limiting)
- `INCR` without transaction with `EXPIRE` — minor race if two first requests hit simultaneously

**Bonus eligibility:** ✅ Qualifies as custom Redis-backed abuse prevention.

---

## Background Mail Dispatch — **Safely implemented**

```python
background_tasks.add_task(send_security_alert, user_email, ...)
```

### Strengths

- Email sent after response prepared — attacker gets immediate honeypot JSON
- `send_security_alert` wraps Resend in try/except — logs failure, no unhandled exception
- Only queued when `alert_email` present

### Weaknesses

- No retry on Resend failure
- No idempotency — repeated triggers send multiple emails (may be desired)
- `RESEND_API_KEY` unset → silent send failure logged only
- HTML injection: `token_name`, `attacker_ip`, `user_agent` interpolated raw into HTML (low risk — values come from request headers controlled by attacker on trigger, could affect email rendering)

---

## Input Validation Gaps

| Field | Issue |
|-------|-------|
| `alert_email` | Any string accepted — invalid emails fail at Resend, not at API |
| `token_type` | Allowlist enforced ✅ |
| `name` | No length/special-char limits |
| Path params | No UUID format validation on `{token_id}` |

---

## Exceptional Design Patterns

1. **Honeypot deception layer** — Security through obscurity done intentionally; attacker sees fake server meltdown
2. **Dual-index Redis schema** — Practical O(1) name lookup without SCAN
3. **Breach telemetry on token document** — Single-key incident history without separate audit table
4. **Accept-header HTML on root** — Small UX polish for browser visits vs API clients

---

## Bug Register

| ID | Severity | File:Line | Description |
|----|----------|-----------|-------------|
| B1 | Medium | `canary_trigger.py:76-78` | Docstring inside `try` block |
| B2 | Medium | All route files | Duplicate `GET /canary/` handlers |
| B3 | High | `config.py:20-21` | Redis failure leaves undefined client |
| B4 | Low | `canary_generation.py:53-58` | Unreachable validation branch |
| B5 | Low | `main.py:10` | Typo `canary_featch_router` |
| B6 | Info | `design-decisions.md` | Docs list 3 token types; code allows 5 |

None of these block flat bonus eligibility; they affect architecture discretionary score.
