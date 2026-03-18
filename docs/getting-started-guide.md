# Agent Knowledge Format (AKF)

## Getting Started Guide

**Start trusting your AI output in 60 seconds.**

AKF is the open metadata standard for AI trust. Install once — trust scores, evidence, and provenance embed natively into Office docs, PDFs, images, and code.

```bash
pip install akf          # Python SDK
npm install akf-format   # TypeScript SDK
```

---

## Pick Your Path

### 1. Knowledge Workers — Trust What You Read

**The problem:** "Is this report real, or did an AI hallucinate it?"

```bash
# Open any document and check trust
akf read quarterly-report.docx

# Trust: 0.92 | Model: GPT-4o | Reviewed: Yes
```

**The outcome:** See trust scores, model provenance, and human-review status for every document you open.

---

### 2. AI Agents & Pipelines — Ambient Trust

**The problem:** "Our agent pipeline ships content with zero provenance."

```bash
# Drop a config file into your project — agents stamp their own work automatically
# CLAUDE.md / .cursorrules / .windsurfrules / AGENTS.md / .github/copilot-instructions.md

# Or use the MCP server (9 tools)
# stamp_file, audit_file, embed_file, extract_file, detect_threats...
```

```python
from akf import stamp_file

stamp_file("output.pdf",
    trust_score=0.95,
    model="gpt-4o",
    agent="my-agent")
```

**The outcome:** Every file your agent produces carries embedded trust metadata automatically. Claude Code, Cursor, Copilot, and any MCP agent stamp their work without manual intervention.

---

### 3. Security & CISOs — Detect What Others Miss

**The problem:** "Traditional DLP can't catch AI-specific threats."

```bash
# Scan for 10 classes of AI content risk
akf scan --recursive ./shared-drive/

# 3 files flagged: unreviewed AI content
```

**The outcome:** Detect unreviewed AI content, trust degradation, and classification drift across your org.

---

### 4. Governance & Compliance — Prove It. Automatically.

**The problem:** "We can't prove AI transparency to regulators."

```bash
# Generate compliance report for EU AI Act
akf audit --regulation eu_ai_act ./reports/

# 47 files audited, 100% compliant
```

**The outcome:** Machine-readable audit trails that satisfy EU AI Act, HIPAA, SOX, and GDPR requirements.

---

### 5. Developers — Build Trust Into Everything

**The problem:** "Adding trust metadata means weeks of custom infrastructure."

```typescript
import { normalize } from 'akf-format';

const stamp = normalize({
    c: 'Revenue analysis complete',
    t: 0.9,
    src: 'internal-kb',
    model: 'claude-4'
});
```

**The outcome:** `pip install` or `npm install`, then one function call. No infra, no API keys, no config.

---

## The Format — 15 Tokens. That's It.

### Without AKF

```markdown
# quarterly-report.md

Revenue grew 23% YoY...
Customer retention improved...

---
Who wrote this? AI or human?
How confident should I be?
What sources back this up?
```

### With AKF

```markdown
# quarterly-report.md

Revenue grew 23% YoY...
Customer retention improved...

---
confidence: 0.92
model: "gpt-4o"
source: "finance-db"
reviewed: true
```

### Trust Score Color Guide

| Score      | Meaning        | Action          |
|------------|----------------|-----------------|
| **0.7+**   | High trust     | Safe to use     |
| **0.4-0.7**| Needs review   | Verify sources  |
| **< 0.4**  | Low confidence | Do not publish  |

---

## Enterprise Ready

### Compliance Frameworks

| Framework    | Coverage                          |
|-------------|-----------------------------------|
| EU AI Act   | Transparency & human oversight     |
| HIPAA       | Healthcare AI audit trails         |
| SOX         | Financial AI controls              |
| GDPR        | Data provenance tracking           |
| ISO 42001   | AI management systems              |
| NIST AI RMF | Risk management framework          |

### 10 AI-Specific Security Detections

1. Unreviewed AI content
2. Trust score degradation
3. Classification drift
4. Provenance gaps
5. Model hallucination risk
6. Knowledge laundering
7. Excessive AI concentration
8. Missing human review
9. Tampered metadata
10. Confidence inflation

---

## Zero-Touch Auto-Stamping

AKF can automatically stamp every file AI touches — no manual `akf stamp` needed.

### Background Daemon

```bash
akf install        # Install background watcher daemon
akf watch ~/Downloads ~/Desktop ~/Documents   # Or run in foreground
```

The daemon monitors directories for new and modified files, using **smart context detection** to automatically infer:

- **Git author** — from commit history
- **Download source** — from macOS extended attributes
- **Classification** — from project `.akf/config.json` rules
- **AI-generated flag** — from LLM tracking + content heuristics
- **Confidence score** — dynamically adjusted based on evidence

### Shell Hook (intercept AI CLI tools)

```bash
# Add to ~/.zshrc or ~/.bashrc
eval "$(akf shell-hook)"
```

Automatically detects when you run `claude`, `chatgpt`, `aider`, `ollama`, or other AI CLI tools, and stamps any files they create or modify.

### VS Code Extension

The AKF VS Code extension auto-stamps files edited by Copilot, Cursor, and other AI coding tools. It detects large AI-style insertions and stamps on save.

### Project Rules

Create `.akf/config.json` in your project root to auto-classify files:

```json
{
  "rules": [
    {"pattern": "*/finance/*", "classification": "confidential", "tier": 2},
    {"pattern": "*/public/*", "classification": "public", "tier": 3}
  ]
}
```

---

## CLI Quick Reference

| Command                              | Description                        |
|--------------------------------------|------------------------------------|
| `akf quickstart`                     | Interactive demo (create→inspect→trust→security) |
| `akf doctor`                         | Check installation health          |
| `akf stamp <file>`                   | Add trust metadata to a file       |
| `akf read <file>`                    | Read trust metadata from a file    |
| `akf audit <path>`                   | Generate compliance audit report   |
| `akf audit --regulation <name> <path>`| Audit against a specific regulation |
| `akf scan <path>`                    | Scan for AI content risks          |
| `akf scan --recursive <path>`        | Recursive security scan            |
| `akf detect <file>`                  | Detect AI-specific threats         |
| `akf install`                        | Install background watcher daemon  |
| `akf watch <dirs>`                   | Watch directories for new files    |
| `akf shell-hook`                     | Print shell hook code for zsh/bash |

---

## Resources

- **GitHub:** [github.com/HMAKT99/AKF](https://github.com/HMAKT99/AKF)
- **npm:** [npmjs.com/package/akf-format](https://www.npmjs.com/package/akf-format)
- **Website:** [akf.dev](https://akf.dev)
- **Schema:** `spec/akf-v1.1.schema.json`
- **License:** MIT

---

*Agent Knowledge Format — EXIF for AI. Open standard. MIT Licensed.*
