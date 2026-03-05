# Skill: Security Scan

Scan files and directories for trust metadata, security issues, and classification problems.

## When to use

- Before sharing files externally
- When reviewing AI-generated content for security
- To get a quick trust overview of a file or directory

## Python API

```python
import akf

# Scan a single file
report = akf.scan("report.docx")
print(report.classification, report.ai_claim_count, report.overall_trust)

# Scan a directory
results = akf.scan_directory("./docs/")

# Get file info
akf.info("report.docx")

# Security score (0-10 with grade A-F)
score = akf.security_score(unit)
print(f"Score: {score.score}/10, Grade: {score.grade}")
```

## CLI

```bash
akf scan report.docx              # Scan single file
akf scan ./docs/ --recursive      # Scan directory
akf info report.docx              # Quick file info
```

## What it checks

- Trust scores across all claims
- Security classification consistency
- AI content labeling
- Provenance chain completeness
- Classification downgrade attempts
- Stale or expired claims
