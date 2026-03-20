# AKF Launch Materials

> **INTERNAL — NOT FOR PUBLIC DISTRIBUTION**
> Copy-paste-ready materials for all launch channels.
> Last updated: 2026-03-15

---

## Positioning

**Primary tagline:** The file format for the AI era

**Narrative arc:** Every technology era creates its own file format. Print
gave us PDF. Photography gave us JPEG. Music gave us MP3. The AI era generates
more content than any era before it — but has no format to carry trust,
provenance, or verification with that content. AKF is that format.

**Secondary descriptors (vary by audience):**
- Developer: "Trust metadata that travels with your files"
- Enterprise: "The trust and provenance standard for AI-generated content"
- AI/ML: "An open format for AI trust, provenance, and verification"

**Key proof points:**
- ~15 tokens of JSON — compact enough for LLMs to read and write
- Embeds into 20+ existing formats (DOCX, PDF, images, HTML, etc.)
- Trust computation with source tiers, temporal decay, AI penalties
- 10 security detection classes
- Compliance mapping (EU AI Act, SOX, NIST AI RMF)
- Dual SDK: Python + TypeScript
- Integrations: LangChain, LlamaIndex, CrewAI, MCP
- **Zero-touch auto-stamping** — background daemon + shell hooks + VS Code extension
- **Smart context detection** — infers git author, download source, AI-generated flag, project classification rules
- **Shell integration** — `eval "$(akf shell-hook)"` intercepts Claude, ChatGPT, Aider, OpenClaw, Ollama and stamps outputs
- **OS-native file monitoring** — kqueue on macOS, polling cross-platform
- **Ambient Trust** — Works with Claude Code, Claude Agent Teams, Cursor, Windsurf, GitHub Copilot, OpenAI Codex, Manus, OpenClaw, M365 Copilot — and any MCP-compatible agent
- **Trust Pipeline** — agent → git commit → CI validation → team review, all with trust metadata

---

## 1. Hacker News — Show HN

### Title

```
Show HN: AKF – The file format for the AI era (trust, provenance, verification)
```

### First Comment (post immediately after submitting)

```
Hey HN — every technology era creates its own file format. Print gave us PDF.
Photography gave us JPEG. The AI era generates more content than ever — reports,
analyses, code, summaries — and none of it carries any record of how trustworthy
it is, where it came from, or whether anyone verified it.

AKF (Agent Knowledge Format) is a file format that solves this. The core is
compact — about 15 tokens of JSON:

    {"v":"1.0","claims":[{"c":"Revenue was $4.2B","t":0.98,"src":"SEC 10-Q"}]}

Every claim carries a trust score, source, and confidence level. The metadata
embeds directly into the files you already use — DOCX (custom XML part), PDF
(metadata stream), HTML (JSON-LD), images (EXIF/XMP), Markdown (frontmatter),
or standalone as .akf files.

The trust model is deliberate. Not all sources are equal:

    effective_trust = confidence × authority_weight × temporal_decay × (1 + penalty)

SEC filing (tier 1) at 0.98 confidence → effective score ~0.98.
AI inference (tier 5) at 0.98 confidence → drops to ~0.29.

There are 10 built-in detection classes — hallucination risk, knowledge
laundering (AI content passed off as human-written), stale claims, trust
degradation chains, etc.

    pip install akf
    akf create --demo
    akf inspect demo.akf
    akf trust demo.akf

The latest version adds zero-touch auto-stamping. Install a background
daemon (`akf install`) or add `eval "$(akf shell-hook)"` to your shell
config, and every file that Claude, ChatGPT, Aider, OpenClaw, or Ollama generates
gets stamped automatically. Smart context detection infers git author,
download source, classification rules, and AI-generated flags without
any manual intervention.

Dual SDK (Python + TypeScript), integrations for LangChain, LlamaIndex,
CrewAI, and an MCP server. Maps to EU AI Act, SOX, NIST AI RMF for compliance.
VS Code extension auto-stamps files edited by Copilot and Cursor.

Source: https://github.com/HMAKT99/AKF
Docs: https://akf.dev
MIT licensed.

Happy to answer questions about the format design or trust model.
```

