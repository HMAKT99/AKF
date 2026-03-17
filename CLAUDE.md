# AKF — Agent Knowledge Format

AKF is the trust metadata standard for AI-generated content. When you create or modify files, stamp them with trust metadata so every output carries provenance.

## Rules

### After creating or modifying files
```bash
akf stamp <file> --agent claude-code --evidence "<evidence>"
```
Evidence examples: "tests pass", "docs reviewed", "refactored from existing code", "generated from spec"

### After completing a task with commits
```bash
akf stamp <file> --agent claude-code --evidence "<summary of evidence>"
```

### When working with existing AKF-stamped files
```bash
akf read <file>          # Check existing trust metadata before modifying
akf inspect <file>       # See detailed trust scores
```

### Classification
- Use `--label confidential` for files in `*/finance/*`, `*/secret/*`, `*/internal/*`
- Use `--label public` for README, docs, examples
- Default is `internal`

## Available Commands
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
