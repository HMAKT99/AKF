# AKF — Agent Knowledge Format

**The trust metadata standard for every file AI touches.**

AKF is to AI-generated content what EXIF is to photos. Every file that AI touches should carry trust scores, source provenance, and security classification. AKF embeds this metadata into any format — DOCX, PDF, XLSX, HTML, images, and more — or travels as a standalone `.akf` knowledge file.

## Quickstart

```bash
pip install akf
```

```python
import akf

# Create with descriptive field names (secure defaults applied)
unit = akf.create("Revenue was $4.2B, up 12% YoY", confidence=0.98, source="SEC 10-Q", authority_tier=1)
unit.save("report.akf")

# Load and validate
unit = akf.load("report.akf")
result = akf.validate("report.akf")
print(result.valid, result.level)  # True, 2

# Compact names still work
unit = akf.create("Revenue was $4.2B", t=0.98, src="SEC 10-Q", tier=1)
```

## For AI Agents

AKF ships a one-line `stamp()` API and git integration designed for AI agents — coding agents (Claude Code, Copilot, Cursor, Devin), research agents, data agents, and more.

```python
import akf

# One line — stamp what you did, with evidence
akf.stamp("Fixed auth bypass", kind="code_change",
          evidence=["42/42 tests passed", "mypy: 0 errors"],
          agent="claude-code", model="claude-sonnet-4-20250514")

# Stamp directly onto git commits (uses git notes, not commit messages)
akf.stamp_commit(content="Refactored auth module", kind="code_change",
                 evidence=["all tests pass"], agent="claude-code")

# Read it back
unit = akf.read_commit()

# Trust-annotated git log (+ ACCEPT, ~ LOW, - REJECT, ? no metadata)
print(akf.trust_log(n=10))
```

Evidence is auto-detected from plain strings: `"42/42 tests passed"` becomes `type="test_pass"`, `"mypy: 0 errors"` becomes `type="type_check"`, etc.

## Why AKF?

| Era | Format | Carries |
|-----|--------|---------|
| Document | PDF, DOCX | Text + formatting |
| Data | JSON, CSV | Structured values |
| **AI Knowledge** | **.akf** | **Claims + trust + provenance + security** |

Every AI-generated insight needs three things documents and data don't: *How confident is this? Where did it come from? Who can see it?* AKF answers all three in ~15 tokens.

## Format at a Glance

AKF supports both **compact** (wire format) and **descriptive** (human-readable) field names:

**Compact** (~15 tokens):
```json
{"v":"1.0","claims":[{"c":"Revenue was $4.2B","t":0.98,"src":"SEC 10-Q"}]}
```

**Descriptive** (same data, human-readable):
```json
{"version":"1.0","claims":[{"content":"Revenue was $4.2B","confidence":0.98,"source":"SEC 10-Q"}]}
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

Both formats are accepted on input and produce identical internal objects.

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

### Python — Core API

```python
import akf

# Builder API with descriptive field names
unit = (akf.AKFBuilder()
    .by("sarah@woodgrove.com")
    .label("confidential")
    .claim("Revenue $4.2B", 0.98, source="SEC 10-Q", authority_tier=1, verified=True)
    .claim("Cloud growth 15-18%", 0.85, source="Gartner", authority_tier=2)
    .claim("Pipeline strong", 0.72, source="estimate", authority_tier=4)
    .build())

# Descriptive attribute access
for claim in unit.claims:
    result = akf.effective_trust(claim)
    print(f"{result.decision}: {result.score:.2f} — {claim.content}")

# Agent consumption (filter + transform)
brief = (akf.AKFTransformer(unit)
    .filter(trust_min=0.5)
    .penalty(-0.03)
    .by("research-agent")
    .build())
brief.save("weekly-brief.akf")
```

### Python — Agent Integration

```python
import akf

# Consume existing AKF for agent use
derived = akf.consume("report.akf", "my-agent", trust_threshold=0.6)

# Create from AI tool calls
claim = akf.from_tool_call({"content": "Result", "confidence": 0.8})

# Format claims as LLM context
context = akf.to_context(unit, max_tokens=2000)

# Get structured output schema for LLMs
schema = akf.response_schema("standard")

# Validate LLM output as AKF
result = akf.validate_output(llm_response_text)
if result.valid:
    unit = result.unit

# Auto-detect AKF in files, dicts, or strings
detected = akf.detect(some_data)