---

## 2. Reddit Posts

### 2a. r/MachineLearning — [P] tag

**Title:** `[P] AKF — an open file format for AI trust and provenance (~15 tokens of JSON per claim)`

**Body:**

```
AI generates claims. Those claims end up in reports, pipelines, and downstream
models. But there's no standard way to record how confident the model was,
what the source material was, or whether a human verified the output.

AKF (Agent Knowledge Format) is a file format that attaches trust metadata
directly to AI-generated content — confidence scores, source provenance chains,
verification status, and security classifications.

The trust computation uses weighted source tiers:

    effective_trust = confidence × authority_weight × temporal_decay × (1 + penalty)

    Tier 1 (1.00): SEC filings, official records
    Tier 2 (0.85): Analyst reports, peer-reviewed
    Tier 3 (0.70): News, industry reports
    Tier 4 (0.50): Internal estimates, CRM data
    Tier 5 (0.30): AI inference, extrapolations

    Decision: score >= 0.7 → ACCEPT | >= 0.4 → LOW | < 0.4 → REJECT

A claim sourced from an SEC filing at 0.98 confidence keeps that score.
The same confidence from an AI inference drops to ~0.29. Temporal decay
degrades stale claims automatically.

10 detection classes flag issues: hallucination risk, knowledge laundering,
ungrounded AI claims, trust degradation chains, excessive AI concentration,
provenance gaps, and more.

The format is compact (~15 tokens per claim) and embeds into 20+ file formats
natively — no sidecars for DOCX, PDF, HTML, images, Markdown, etc.

Integrations for LangChain (callback handler + doc loader), LlamaIndex
(node parser + trust filter), and CrewAI (trust-aware agent tool).

    pip install akf
    npm install akf-format

Spec & docs: https://akf.dev
Source: https://github.com/HMAKT99/AKF
MIT license.
```

### 2b. r/programming

**Title:** `AKF: a file format for AI-generated content — embeds trust scores and provenance into DOCX, PDF, images, and 20+ formats`

**Body:**

```
Every technology era creates file formats for the content it produces.
Print → PDF. Photography → JPEG. Music → MP3.

AI generates more content than any of them, and it all lives inside existing
formats with zero provenance. No record of which model made it, how confident
it was, or what the source was.

AKF is a file format that fixes this. It embeds trust metadata directly into
the formats you already use:

- DOCX/XLSX/PPTX — OOXML custom XML part
- PDF — metadata stream
- HTML — JSON-LD script tag
- Images — EXIF/XMP metadata
- Markdown — YAML frontmatter
- Standalone — .akf files

The format is compact (~15 tokens of JSON per claim):

    {"v":"1.0","claims":[{"c":"Revenue was $4.2B","t":0.98,"src":"SEC 10-Q"}]}

Python SDK:

    import akf

    akf.stamp("Revenue was $4.2B, up 12% YoY",
              confidence=0.98, source="SEC 10-Q",
              agent="claude-code", model="claude-sonnet-4-20250514")

    akf.embed("report.docx", claims=[...], classification="confidential")

CLI:

    pip install akf
    akf create --demo && akf inspect demo.akf && akf trust demo.akf

Dual SDK — Python (`pip install akf`) and TypeScript (`npm install akf-format`).
Open spec, JSON Schema, MIT license.

GitHub: https://github.com/HMAKT99/AKF
Docs: https://akf.dev
```

### 2c. r/LocalLLaMA

**Title:** `AKF — a file format to track what your local models generate (trust scores, provenance, model/source tagging)`

**Body:**

