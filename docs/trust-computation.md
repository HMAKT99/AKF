# Trust Computation

## Formula

```
effective_trust = t × authority_weight × temporal_decay × (1 + cumulative_penalty)
```

### Components

**Base confidence (t):** The raw trust score assigned to the claim [0.0 - 1.0].

**Authority weight:** Derived from the claim's tier:

| Tier | Weight | Description | Example |
|------|--------|-------------|---------|
| 1 | 1.00 | Primary source | SEC filings, official records |
| 2 | 0.85 | Authoritative secondary | Analyst reports, peer-reviewed |
| 3 | 0.70 | General secondary | News, industry reports |
| 4 | 0.50 | Internal estimate | CRM data, team assessments |
| 5 | 0.30 | AI inference | Model outputs, extrapolations |

**Temporal decay:** `0.5^(age_days / half_life_days)`

If no `decay` field is set, temporal decay is 1.0 (no decay).

**Cumulative penalty:** Sum of all `pen` values from the provenance chain. Penalties are negative, so `(1 + penalty)` reduces the score.

### Decision Thresholds

| Score | Decision | Meaning |
|-------|----------|---------|
| >= 0.70 | ACCEPT | High confidence, suitable for decisions |
| >= 0.40 | LOW | Moderate confidence, use with caution |
| < 0.40 | REJECT | Low confidence, not suitable for decisions |

## Worked Example: Woodgrove Bank

### Sarah's Claims

**Claim 1:** "Revenue was $4.2B" — t=0.98, tier=1 (SEC filing)
```
effective = 0.98 × 1.00 × 1.0 × 1.0 = 0.98 → ACCEPT
```

**Claim 2:** "Cloud growth 15-18%" — t=0.85, tier=2 (Gartner)
```
effective = 0.85 × 0.85 × 1.0 × 1.0 = 0.7225 → ACCEPT
```

**Claim 3:** "Pipeline strong" — t=0.72, tier=4 (CRM estimate)
```
effective = 0.72 × 0.50 × 1.0 × 1.0 = 0.36 → REJECT
```

### Copilot's AI Claims

**Claim 4:** "AI adoption 34%" — t=0.78, tier=2 (McKinsey survey)
```
effective = 0.78 × 0.85 × 1.0 × 1.0 = 0.663 → LOW
```

**Claim 5:** "H2 will accelerate to 25%" — t=0.63, tier=5 (AI inference)
```
effective = 0.63 × 0.30 × 1.0 × 1.0 = 0.189 → REJECT
```

### After Agent Consumption (penalty = -0.03)

Claims surviving threshold 0.5 filter: Claims 1, 2 (above 0.5 effective trust)

After -0.03 penalty:
```
Claim 1: 0.95 × 1.00 × 1.0 × 0.97 = 0.9215 → ACCEPT
Claim 2: 0.82 × 0.85 × 1.0 × 0.97 = 0.6760 → LOW
```

### Temporal Decay Example

Claim 1 with decay=90 (quarterly):
```
Day 0:   0.98 × 1.00 × 1.000 = 0.980 → ACCEPT
Day 45:  0.98 × 1.00 × 0.707 = 0.693 → LOW
Day 90:  0.98 × 1.00 × 0.500 = 0.490 → LOW
Day 180: 0.98 × 1.00 × 0.250 = 0.245 → REJECT
Day 365: 0.98 × 1.00 × 0.060 = 0.059 → REJECT
```
