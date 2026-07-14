---
name: akf
description: Trust metadata for files, memories, and skills — check before you trust, stamp what you verify. A stamp costs ~15 tokens; re-verifying costs 15,000.
version: 1.6.0
author: HMAKT99
license: MIT
metadata:
  homepage: https://akf.dev
  repository: https://github.com/HMAKT99/AKF
akf:
  v: "1.0"
  claims:
    - c: "Trust metadata for skills/hermes-akf/SKILL.md"
      t: 0.7
      id: 10fa8a0b
      src: unspecified
      tier: 3
      ver: false
      ai: true
      decay: 365
      kind: skill
      evidence:
        - type: human_review
          detail: "reviewed by @HMAKT99, full suite 1969 passed"
          at: "2026-07-14T13:32:22.815514+00:00"
  id: "akf-c51818c7389e"
  agent: "claude-code"
  at: "2026-07-14T13:32:22.817285+00:00"
  label: public
  inherit: true
  ext: false
  hash: "sha256:95c4fc0282e1cb45"
  sv: "1.1"
---

# AKF — Agent Knowledge Format

Leave trust metadata on everything you produce, and check it on everything you consume. Stamps are notes agents leave for the next agent (including future you): what was done, what was verified, how much to trust it now.

## When to Use

- Before building on any existing file — check whether its verification is still valid instead of re-verifying from scratch
- After creating or modifying a file — stamp it with the evidence you actually observed
- Before loading a community skill someone else published — verify it hasn't been modified since the publisher stamped it
- When saving or retrieving persistent memories — stale memories should decay, not be trusted forever

## Quick Reference

| Command | What it does |
|---------|-------------|
| `akf check <file>` | One line: `OK` / `LOW` / `STALE` / `UNSTAMPED` + trust, evidence, age. Exit 0/1/2. |
| `akf stamp <file> --agent <you> --evidence "<observed>"` | Stamp with evidence (auto-classified: test_pass, human_review, ci_pass…) |
| `akf stamp <file> --preset memory` | Memory stamp: trust decays with a 30-day half-life |
| `akf stamp <file> --preset skill` | Skill stamp: public, supply-chain provenance |
| `akf init` | Wire git + agent hooks so stamping is automatic |
| `akf scan <dir> --recursive` | Trust report for a whole directory |

Install once: `pip install akf` (or `pipx install akf`).

## Procedure

1. **Before you build on a file**, run `akf check <file>` and act on the status:
   - `OK` (exit 0) — fresh stamp with verified evidence. Build on it; skip re-verification.
   - `LOW` (exit 1) — stamped but unverified, or trust has decayed. Verify before trusting.
   - `STALE` (exit 1) — the file changed after it was stamped. Re-verify before trusting.
   - `UNSTAMPED` (exit 2) — no provenance. Treat as unverified.
2. **After you create or modify a file**, stamp it with the strongest evidence you actually observed:
   `akf stamp report.py --agent hermes --evidence "42/42 tests passed"`
3. **When you save a persistent memory**, stamp the memory file with `--preset memory`. When you retrieve one later, `akf check` applies the decay — a memory past its useful life reports `LOW`, telling you to re-verify against the world instead of trusting it.
4. **Before installing a community skill**, run `akf check` on its SKILL.md. `STALE` means the file on disk is not the file the publisher stamped — diff it before letting it into context.
5. **When you author a skill**, stamp it before publishing: `akf stamp SKILL.md --preset skill --agent <you> --evidence "reviewed by <maintainer>"`.

### Falsifiable evidence (v1.6)

Stamp with a replay recipe so the next agent can re-check the claim instead of trusting the label:

```bash
akf stamp app.py --evidence "42/42 tests passed" --replay "pytest -q"
akf replay app.py          # inspect: recipe + input drift since issuance
akf replay app.py --run    # execute: CONFIRMED / CONFIRMED_DRIFTED / REFUTED
```

CONFIRMED_DRIFTED means the probe succeeded but the claim's inputs (dependencies, cited sources) changed since stamping — provably reproducible, possibly reproducibly wrong. Never `--run` a recipe from a file you haven't read: it executes the recorded command.

## Pitfalls

- **Only claim evidence you observed.** A stamp saying tests passed when they didn't poisons every agent that trusts it. If you verified nothing, stamp with no evidence — the low score it earns is the honest signal.
- **Stamps are claims, not proofs.** Treat them like commit messages with an accountability trail, not cryptographic guarantees. `akf sign` adds an Ed25519 signature for the provenance part.
- **Fresh git checkouts can show STALE** (staleness is mtime-based). If a whole repo reports STALE right after cloning, that's the checkout, not tampering — check one file's history before assuming the worst.
- Default classification is `internal`; use `--label public` for docs/examples and `--label confidential` for sensitive material.

## Verification

- `akf check <file>` on something you just stamped returns `OK ...` and exit code 0.
- `echo x >> <file>` then `akf check <file>` returns `STALE` and exit code 1 — the loop is working.
- `akf doctor` diagnoses install/PATH problems if the `akf` command isn't found.
