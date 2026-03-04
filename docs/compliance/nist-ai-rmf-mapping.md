# AKF Compliance: NIST AI Risk Management Framework Mapping

## Overview

The NIST AI RMF provides a framework for managing AI risks. AKF metadata directly supports several core functions.

## Function Mapping

### GOVERN — Governance

**AKF Coverage**:
- `classification` enforces data handling policies
- `inherit_classification` prevents accidental declassification
- `allow_external` controls sharing boundaries

### MAP — Context and Risk

**AKF Coverage**:
- `risk` field on claims documents known AI risks
- `ai_generated` flag identifies AI-produced content
- `authority_tier` establishes source reliability hierarchy

### MEASURE — Assessment

**AKF Coverage**:
- `confidence` scores provide quantitative trust measurement
- `akf.trust.effective_trust()` computes multi-factor trust scores
- `akf.data.quality_report()` generates quality assessments

### MANAGE — Risk Management

**AKF Coverage**:
- `akf.compliance.audit()` performs comprehensive risk assessment
- `akf.security.detect_laundering()` identifies classification manipulation
- `akf.security.security_score()` provides overall security posture

## Usage

```python
import akf

unit = akf.load("ai-output.akf")
result = akf.check_regulation(unit, "nist_ai")
print(f"NIST AI RMF Score: {result.score}")
```