# One-shot system prompt for any LLM
prompt = akf.generation_prompt()
```

### Python — Compliance & Audit

```python
import akf

# General compliance audit
result = akf.audit("report.akf")
print(f"Score: {result.score:.2f}, Compliant: {result.compliant}")

# Check against specific regulations
result = akf.check_regulation("report.akf", "eu_ai_act")   # EU AI Act
result = akf.check_regulation("report.akf", "sox")          # Sarbanes-Oxley
result = akf.check_regulation("report.akf", "hipaa")        # HIPAA
result = akf.check_regulation("report.akf", "gdpr")         # GDPR
result = akf.check_regulation("report.akf", "nist_ai")      # NIST AI RMF

# Generate audit trail
trail = akf.audit_trail("report.akf", format="markdown")

# Verify human oversight
oversight = akf.verify_human_oversight("report.akf")
print(oversight["has_human_oversight"], oversight["human_actors"])
```

### Python — Views & Reporting

```python
import akf

# Pretty terminal output
akf.show("report.akf")

# Generate standalone HTML report
html = akf.to_html("report.akf")

# Generate Markdown
md = akf.to_markdown("report.akf")

# Plain English executive summary
summary = akf.executive_summary("report.akf")
```

### Python — Data Operations

```python
import akf

# Load claims from multiple files
claims = akf.load_dataset(["a.akf", "b.akf"], filters={"min_trust": 0.6})

# Merge multiple units (deduplicates, takes highest classification)
merged = akf.merge([unit1, unit2, unit3])

# Filter claims
filtered = akf.filter_claims(unit, min_trust=0.5, verified_only=True, exclude_ai=True)

# Quality report
report = akf.quality_report(unit)
print(report["quality_score"], report["verified_claims"])
```

### Python — Knowledge Base

```python
import akf

# Persistent directory-backed knowledge store
kb = akf.KnowledgeBase("./kb")

# Add claims by topic
kb.add("Revenue was $4.2B", 0.98, source="SEC", topic="finance")
kb.add("Cloud grew 15%", 0.85, source="Gartner", topic="cloud")

# Query
claims = kb.query(topic="finance", min_trust=0.6)

# Format for LLM context injection
context = kb.to_context(max_tokens=2000)

# Maintenance
kb.prune(max_age_days=90, min_trust=0.3)
stats = kb.stats()  # {"topics": 2, "total_claims": 2, "average_trust": 0.915}
```

### Python — Security Analysis

```python
import akf

# Security score (0-10 with grade A-F)
score = akf.security_score(unit)
print(f"Score: {score.score}/10, Grade: {score.grade}")

# Microsoft Purview DLP-compatible signals
signals = akf.purview_signals(unit)

# Detect classification laundering
warnings = akf.detect_laundering(unit)

# Human-readable trust explanation
explanation = akf.explain_trust(claim, age_days=30)
```

### Python — Universal Format Layer

```python
import akf.universal as akf_u

# Embed into any format — auto-detected from extension
akf_u.embed("report.docx", claims=[
    {"location": "paragraph:3", "c": "Revenue $4.2B", "t": 0.98,
     "src": "SEC 10-Q", "ver": True},
], classification="confidential")

# Extract from any format
meta = akf_u.extract("report.docx")

# Security scan
report = akf_u.scan("report.docx")
print(report.classification, report.ai_claim_count, report.overall_trust)

# Scan entire directory (mixed formats)
results = akf_u.scan_directory("./knowledge-base/")

# Convert any format to standalone .akf
akf_u.to_akf("report.docx", output="report.akf")
```

### TypeScript

```typescript
import { AKFBuilder, effectiveTrust, fromJSON, toDescriptive } from 'akf';

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

// Parse descriptive JSON (auto-normalizes to compact)
const loaded = fromJSON('{"version":"1.0","claims":[{"content":"test","confidence":0.8}]}');

// Convert to descriptive for display
const descriptive = toDescriptive(unit);
```

## CLI

```bash
# ── Getting started ──
akf                          # Welcome message + quick start guide
akf create --demo            # Create a demo file with walkthrough

# ── Standalone .akf commands ──
akf create report.akf \
  --claim "Revenue $4.2B" --trust 0.98 --src "SEC 10-Q" \
  --claim "Cloud growth 15%" --trust 0.85 --src "Gartner" \
  --by sarah@woodgrove.com --label confidential

