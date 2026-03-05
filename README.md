<p align="center">
  <img src="https://img.shields.io/badge/format-.akf-blue?style=for-the-badge" alt="AKF Format" />
  <img src="https://img.shields.io/pypi/v/akf?style=for-the-badge&color=blue" alt="PyPI" />
  <img src="https://img.shields.io/npm/v/akf?style=for-the-badge&color=blue" alt="npm" />
  <img src="https://img.shields.io/github/license/HMAKT99/AKF?style=for-the-badge" alt="License" />
  <img src="https://img.shields.io/github/stars/HMAKT99/AKF?style=for-the-badge" alt="Stars" />
</p>

<h1 align="center">AKF — Agent Knowledge Format</h1>

<p align="center">
  <strong>The trust metadata standard for every file AI touches.</strong><br/>
  Trust scores · Source provenance · Security classification · Compliance audit<br/>
  Embeds natively into DOCX, PDF, XLSX, images, code, and 20+ formats.
</p>

<p align="center">
  <a href="#quickstart">Quickstart</a> ·
  <a href="#for-ai-agents">AI Agents</a> ·
  <a href="#mcp-server">MCP Server</a> ·
  <a href="#skills">Agent Skills</a> ·
  <a href="#cli">CLI</a> ·
  <a href="https://akf.dev">Website</a>
</p>

---

## What is AKF?

AKF is to AI-generated content what **EXIF is to photos**. Every file that AI touches should carry:

- **Trust scores** — How confident is this claim? (0–1)
- **Source provenance** — Where did it come from? (SEC filing → analyst → AI agent)
- **Security classification** — Who can see it? (public, internal, confidential)

AKF answers all three in **~15 tokens** of JSON, embedded directly into the file.

```
AI generates content → AKF stamps trust metadata → Anyone can verify it
```

## Quickstart

```bash
pip install akf    # Python
npm install akf    # TypeScript / Node.js
```

```python
import akf

# Stamp trust metadata onto any AI output
akf.stamp("Revenue was $4.2B, up 12% YoY",
          confidence=0.98, source="SEC 10-Q",
          agent="claude-code", model="claude-sonnet-4-20250514")

# Embed into Office docs, PDFs, images — any format
akf.embed("report.docx", claims=[...], classification="confidential")

# Audit for compliance (EU AI Act, HIPAA, SOX, GDPR, NIST AI, ISO 42001)
result = akf.audit("report.akf", regulation="eu_ai_act")
print(f"Compliant: {result.compliant}")

# Run all 10 security detection classes
from akf import run_all_detections
report = run_all_detections(unit)
```

## For AI Agents

AKF is designed **agent-first**. One-line APIs for stamping, streaming, and auditing AI output.

```python
import akf

# ── Stamp what you did, with evidence ──
akf.stamp("Fixed auth bypass", kind="code_change",
          evidence=["42/42 tests passed", "mypy: 0 errors"],
          agent="claude-code", model="claude-sonnet-4-20250514")

# ── Stream trust metadata in real-time ──
with akf.stream("output.md", model="gpt-4o") as s:
    for chunk in llm_response:
        s.write(chunk)
# Trust metadata auto-attaches when stream closes

# ── Stamp git commits (uses git notes, not commit messages) ──
akf.stamp_commit(content="Refactored auth module", kind="code_change",
                 evidence=["all tests pass"], agent="claude-code")

# ── Trust-annotated git log ──
# + ACCEPT  ~ LOW  - REJECT  ? no metadata
print(akf.trust_log(n=10))
```

Evidence is auto-detected: `"42/42 tests passed"` → `type="test_pass"`, `"mypy: 0 errors"` → `type="type_check"`.

## MCP Server

