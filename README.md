---
_akf: '{"v":"1.0","claims":[{"c":"Trust metadata for README.md","t":0.7,"id":"1979cbeb","src":"unspecified","tier":5,"ver":false,"ai":true,"evidence":[{"type":"other","detail":"updated certify and github action references","at":"2026-03-18T04:21:48.869226+00:00"}]}],"id":"akf-c33254656fc5","agent":"claude-code","at":"2026-03-18T04:21:48.870623+00:00","label":"public","inherit":true,"ext":false,"sv":"1.1"}'
---
<p align="center">
  <img src="https://img.shields.io/badge/format-.akf-blue?style=for-the-badge" alt="AKF Format" />
</p>

<p align="center">
  <a href="https://github.com/HMAKT99/AKF/stargazers"><img src="https://img.shields.io/github/stars/HMAKT99/AKF?style=flat-square&color=yellow" alt="Stars" /></a>
  <a href="https://www.npmjs.com/package/akf-format"><img src="https://img.shields.io/npm/v/akf-format?style=flat-square&label=npm" /></a>
  <a href="https://www.npmjs.com/package/akf-format"><img src="https://img.shields.io/npm/dw/akf-format?style=flat-square&label=npm%20downloads" /></a>
  <a href="https://github.com/HMAKT99/AKF/actions"><img src="https://img.shields.io/github/actions/workflow/status/HMAKT99/AKF/ci.yml?style=flat-square&label=CI" /></a>
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
  <a href="https://akf.dev"><img src="https://img.shields.io/badge/docs-akf.dev-blue?style=flat-square" /></a>
</p>

<h1 align="center">AKF — The AI Native File Format</h1>

<p align="center">
  <strong>Trust scores · Source provenance · Security classification · Compliance readiness</strong><br/>
  Embeds natively into DOCX, PDF, XLSX, images, code, and all major formats.<br/>
  Think EXIF for AI — ~15 tokens of JSON that travel with your files.
</p>

<p align="center">
  <img src="https://vhs.charm.sh/vhs-3OOIFnSZOds1SrvHNxwNY.gif" alt="AKF Demo — stamp, inspect, audit in 10 seconds" width="700" />
</p>

<p align="center">
  <a href="https://github.com/HMAKT99/AKF">⭐ Star on GitHub</a> ·
  <a href="https://akf.dev">Try Online</a> ·
  <a href="https://huggingface.co/spaces/HANAKT19/akf">HuggingFace Demo</a>
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

## The Problem

AI generates reports, code, docs, images — and **none of it carries provenance.** Your team opens a file with no idea: Who made it? AI or human? Can we trust it? Is it compliant?

**EU AI Act Article 50 takes effect August 2, 2026.** After that, AI-generated content must carry transparency metadata. Penalties: up to EUR 35M / 7% of global turnover.

## The Solution

AKF is the **AI native file format** — ~15 tokens of JSON that embed into any file:

| What | How |
|------|-----|
| **Trust score** | 0–1 confidence based on source tier |
| **Source provenance** | SEC filing → analyst → AI agent chain |
| **Compliance** | One command: `akf audit file --regulation eu_ai_act` |

```
AI generates content → AKF stamps trust metadata → Anyone can verify it
```

### vs Alternatives

| | AKF | C2PA | Watermarking | Manual tracking |
|---|:---:|:---:|:---:|:---:|
| Works on documents/code | ✅ | ❌ (media only) | ❌ | ⚠️ |
| No Certificate Authority needed | ✅ | ❌ | ✅ | ✅ |
| Trust scores | ✅ | ❌ | ❌ | ❌ |
| Source provenance chain | ✅ | ✅ | ❌ | ⚠️ |
| Compliance auditing | ✅ | ❌ | ❌ | ❌ |
| ~15 tokens (LLM-friendly) | ✅ | ❌ | N/A | N/A |
| 20+ file formats | ✅ | ⚠️ (media) | ⚠️ (text) | ❌ |
| Free & open source | ✅ | ⚠️ | Varies | ✅ |

