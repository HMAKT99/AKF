# Skill: Security Detection

Run AKF's 10 enterprise security detection classes against trust metadata.

## When to use

- During security reviews of AI-generated content
- When monitoring AI content pipelines
- Before publishing content to catch trust issues

## 10 Detection classes

| # | Detection | What it catches |
|---|-----------|----------------|
| 1 | AI Without Review | AI output with no human oversight |
| 2 | Trust Below Threshold | Claims below org trust policies |
| 3 | Hallucination Risk | High-confidence AI without sources |
| 4 | Knowledge Laundering | Confidential data leaking via trust chains |
| 5 | Classification Downgrade | Security labels silently reduced |
| 6 | Stale Claims | Expired trust scores still in use |
| 7 | Ungrounded Claims | AI assertions without evidence |
| 8 | Trust Degradation | Trust eroding across multi-hop chains |
| 9 | AI Concentration | Over-reliance on AI content |
| 10 | Provenance Gap | Missing links in trust chain |

## Python API

```python
from akf import run_all_detections, detect_hallucination_risk

# Run all 10 detections
report = run_all_detections(unit)
for finding in report.findings:
    print(f"[{finding.severity}] {finding.detection}: {finding.message}")

# Run individual detections
result = detect_hallucination_risk(unit)
if result.triggered:
    print(f"Risk: {result.message}")
    for claim in result.affected_claims:
        print(f"  - {claim}")
```

## Individual detection functions

```python
from akf import (
    detect_ai_without_review,
    detect_trust_below_threshold,
    detect_hallucination_risk,
    detect_knowledge_laundering,
    detect_classification_downgrade,
    detect_stale_claims,
    detect_ungrounded_claims,
    detect_trust_degradation_chain,
    detect_excessive_ai_concentration,
    detect_provenance_gap,
)
```
