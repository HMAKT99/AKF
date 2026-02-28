# AKF — Agent Knowledge Format

**The simplest file format for AI-generated knowledge with built-in trust, provenance, and security.**

AKF is to AI knowledge what JSON is to data — a minimal format that carries trust scores, source provenance, and security classification alongside every knowledge claim. Any LLM can produce valid AKF from a one-shot example.

## Quickstart

```bash
pip install akf
```

```python
import akf

# Create
unit = akf.create("Revenue was $4.2B, up 12% YoY", t=0.98, src="SEC 10-Q", tier=1)
unit.save("report.akf")

# Load
unit = akf.load("report.akf")

# Validate
result = akf.validate("report.akf")
print(result.valid, result.level)  # True, 2
```

## Why AKF?

| Era | Format | Carries |
|-----|--------|---------|
| Document | PDF, DOCX | Text + formatting |
| Data | JSON, CSV | Structured values |
| **AI Knowledge** | **.akf** | **Claims + trust + provenance + security** |

Every AI-generated insight needs three things documents and data don't: *How confident is this? Where did it come from? Who can see it?* AKF answers all three in ~15 tokens.

## Format at a Glance

**Minimal** (~15 tokens):
```json
{"v":"1.0","claims":[{"c":"Revenue was $4.2B","t":0.98}]}
```

**Practical** (with source and tier):
```json
{"v":"1.0","by":"sarah@woodgrove.com","label":"confidential","claims":[
  {"c":"Revenue $4.2B, up 12%","t":0.98,"src":"SEC 10-Q","tier":1,"ver":true},
  {"c":"Cloud growth 15-18%","t":0.85,"src":"Gartner","tier":2},
  {"c":"Pipeline strong","t":0.72,"src":"CRM estimate","tier":4}
]}
```

**Full** (with provenance, decay, AI flags):
```json
{"v":"1.0","by":"sarah@woodgrove.com","label":"confidential","inherit":true,
 "claims":[
   {"c":"Revenue $4.2B","t":0.98,"src":"SEC 10-Q","tier":1,"ver":true,"decay":90},
   {"c":"H2 will accelerate","t":0.63,"tier":5,"ai":true,"risk":"AI inference"}
 ],
 "prov":[
   {"hop":0,"by":"sarah@woodgrove.com","do":"created","at":"2025-07-15T09:30:00Z"},
   {"hop":1,"by":"copilot-m365","do":"enriched","at":"2025-07-15T10:15:00Z"}
 ]}
```

## Installation

```bash
# Python
pip install akf

# TypeScript / Node.js
npm install akf
```

## SDK Usage

### Python

```python
import akf

# Builder API
unit = (akf.AKFBuilder()
    .by("sarah@woodgrove.com")
    .label("confidential")
    .claim("Revenue $4.2B", 0.98, src="SEC 10-Q", tier=1, ver=True)
    .claim("Cloud growth 15-18%", 0.85, src="Gartner", tier=2)
    .claim("Pipeline strong", 0.72, src="estimate", tier=4)
    .build())

# Trust computation
for claim in unit.claims:
    result = akf.effective_trust(claim)
    print(f"{result.decision}: {result.score:.2f} — {claim.c}")

# Agent consumption (filter + transform)
brief = (akf.AKFTransformer(unit)
    .filter(trust_min=0.5)
    .penalty(-0.03)
    .by("research-agent")
    .build())
brief.save("weekly-brief.akf")
```

### TypeScript

```typescript
import { AKFBuilder, effectiveTrust } from 'akf';

const unit = new AKFBuilder()
  .by('sarah@woodgrove.com')
  .label('confidential')
  .claim('Revenue $4.2B', 0.98, { src: 'SEC 10-Q', tier: 1, ver: true })
  .claim('Cloud growth 15-18%', 0.85, { src: 'Gartner', tier: 2 })
  .build();

unit.claims.forEach(claim => {
  const result = effectiveTrust(claim);
  console.log(`${result.decision}: ${result.score} — ${claim.c}`);
});
```

## CLI

```bash
# Create
akf create report.akf \
  --claim "Revenue $4.2B" --trust 0.98 --src "SEC 10-Q" \
  --claim "Cloud growth 15%" --trust 0.85 --src "Gartner" \
  --by sarah@woodgrove.com --label confidential

# Validate
akf validate report.akf
# ✅ Valid AKF (Level 2: Practical) | 2 claims | confidential | ✓ integrity

# Inspect with trust indicators
akf inspect report.akf
# 🟢 0.98  "Revenue $4.2B"       SEC 10-Q   Tier 1  verified
# 🟡 0.85  "Cloud growth 15%"    Gartner    Tier 2

# Compute effective trust
akf trust report.akf

# Agent consumption
akf consume report.akf --output brief.akf --threshold 0.6 --agent research-bot

# Provenance chain
akf provenance report.akf --format tree
# sarah@woodgrove.com created (+2 claims)
#   └→ research-bot consumed (+2 claims)

# AI enrichment
akf enrich report.akf --agent copilot --claim "AI insight" --trust 0.75

# Diff two files
akf diff report.akf brief.akf
```

## Trust Computation

```
effective_trust = t × authority_weight × temporal_decay × (1 + penalty)
```

| Tier | Weight | Example |
|------|--------|---------|
| 1 | 1.00 | SEC filings, official records |
| 2 | 0.85 | Analyst reports, peer-reviewed |
| 3 | 0.70 | News, industry reports |
| 4 | 0.50 | Internal estimates, CRM data |
| 5 | 0.30 | AI inference, extrapolations |

**Decision:** score >= 0.7 ACCEPT | >= 0.4 LOW | < 0.4 REJECT

## Provenance

Every transformation is tracked:

```
sarah@woodgrove.com created (+3 claims) — sha256:a3f2...
  └→ copilot-m365 enriched (+2 claims) — sha256:b7c1...
    └→ sarah@woodgrove.com reviewed (+1, -1 rejected) — sha256:c3d4...
      └→ research-agent consumed (2 accepted) — sha256:d9e4...
```

## For LLMs

Tell your LLM: *"Output in AKF format."*

Include this one-shot example in your prompt:

```
Output knowledge as AKF:
{"v":"1.0","claims":[{"c":"<claim>","t":<0-1>,"src":"<source>","tier":<1-5>,"ai":true}]}
```

LLMs produce valid AKF 95%+ of the time from a single example.

## Specification

- [Full Format Spec](spec/akf-v1.0-spec.md)
- [JSON Schema](spec/akf-v1.0.schema.json)
- [Trust Computation](docs/trust-computation.md)
- [Purview Integration](docs/purview-integration.md)
- [LLM Integration](docs/llm-integration.md)

## Contributing

1. Fork the repo
2. Create a feature branch
3. Make your changes with tests
4. Submit a PR

All example .akf files must validate against the JSON Schema. All tests must pass.

## License

MIT