```
If you're running local models, you know the problem: outputs scattered across
files with no record of which model generated what, how confident it was,
or what source material it was working from. Two months later you find a
summary and have no idea if it came from Llama 3, Mistral, or something
you fine-tuned.

AKF (Agent Knowledge Format) is a lightweight file format that stamps trust
metadata onto AI outputs. It auto-tracks the model and provider from your
SDK calls.

    import akf

    akf.stamp("Summary of quarterly earnings",
              confidence=0.85, source="company_report.pdf",
              model="llama-3-70b", agent="my-local-pipeline")

The metadata is ~15 tokens of JSON per claim — it's not bloating your files.
It embeds directly into DOCX, PDF, Markdown, images, or any format you're
generating into.

The CLI gives you quick inspection:

    akf inspect report.akf     # See what's in the file
    akf trust report.akf       # Compute trust scores
    akf scan ./outputs/ --recursive  # Scan a directory

Even better — you can make it fully automatic:

    # Add to ~/.zshrc — auto-stamps files from AI CLI tools
    eval "$(akf shell-hook)"

    # Or install a background daemon
    akf install

It intercepts claude, chatgpt, openclaw, ollama, aider, and other AI tools, then
stamps any files they create or modify. Smart context detection infers
the model, git author, and project classification rules automatically.

There's also an MCP server if you want agents to create and validate trust
metadata programmatically, and integrations for LangChain, LlamaIndex, and
CrewAI.

    pip install akf
    npm install akf-format

GitHub: https://github.com/HMAKT99/AKF
Docs: https://akf.dev
```

---

## 3. Twitter/X Thread

```
1/ Every technology era creates its file format.

Print → PDF
Photos → JPEG
Music → MP3

AI generates more content than all of them. Its file format? Doesn't exist.

Until now. Meet AKF.

pip install akf

🧵

2/ AKF stamps trust metadata onto AI-generated content.

Every claim carries: who made it, how confident they were, what the source was,
and whether anyone verified it.

~15 tokens of JSON. Embeds directly into the file.

{"v":"1.0","claims":[{"c":"Revenue $4.2B","t":0.98,"src":"SEC 10-Q"}]}

3/ It works inside the files you already use.

DOCX, PDF, Excel, PowerPoint, images, HTML, Markdown — 20+ formats.

No sidecars. No databases. The trust metadata travels with the file.

akf embed report.docx --claim "Revenue $4.2B" --trust 0.98

4/ Not all sources are equal. AKF's trust model knows this.

SEC filing at 0.98 confidence → score stays ~0.98
AI inference at 0.98 confidence → score drops to ~0.29

10 detection classes catch hallucination risk, knowledge laundering,
stale claims, and more.

5/ Zero-touch mode. No manual stamping needed.

Add one line to your shell config:

eval "$(akf shell-hook)"

Now every file Claude, ChatGPT, Aider, OpenClaw, or Ollama touches gets stamped
automatically. Smart context detection infers git author, download source,
and project classification rules.

akf install  # Or run a background daemon

6/ Maps directly to compliance frameworks:

• EU AI Act (transparency, human oversight)
• SOX 302/404 (internal controls)
• NIST AI RMF (risk management)

akf audit report.akf --regulation eu_ai_act

7/ Open source. MIT license. Python + TypeScript SDKs.

Integrations for LangChain, LlamaIndex, CrewAI, and MCP.
VS Code extension for Copilot/Cursor auto-stamping.

pip install akf
npm install akf-format

GitHub: github.com/HMAKT99/AKF
Docs: akf.dev

The AI era finally has its file format.
```

---

## 4. LinkedIn Post

```
Every technology era creates its own file format.

Print gave us PDF. Photography gave us JPEG. Music gave us MP3.

The AI era generates more content than any before it — reports, analyses,
summaries, code — yet none of it carries any record of how trustworthy it is,
where it came from, or whether a human verified it.

We built AKF (Agent Knowledge Format) to fill that gap.

AKF is an open file format that attaches trust scores, source provenance,
and security classifications to AI-generated content. It embeds directly
into the file formats organizations already use — Word, Excel, PowerPoint,
PDF, and 20+ others.

For technical teams: pip install akf and you're up in 30 seconds. Add
eval "$(akf shell-hook)" to your shell config and every file Claude,
ChatGPT, OpenClaw, or Copilot touches gets stamped automatically — zero manual work.

For compliance teams: AKF maps directly to EU AI Act, SOX, and NIST AI RMF
requirements. One command gives you an actionable compliance report.

For leadership: 10 built-in detection classes catch hallucination risk,
knowledge laundering, and trust degradation before they reach stakeholders.
Smart context detection automatically identifies AI-generated content,
even without explicit stamping.

The trust model is transparent — every claim carries a confidence score,
source tier, temporal decay factor, and verification status. No black boxes.

Open source (MIT), dual-SDK (Python + TypeScript), with integrations for
LangChain, LlamaIndex, CrewAI, and MCP.

The AI era finally has its file format.

→ github.com/HMAKT99/AKF
→ akf.dev

#AIGovernance #OpenSource #TrustInAI #AICompliance #LLM
```