## Quickstart

```bash
pip install akf    # Python
npm install akf-format    # TypeScript / Node.js

akf doctor         # Check your install — detects PATH issues and guides setup
```

> **`akf` command not found?** Run `akf doctor` to auto-detect your setup, or use `python3 -m akf` (always works).
> - Install with pipx: `pipx install akf` (recommended — auto-handles PATH)
> - **Windows:** use `python3 -m akf` or install via `pipx`

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
```

## For AI Agents

AKF is designed **agent-first**. One-line APIs for stamping, streaming, and auditing.

```python
import akf

# Stamp with evidence (auto-detected: test_pass, type_check, etc.)
akf.stamp("Fixed auth bypass", kind="code_change",
          evidence=["42/42 tests passed", "mypy: 0 errors"],
          agent="claude-code", model="claude-sonnet-4-20250514")

# Stream trust metadata in real-time
with akf.stream("output.md", model="gpt-4o") as s:
    for chunk in llm_response:
        s.write(chunk)

# Trust-annotated git commits (uses git notes)
akf.stamp_commit(content="Refactored auth module", kind="code_change",
                 evidence=["all tests pass"], agent="claude-code")
print(akf.trust_log(n=10))  # + ACCEPT  ~ LOW  - REJECT  ? none
```

## Multi-Agent Teams

AKF supports multi-agent orchestration — Claude Agent Teams, Copilot Cowork, Codex multi-agent, and any A2A-compatible platform.

```python
import akf

# Agent-to-agent delegation with trust ceiling
policy = akf.DelegationPolicy(
    delegator="lead-agent", delegate="research-bot",
    trust_ceiling=0.7, allowed_actions=["search", "summarize"]
)
result = akf.delegate(parent_unit, policy)

# Multi-agent streaming session
with akf.TeamStream(["research", "writer", "reviewer"]) as ts:
    ts.write("research", "Found 3 sources", confidence=0.8)
    ts.write("writer", "Drafted summary", confidence=0.75)
    ts.write("reviewer", "Approved with edits", confidence=0.9)
    scores = ts.aggregate()  # per-agent + team trust

# Cross-platform agent identity
card = akf.create_agent_card(name="Research Bot", platform="claude-code",
                             capabilities=["search", "summarize"])
akf.verify_agent_card(card)  # SHA-256 hash verification

# Team certification (per-agent breakdown)
report = akf.certify_team("src/", min_trust=0.7)
# report.all_agents_certified — each agent must individually pass
```

**CLI:**
```bash
akf agent create --name "Bot" --platform claude-code --capabilities search,summarize
akf agent list
akf agent verify <id>
akf agent export-a2a <id> --output card.json   # A2A protocol bridge
akf agent import-a2a card.json
akf certify src/ --team                         # Per-agent breakdown
```

## MCP Server

AKF ships an [MCP](https://modelcontextprotocol.io) server so any AI agent can create, validate, scan, and audit trust metadata.

```bash
# Install from the repo
pip install ./packages/mcp-server-akf
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

**9 MCP tools:** `create_claim` · `validate_file` · `scan_file` · `trust_score` · `stamp_file` · `audit_file` · `embed_file` · `extract_file` · `detect_threats`

## Ambient Trust

AKF works where AI agents work. Drop a config file, and every AI-generated file carries trust metadata automatically.

| Agent | How it works |
|-------|-------------|
| **Claude Code** | Reads `CLAUDE.md` — stamps every file it creates with confidence and evidence |
| **Cursor** | Reads `.cursorrules` — stamps AI edits before you review |
| **Windsurf** | Reads `.windsurfrules` — stamps AI edits with trust metadata |
| **GitHub Copilot** | Reads `.github/copilot-instructions.md` (native) + shell hook for CLI |
| **OpenAI Codex** | Reads `AGENTS.md` — stamps files in cloud sandbox and local |
| **Manus / Other Agents** | MCP server + shell hook — works with any agent that supports MCP or CLI |
| **Any MCP agent** | 9 MCP tools — stamp, audit, embed, extract, detect, validate, scan, trust, create |
| **Any CLI tool** | `eval "$(akf shell-hook)"` — intercepts `claude`, `chatgpt`, `aider`, `openclaw`, `ollama`, `manus` |

