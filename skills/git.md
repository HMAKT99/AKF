# Skill: Trust-Annotated Git

Attach trust metadata to git commits and view trust-annotated git logs.

## When to use

- After making code changes with AI assistance
- When reviewing git history for AI-generated commits
- To maintain trust provenance across code changes

## Python API

```python
import akf

# Stamp a git commit (uses git notes, not commit messages)
akf.stamp_commit(content="Refactored auth module",
                 kind="code_change",
                 evidence=["all tests pass", "mypy: 0 errors"],
                 agent="claude-code")

# Read trust metadata from current commit
unit = akf.read_commit()

# Trust-annotated git log
# + ACCEPT  ~ LOW  - REJECT  ? no metadata
log = akf.trust_log(n=10)
print(log)
```

## CLI

```bash
# Stamp current commit
akf stamp --agent claude-code --evidence "tests pass" --kind code_change

# View trust-annotated log
akf log --trust

# Output example:
# + a3f2c1d Fixed auth bypass (trust: 0.95, agent: claude-code)
# ~ b7c1e2f Updated docs (trust: 0.60, agent: copilot)
# ? c3d4f3a Manual commit (no AKF metadata)
```

## How it works

- Trust metadata is stored in **git notes** (not commit messages)
- Non-invasive — doesn't change commit hashes or history
- Works with any git workflow (rebase, merge, cherry-pick)
- Evidence auto-detected from strings