---

## 5. Product Hunt

### Tagline

```
The file format for the AI era — trust, provenance, and verification for every AI output
```

### Description

```
AKF (Agent Knowledge Format) is an open file format that stamps trust scores,
source provenance, and security classifications onto AI-generated content.

THE PROBLEM
AI generates content — reports, analyses, code, summaries. Someone puts it in
a document. Six months later, nobody knows which claims were AI-generated,
what the sources were, how confident the model was, or whether anyone verified it.

Every technology era creates its own file format. Print → PDF. Photos → JPEG.
The AI era has been missing one. Until now.

THE FORMAT
AKF is compact — about 15 tokens of JSON per claim:

{"v":"1.0","claims":[{"c":"Revenue $4.2B","t":0.98,"src":"SEC 10-Q","tier":1}]}

Trust score. Source. Confidence. Verification status. Embedded directly in the file.

WORKS WITH YOUR FILES
AKF embeds natively into DOCX, PDF, Excel, PowerPoint, images, HTML, Markdown,
and 20+ other formats. No sidecars. No external databases.

TRUST MODEL
Not all sources are equal. AKF weights SEC filings (tier 1) differently than
AI inferences (tier 5). 10 detection classes catch hallucination risk,
knowledge laundering, stale claims, and more.

COMPLIANCE
Maps to EU AI Act, SOX 302/404, and NIST AI RMF.

ZERO-TOUCH MODE
One line in your shell config and every AI-generated file gets stamped
automatically. Smart context detection infers git author, download source,
and project classification rules.

    eval "$(akf shell-hook)"    # Intercepts claude, chatgpt, openclaw, aider, ollama
    akf install                 # Background daemon for ~/Downloads, ~/Desktop

INSTALL
pip install akf          # Python
npm install akf-format   # TypeScript

INTEGRATIONS
LangChain, LlamaIndex, CrewAI, MCP server, VS Code AI monitor, GitHub Action,
Office Add-in, Google Workspace Add-on.

Open source. MIT license.
```

### Maker Comment

```
Hey Product Hunt!

I built AKF because I noticed something obvious: every technology era
creates a file format for the content it produces, but the AI era doesn't
have one.

AI generates reports, analyses, summaries — and all of it sits inside Word
docs and PDFs with zero record of how trustworthy it is. The "aha" moment was
embedding AKF metadata into a Word document and seeing trust scores show up
in the document properties panel. That's when I knew this could work — the
trust metadata lives inside the formats people already use.

The trust model is deliberate: a claim sourced from an SEC filing (tier 1)
keeps its high confidence, but an AI inference (tier 5) gets penalized hard.
You can filter, route, and flag content based on actual trust levels — not
just whether it was AI-generated.

The spec is open and I want this to become a standard any tool can adopt.

Try it: pip install akf && akf create --demo && akf inspect demo.akf
```

---

## 6. Blog Post (dev.to / Medium)

### Title

```
The File Format for the AI Era: Why AI-Generated Content Needs Its Own Standard
```

### Tags (dev.to)

```
ai, opensource, python, typescript
```

### Body

