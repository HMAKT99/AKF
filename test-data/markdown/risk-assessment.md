---
akf:
  classification: restricted
  claims:
    - c: "Model drift: 3% accuracy decline"
      t: 0.7
      src: ML monitoring
      ai: true
    - c: 12 PII incidents detected
      t: 0.95
      src: Security audit
      ai: true
---
# Risk Assessment — AI Systems

## High-Risk Areas
1. **Model Drift**: GPT-4o predictions showing 3% accuracy decline over 6 months
2. **Data Privacy**: 12 incidents of PII detected in training data (all remediated)
3. **Bias**: Gender bias detected in hiring recommendations (mitigation deployed)

## Mitigation Status
- Model retraining scheduled for Q4 2026
- PII scanner deployed across all pipelines
- Bias audit completed by external auditor (Deloitte)

## Compliance Status
- EU AI Act: Article 13 transparency — PARTIAL
- SOX 404: Internal controls — COMPLIANT
- HIPAA: PHI handling — COMPLIANT
