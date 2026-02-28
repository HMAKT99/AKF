# AKF — Agent Knowledge Format v1.0 Specification

## Overview

AKF (Agent Knowledge Format) is a lightweight, LLM-native file format for structured knowledge exchange with built-in trust, provenance, and security metadata.

- **File extension:** `.akf`
- **MIME type:** `application/vnd.akf+json`
- **Encoding:** UTF-8 JSON

## Design Principles

1. **Minimal** — Smallest valid file is ~15 tokens
2. **Flat** — Maximum 2 levels of nesting
3. **Defaults** — Only `v`, `claims[]`, `c`, and `t` are required
4. **Extensible** — Unknown fields silently ignored
5. **LLM-native** — Producible from a one-shot example
6. **Token-efficient** — 80-85% smaller than verbose JSON

## Envelope Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| v | string | YES | — | Spec version (semver) |
| id | string | no | auto UUID | Unique knowledge unit ID |
| by | string | no | — | Creator email or agent ID |
| agent | string | no | — | AI agent ID if AI-created |
| at | ISO-8601 | no | now() | Creation timestamp |
| label | string | no | "internal" | Security classification |
| inherit | bool | no | true | Children inherit label |
| ext | bool | no | false | Allow external sharing |
| ttl | int | no | — | Retention period (days) |
| claims | array | YES | — | Array of claim objects |
| prov | array | no | — | Provenance chain |
| hash | string | no | — | Integrity hash |
| meta | object | no | — | Free-form metadata |

### Label Values

`public` | `internal` | `confidential` | `highly-confidential` | `restricted`

## Claim Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| c | string | YES | — | Claim content |
| t | float | YES | — | Trust score [0.0-1.0] |
| id | string | no | auto | Claim ID |
| src | string | no | — | Source name |
| uri | string | no | — | Source URL |
| tier | int | no | 3 | Authority tier [1-5] |
| ver | bool | no | false | Human verified |
| ver_by | string | no | — | Who verified |
| ai | bool | no | false | AI generated |
| risk | string | no | — | Risk description |
| decay | int | no | — | Half-life in days |
| exp | ISO-8601 | no | — | Hard expiry |
| tags | string[] | no | — | Tags |
| contra | string | no | — | Contradicting claim ID |
| fidelity | object | no | — | Multi-resolution {h, s, f} |

## Provenance Hop Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| hop | int | yes | Hop number (0 = origin) |
| by | string | yes | Actor |
| do | string | yes | Action (created/enriched/reviewed/consumed/transformed) |
| at | ISO-8601 | yes | Timestamp |
| h | string | no | SHA-256 hash |
| pen | float | no | Transform penalty (must be negative) |
| adds | string[] | no | Claim IDs added |
| drops | string[] | no | Claim IDs rejected |

## Trust Computation

```
effective_trust = t × authority_weight × temporal_decay × (1 + penalty)
```

**Authority weights:** {1: 1.00, 2: 0.85, 3: 0.70, 4: 0.50, 5: 0.30}

**Temporal decay:** `0.5^(age_days / half_life_days)` — defaults to 1.0 if no decay

**Decision thresholds:** ≥0.7 ACCEPT | ≥0.4 LOW | <0.4 REJECT

## Classification Hierarchy

```
public(0) < internal(1) < confidential(2) < highly-confidential(3) < restricted(4)
```

When `inherit: true`, derived documents must maintain at least the parent's classification level.

## Validation Rules

1. `v` must be present and valid semver
2. `claims` must be non-empty array
3. Each claim must have `c` (string) and `t` (float 0.0-1.0)
4. `tier` must be 1-5
5. `label` must be a valid classification
6. Inherited label must be ≥ parent label
7. Provenance hops must be sequential from 0
8. `pen` must be negative
9. AI tier-5 claims SHOULD have `risk` (warning)
10. `hash` must have algorithm prefix (sha256:, sha3-512:, blake3:)
11. All timestamps must be valid ISO-8601
12. Unknown fields are ALLOWED everywhere
