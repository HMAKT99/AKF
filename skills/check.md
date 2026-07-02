---
akf:
  v: "1.0"
  claims:
    - c: Trust metadata for skills/check.md
      t: 0.7
      id: e00e890c
      src: unspecified
      tier: 5
      ver: false
      ai: true
      evidence:
        - type: other
          detail: "docs reviewed, matches shipped CLI behavior"
          at: "2026-07-02T16:52:28.328391+00:00"
  id: "akf-bda73947450c"
  agent: "claude-code"
  at: "2026-07-02T16:52:28.328612+00:00"
  label: public
  inherit: true
  ext: false
  hash: "sha256:6ce05b15b41d3215"
  sv: "1.1"
---
# Skill: Check Before You Trust

Check a file's trust metadata before building on it — one line, ~20 tokens, so you can skip re-verification when work is already verified.

## When to use

- Before modifying or extending a file another agent (or a past session) produced
- Before re-running tests, re-reading, or re-deriving something that may already be verified
- When deciding whether to trust a file handed off from another tool (Cursor, Copilot, Claude Code)

## CLI

```bash
akf check <file>
# OK trust=0.65 agent=claude-code evidence=test_pass age=1d claims=1

akf check <file> --json          # structured output
akf check <file> --threshold 0.8 # stricter gate
```

## How to act on the result

| Status | Exit | Action |
|--------|------|--------|
| `OK` | 0 | Fresh stamp with verified evidence — build on it, skip re-verification |
| `LOW` | 1 | Stamped but unverified (no test/review evidence) — verify before trusting |
| `STALE` | 1 | File modified after stamping, or claims expired — re-verify |
| `UNSTAMPED` | 2 | No metadata — treat as unverified |

## Python API

```python
import akf

result = akf.check_file("auth.py")
if result.status == "OK":
    ...  # skip re-verification
print(result.summary_line())   # OK trust=0.65 agent=claude-code evidence=test_pass age=1d claims=1
print(result.to_dict())        # full structured result
```

## How trust is computed

Verification receipts upgrade a stamp's authority: a bare AI stamp scores LOW no matter its confidence, but `test_pass`/`ci_pass` evidence lifts it to verified-process authority, and `human_review` higher still. Weak signals alone (`lint_clean`, `type_check`) don't clear the default 0.6 threshold.

Staleness is mechanical: if the file's mtime is later than the stamp timestamp, the stamp no longer describes the file — `STALE`.
