---
name: akf
description: AKF is the AI native file format, EXIF for AI. Use it before building on any existing file, memory, or downloaded skill to see whether its verification is still valid, and after you create or change a file to leave a ~15-token stamp of what you actually verified. Triggers on "can I trust this file", "is this still valid", "stamp this", provenance, handoff between agents.
license: MIT
metadata:
  version: "1.6.2"
  homepage: https://akf.dev
  repository: https://github.com/HMAKT99/AKF
akf:
  v: "1.0"
  claims:
    - c: Trust metadata for skills/akf/SKILL.md
      t: 0.7
      id: 2da9e7ae
      src: unspecified
      tier: 3
      ver: false
      ai: true
      decay: 365
      kind: skill
      evidence:
        - type: human_review
          detail: "reviewed by @HMAKT99"
          at: "2026-10-20T02:51:06.197720+00:00"
  id: "akf-ebe9312d9328"
  agent: "claude-code"
  at: "2026-10-20T02:51:06.198263+00:00"
  label: public
  inherit: true
  ext: false
  hash: "sha256:40940ddf657bbc23"
  meta:
    content_hash: "sha256:136349861f3c5ba3"
  sv: "1.1"
---

# AKF: the AI native file format

AKF embeds trust scores, provenance, and evidence into 20+ file formats as ~15 tokens of metadata. A stamp is a note one agent leaves for the next: what was done, what was verified, how much to trust it now. Reading a stamp costs ~15 tokens. Re-verifying the work costs thousands.

## When to use

- Before you build on a file another agent or session produced.
- After you create or modify a file and have observed something that verifies it.
- Before loading a community skill into context.
- When saving or reading persistent memory notes.

## Setup

```bash
pip install akf        # or: pipx install akf
akf doctor             # diagnoses PATH and install problems
```

## Procedure

### 1. Check before you build

```bash
akf check <file>
```

or, for several files at once, `bash scripts/check-before-build.sh <file>...` (lists which files need re-verification).

| Status | Exit | Meaning | What to do |
|--------|------|---------|-----------|
| `OK` | 0 | Fresh stamp with verified evidence | Build on it. Skip re-verification. |
| `LOW` | 1 | Stamped but no test/review evidence, or trust has decayed | Verify the claims you depend on, then restamp. |
| `STALE` | 1 | File changed after stamping, or a local dependency it imports changed | Re-verify. The old evidence describes a different file. |
| `UNSTAMPED` | 2 | No provenance at all | Treat as unverified. |

### 2. Stamp what you verified

```bash
akf stamp <file> --agent <your-name> --evidence "<what you observed>"
```

Evidence is classified from the text, and the class drives the trust score. See [references/evidence.md](references/evidence.md) for the patterns that classify and the ones that do not. Examples: `"42/42 tests passed"`, `"mypy: 0 errors"`, `"CI green"`, `"reviewed by @maintainer"`.

### 3. Memories and skills

```bash
akf stamp memory/facts.md --preset memory   # 30-day trust decay: old memories go LOW on their own
akf stamp SKILL.md --preset skill           # public, supply-chain provenance
akf check downloaded/SKILL.md               # STALE = not the file the publisher stamped
```

### 4. Make the claim replayable (optional, strongest)

```bash
akf stamp app.py --evidence "42/42 tests passed" --replay "pytest -q"
akf replay app.py          # inspect: recipe plus input drift since stamping
akf replay app.py --run    # execute: CONFIRMED / CONFIRMED_DRIFTED / REFUTED
```

`CONFIRMED_DRIFTED` means the probe passed but the claim's inputs (dependencies, cited sources) changed since stamping: reproducible, possibly reproducibly wrong.

## Pitfalls

- **Only claim evidence you observed.** A stamp that says tests passed when they did not poisons every agent that trusts it. If you verified nothing, stamp with no evidence: the low score is the honest signal.
- **Never `akf replay --run` on a file you have not read.** It executes the recorded command.
- **Stamps are claims, not proofs.** They are like commit messages with an accountability trail. `akf sign` adds an Ed25519 signature for the provenance part only.
- **Fresh clones can show STALE.** Staleness is mtime-based, so a whole repo reporting STALE right after checkout is the checkout, not tampering.
- **Classification defaults to `internal`.** Use `--label public` for docs and examples, `--label confidential` for finance, secret, or internal paths.

## Verification

- `akf check <file>` on a file you just stamped with real evidence prints `OK` and exits 0.
- Append a byte to that file and `akf check` prints `STALE` and exits 1. If so, the loop works.
