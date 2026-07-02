---
akf:
  v: "1.0"
  claims:
    - c: "Trust metadata for docs/recipes/agent-memory.md"
      t: 0.7
      id: "69083628"
      src: unspecified
      tier: 5
      ver: false
      ai: true
      evidence:
        - type: other
          detail: examples verified against shipped CLI behavior
          at: "2026-07-02T17:06:46.584905+00:00"
  id: "akf-6ba1923dc909"
  agent: "claude-code"
  at: "2026-07-02T17:06:46.587959+00:00"
  label: public
  inherit: true
  ext: false
  hash: "sha256:757b9950b22601f4"
  sv: "1.1"
---
# Recipe: Trust Metadata for Agent Memory

Agents with persistent memory have a known failure mode: **stale or wrong
memories poison future sessions.** A memory written three months ago about a
codebase that has since been refactored is worse than no memory at all — the
agent trusts it and builds on a lie.

AKF's schema already has everything memory trust needs: `confidence`,
`decay_half_life`, `src`, and per-claim timestamps. This recipe wires them to
your agent's memory directory.

## The idea

Stamp every memory file with `--preset memory`. The preset sets a **30-day
trust half-life**: a memory that starts at 0.7 confidence is worth ~0.35
after a month and ~0.17 after two. `akf check` applies the decay
automatically — old memories fall below the trust threshold and report `LOW`,
telling the agent to re-verify before relying on them.

```bash
# When the agent writes a memory
akf stamp memory/project-facts.md --preset memory --agent claude-code \
    --evidence "observed in session 2026-07-02"

# When a later session reads it
akf check memory/project-facts.md
# fresh:      OK trust=0.75 agent=claude-code age=2d ...
# two months: LOW trust=0.17 agent=claude-code age=61d reason=below_threshold
```

## Stamping a whole memory directory

```bash
for f in memory/*.md; do
  akf stamp "$f" --preset memory --agent claude-code
done
```

## Rules stanza for your agent

Add to your CLAUDE.md / AGENTS.md:

```markdown
## Memory trust
- After writing a memory file: `akf stamp <file> --preset memory --agent <your-id>`
- Before relying on a memory: `akf check <file>` — LOW or STALE means the
  memory is old or was edited without re-verification; confirm it against
  the current state of the world before using it.
```

## Choosing a half-life

The preset default is 30 days. For a different shelf life, stamp from Python
with an explicit `decay_half_life`:

```python
import akf

# Volatile fact: which branch is deployed (1-day half-life)
akf.stamp_file("memory/deploy-state.md", agent="claude-code",
               kind="memory", decay_half_life=1,
               claims=["main is deployed to prod"])
```

| Memory type | Suggested half-life |
|-------------|--------------------|
| Deploy/runtime state | 1 day |
| In-progress work notes | 7 days |
| Project facts, conventions | 30 days (preset default) |
| User preferences | 365 days |

## Why this beats timestamp-checking

A timestamp tells an agent *when* a memory was written; it doesn't say *how
much to discount it*. Decay converts age into a trust score on the same 0–1
scale as everything else, so one threshold (`akf check`) gates memories, code
stamps, and handoffs uniformly.
