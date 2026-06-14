# Sentinel API / CanaryBox — RaspAPI Evaluation Pack

**Evaluator role:** Senior Hack Club YSWS Code Reviewer (simulated)  
**Project:** [sentinel-api](https://github.com/AWERDdev/sentinel-api)  
**Tracked time:** 8 hours 22 minutes (**8.36 h**)  
**Evaluation date:** 2026-06-14  

---

## Contents

| Document | Description |
|----------|-------------|
| [architecture-audit.md](./architecture-audit.md) | Structural strengths, weaknesses, and design patterns |
| [technical-findings.md](./technical-findings.md) | Bugs, security notes, and implementation risks |
| [flat-bonuses-audit.md](./flat-bonuses-audit.md) | Line-by-line rubric evidence for each flat bonus |
| [discretionary-multipliers.md](./discretionary-multipliers.md) | Architecture and originality scoring rationale |
| [full-raspapi-rubric.md](./full-raspapi-rubric.md) | Complete official rubric (auth, pagination, extra endpoints) |
| [payout-calculation.md](./payout-calculation.md) | Step-by-step math and projection ranges |

---

## Executive Summary

Sentinel API is a **functional honeypot canary-token service** with real Redis persistence, Resend email alerts, Redis-backed rate limiting, and Pydantic validation. The concept is above average for RaspAPI submissions; the code is modular and documented but not production-polished.

### Quick verdict

| Metric | Value |
|--------|-------|
| **User-rubric base multiplier** | `1.35` (persistence + external API + rate limit + validation) |
| **Realistic total multiplier** | `1.94` – `2.11` |
| **Projected raspberries** | **65 – 70** (user rubric) · **78 – 85** (full official rubric) |
| **Pi Zero 2 W threshold (~40 tickets at 10 h baseline)** | **Clears comfortably** |

---

## Formula reference

```
Base Multiplier     = 1.0 + Σ(flat bonuses)          [flat sum capped at 1.5]
Total Multiplier    = Base × Architecture × Originality
Projected Raspberries = Hours × 4 × Total Multiplier
```

**Hours used:** 8 h 22 m = **8.3667 h** (rounded to **8.36** in projections)
