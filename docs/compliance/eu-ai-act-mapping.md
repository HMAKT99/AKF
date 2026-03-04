# AKF Compliance: EU AI Act Mapping

## Overview

The EU AI Act requires transparency, human oversight, and documentation for AI systems. AKF provides the metadata infrastructure to meet these requirements.

## Article Mapping

### Article 12 — Record-keeping

**Requirement**: AI systems must maintain logs of their operation.

**AKF Coverage**:
- `provenance` chain records every transformation with timestamps and actors
- `integrity_hash` ensures tamper-evident audit trail
- `akf.compliance.audit_trail()` generates compliance-ready reports

### Article 13 — Transparency

**Requirement**: AI systems must be designed to be sufficiently transparent.

**AKF Coverage**:
- `ai_generated: true` flag identifies AI-produced content
- `source` field traces information origin
- `risk` field documents known limitations
- `confidence` score quantifies uncertainty

### Article 14 — Human Oversight

**Requirement**: AI systems must allow human oversight.

**AKF Coverage**:
- `verified` and `verified_by` fields record human review
- `akf.compliance.verify_human_oversight()` checks for human actors in provenance
- `authority_tier` enables human override of AI claims

### Article 15 — Accuracy and Robustness

**Requirement**: AI systems must achieve appropriate levels of accuracy.

**AKF Coverage**:
- `confidence` scores provide calibrated accuracy signals
- `authority_tier` weights claims by source reliability
- `akf.trust.effective_trust()` computes aggregate trustworthiness

## Usage

```python
import akf

unit = akf.load("output.akf")
result = akf.check_regulation(unit, "eu_ai_act")
print(f"Compliant: {result.compliant}")
print(f"Score: {result.score}")
for check in result.checks:
    print(f"  {check['check']}: {'PASS' if check['passed'] else 'FAIL'}")
```
