---
akf:
  v: "1.0"
  claims:
    - c: Trust metadata for CLAUDE.md
      t: 0.7
      id: cf117d0c
      src: unspecified
      tier: 5
      ver: false
      ai: true
      evidence:
        - type: other
          detail: "docs reviewed, protocol matches shipped akf check behavior"
          at: "2026-07-02T16:52:28.182634+00:00"
  id: "akf-c8cf5407d8a6"
  agent: "claude-code"
  at: "2026-07-02T16:52:28.183459+00:00"
  label: public
  inherit: true
  ext: false
  hash: "sha256:2cc31b8895ecb034"
  sv: "1.1"
---
# AKF — Agent Knowledge Format

AKF is the trust metadata standard for AI-generated content. Stamps are notes agents leave for the next agent: what was done, what was verified, and how much to trust it. A stamp costs ~15 tokens; re-verifying costs thousands.

## The protocol

### Before building on an existing file — check it
```bash
akf check <file>
```
- `OK` — fresh stamp with verified evidence. Build on it; skip re-verification.
- `STALE` — modified after stamping. Re-verify before trusting.
- `LOW` — stamped but unverified (no test/review evidence). Verify before trusting.
- `UNSTAMPED` — no metadata. Treat as unverified.

### After creating or modifying files — stamp what you verified
```bash
akf stamp <file> --agent claude-code --evidence "<evidence>"
```
Evidence is auto-classified and drives trust: `"42/42 tests passed"` (test_pass), `"mypy: 0 errors"` (type_check), `"reviewed by @user"` (human_review), `"CI green"` (ci_pass). Only claim evidence you actually observed — a stamp that says tests passed when they didn't poisons every agent that trusts it.

### Deeper inspection when needed
```bash
akf read <file>          # Full trust metadata
akf inspect <file>       # Pretty-printed trust scores
```

### Classification
- Use `--label confidential` for files in `*/finance/*`, `*/secret/*`, `*/internal/*`
- Use `--label public` for README, docs, examples
- Default is `internal`

## Available Commands
- `akf check <file>` — One-line trust check (OK/LOW/STALE/UNSTAMPED, exit codes 0/1/2)
- `akf stamp <file>` — Add trust metadata to any file
- `akf read <file>` — Read trust metadata from any file
- `akf inspect <file>` — Pretty-print trust scores
- `akf embed <file>` — Embed metadata into DOCX/PDF/images
- `akf extract <file>` — Extract metadata from any format
- `akf scan <dir>` — Security scan a directory
- `akf audit <file>` — Compliance audit (EU AI Act, SOX, NIST)
- `akf trust <file>` — Compute effective trust scores

## Project Structure
- `python/akf/` — Python SDK source
- `typescript/src/` — TypeScript SDK source
- `site/` — Website (Vite + React + Tailwind)
- `spec/` — Format specification and JSON schema
- `packages/` — Framework integrations (MCP, LangChain, LlamaIndex, CrewAI)
- `extensions/` — VS Code, GitHub Action, Office, Google Workspace
- `skills/` — Agent skill files