**The trust pipeline:**
```
Agent writes code → Git commit stamped → CI runs akf certify → Team reviews with context
```

Set up in 60 seconds:
```bash
# 1. Agent stamps its own work (already in this repo)
cat CLAUDE.md        # or .cursorrules / .windsurfrules / AGENTS.md / .github/copilot-instructions.md

# 2. Git hooks stamp every commit
akf init --git-hooks

# 3. CI certifies trust on every PR
#    uses: HMAKT99/AKF/extensions/github-action@main

# 4. Shell hook intercepts AI CLI tools
eval "$(akf shell-hook)"
```

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
| `delegate` | Agent-to-agent trust delegation |
| `team` | Multi-agent streaming sessions |

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
| `.mp4` `.mov` `.webm` `.mkv` | Sidecar `.akf.json` companion |
| `.mp3` `.wav` `.flac` `.ogg` | Sidecar `.akf.json` companion |
| Everything else | Sidecar `.akf.json` companion |

```python
# One API for all formats
akf.embed("report.docx", claims=[...], classification="confidential")
meta = akf.extract("report.docx")
akf.scan("report.docx")
```

## Zero-Touch Auto-Stamping

AKF can automatically stamp every file AI touches — no manual intervention needed.

```bash
# Install the background watcher
akf install

# Or run in foreground
akf watch ~/Downloads ~/Desktop ~/Documents
```

The background watcher monitors directories for new and modified files and stamps them with trust metadata. **Smart context detection** automatically infers:

- **Git author** — from `git log` history
- **Download source** — from macOS extended attributes
- **Classification** — from project `.akf/config.json` rules
- **AI-generated flag** — from LLM tracking timestamps + content heuristics
- **Confidence score** — dynamically adjusted based on available evidence

### Shell Hook (intercept AI CLI tools)

```bash
# Add to ~/.zshrc or ~/.bashrc
eval "$(akf shell-hook)"
```

Automatically detects when you run `claude`, `chatgpt`, `aider`, `openclaw`, `ollama`, or other AI CLI tools, and stamps any files they create or modify. Also pre-stamps files before upload to content platforms (`gws`, `box`, `m365`, `dbxcli`, `rclone`) so trust metadata travels with the file. Use `--no-upload-hooks` to disable.

### Project Rules

Create `.akf/config.json` in your project root:

```json
{
  "rules": [
    {"pattern": "*/finance/*", "classification": "confidential", "tier": 2},
    {"pattern": "*/public/*", "classification": "public", "tier": 3}
  ]
}
```

Files matching these patterns are automatically classified when stamped.

## CLI

```bash
# ── Quick start ──
akf                          # Welcome + quick start
akf quickstart               # Interactive demo
akf doctor                   # Check installation health

# ── Stamp & create ──
akf create report.akf \
  --claim "Revenue $4.2B" --trust 0.98 --src "SEC 10-Q" \
  --by sarah@acme.com --label confidential

# ── Validate & inspect ──
akf validate report.akf
akf inspect report.akf
akf trust report.akf

# ── Certify (aggregate pass/fail gate) ──
akf certify report.akf                        # Trust + detection + compliance
akf certify src/ --min-trust 0.8              # Custom threshold
akf certify . --evidence-file results.xml     # Attach test evidence
akf certify . --format json --fail-on-untrusted  # CI-friendly output
akf certify src/ --team                       # Per-agent trust breakdown

# ── Compliance ──
akf audit report.akf                          # Compliance readiness check
akf audit report.akf --regulation eu_ai_act   # EU AI Act
akf audit report.akf --trail                  # Audit trail

# ── Universal format commands ──
akf embed report.docx --classification confidential \
  --claim "Revenue $4.2B" --trust 0.98
akf extract report.docx
akf scan report.docx
akf scan ./docs/ --recursive

# ── Auto-stamping ──
akf install                                   # Install background watcher
akf watch ~/Downloads ~/Documents             # Watch directories
akf shell-hook                                # Print shell hook code
akf shell-hook --no-upload-hooks              # Without content platform hooks
akf uploads                                   # View upload stamp log

# ── Git integration ──
akf stamp <file> --agent claude-code --evidence "tests pass"

# ── Agent identity & teams ──
akf agent create --name "Bot" --platform claude-code
akf agent list
akf agent verify <agent_id>
akf agent export-a2a <id> --output card.json  # A2A protocol bridge
akf agent import-a2a card.json

# ── Knowledge Base ──
akf kb stats ./kb
akf kb query ./kb --topic finance
```

