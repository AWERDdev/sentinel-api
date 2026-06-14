# Sentinel API / CanaryBox — RaspAPI YSWS Evaluation

**Reviewer role:** Senior Hack Club YSWS Code Reviewer & Evaluator  
**Project:** Sentinel API (CanaryBox)  
**Repository:** `sentinel-api`  
**Logged time:** 8 hours 22 minutes (**8.36 h**, WakaTime/Hackatime verified)  
**Evaluation date:** 2026-06-14  

---

## Executive Summary

Sentinel API is a functional honeypot canary-token service built with FastAPI, Redis persistence, Resend email alerts, and a custom Redis-backed IP rate limiter. The project clearly implements all four flat-bonus categories requested in the review brief, plus additional endpoints and documentation that qualify under the full official RaspAPI rubric.

**Projected payout (realistic midpoint):** **~69 Raspberries**  
**Projected range (conservative → optimistic):** **54 – 74 Raspberries**

---

## 🛡️ Code Quality & Architecture Audit

### Strengths

- **Modular layout** — Clear separation across `routes/`, `models/`, `config.py`, and `logger_config/`, with four dedicated route modules for generate, fetch, trigger, and delete flows.
- **Redis as dual-purpose store** — Primary token records (`canary:token:{uuid}`), secondary name index (`canary:name:{normalized}`), and rate-limit counters (`rate_limit:{ip}`) with `INCR` + `EXPIRE` windowing in `config.py`.
- **Stateful breach telemetry** — Trigger handler mutates `status`, `breach_count`, and append-only `logs[]`, then writes JSON back to Redis before alerting.
- **Non-blocking alerts** — `BackgroundTasks` dispatches Resend emails so the honeypot response returns immediately to the attacker.
- **Deceptive honeypot response** — Trigger endpoint returns plausible failure JSON (`SERVER_HAS_LEFT_THE_CHAT`) rather than exposing tripwire semantics.
- **Unified logging factory** — `setupLogger()` configures scoped loggers (`app`, `app.redis`, `app.rate_limiter`) with file + console handlers and Vercel-aware `/tmp/` paths.
- **Environment handling** — `redis_Settings` via Pydantic `BaseSettings` with `REDIS_*` prefix; Resend key and `DOMAIN` loaded for production tripwire URLs.
- **Documentation depth** — `DOCS/architecture.md`, `api-reference.md`, `design-decisions.md`, `setup-guide.md`, plus Postman fixtures exceed typical teen-project documentation norms.

### Room for Improvement

| Issue | Severity | Location | Recommendation |
|-------|----------|----------|----------------|
| Docstring placed inside `try` block (not attached to function) | Medium | `routes/canary_trigger.py:76-78` | Move docstring directly under `async def trigger_canary` |
| Four duplicate `@router.get('/')` handlers on same `/canary` prefix | Medium | All route modules | Keep one welcome route; remove duplicates |
| `redis_connect` undefined if connection fails | High | `config.py:20-21` | Fail fast on startup or use a health gate |
| No `EmailStr` validation on `alert_email` | Low | `models/canary_model.py` | Use Pydantic `EmailStr` |
| Sync `redis` client inside `async def trigger_canary` | Low | `routes/canary_trigger.py` | Use `redis.asyncio` or run sync calls in thread pool |
| Docs/code drift on `allowed_types` | Low | `DOCS/design-decisions.md` vs `canary_generation.py` | Align docs with `["http","https","aws","web","url"]` |
| Typo import alias | Cosmetic | `main.py:10` | Rename `canary_featch_router` → `canary_fetch_router` |
| No auth on management endpoints | Design gap | All routes | Acknowledged in docs; blocks +0.15 Authorization bonus |
| Redundant `dotenv.load_dotenv()` in every route file | Low | All routes | Rely on Pydantic settings only |

---

## 🔢 Multiplier Matrix Summary

### User-Specified Flat Bonuses (Review Brief)

| Component | Award | Verdict |
|-----------|-------|---------|
| Baseline | `1.0` | — |
| Persistence | **+0.10** | ✅ Redis read/write of JSON token models, name index, breach state |
| External API | **+0.10** | ✅ Active `resend.Emails.send()` on trigger |
| Rate Limiting | **+0.10** | ✅ Custom `ratelimiter` dependency with Redis window |
| Validation & Safety | **+0.05** | ✅ Pydantic models, HTTPException traps, structured logging |
| **Subtotal (flat)** | **+0.35** | **Base multiplier = 1.35** |

