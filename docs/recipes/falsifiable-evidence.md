---
akf:
  v: "1.0"
  claims:
    - c: "Trust metadata for docs/recipes/falsifiable-evidence.md"
      t: 0.7
      id: 5c39b04f
      src: unspecified
      tier: 5
      ver: false
      ai: true
      evidence:
        - type: other
          detail: examples verified against published akf 1.6.0
          at: "2026-08-02T02:31:14.524508+00:00"
  id: "akf-90ca35be4af5"
  agent: "claude-code"
  at: "2026-08-02T02:31:14.525191+00:00"
  label: public
  inherit: true
  ext: false
  hash: "sha256:9bd968817e4b80e7"
  sv: "1.1"
---
# Recipe: Falsifiable Evidence

A stamp is a claim: "this was verified." But a claim is only as good as your
trust in whoever made it — and a trusted source can still be confidently
wrong. A signature proves *who* said it; it doesn't prove the thing is true.

The only way to know a claim is still true is to **re-derive it**. AKF lets a
stamp carry the recipe for doing exactly that: a probe command, its expected
result, and a fingerprint of the inputs the claim was made against. Anyone can
re-run it. Trust stops depending on the label.

## Stamp with a replay recipe

```bash
akf stamp auth.py --agent claude-code \
    --evidence "42/42 tests passed" \
    --replay "pytest tests/test_auth.py -q"
```

The recipe records:

- **command** — how to re-verify the claim
- **expected_exit** — the exit code that means "confirmed" (default 0)
- **output_digest** — optional hash of the expected output
- **input_hash** — a fingerprint of the claim's input closure (the file's
  recorded dependencies + any pinned sources), captured **at issuance**

## Re-verify

```bash
# Inspect only — show the recipe and whether inputs drifted (no execution)
akf replay auth.py

# Re-run the probe
akf replay auth.py --run
```

Four verdicts:

| Verdict | Exit | Meaning |
|---------|------|---------|
| `CONFIRMED` | 0 | Probe passed, **and** inputs match what the claim was made against |
| `CONFIRMED_DRIFTED` | 1 | Probe passed, but against inputs that changed since issuance — provably reproducible, possibly *reproducibly wrong* |
| `REFUTED` | 2 | Probe ran and did not produce the claimed result |
| `UNREPLAYABLE` | 3 | No recipe recorded |

The `CONFIRMED` / `CONFIRMED_DRIFTED` split is the important one. A probe that
still passes tells you the claim reproduces — but if a dependency or cited
source moved since the stamp was written, it reproduced against a *different
world* than the one the claim described. That's the difference between an
audit and a reputation.

## Safety

Running a recipe executes a command recorded inside the file's stamp.

- `akf replay <file>` (no `--run`) never executes — it only shows the recipe
  and drift status.
- `--run` executes the command **with your privileges**. Never `--run` a
  stamp from a file you haven't read — treat it like any script from an
  untrusted source.

## Why this matters for agents

Agent pipelines cache "verified" and build on it. But a wrong verification
gets cached as trusted and every later step quietly inherits it — harder to
catch than honest re-checking. Falsifiable evidence turns the cache into
something checkable: instead of re-deriving everything (expensive) or trusting
blindly (dangerous), an agent re-runs the probe (cheap) exactly when it needs
to.

```python
import akf

result = akf.verify_file("auth.py", run=True)
if result.verdict == "CONFIRMED":
    ...  # build on it
elif result.verdict == "CONFIRMED_DRIFTED":
    ...  # passed, but inputs moved — decide whether the drift matters
else:
    ...  # REFUTED / UNREPLAYABLE — re-verify from scratch
```

## Combine with check

`akf check` reads what a stamp *claims* (fast, ~20 tokens). `akf replay`
re-runs what it can *prove* (slower, executes code). Use `check` on the hot
path to skip re-verification, and `replay` when the stakes justify actually
re-deriving the claim — a release gate, a security-sensitive dependency, or a
memory an agent is about to act on.
