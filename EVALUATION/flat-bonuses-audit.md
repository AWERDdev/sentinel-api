# Flat Bonuses Audit (User-Specified Rubric)

Baseline multiplier: **1.0**

---

## Persistence (+0.10) — **AWARDED**

| Criterion | Status |
|-----------|--------|
| External key-value store | Redis via `redis.from_url` |
| Complex state mutations | Trigger updates status, breach_count, logs |
| CRUD lifecycle | Create, read, update (trigger), delete |
| Secondary indexing | Name → UUID mapping |

**Score: +0.10**

---

## External API integration (+0.10) — **AWARDED**

| Criterion | Status |
|-----------|--------|
| Out-of-band network call | `resend.Emails.send()` |
| Non-trivial integration | HTML email construction, API key config |
| Production path documented | `RESEND_API_KEY`, local testing notes |

**Score: +0.10**

---

## Rate limiting / abuse prevention (+0.10) — **AWARDED**

| Criterion | Status |
|-----------|--------|
| Windowed state checks | `INCR` + `EXPIRE` on first request |
| Redis-backed (not in-memory) | Keys `rate_limit:{ip}` |
| Returns 429 | Yes |
| Global coverage | All routes |

**Score: +0.10**

---

## Input validation & error architecture (+0.05) — **AWARDED**

| Criterion | Status |
|-----------|--------|
| Pydantic schemas | `CanaryTokenCreate`, `CanaryToken`, `redis_Settings` |
| Type casting / env | `BaseSettings` with typed ints for rate limits |
| HTTPException traps | 400/403/404/429/500 across routes |
| System logs | Three dedicated loggers + file handlers |

**Score: +0.05**

---

## User-rubric subtotal

| Bonus | Value |
|-------|-------|
| Persistence | +0.10 |
| External API | +0.10 |
| Rate limiting | +0.10 |
| Validation & safety | +0.05 |
| **Sum** | **+0.35** |

### **Base multiplier (user rubric) = 1.35**

---

## Not in user matrix but relevant for official review

See [full-raspapi-rubric.md](./full-raspapi-rubric.md) for authorization (+0.15), pagination (+0.00), and additional endpoints (+0.12 max).
