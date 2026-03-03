# AKF — Agent Knowledge Format

**The trust metadata standard for every file AI touches.**

AKF is to AI-generated content what EXIF is to photos. Every file that AI touches should carry trust scores, source provenance, and security classification. AKF embeds this metadata into any format — DOCX, PDF, XLSX, HTML, images, and more — or travels as a standalone `.akf` knowledge file.

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

## Works With Every Format

AKF metadata embeds into any file AI touches:

| Format | How It Works |
|--------|-------------|
| `.akf` | Native (standalone knowledge claims) |
| `.docx` `.xlsx` `.pptx` | Embedded in OOXML custom XML part |
| `.pdf` | Embedded in PDF metadata |
| `.html` | JSON-LD `<script type="application/akf+json">` |
| `.md` | YAML frontmatter |
| `.png` `.jpg` | EXIF/XMP metadata |
| `.json` | Reserved `_akf` key |
| Everything else | Sidecar `.akf.json` companion file |

One API for all formats:

```python
import akf

# Embed trust metadata into any file
akf.embed("report.docx", claims=[...], classification="confidential")
akf.embed("data.xlsx", claims=[...])
akf.embed("slides.pptx", claims=[...])
akf.embed("notes.md", claims=[...])
akf.embed("chart.png", claims=[...])

# Extract from any file
meta = akf.extract("report.docx")

# Security scan any file or directory
akf.scan("report.docx")
akf.info("report.docx")
```

## Installation

```bash
# Core (standalone .akf + sidecar + Markdown/HTML/JSON)
pip install akf

# With Office format support
pip install akf[office]    # DOCX + XLSX + PPTX
pip install akf[pdf]       # PDF
pip install akf[image]     # PNG/JPEG
pip install akf[all]       # Everything

# TypeScript / Node.js
npm install akf
```

## SDK Usage

### Python — Standalone .akf

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

### Python — Universal Format Layer

```python
import akf.universal as akf_u

# Embed into any format — auto-detected from extension
akf_u.embed("report.docx", claims=[
    {"location": "paragraph:3", "c": "Revenue $4.2B", "t": 0.98,
     "src": "SEC 10-Q", "ver": True},
    {"location": "paragraph:7", "c": "Growth accelerating", "t": 0.63,
     "src": "AI inference", "ai": True},
], classification="confidential")

# Extract from any format
meta = akf_u.extract("report.docx")

# Security scan
report = akf_u.scan("report.docx")
print(report.classification, report.ai_claim_count, report.overall_trust)

# Scan entire directory (mixed formats)
results = akf_u.scan_directory("./knowledge-base/")

# Cross-format provenance — track AI transformations
akf_u.derive(source="data.xlsx", output="summary.docx",
             agent_id="copilot-v2", action="summarized")

# Auto-enrich AI-generated files
akf_u.auto_enrich("copilot-output.docx", agent_id="copilot-v2")

# Convert any format to standalone .akf
akf_u.to_akf("report.docx", output="report.akf")

# Sidecar for unsupported formats (video, audio, etc.)
akf_u.create_sidecar("video.mp4", metadata={
    "classification": "internal",
    "ai_contribution": 0.8,
    "claims": [{"c": "AI voiceover", "t": 0.7, "ai": True}]
})
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
# ── Standalone .akf commands ──

# Create
akf create report.akf \
  --claim "Revenue $4.2B" --trust 0.98 --src "SEC 10-Q" \
  --claim "Cloud growth 15%" --trust 0.85 --src "Gartner" \
  --by sarah@woodgrove.com --label confidential

# Validate, inspect, trust, consume, provenance, enrich, diff
akf validate report.akf
akf inspect report.akf
akf trust report.akf
akf consume report.akf --output brief.akf --threshold 0.6 --agent research-bot
akf provenance report.akf --format tree
akf enrich report.akf --agent copilot --claim "AI insight" --trust 0.75
akf diff report.akf brief.akf

# ── Universal format commands (works with ANY file) ──

# Embed AKF metadata into any file
akf embed report.docx --classification confidential \
  --claim "Revenue $4.2B" --trust 0.98

# Extract metadata
akf extract report.docx

# Quick info check
akf info report.docx
#   Format:          DOCX
#   AKF enriched:    Yes
#   Classification:  Confidential
#   Claims:          2

# Security scan (file or directory)
akf scan report.docx
akf scan ./knowledge-base/ --recursive

# Convert any format to standalone .akf
akf convert report.docx --output report.akf

# Create sidecar for any file
akf sidecar video.mp4 --classification internal

# List supported formats
akf formats
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
