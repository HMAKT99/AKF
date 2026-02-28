# AKF — Agent Knowledge Format (Python SDK)

Lightweight file format for AI-generated knowledge with built-in trust, provenance, and security.

## Install

```bash
pip install akf
```

## Usage

```python
import akf

# Create a single-claim unit
unit = akf.create("Revenue $4.2B", t=0.98, src="SEC 10-Q", tier=1)
unit.save("report.akf")

# Load and validate
unit = akf.load("report.akf")
result = akf.validate(unit)

# Builder API
unit = (akf.AKFBuilder()
    .by("sarah@woodgrove.com")
    .label("confidential")
    .claim("Revenue $4.2B", 0.98, src="SEC 10-Q", tier=1, ver=True)
    .claim("Cloud growth 15%", 0.85, src="Gartner", tier=2)
    .build())

# Trust computation
for claim in unit.claims:
    result = akf.effective_trust(claim)
    print(f"{result.decision}: {result.score:.2f}")

# Agent consumption
brief = (akf.AKFTransformer(unit)
    .filter(trust_min=0.5)
    .penalty(-0.03)
    .by("research-agent")
    .build())
```

## CLI

```bash
akf create report.akf --claim "Revenue $4.2B" --trust 0.98
akf validate report.akf
akf inspect report.akf
akf trust report.akf
akf consume report.akf --output brief.akf --threshold 0.6
akf provenance report.akf
```