```markdown
Every technology era creates its own file format.

Print gave us PDF — a portable way to preserve documents exactly as intended.
Photography gave us JPEG — a compact way to store and share images. Music gave
us MP3 — a way to compress audio without losing what matters.

These formats didn't just store data. They carried metadata. A JPEG knows what
camera took it, when, and where. A PDF knows who authored it and when it was
modified. This metadata is invisible to most users but essential for anyone who
needs to verify where content came from.

The AI era generates more content than any before it. Reports, analyses, code,
summaries, translations — all produced by LLMs at unprecedented speed. And none
of it carries any metadata about how trustworthy it is.

An LLM generates a claim like "Revenue was $4.2B, up 12% YoY." Someone pastes
it into a report. That report gets shared, cited, and built upon. Six months
later, nobody knows:

- Was this AI-generated or human-written?
- How confident was the model?
- What was the source material?
- Has anyone verified this?

The AI era is missing its file format. AKF is that format.

## What is AKF?

AKF (Agent Knowledge Format) is an open file format that stamps trust metadata
onto AI-generated content. Every claim carries a confidence score, source
provenance, and verification status. The format is compact — about 15 tokens
of JSON:

```json
{
  "v": "1.0",
  "claims": [
    {"c": "Revenue was $4.2B", "t": 0.98, "src": "SEC 10-Q", "tier": 1},
    {"c": "H2 will accelerate", "t": 0.63, "tier": 5, "ai": true}
  ]
}
```

The first claim cites an SEC filing (tier 1) with 0.98 confidence. The second
is an AI inference (tier 5) with lower confidence. Anyone reading this file
immediately knows what to trust and what to question.

## It lives inside your files

AKF doesn't force you to adopt a new file format for everything. It embeds
directly into the formats you already use:

- **DOCX/XLSX/PPTX** — OOXML custom XML part
- **PDF** — metadata stream
- **HTML** — JSON-LD script tag
- **Markdown** — YAML frontmatter
- **Images** — EXIF/XMP metadata
- **Standalone** — native `.akf` files

One API handles all of them:

```python
import akf

akf.embed("report.docx", claims=[...], classification="confidential")
meta = akf.extract("report.docx")
```

This is what makes AKF practical. You don't need to change your workflow. The
trust metadata rides along inside the files you're already producing.

## The trust model

Not all sources are equal. A claim from an SEC filing is fundamentally
different from an AI extrapolation, even if the model says "confidence: 0.98"
for both. AKF's trust formula reflects this:

```
effective_trust = confidence × authority_weight × temporal_decay × (1 + penalty)
```

Source tiers range from 1 (SEC filings, official records) to 5 (AI inference,
extrapolations). A claim from an SEC filing at 0.98 confidence stays at ~0.98.
The same confidence from an AI inference drops to ~0.29.

This isn't arbitrary — it matches how analysts actually assess information.
Primary sources deserve more weight than AI extrapolations.

## 10 detection classes

AKF includes built-in security detections that catch problems before they spread:

```python
from akf import run_all_detections

report = run_all_detections(unit)
for finding in report.findings:
    print(f"[{finding.severity}] {finding.detection}: {finding.message}")
```

The detections cover hallucination risk, knowledge laundering (AI content passed
off as human-written), stale claims, trust degradation chains, ungrounded AI
claims, and more.

## Built for AI agents

AKF is designed agent-first. One-line APIs for stamping and streaming:

```python
akf.stamp("Fixed auth bypass", kind="code_change",
          evidence=["42/42 tests passed", "mypy: 0 errors"],
          agent="claude-code", model="claude-sonnet-4-20250514")

with akf.stream("output.md", model="gpt-4o") as s:
    for chunk in llm_response:
        s.write(chunk)
