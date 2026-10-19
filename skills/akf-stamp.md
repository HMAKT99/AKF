---
name: akf-stamp
description: Stamp files with AKF trust metadata — the AI native file format
version: 1.2.9
author: HMAKT99
tags: [trust, metadata, provenance, compliance, ai-native, file-format]
---

# AKF Stamp — The AI Native File Format

Every file your AI touches should carry provenance. AKF is EXIF for AI — ~15 tokens of JSON that embed trust scores, source provenance, and compliance metadata into 20+ file formats.

## After creating or modifying files

```bash
akf stamp <file> --agent claude-code --evidence "<what you did>"
```

Evidence examples: "tests pass", "docs reviewed", "refactored from existing code", "generated from spec"

## Check existing metadata before modifying

```bash
akf read <file>
akf inspect <file>
```

## Compliance audit

```bash
akf audit <file> --regulation eu_ai_act
akf audit <file> --regulation hipaa
akf audit <file> --regulation sox
```

## Classification

- `--label confidential` for finance/secret/internal paths
- `--label public` for README, docs, examples
- Default: `internal`

## Install

```bash
pip install akf
```

## Links

- https://akf.dev
- https://github.com/HMAKT99/AKF
- `npm install akf-format`
