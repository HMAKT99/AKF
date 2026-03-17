# Skill: Stamp Trust Metadata

Stamp trust metadata onto any AI-generated output using AKF.

## When to use

- After generating content, code, or analysis
- After completing a task with verifiable evidence
- When committing code changes

## Python API

```python
import akf

# Stamp content with trust metadata
akf.stamp("Fixed authentication bypass vulnerability",
          kind="code_change",
          confidence=0.95,
          evidence=["42/42 tests passed", "mypy: 0 errors"],
          agent="claude-code",
          model="claude-sonnet-4-20250514")

# Stamp a file directly
akf.stamp_file("report.pdf",
               model="gpt-4o",
               claims=["Revenue $4.2B"],
               trust_score=0.95)

# Stamp a git commit
akf.stamp_commit(content="Refactored auth module",
                 kind="code_change",
                 evidence=["all tests pass"],
                 agent="claude-code")
```

## CLI

```bash
akf stamp <file> --agent claude-code --evidence "tests pass"
akf create report.akf --claim "Revenue $4.2B" --trust 0.98 --src "SEC 10-Q"
```

## Evidence auto-detection

Plain strings are auto-classified:
- `"42/42 tests passed"` → `type="test_pass"`
- `"mypy: 0 errors"` → `type="type_check"`
- `"lint: clean"` → `type="lint_clean"`
- `"reviewed by @user"` → `type="human_review"`

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | str | What was done or claimed |
| `kind` | str | Type: `code_change`, `analysis`, `review`, `generation` |
| `confidence` | float | Trust score 0.0–1.0 |
| `evidence` | list[str] | Supporting evidence strings |
| `agent` | str | Agent name (e.g., `claude-code`) |
| `model` | str | Model used (e.g., `claude-sonnet-4-20250514`) |
| `source` | str | Data source reference |
