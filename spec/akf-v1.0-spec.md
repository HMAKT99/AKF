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
| model | string | no | — | Model identifier |
| tools | string[] | no | — | Tools used by the agent |
| session | string | no | — | Session identifier |
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
| kind | string | no | — | Claim kind (claim, code_change, decision, suggestion, review, test_result, diagnosis) |
| src_hash | string | no | — | Content hash of the cited source at stamp time (v1.6) — enables source-change staleness |
| evidence | array | no | — | Evidence objects supporting the claim |

## Evidence Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| type | string | yes | Evidence type (test_pass, type_check, lint_clean, ci_pass, human_review, other) |
| detail | string | yes | Description of the evidence |
| at | ISO-8601 | no | Timestamp |
| tool | string | no | Tool that produced this evidence |
| metrics | object | no | Parsed receipt strength (v1.6): coverage, tests_passed, tests_total |
| replay | object | no | Falsifiable probe recipe (v1.6) — see below |

### Replay Fields (v1.6)

A replay recipe makes evidence falsifiable: a signature proves who said it; a replay proves it could have been true.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| command | string | yes | Shell command that re-verifies the claim |
| cwd | string | no | Working directory, relative to the stamped file |
| expected_exit | int | no | Exit code meaning confirmed (default 0) |
| output_digest | string | no | Content hash of the expected output |
| input_hash | string | no | Fingerprint of the claim's input closure at issuance — distinguishes CONFIRMED from CONFIRMED_DRIFTED |

Envelope `meta.deps` (v1.6) maps first-degree local dependency paths to content hashes, enabling transitive-dependency staleness detection.

Envelope `meta.content_hash` is a `sha256:` fingerprint (16 hex) of the file's content with its embedded stamp removed. `akf check` uses it to avoid reporting STALE when only the file's mtime changed, as after a fresh checkout.

## Trust Grounding

A claim is **grounded** when it has one or more evidence items. Grounding is informational — it does not change the trust score formula, but indicates whether the claim is backed by verifiable artifacts (test results, type checks, CI runs, human reviews).

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