```

There are integrations for LangChain (callback handler + doc loader),
LlamaIndex (node parser + trust filter), CrewAI (trust-aware agent tool),
and an MCP server for any agent that speaks the protocol.

## Zero-touch mode

Manual stamping is fine for pipelines, but what about the files you create
interactively — chatting with Claude, running Aider, using Copilot in VS Code?

AKF has three layers of automatic stamping:

**Shell hook** — add one line to your shell config:

```bash
eval "$(akf shell-hook)"
```

Now whenever you run `claude`, `chatgpt`, `aider`, `openclaw`, `ollama`, or any other AI
CLI tool, AKF snapshots the files before and stamps any new or modified files
after. Smart context detection automatically infers git author, download
source, project classification rules, and AI-generated flags.

**Background daemon** — `akf install` runs a file watcher that monitors
`~/Downloads`, `~/Desktop`, and `~/Documents`. New files get stamped with
context-aware metadata automatically.

**VS Code extension** — detects large AI-style insertions from Copilot, Cursor,
and other AI coding tools, and stamps on save.

The goal: if AI touched it, AKF knows about it. No manual intervention.

## Compliance built in

AKF maps directly to regulatory frameworks:

| Regulation | Requirement | AKF Field |
|------------|-------------|-----------|
| EU AI Act Art. 13 | Transparency | `ai`, `src`, `provenance` |
| EU AI Act Art. 14 | Human oversight | `ver`, `ver_by` |
| SOX 302/404 | Internal controls | `classification`, `tier`, audit trail |
| NIST AI RMF | Risk management | `risk`, `t`, `security` |

Run `akf audit report.akf --regulation eu_ai_act` for an actionable compliance
report.

## Get started

```bash
pip install akf          # Python
npm install akf-format   # TypeScript / Node.js

akf create --demo
akf inspect demo.akf
akf trust demo.akf
```

The format spec, JSON schema, and SDKs are all open source under MIT.

- **GitHub:** [github.com/HMAKT99/AKF](https://github.com/HMAKT99/AKF)
- **Docs:** [akf.dev](https://akf.dev)

Every era gets its file format. The AI era finally has one.
```

---

## 7. Awesome-List PR Descriptions

### awesome-ai / awesome-artificial-intelligence

```markdown
## [AKF — Agent Knowledge Format](https://github.com/HMAKT99/AKF)

Open file format for AI trust and provenance. Stamps confidence scores, source
provenance chains, and security classifications onto AI-generated content.
Embeds into 20+ formats (DOCX, PDF, images, HTML, etc.). Python and TypeScript
SDKs. Compliance mapping for EU AI Act, SOX, and NIST AI RMF. MIT licensed.
```

### awesome-llm / awesome-llm-tools

```markdown
## [AKF — Agent Knowledge Format](https://github.com/HMAKT99/AKF)

Lightweight file format (~15 tokens JSON) for stamping trust scores and
provenance onto LLM outputs. Auto-tracks model/provider, embeds into DOCX/PDF/
images natively. Integrations for LangChain, LlamaIndex, CrewAI, and MCP.
10 security detection classes (hallucination risk, knowledge laundering, etc.).
Python (`pip install akf`) + TypeScript (`npm install akf-format`). MIT licensed.
```

---

## 8. GitHub Housekeeping

### Repo Description

```
The file format for the AI era — trust scores, source provenance, security classification. Embeds into DOCX, PDF, images, and 20+ formats. Python + TypeScript SDKs.
```

### Topics

```
ai, trust, metadata, governance, llm, file-format, provenance, compliance,
ai-safety, python, typescript, open-standard
```

### Good First Issues

**Issue 1: Add AKF embedding support for EPUB files**

```markdown
**Title:** Add EPUB embedding support

**Labels:** good first issue, enhancement

**Body:**
AKF currently embeds into DOCX, PDF, HTML, images, and other formats.
EPUB is a natural fit since it's essentially a ZIP of HTML/XML files.

**What to do:**
- Add an EPUB handler to `python/akf/universal.py`
- Embed AKF metadata as an OPF `<meta>` element or as a JSON-LD script in
  the content documents
- Add extract support to read it back
- Add tests

**Relevant files:**
- `python/akf/universal.py` — format embedding/extraction logic
- `python/tests/test_universal.py` — tests

**Helpful context:**
- Look at the HTML embedding handler for reference (JSON-LD approach)
- EPUB 3 supports custom metadata in the OPF package document
```

**Issue 2: Add `--format json` flag to CLI trust command**

