---
akf:
  classification: public
  claims:
    - c: "Multi-agent verification reduces error by 40%"
      t: 0.88
      src: Experiment
---
# Trust Scoring in Multi-Agent AI Systems

## Abstract
We propose a hierarchical trust framework for multi-agent AI outputs.
Each claim carries a confidence score weighted by authority tier,
provenance depth, and cross-agent verification status.

## Methodology
- Dataset: 10,000 AI-generated claims across 5 domains
- Models: GPT-4o, Claude 3.5, Gemini Pro, Llama 3
- Metrics: Precision@0.8, trust calibration error

## Results
| Model | Precision@0.8 | Calibration Error |
|-------|---------------|-------------------|
| GPT-4o | 0.92 | 0.034 |
| Claude 3.5 | 0.94 | 0.028 |
| Gemini Pro | 0.89 | 0.041 |
| Llama 3 | 0.85 | 0.055 |

## Conclusion
Multi-agent verification reduces trust calibration error by 40%.
