# Payout Calculation

## Inputs

| Variable | Value |
|----------|-------|
| Tracked time | 8 h 22 m 7 s |
| Decimal hours | 8 + 22/60 + 7/3600 = **8.3669 h** |
| Rounded (per rubric) | **8.36 h** |
| Formula constant | ×4 raspberries per hour |

---

## Scenario A — User-specified rubric (4 flat bonuses only)

### Flat bonuses

```
Persistence      +0.10
External API     +0.10
Rate limiting    +0.10
Validation       +0.05
─────────────────────
Sum              +0.35
Base multiplier  1.35
```

### Discretionary (assigned)

```
Architecture     ×1.15
Originality      ×1.25
```

### Total multiplier

```
1.35 × 1.15 × 1.25 = 1.940625
```

### Payout

```
8.36 × 4 × 1.940625 = 64.89 → 65 raspberries
```

### Sensitivity range (reviewer variance)

| Case | Architecture | Originality | Total mult. | Raspberries |
|------|--------------|-------------|-------------|-------------|
| Strict | ×1.10 | ×1.15 | 1.708 | **57** |
| Assigned | ×1.15 | ×1.25 | 1.941 | **65** |
| Generous | ×1.20 | ×1.30 | 2.106 | **70** |

**User-rubric projection: 57 – 70 raspberries (midpoint ~65)**

---

## Scenario B — Full official rubric (+ auth, extra endpoints)

### Flat bonuses

```
Authorization    +0.15
Persistence      +0.10
External API     +0.10
Rate limiting    +0.10
Validation       +0.05
Extra endpoints  +0.12  (4 × 0.03)
Pagination       +0.00
─────────────────────
Sum              +0.62
Base multiplier  1.62
```

### Discretionary

Same as Scenario A: ×1.15 × ×1.25 = ×1.4375

### Total multiplier

```
1.62 × 1.15 × 1.25 = 2.32875
```

### Payout

```
8.36 × 4 × 2.32875 = 77.87 → 78 raspberries
```

### Sensitivity range

| Case | Total mult. | Raspberries |
|------|-------------|-------------|
| Strict (auth +0.10, ×1.10, ×1.15) | 1.99 | **66** |
| Assigned | 2.329 | **78** |
| Generous (×1.20, ×1.30) | 2.527 | **85** |

**Full-rubric projection: 66 – 85 raspberries (midpoint ~78)**

---

## Hardware target — Raspberry Pi Zero 2 W

| Reference | Threshold | This project |
|-----------|-----------|--------------|
| Naive baseline (10 h × 4 × 1.0) | ~40 tickets | — |
| Summer of Making shop listing | ~10 h equivalent | 8.36 h logged |
| **Projected payout (assigned)** | — | **65 – 78 raspberries** |

### Status: **CLEAR**

Even under the strict user-rubric case (**57 raspberries**), the project exceeds a ~40-ticket Pi-equivalent baseline when multipliers are applied to 8.36 h. Under RaspAPI's direct YSWS model, meeting program requirements (API shipped, docs, public repo) is the primary gate; multiplier affects raspberry currency for broader Hack Club reward systems.

At **×1.0** with no bonuses: `8.36 × 4 = 33.4` — below 40, which underscores why flat bonuses and quality multipliers matter for hardware-equivalent thresholds.

---

## Worked example (matches official docs format)

> API with Auth (+0.15), DB (+0.10), Rate limit (+0.10), Error handling (+0.05), 2 extra endpoints (+0.06) → `1.0 + 0.46 = 1.46`

This project exceeds that example on endpoints (+0.12 vs +0.06) and matches on all other cited categories → **1.62 base** before quality buffs.