## Security Detections

10 built-in detection classes: AI content without review, trust below threshold, hallucination risk, knowledge laundering, classification downgrade, stale claims, ungrounded AI claims, trust degradation chain, excessive AI concentration, provenance gap.

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

**Delegation ceiling:** When an agent delegates to another, the delegate's output trust is capped at `min(score, delegation_ceiling)`. This prevents trust inflation in multi-agent chains.

## Integrations & Extensions

**Framework integrations** (install from repo via `pip install ./packages/<name>`):

| Package | Description |
|---------|-------------|
| [`mcp-server-akf`](packages/mcp-server-akf/) | MCP server — create, validate, scan, trust |
| [`langchain-akf`](packages/langchain-akf/) | LangChain callback handler + document loader (experimental) |
| [`llama-index-akf`](packages/llama-index-akf/) | LlamaIndex node parser + trust filter (experimental) |
| [`crewai-akf`](packages/crewai-akf/) | CrewAI tool for trust-aware agents (experimental) |

**Editor & CI extensions** (source in repo):

| Extension | Description |
|-----------|-------------|
| [VS Code](extensions/vscode/) | Syntax highlighting, hover info, validation for `.akf` files |
| [VS Code AI Monitor](editors/vscode/) | Auto-stamp files edited by Copilot, Cursor, and other AI tools |
| [GitHub Action](extensions/github-action/) | CI trust gate — runs `akf certify` on PRs with optional PR comments |
| [Google Workspace](extensions/google-workspace/) | Add-on for Docs, Sheets, Slides (preview) |
| [Office Add-in](extensions/office-addin/) | Add-in for Word, Excel, PowerPoint (preview) |

## For LLMs

Prompt with one example and LLMs produce valid AKF **95%+ of the time**:

```
Output knowledge as AKF:
{"v":"1.0","claims":[{"c":"<claim>","t":<0-1>,"src":"<source>","tier":<1-5>,"ai":true}]}
```

See [LLM-PROMPT.md](spec/LLM-PROMPT.md) for a full system prompt.

## Documentation

| Doc | Description |
|-----|-------------|
| [Full Spec](spec/akf-v1.0-spec.md) | Complete format specification |
| [JSON Schema](spec/akf-v1.1.schema.json) | Machine-readable schema |
| [Producing AKF](spec/PRODUCING-AKF.md) | Quick start for 8 languages |
| [Trust Computation](docs/trust-computation.md) | Scoring algorithm details |
| [LLM Integration](docs/llm-integration.md) | Prompting strategies |
| [EU AI Act](docs/compliance/eu-ai-act-mapping.md) | Compliance mapping |
| [NIST AI RMF](docs/compliance/nist-ai-rmf-mapping.md) | Framework mapping |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing, and PR process.

## Free and Open — Forever

AKF is free and open source under the MIT license. The format specification will always be free. No feature will ever be gated behind a paid tier. AKF is a standard, and standards must be free to be universal.

## License

MIT — use it everywhere, embed it in everything.