akf validate report.akf
akf inspect report.akf
akf trust report.akf
akf consume report.akf --output brief.akf --threshold 0.6 --agent research-bot
akf provenance report.akf --format tree
akf enrich report.akf --agent copilot --claim "AI insight" --trust 0.75
akf diff report.akf brief.akf

# ── Compliance ──
akf audit report.akf                          # General audit
akf audit report.akf --regulation eu_ai_act   # EU AI Act check
akf audit report.akf --trail                  # Show audit trail

# ── Knowledge Base ──
akf kb stats ./kb                             # Show KB statistics
akf kb query ./kb --topic finance             # Query by topic
akf kb prune ./kb --max-age 90 --min-trust 0.3  # Prune stale claims

# ── Universal format commands (works with ANY file) ──
akf embed report.docx --classification confidential \
  --claim "Revenue $4.2B" --trust 0.98
akf extract report.docx
akf info report.docx
akf scan report.docx
akf scan ./knowledge-base/ --recursive
akf convert report.docx --output report.akf
akf sidecar video.mp4 --classification internal
akf formats
```

## Trust Computation

```
effective_trust = confidence × authority_weight × temporal_decay × (1 + penalty)
```

| Tier | Weight | Example |
|------|--------|---------|
| 1 | 1.00 | SEC filings, official records |
| 2 | 0.85 | Analyst reports, peer-reviewed |
| 3 | 0.70 | News, industry reports |
| 4 | 0.50 | Internal estimates, CRM data |
| 5 | 0.30 | AI inference, extrapolations |

**Decision:** score >= 0.7 ACCEPT | >= 0.4 LOW | < 0.4 REJECT

## Secure Defaults

New units are born secure. `akf.create()` and `AKFBuilder` apply:

| Field | Default |
|-------|---------|
| `classification` | `"internal"` |
| `inherit_classification` | `True` |
| `allow_external` | `False` |
| `source` | `"unspecified"` |
| `authority_tier` | `3` |
| `verified` | `False` |
| `ai_generated` | `False` |

## Provenance

Every transformation is tracked:

```
sarah@woodgrove.com created (+3 claims) — sha256:a3f2...
  └→ copilot-m365 enriched (+2 claims) — sha256:b7c1...
    └→ sarah@woodgrove.com reviewed (+1, -1 rejected) — sha256:c3d4...
      └→ research-agent consumed (2 accepted) — sha256:d9e4...
```

## Framework Integrations

| Package | Description |
|---------|-------------|
| [`langchain-akf`](packages/langchain-akf/) | LangChain callback handler + document loader |
| [`mcp-server-akf`](packages/mcp-server-akf/) | MCP server with create, validate, scan, trust tools |
| [`llama-index-akf`](packages/llama-index-akf/) | LlamaIndex integration (stub) |
| [`crewai-akf`](packages/crewai-akf/) | CrewAI integration (stub) |

## Extensions

| Extension | Description |
|-----------|-------------|
| [VSCode](extensions/vscode/) | Syntax highlighting, hover info, validation for `.akf` files |
| [GitHub Action](extensions/github-action/) | Validate `.akf` files in CI, fail on untrusted claims |

## For LLMs

Tell your LLM: *"Output in AKF format."*

Include this one-shot example in your prompt:

```
Output knowledge as AKF:
{"v":"1.0","claims":[{"c":"<claim>","t":<0-1>,"src":"<source>","tier":<1-5>,"ai":true}]}
```

LLMs produce valid AKF 95%+ of the time from a single example. See [LLM-PROMPT.md](spec/LLM-PROMPT.md) for a full copy-paste system prompt and structured output schema.

## Specification & Documentation

- [Full Format Spec](spec/akf-v1.0-spec.md)
- [JSON Schema](spec/akf-v1.0.schema.json)
- [Producing AKF](spec/PRODUCING-AKF.md) — quick start for 8 languages
- [LLM Prompt](spec/LLM-PROMPT.md) — system prompt + structured output schema
- [Trust Computation](docs/trust-computation.md)
- [Purview Integration](docs/purview-integration.md)
- [LLM Integration](docs/llm-integration.md)
- [EU AI Act Mapping](docs/compliance/eu-ai-act-mapping.md)
- [NIST AI RMF Mapping](docs/compliance/nist-ai-rmf-mapping.md)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and PR process.

## License

MIT
