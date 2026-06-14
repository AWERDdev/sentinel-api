# Payout Calculation — Step by Step

## Inputs

| Variable | Value |
|----------|-------|
| Logged time | 8 h 22 min = **8.3667 h** → rounded **8.36 h** (per tracking) |
| RaspAPI formula constant | **× 4** raspberries per hour |
| Flat bonus cap (official) | **1.5** |

---

## Method A — Review Brief Rubric (4 flat categories)

### Step 1: Flat bonuses

```
Baseline                    = 1.00
+ Persistence               = 0.10
+ External API              = 0.10
+ Rate limiting             = 0.10
+ Validation & safety       = 0.05
─────────────────────────────────
Base Multiplier             = 1.35
```

### Step 2: Discretionary multipliers

| Scenario | Architecture | Originality | Total Multiplier |
|----------|--------------|-------------|----------------|
| Conservative | ×1.05 | ×1.15 | 1.35 × 1.05 × 1.15 = **1.6301** |
| Realistic | ×1.15 | ×1.22 | 1.35 × 1.15 × 1.22 = **1.8945** |
| Optimistic | ×1.18 | ×1.28 | 1.35 × 1.18 × 1.28 = **2.0381** |

### Step 3: Raspberries

```
Raspberries = 8.36 × 4 × Total Multiplier
```

| Scenario | Calculation | Result |
|----------|-------------|--------|
| Conservative | 8.36 × 4 × 1.6301 | **54.5** |
| Realistic | 8.36 × 4 × 1.8945 | **63.4** |
| Optimistic | 8.36 × 4 × 2.0381 | **68.2** |

**Range: 54 – 68 Raspberries** (brief rubric only)

---

## Method B — Full Official RaspAPI Rubric

### Step 1: Flat bonuses

```
Baseline                    = 1.00
+ Persistence               = 0.10
+ External API              = 0.10
+ Rate limiting             = 0.10
+ Validation                = 0.05
+ Extra endpoints (4×0.03)  = 0.12
+ Authorization             = 0.00
+ Pagination                = 0.00
─────────────────────────────────
Sum                         = 0.47  (under 1.5 cap)
Base Multiplier             = 1.47
```

### Step 2: Discretionary (realistic)

```
1.47 × 1.15 × 1.22 = 2.0639
```

### Step 3: Raspberries

```
8.36 × 4 × 2.0639 = 69.0 Raspberries
```

### Full range

| Scenario | Total mult. | Raspberries |
|----------|-------------|-------------|
| Conservative | 1.7747 | **59.3** |
| Realistic | 2.0639 | **69.0** |
| Optimistic | 2.2195 | **74.2** |

**Range: 59 – 74 Raspberries** (full rubric)

---

## Official RaspAPI example cross-check

From Hack Club docs:

> Auth +0.15, DB +0.10, Rate limit +0.10, Error handling +0.05, 2 extra endpoints +0.06  
> → 1.0 + 0.46 = **1.46** (under cap)

This project without auth but with 4 extra endpoints:

> 1.0 + 0.10 + 0.10 + 0.10 + 0.05 + 0.12 = **1.47**

Comparable to the documented example, minus auth (+0.15) plus two more endpoints (+0.06) → net **+0.01** vs example.

---

## Hardware redemption note

If Pi Zero 2 W kit ≈ **60 Raspberries**:

- Brief rubric conservative (54.5): **below threshold**
- Brief rubric realistic (63.4): **above threshold**
- Full rubric realistic (69.0): **comfortably above**

Recommend targeting **full rubric credit** for extra endpoints during submission review.