AKF ships an [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server so any AI agent can create, validate, scan, and audit trust metadata.

```bash
# Install
pip install mcp-server-akf

# Add to your MCP config (Claude Desktop, Cursor, etc.)
```

```json
{
  "mcpServers": {
    "akf": {
      "command": "python",
      "args": ["-m", "mcp_server_akf"]
    }
  }
}
```

**Available MCP tools:**

| Tool | Description |
|------|-------------|
| `akf_create` | Create AKF trust metadata with claims and provenance |
| `akf_validate` | Validate an AKF file against the schema |
| `akf_scan` | Security scan any file for trust metadata |
| `akf_trust` | Compute effective trust score for claims |

## Skills

AKF provides [agent skill files](skills/) that AI agents can discover and use. Drop these into your agent's context:

| Skill | What it does |
|-------|-------------|
| [`stamp.md`](skills/stamp.md) | Stamp trust metadata onto AI outputs |
| [`audit.md`](skills/audit.md) | Audit files for regulatory compliance |
| [`scan.md`](skills/scan.md) | Security scan files and directories |
| [`embed.md`](skills/embed.md) | Embed trust metadata into Office/PDF/images |
| [`detect.md`](skills/detect.md) | Run 10 security detection classes |
| [`stream.md`](skills/stream.md) | Stream trust metadata in real-time |
| [`git.md`](skills/git.md) | Trust-annotated git workflows |
| [`convert.md`](skills/convert.md) | Convert between formats |

## Format at a Glance

**Compact** (~15 tokens — optimized for AI):
```json
{"v":"1.0","claims":[{"c":"Revenue was $4.2B","t":0.98,"src":"SEC 10-Q"}]}
```

**Descriptive** (human-readable — same data):
```json
{"version":"1.0","claims":[{"content":"Revenue was $4.2B","confidence":0.98,"source":"SEC 10-Q"}]}
```

**Full** (with provenance, decay, AI flags, security):
```json
{"v":"1.0","by":"sarah@acme.com","label":"confidential","inherit":true,
 "claims":[
   {"c":"Revenue $4.2B","t":0.98,"src":"SEC 10-Q","tier":1,"ver":true,"decay":90},
   {"c":"H2 will accelerate","t":0.63,"tier":5,"ai":true,"risk":"AI inference"}
 ],
 "prov":[
   {"hop":0,"by":"sarah@acme.com","do":"created","at":"2025-07-15T09:30:00Z"},
   {"hop":1,"by":"copilot-agent","do":"enriched","at":"2025-07-15T10:15:00Z"}
 ]}
```

## Works With Every Format

AKF embeds natively — no sidecars needed for most formats:

| Format | How It Works |
|--------|-------------|
| `.akf` | Native standalone knowledge file |
| `.docx` `.xlsx` `.pptx` | OOXML custom XML part |
| `.pdf` | PDF metadata stream |
| `.html` | JSON-LD `<script type="application/akf+json">` |
| `.md` | YAML frontmatter |
| `.png` `.jpg` | EXIF/XMP metadata |
| `.json` | Reserved `_akf` key |
| Everything else | Sidecar `.akf.json` companion |

```python
# One API for all formats
akf.embed("report.docx", claims=[...], classification="confidential")
meta = akf.extract("report.docx")
akf.scan("report.docx")
```

## CLI

```bash
# ── Quick start ──
akf                          # Welcome + quick start
akf create --demo            # Create a demo file

# ── Stamp & create ──
akf create report.akf \
  --claim "Revenue $4.2B" --trust 0.98 --src "SEC 10-Q" \
  --by sarah@acme.com --label confidential

# ── Validate & inspect ──
akf validate report.akf
akf inspect report.akf
akf trust report.akf

# ── Compliance ──
akf audit report.akf                          # General audit
akf audit report.akf --regulation eu_ai_act   # EU AI Act
akf audit report.akf --trail                  # Audit trail

# ── Universal format commands ──
akf embed report.docx --classification confidential \
  --claim "Revenue $4.2B" --trust 0.98
akf extract report.docx
akf scan report.docx
akf scan ./docs/ --recursive

# ── Git integration ──
akf stamp --agent claude-code --evidence "tests pass"
akf log --trust                               # Trust-annotated git log

# ── Knowledge Base ──
akf kb stats ./kb
akf kb query ./kb --topic finance
```

## 10 Security Detection Classes

AKF includes enterprise-grade security detections:

| # | Detection | What It Catches |
|---|-----------|----------------|
| 1 | AI Content Without Review | AI output published without human oversight |
| 2 | Trust Below Threshold | Claims falling below organizational trust policies |
| 3 | Hallucination Risk | High-confidence AI claims without source verification |
| 4 | Knowledge Laundering | Confidential data leaking through trust chains |
| 5 | Classification Downgrade | Security labels being silently reduced |
| 6 | Stale Claims | Expired or outdated trust scores still in use |
| 7 | Ungrounded AI Claims | AI assertions with no supporting evidence |
| 8 | Trust Degradation Chain | Trust eroding across multi-hop provenance |
| 9 | Excessive AI Concentration | Over-reliance on AI-generated content |
| 10 | Provenance Gap | Missing links in the trust chain |

```python
from akf import run_all_detections
report = run_all_detections(unit)
for finding in report.findings:
    print(f"[{finding.severity}] {finding.detection}: {finding.message}")
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

**Decision:** score ≥ 0.7 → ACCEPT · ≥ 0.4 → LOW · < 0.4 → REJECT

## Framework Integrations

| Package | Status | Description |
|---------|--------|-------------|
| [`mcp-server-akf`](packages/mcp-server-akf/) | ✅ Ready | MCP server — create, validate, scan, trust |
| [`langchain-akf`](packages/langchain-akf/) | ✅ Ready | LangChain callback handler + document loader |
| [`llama-index-akf`](packages/llama-index-akf/) | 🚧 Beta | LlamaIndex node parser + trust filter |
| [`crewai-akf`](packages/crewai-akf/) | 🚧 Beta | CrewAI tool for trust-aware agents |

## Extensions

| Extension | Description |
|-----------|-------------|
| [VS Code](extensions/vscode/) | Syntax highlighting, hover info, validation for `.akf` files |
| [GitHub Action](extensions/github-action/) | CI validation — fail builds on untrusted claims |
| [Google Workspace](extensions/google-workspace/) | Add-on for Docs, Sheets, Slides |
| [Office Add-in](extensions/office-addin/) | Add-in for Word, Excel, PowerPoint |

## For LLMs

Tell your LLM: *"Output in AKF format."*

```
Output knowledge as AKF:
{"v":"1.0","claims":[{"c":"<claim>","t":<0-1>,"src":"<source>","tier":<1-5>,"ai":true}]}
```

LLMs produce valid AKF **95%+ of the time** from a single example. See [LLM-PROMPT.md](spec/LLM-PROMPT.md) for a full system prompt.

## Documentation

| Doc | Description |
|-----|-------------|
| [Full Spec](spec/akf-v1.0-spec.md) | Complete format specification |
| [JSON Schema](spec/akf-v1.0.schema.json) | Machine-readable schema |
| [Producing AKF](spec/PRODUCING-AKF.md) | Quick start for 8 languages |
| [Trust Computation](docs/trust-computation.md) | Scoring algorithm details |
| [LLM Integration](docs/llm-integration.md) | Prompting strategies |
| [EU AI Act](docs/compliance/eu-ai-act-mapping.md) | Compliance mapping |
| [NIST AI RMF](docs/compliance/nist-ai-rmf-mapping.md) | Framework mapping |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and PR process.

## License

MIT — use it everywhere, embed it in everything.
