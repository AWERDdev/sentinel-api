# Discretionary Multiplier Scoring

Hack Club RaspAPI applies two post-cap multipliers:

- **Exceptional code quality / architecture:** up to **×1.2**
- **Cool project / originality:** up to **×1.3**

These stack **multiplicatively** on the flat base multiplier.

---

## Architecture Multiplier — **×1.15**

### What reviewers typically look for

| Signal | Present? |
|--------|----------|
| `/routes`, `/models`, `/config` separation | ✅ |
| Unified logging factory | ✅ |
| Environment-driven settings | ✅ Partial |
| Docstrings on endpoints | ✅ Most routes |
| External documentation | ✅ Strong |
| No duplicated dead code | ❌ 4× welcome route |
| Fail-fast infrastructure | ❌ Redis connect |
| Test coverage | ❌ Manual fixtures only |
| Consistent async/sync model | ❌ |

### Comparison to peer YSWS submissions

Above average for a first API project: modular routers, design docs, and honeypot threat-model writeups exceed typical "CRUD todo app" submissions.

Below top tier: missing auth, tests, and polish issues (typo imports, docstring placement) prevent full ×1.2.

**Range applied in payout model:** ×1.05 (conservative) – ×1.18 (optimistic)  
**Point estimate:** **×1.15**

---

## Originality Multiplier — **×1.22**

### Concept: Honeypot Canary Token Service

**Problem solved:** Detect unauthorized access when decoy credentials/URLs embedded in configs, repos, or env files are touched.

**Differentiators:**

1. **Multi-format decoys** — HTTP(S) tracking URLs and fake AWS credential blocks (`AKIA_{token_id}`)
2. **Attacker deception** — Returns humorous fake error JSON instead of "you triggered a canary"
3. **Out-of-band alerting** — Email with IP, UA, timestamp via Resend
4. **Stateful incident log** — Per-token `logs[]` and `breach_count` in Redis

### Prior art context

Commercial/open-source canary token systems exist (Thinkst Canarytokens, AWS honey tokens). This project is **not wholly novel** but is **highly creative for a teen-built YSWS API** — especially the deceptive response copy and AWS-format generation.

### Originality tier mapping

| Tier | Multiplier | Fit |
|------|------------|-----|
| Generic CRUD clone | ×1.0 | — |
| Useful niche tool | ×1.10–×1.15 | — |
| **Creative security utility with clear real-world use** | **×1.18–×1.25** | **← ×1.22** |
| Exceptional / never seen before | ×1.28–×1.30 | Not quite |

**Range applied in payout model:** ×1.15 (conservative) – ×1.28 (optimistic)  
**Point estimate:** **×1.22**

---

## Combined discretionary effect

```
Flat base (brief):     1.35
× Architecture:        1.15
× Originality:         1.22
= Total multiplier:    1.894
```

Discretionary buff contributes **+40%** over flat base alone — originality carries slightly more weight than architecture in this submission.