```markdown
**Title:** Add JSON output format to `akf trust` CLI command

**Labels:** good first issue, enhancement

**Body:**
The `akf trust` command currently outputs human-readable text. Adding a
`--format json` flag would make it easy to pipe trust scores into other tools.

**What to do:**
- Add a `--format` option (values: `text`, `json`) to the `trust` CLI command
- Default to `text` (current behavior)
- JSON output should include all computed trust fields (effective_trust,
  confidence, authority_weight, temporal_decay, decision)
- Add tests

**Relevant files:**
- `python/akf/cli.py` — CLI definitions
- `python/tests/test_cli.py` — CLI tests
```

**Issue 3: Add TypeScript examples to README**

```markdown
**Title:** Add TypeScript usage examples to README

**Labels:** good first issue, documentation

**Body:**
The root README shows Python examples but no TypeScript. Since we ship a
TypeScript SDK (`npm install akf-format`), we should show equivalent examples.

**What to do:**
- Add a "TypeScript" tab/section alongside the Python quickstart
- Show creating a claim, normalizing between compact/descriptive, and basic
  validation
- Keep it concise (3-4 code blocks max)

**Relevant files:**
- `README.md`
- `typescript/src/` — SDK source for reference
- `typescript/README.md` — existing TS-specific docs
```

---

## 9. Discord/Community Posts

### CrewAI Discord

```
Hey everyone — I built an AKF integration for CrewAI that adds trust metadata
to your agent outputs.

AKF (Agent Knowledge Format) is a file format for AI-generated content. It
stamps confidence scores, source provenance, and security classifications
onto claims — so downstream agents and humans know what to trust.

Example: your research agent pulls data from multiple sources. AKF records
the source tier and confidence for each claim. Downstream agents can filter
by trust score — only use claims above 0.7, flag anything from tier 5
sources, etc.

Install: pip install akf
CrewAI integration: pip install ./packages/crewai-akf (from repo)
Docs: https://akf.dev
GitHub: https://github.com/HMAKT99/AKF

Happy to answer questions or help with integration.
```

### LangChain Discord

```
Built an AKF integration for LangChain — callback handler + document loader
for trust metadata.

AKF (Agent Knowledge Format) is a file format that attaches trust scores,
provenance chains, and security classifications to AI outputs. It embeds
into DOCX, PDF, images, and 20+ other formats natively.

The LangChain integration:
- Callback handler: auto-stamps trust metadata on chain outputs
- Document loader: loads .akf files as LangChain Documents with trust in metadata

Install the core: pip install akf
LangChain integration: pip install ./packages/langchain-akf (from repo)

GitHub: https://github.com/HMAKT99/AKF
Docs: https://akf.dev
```

### LlamaIndex Discord

```
Sharing an AKF integration for LlamaIndex — node parser + trust filter for
AI trust metadata.

AKF (Agent Knowledge Format) is a file format that stamps confidence scores
and source provenance onto AI content (~15 tokens of JSON per claim).

The LlamaIndex integration:
- Node parser: extracts AKF claims as nodes with trust metadata
- Trust filter: filters nodes by trust score threshold before retrieval

Use case: your RAG pipeline pulls from mixed sources. AKF lets you weight
results by source quality — tier 1 (official records) ranks higher than
tier 5 (AI inference).

pip install akf
LlamaIndex integration: pip install ./packages/llama-index-akf (from repo)

GitHub: https://github.com/HMAKT99/AKF
Docs: https://akf.dev
```

---

## 10. Dev.to Tags & Metadata

```yaml
title: "The File Format for the AI Era: Why AI-Generated Content Needs Its Own Standard"
published: true
tags: ai, opensource, python, typescript
canonical_url: https://akf.dev/blog/file-format-for-ai
cover_image: # Use akf.dev og:image or a custom banner
series: # leave empty unless doing a series
```

---

## Quick Reference — Key URLs & Install Commands

| Item | Value |
|------|-------|
| GitHub | `https://github.com/HMAKT99/AKF` |
| Website | `https://akf.dev` |
| Python install | `pip install akf` |
| TypeScript install | `npm install akf-format` |
| PyPI | `https://pypi.org/project/akf/` |
| npm | `https://www.npmjs.com/package/akf-format` |
| License | MIT |
| Primary tagline | "The file format for the AI era" |
| Closing line | "Every era gets its file format. The AI era finally has one." |
