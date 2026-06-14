# Discretionary Multiplier Scoring

Official RaspAPI buffs (from program docs):

| Buff | Multiplier |
|------|------------|
| Cool project | ×1.3 |
| Exceptional code quality / architecture | ×1.2 |

These stack **multiplicatively** on top of the flat-bonus base.

---

## Architecture multiplier — **×1.15** (range: ×1.10 – ×1.20)

### Points earned

- Clean `/routes`, `/models`, `/config`, `/utils` separation
- Unified logging factory with domain-specific log files
- Environment handling via Pydantic `BaseSettings` (`redis_Settings`)
- Extensive handwritten documentation (`DOCS/`, README, test fixtures)
- Thoughtful design-decisions doc explaining trade-offs
- FastAPI `BackgroundTasks` used correctly for email isolation
- Content-negotiated HTML root endpoint

### Points withheld (why not ×1.20)

- Inconsistent indentation and style in `canary_trigger.py`
- Confusing field naming (`auth_string` vs `CanaryToken` payload field)
- Auth helper not wired as FastAPI `Depends`
- No automated tests or CI
- Incomplete `requirements.txt`
- Sync blocking Redis inside async route
- README/API docs partially out of sync with auth path params
- `POST /generate-token` lacks operator authentication

### Reviewer realism

For a teenager YSWS submission, this is **above average** structure — closer to "good portfolio project" than "exceptional production architecture." A strict reviewer lands at **×1.15**; a generous one may grant **×1.20** if documentation weight is valued heavily.

**Assigned: ×1.15**

---

## Originality multiplier — **×1.25** (range: ×1.15 – ×1.30)

### Points earned

- **Security honeypot canary tokens** — creative, problem-driven concept
- Multi-format decoys (HTTP tripwire URL, fake AWS credential block)
- Deceptive attacker-facing response (returns fake "panic" JSON instead of revealing trap)
- Out-of-band operator alerting (email with forensic metadata)
- Clear real-world use case: detect credential leaks and unauthorized access

### Points withheld (why not ×1.30)

- Canary tokens are an established industry pattern (Thinkst Canary, Canarytokens.org)
- Scope is a single-service CRUD API without novel ML, graph analysis, or multi-tenant features
- Trigger endpoint is a straightforward GET logger — clever deception text, but mechanically simple

### Reviewer realism

Concept is **meaningfully cooler than a todo API or random data CRUD** — warrants a "cool project" buff. Full **×1.30** is possible if the reviewer values the security angle and deceptive UX; **×1.25** is a fair critical middle ground.

**Assigned: ×1.25**

---

## Combined discretionary product

```
×1.15 × ×1.25 = ×1.4375
```

(Range across reviewer variance: **×1.265 – ×1.560**)
