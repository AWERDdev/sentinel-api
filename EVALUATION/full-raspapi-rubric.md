# Full Official RaspAPI Rubric Mapping

Source: Hack Club RASPAPI **Buffs & Multipliers** documentation.

---

## Payout formula

```
Payout = hours × 4 × multiplier
```

Example from docs: 6 hours × 1.25 multiplier × 4 = **30 raspberries**

---

## Stage 1 — Flat Bonuses (additive, cap 1.5)

| Buff | Bonus | Sentinel API | Award |
|------|-------|--------------|-------|
| Authorization (JWT, tokens, API keys) | +0.15 | Not implemented | **0.00** |
| Persistence (database, file storage) | +0.10 | Redis JSON tokens + indexes | **0.10** |
| External API (non-trivial) | +0.10 | Resend email API | **0.10** |
| Rate limiting / abuse prevention | +0.10 | Redis IP window limiter | **0.10** |
| Pagination | +0.05 | Not present | **0.00** |
| Error handling & input validation | +0.05 | Pydantic + HTTPException + logs | **0.05** |
| Additional endpoints (max 4) | +0.03 each | See below | **0.12** |

### Additional endpoint credit

| # | Endpoint | Core? |
|---|----------|-------|
| 1 | `POST /canary/generate-token` | Core minimum |
| 2 | `GET /canary/fetch/id/{id}` | Core minimum |
| 3 | `GET /canary/trigger/{id}` | Core minimum |
| — | `GET /canary/fetch/name/{name}` | **Extra +0.03** |
| — | `DELETE /canary/delete/id/{id}` | **Extra +0.03** |
| — | `DELETE /canary/delete/name/{name}` | **Extra +0.03** |
| — | `GET /canary/docs` | **Extra +0.03** |

**Flat sum:** 0.47 → **Base multiplier 1.47** (cap not hit)

---

## Stage 2 — Multiplier Buffs (multiplicative)

| Buff | Multiplier | Sentinel API | Award |
|------|------------|--------------|-------|
| Cool project | ×1.3 max | Honeypot canary service | **×1.22** |
| Exceptional code quality / architecture | ×1.2 max | Modular FastAPI + docs | **×1.15** |

**Note:** Docs show these as separate multiplier buffs applied after flat cap. User brief combines them as:

```
Total = Base × Architecture × Originality
```

---

## Worked example (this project)

```
Hours logged     = 8.36
Flat base        = 1.47
Architecture     = ×1.15
Originality      = ×1.22
─────────────────────────────
Total multiplier = 1.47 × 1.15 × 1.22 = 2.064
Raspberries      = 8.36 × 4 × 2.064 = 69.0
```

---

## Comparison to official doc example

**Doc example API:**

- Auth +0.15, DB +0.10, Rate +0.10, Errors +0.05, 2 extras +0.06
- Base = **1.46**

**Sentinel API:**

- No auth, DB +0.10, External +0.10, Rate +0.10, Errors +0.05, 4 extras +0.12
- Base = **1.47**

Net: **+0.01** vs doc example (gained +0.06 from endpoints, lost −0.15 from auth, gained +0.10 from Resend external API counted separately from persistence).

---

## Submission recommendations

To maximize reviewer score without large rewrites:

1. Add `EmailStr` on `alert_email` (+ polish for validation bonus defense)
2. Remove duplicate welcome routes (+ architecture score)
3. Add API key auth on generate/delete only (+0.15 authorization — largest single bonus)
4. Document pagination as N/A or add `GET /canary/list?limit=&offset=` (+0.05)

Potential base with auth only: 1.47 + 0.15 = **1.62 → capped at 1.5** (+0.03 net to cap ceiling).