### Full Official RaspAPI Flat Bonuses (Reference)

| Component | Award | Verdict |
|-----------|-------|---------|
| Authorization (JWT/API keys) | +0.00 | ❌ Not implemented (intentionally out of scope) |
| Persistence | +0.10 | ✅ |
| External API | +0.10 | ✅ |
| Rate limiting | +0.10 | ✅ |
| Pagination | +0.00 | ❌ No list endpoints with cursor/limit |
| Validation & error handling | +0.05 | ✅ |
| Additional endpoints (max 4 × +0.03) | **+0.12** | ✅ fetch-by-name, delete-by-id, delete-by-name, `/canary/docs` |
| **Subtotal (flat, capped at 1.5)** | **+0.47** | **Base multiplier = 1.47** (under cap) |

### Discretionary Multipliers

| Multiplier | Rating | Justification |
|------------|--------|---------------|
| **Architecture** | **×1.15** | Solid modular structure, logging factory, env settings, and extensive docs — held back by duplicate routes, sync Redis in async handler, and missing startup fail-fast |
| **Concept Originality** | **×1.22** | Genuinely useful honeypot/canary concept with AWS credential decoys, breach logging, and deceptive responses — creative for a teen API project but not wholly novel (Thinkst Canarytokens precedent) |

---

## 🎯 Final Payout Projections

### Formula

```
Base Multiplier     = 1.0 + Σ(Flat Bonuses)
Total Multiplier    = Base × Architecture × Originality
Raspberries         = Hours × 4 × Total Multiplier
```

### Scenarios

| Scenario | Flat base | Arch | Orig | Total mult. | Raspberries |
|----------|-----------|------|------|-------------|-------------|
| **Conservative** (brief rubric) | 1.35 | ×1.05 | ×1.15 | **1.630** | **54.5** |
| **Realistic midpoint** (brief rubric) | 1.35 | ×1.15 | ×1.22 | **1.894** | **63.4** |
| **Optimistic** (brief rubric) | 1.35 | ×1.18 | ×1.28 | **2.038** | **68.2** |
| **Full RaspAPI realistic** | 1.47 | ×1.15 | ×1.22 | **2.064** | **69.0** |
| **Full RaspAPI optimistic** | 1.47 | ×1.18 | ×1.28 | **2.219** | **74.2** |

### Headline Numbers (Review Brief Rubric)

- **Calculated Total Multiplier (realistic):** `1.894`
- **Total Tracked Time:** `8.36 Hours`
- **Projected Earnings Range:** **`54 to 74 Raspberries / Tickets`**
- **Best single-point estimate:** **`~63–69 Raspberries`**

### Hardware Target Status — Raspberry Pi Zero 2 W Kit

Hack Club RaspAPI hardware redemption thresholds vary by cohort and inventory, but Pi Zero kits typically sit in the **~50–70 Raspberry** band for comparable YSWS programs.

| Assessment | Detail |
|------------|--------|
| **Status** | **Likely qualifies — borderline to comfortable** |
| **Conservative case (54)** | May fall just short if threshold is at the high end (~60+) |
| **Realistic case (63–69)** | Should clear a typical Pi Zero 2 W kit threshold |
| **Optimistic case (74)** | Comfortably clears with margin |

**Risk factor:** Without Authorization (+0.15) and Pagination (+0.05), the flat base stays below the 1.5 cap ceiling — discretionary multipliers carry more weight in final payout.

---

## Folder Contents

| File | Description |
|------|-------------|
| [flat-bonuses-audit.md](./flat-bonuses-audit.md) | Evidence-backed flat bonus scoring |
| [architecture-audit.md](./architecture-audit.md) | Structural code review with file references |
| [discretionary-multipliers.md](./discretionary-multipliers.md) | Architecture × originality scoring rationale |
| [payout-calculation.md](./payout-calculation.md) | Step-by-step math |
| [technical-findings.md](./technical-findings.md) | Bugs, patterns, and security notes |
| [full-raspapi-rubric.md](./full-raspapi-rubric.md) | Official Hack Club rubric mapping |
