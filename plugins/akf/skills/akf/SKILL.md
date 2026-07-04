---
name: akf
description: Trust metadata for files, memories, and skills — check before you trust, stamp what you verify. Use before building on existing files, after completing verified work, and when handling agent memories or downloaded skills.
akf:
  v: "1.0"
  claims:
    - c: Trust metadata for plugins/akf/skills/akf/SKILL.md
      t: 0.7
      id: a569fafc
      src: unspecified
      tier: 3
      ver: false
      ai: true
      decay: 365
      kind: skill
      evidence:
        - type: human_review
          detail: "reviewed by @HMAKT99, claude plugin validate passed"
          at: "2026-07-04T07:38:00.697134+00:00"
  id: "akf-fc4aaa7b1cff"
  agent: "claude-code"
  at: "2026-07-04T07:38:00.698185+00:00"
  label: public
  inherit: true
  ext: false
  hash: "sha256:68a8c0fdc8d95249"
  sv: "1.1"
---

# AKF — Agent Knowledge Format

Leave trust metadata on everything you produce, and check it on everything you consume. Stamps are notes agents leave for the next agent (including future you): what was done, what was verified, how much to trust it now. A stamp costs ~15 tokens; re-verifying costs 15,000.

This plugin auto-stamps files you write via a PostToolUse hook. Your job is the read path and the evidence.

## Before building on an existing file

```bash
akf check <file>
```

- `OK` (exit 0) — fresh stamp with verified evidence. Build on it; skip re-verification.
- `LOW` (exit 1) — stamped but unverified, or trust decayed. Verify before trusting.
- `STALE` (exit 1) — file modified after stamping, or a local dependency it imports changed (`reason=dependency_changed`). Re-verify.
- `UNSTAMPED` (exit 2) — no provenance. Treat as unverified.

## After completing verified work

Stamp with the strongest evidence you actually observed:

```bash
akf stamp report.py --agent claude-code --evidence "42/42 tests passed"
```

Evidence is auto-classified and drives trust: test runs and human review clear the trust bar; bare stamps stay LOW by design. **Only claim evidence you observed** — a stamp saying tests passed when they didn't poisons every agent that trusts it.

## Memories and skills

```bash
akf stamp memory/facts.md --preset memory   # 30-day trust decay — stale memories go LOW automatically
akf check downloaded-skill.md               # STALE = not the file the publisher stamped
```

## Setup

If `akf` isn't installed: `pip install akf` (or `pipx install akf`), then `akf init` in the project to wire git hooks. `akf doctor` diagnoses PATH issues.
