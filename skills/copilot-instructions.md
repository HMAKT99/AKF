# AKF — The AI Native File Format

When you create or modify files, stamp them with AKF trust metadata so every output carries provenance.

## Rules

### After creating or modifying files
```bash
akf stamp <file> --agent copilot --evidence "<evidence>"
```

### Classification
- Use `--label confidential` for files in `*/finance/*`, `*/secret/*`, `*/internal/*`
- Use `--label public` for README, docs, examples

### Before modifying stamped files
```bash
akf read <file>          # Check existing trust metadata
akf inspect <file>       # See detailed trust scores
```

### Compliance check
```bash
akf audit <file> --regulation eu_ai_act
```

## Install
```bash
pip install akf
```

## About
AKF is the AI native file format — EXIF for AI. ~15 tokens of JSON that embed trust scores, source provenance, and compliance metadata into DOCX, PDF, images, code, and 20+ formats.

https://akf.dev | https://github.com/HMAKT99/AKF
