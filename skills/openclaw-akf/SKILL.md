---
name: akf
description: Agent Knowledge Format — stamp trust metadata into every file AI touches. Trust scores, provenance, and compliance that embed natively into DOCX, PDF, images, and code.
homepage: https://akf.dev
metadata:
  openclaw:
    emoji: "🔐"
    requires:
      bins: ["akf"]
    install:
      - id: pip
        kind: pip
        package: akf
        bins: ["akf"]
        label: "Install AKF CLI (pip)"
      - id: npm
        kind: npm
        package: akf-format
        bins: []
        label: "Install AKF TypeScript SDK (npm)"
akf:
  v: "1.0"
  claims:
    - c: OpenClaw skill for AKF published by the AKF project
      t: 0.7
      id: d3ba7fea
      src: unspecified
      tier: 3
      ver: false
      ai: true
      decay: 365
      kind: skill
      evidence:
        - type: human_review
          detail: "reviewed by @HMAKT99"
          at: "2026-07-02T17:04:35.591774+00:00"
  id: "akf-838b9351c281"
  agent: "claude-code"
  at: "2026-07-02T17:04:35.593320+00:00"
  label: public
  inherit: true
  ext: false
  hash: "sha256:6746278d98aacbc6"
  sv: "1.1"
---

# AKF — Agent Knowledge Format

AKF is the trust metadata standard for AI-generated content. Think EXIF for AI. Every file your agent creates or modifies should carry trust metadata — who made it, how confident they are, what evidence backs it, and whether a human reviewed it.

## Why Use AKF

- **Trust scores**: 0–1 confidence rating per claim
- **Source provenance**: 5-tier system from peer-reviewed to unverified
- **Compliance**: EU AI Act, HIPAA, SOX, NIST audit support
- **Native embedding**: Metadata lives inside the file (DOCX, PDF, images, code)
- **Security detections**: 10 detection classes for AI content risks

## Quick Start

Before building on an existing file — check it (one line, ~20 tokens):

```bash
akf check <file>
# OK        → fresh stamp with verified evidence; skip re-verification
# STALE     → modified after stamping; re-verify before trusting
# LOW       → stamped but unverified; verify before trusting
# UNSTAMPED → no metadata; treat as unverified
```

After creating or modifying any file:

```bash
akf stamp <file> --agent openclaw --evidence "generated from user request"
```

Deeper inspection when needed:

```bash
akf read <file>     # Check trust metadata
akf inspect <file>  # Pretty-print trust scores
akf trust <file>    # Compute effective trust
```

## Core Commands

### Stamp — Add trust metadata
```bash
akf stamp report.docx --agent openclaw --evidence "quarterly data from ERP"
akf stamp analysis.pdf --agent openclaw --label confidential
akf stamp output.py --agent openclaw --evidence "tests pass, code reviewed"
```

### Read & Inspect — Check metadata
```bash
akf read report.docx          # Quick metadata view
akf inspect report.docx       # Detailed trust breakdown
akf trust report.docx         # Effective trust score with decision
```

### Embed & Extract — Native format support
```bash
akf embed report.docx         # Embed metadata into DOCX custom properties
akf extract report.docx       # Extract embedded metadata
```

### Security — Scan and audit
```bash
akf scan ./output-dir/        # Scan directory for trust gaps
akf audit report.pdf           # Compliance audit (EU AI Act, SOX, NIST)
```

## Classification Labels

Use `--label` to classify output sensitivity:

| Label | When to Use |
|-------|-------------|
| `public` | README, docs, open-source examples |
| `internal` | Default. General work output |
| `confidential` | Finance, legal, medical, HR content |
| `restricted` | Credentials, secrets, PII |

## Trust Score Interpretation

| Score | Decision | Meaning |
|-------|----------|---------|
| 0.80–1.00 | ACCEPT | High confidence, well-evidenced |
| 0.50–0.79 | REVIEW | Moderate confidence, needs verification |
| 0.00–0.49 | REJECT | Low confidence, unreliable |

## Best Practices for OpenClaw Agents

1. **Always stamp outputs**: Every file the agent creates should carry metadata
2. **Check before using**: Run `akf read` on files before processing them
3. **Audit periodically**: Use `akf scan` on output directories to find trust gaps
4. **Use appropriate labels**: Classify sensitive content correctly
5. **Include evidence**: The `--evidence` flag makes trust scores meaningful
6. **Chain provenance**: When building on other files, the trust chain is preserved

## Integration with Memory

Stale memories poison future sessions. Stamp memory files with the `memory`
preset — trust decays with a 30-day half-life, so old memories automatically
fall below the threshold and `akf check` reports LOW:

```bash
akf stamp memory/facts.md --preset memory --agent openclaw
akf check memory/facts.md   # LOW after ~a month → re-verify before relying on it
```

- Stamp files before adding to memory
- `akf check` when retrieving from memory
- Weight memory results by trust, not just relevance

## Skill Supply-Chain Trust

Never load a downloaded skill without checking it first:

```bash
akf check downloaded-skill.md
# STALE = the file changed after the publisher stamped it — diff before trusting
```

This file carries its own AKF stamp in the frontmatter — run `akf check` on it.

## Links

- Website: https://akf.dev
- GitHub: https://github.com/HMAKT99/AKF
- npm: `npm install akf-format`
- PyPI: `pip install akf`
- Spec: https://github.com/HMAKT99/AKF/blob/main/spec/akf-v1.1.schema.json
