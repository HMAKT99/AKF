# Skill: Audit for Compliance

Audit AKF-stamped files against regulatory frameworks.

## When to use

- Before publishing or sharing AI-generated content
- During compliance reviews
- When checking content against specific regulations

## Supported regulations

| Regulation | Key | What it checks |
|-----------|-----|----------------|
| EU AI Act | `eu_ai_act` | AI labeling, human oversight, risk classification |
| HIPAA | `hipaa` | PHI protection, access controls, audit trails |
| SOX | `sox` | Financial accuracy, internal controls |
| GDPR | `gdpr` | Data provenance, consent tracking |
| NIST AI RMF | `nist_ai` | Risk management framework alignment |
| ISO 42001 | `iso_42001` | AI management system standards |

## Python API

```python
import akf

# General compliance audit (runs 10 checks)
result = akf.audit("report.akf")
print(f"Score: {result.score:.2f}, Compliant: {result.compliant}")

# Audit against specific regulation
result = akf.audit("report.akf", regulation="eu_ai_act")

# Check specific regulation
result = akf.check_regulation("report.akf", "hipaa")

# Generate audit trail
trail = akf.audit_trail("report.akf", format="markdown")

# Verify human oversight
oversight = akf.verify_human_oversight("report.akf")
```

## CLI

```bash
akf audit report.akf                          # General audit
akf audit report.akf --regulation eu_ai_act   # EU AI Act
akf audit report.akf --regulation hipaa       # HIPAA
akf audit report.akf --trail                  # Audit trail
```

## Output

The audit returns:
- `score` (float): Compliance score 0.0–1.0
- `compliant` (bool): Whether the file passes
- `checks` (list): Individual check results with pass/fail and recommendations
- `regulation` (str): Which regulation was checked
