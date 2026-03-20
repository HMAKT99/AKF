# AKF Launch Materials

> **INTERNAL — NOT FOR PUBLIC DISTRIBUTION**
> Copy-paste-ready materials for all launch channels.
> Last updated: 2026-03-20

---

## Positioning

**Primary tagline:** The file format for the AI era

**Narrative arc:** Every technology era creates its own file format. Print
gave us PDF. Photography gave us JPEG. Music gave us MP3. The AI era generates
more content than any era before it — but has no format to carry trust,
provenance, or verification with that content. AKF is that format.

**Urgency tagline:** EU AI Act Article 50 takes effect August 2, 2026 — every AI-generated document must carry transparency metadata. The clock is ticking.

**Secondary descriptors (vary by audience):**
- Developer: "Trust metadata that travels with your files"
- Enterprise: "The trust and provenance standard for AI-generated content"
- AI/ML: "An open format for AI trust, provenance, and verification"
- Compliance: "Article 50 compliance in one line of code"

**Key proof points:**
- ~15 tokens of JSON — compact enough for LLMs to read and write
- Embeds into 20+ existing formats (DOCX, PDF, images, HTML, etc.)
- Trust computation with source tiers, temporal decay, AI penalties
- 10 security detection classes
- Compliance mapping (EU AI Act Art. 50, Colorado SB 205, SOX, DORA, NIST AI RMF, ISO 42001)
- Dual SDK: Python + TypeScript
- Integrations: LangChain, LlamaIndex, CrewAI, MCP
- **Zero-touch auto-stamping** — background daemon + shell hooks + VS Code extension
- **Smart context detection** — infers git author, download source, AI-generated flag, project classification rules
- **Shell integration** — `eval "$(akf shell-hook)"` intercepts Claude, ChatGPT, Aider, OpenClaw, Ollama and stamps outputs
- **OS-native file monitoring** — kqueue on macOS, polling cross-platform
- **Ambient Trust** — Works with Claude Code, Claude Agent Teams, Cursor, Windsurf, GitHub Copilot, OpenAI Codex, Manus, OpenClaw, M365 Copilot — and any MCP-compatible agent
- **Trust Pipeline** — agent → git commit → CI validation → team review, all with trust metadata
- **Pre-upload stamping** — `gws upload`, `box files:upload`, `m365 spo file add`, `rclone copy` — stamps files *before* they leave your machine so trust metadata travels to Google Workspace, Box, M365, Dropbox
- **MCP server** — 9 tools (stamp, audit, embed, extract, detect, validate, scan, trust, create) — works with any MCP-compatible agent

**Regulatory deadlines driving urgency:**
- **Aug 2, 2026** — EU AI Act Article 50: AI-generated text for public interest must be labeled. Fines up to EUR 35M / 7% global turnover.
- **Jun 30, 2026** — Colorado AI Act (SB 205): High-risk AI deployers must perform impact assessments. NIST/ISO compliance is an affirmative defense.
- **Aug 2, 2025** — EU AI Act GPAI rules already enforced. Fines up to EUR 15M / 3% global turnover.
- **Jan 17, 2025** — DORA enforced for financial entities. Fines up to 2% global turnover.

---

## 1. Hacker News — Show HN

### Title (pick one)

```
Show HN: AKF – The file format for the AI era (trust, provenance, verification)
```

**Alternative title (urgency hook — use if launching close to Aug 2026):**

```
Show HN: AKF – In 4 months, EU law requires AI content to be labeled. Here's an open format for it
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

The shell hook also pre-stamps files before you upload them to content
platforms — `gws upload`, `box files:upload`, `rclone copy` — so the trust
metadata travels with the file to Google Workspace, Box, M365, or Dropbox.

Why now: EU AI Act Article 50 takes effect August 2, 2026. AI-generated
text published for public interest must be labeled as AI-generated.
Fines up to EUR 35M or 7% of global turnover. Colorado's AI Act (SB 205)
kicks in June 30, 2026 — first US state law requiring AI risk management.
AKF maps directly to both.

Dual SDK (Python + TypeScript), integrations for LangChain, LlamaIndex,
CrewAI, and an MCP server with 9 tools. Maps to EU AI Act, Colorado SB 205,
SOX, DORA, NIST AI RMF, and ISO 42001 for compliance.
VS Code extension auto-stamps files edited by Copilot and Cursor.

Source: https://github.com/HMAKT99/AKF
Docs: https://akf.dev
MIT licensed.

Happy to answer questions about the format design or trust model.
```

---

## 2. Reddit Posts

### 2a. r/MachineLearning — [P] tag

**Title:** `[P] AKF — open file format for AI trust and provenance. EU AI Act Article 50 requires AI content labeling by Aug 2026 — here's a format for it`

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
(node parser + trust filter), CrewAI (trust-aware agent tool), and an MCP
server with 9 tools for any agent that speaks the protocol.

Why this matters now: EU AI Act Article 50 takes effect August 2, 2026.
AI-generated text for public interest must be labeled. Fines up to EUR 35M
or 7% of global turnover. Colorado SB 205 kicks in June 30, 2026 — first
US state AI law. AKF's `akf audit --regulation eu_ai_act` maps directly.

    pip install akf
    npm install akf-format

Spec & docs: https://akf.dev
Source: https://github.com/HMAKT99/AKF
MIT license.
```

### 2b. r/programming

**Title:** `AKF: trust metadata for AI content that embeds into DOCX, PDF, images. EU law requires AI labeling by Aug 2026 — here's an open format`

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

The shell hook also pre-stamps files before CLI uploads — `gws upload`,
`box files:upload`, `rclone copy` — so trust metadata travels with the file
to Google Workspace, Box, or Dropbox.

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

### Thread A — Urgency hook (recommended)

```
1/ In 134 days, EU law will require every AI-generated document to be labeled.

Fines: up to EUR 35M or 7% of global turnover.

Most companies have no way to do this.

We built an open format that solves it in one line of code.

🧵

2/ The problem: AI generates reports, analyses, code, summaries.

Someone pastes GPT output into a Word doc. That doc gets shared.

6 months later, nobody knows:
→ Was this AI-generated?
→ How confident was the model?
→ What was the source?
→ Has anyone verified it?

EU AI Act Article 50 says this can't continue.

3/ AKF (Agent Knowledge Format) stamps trust metadata onto AI content.

~15 tokens of JSON. Embeds directly inside the file.

{"v":"1.0","claims":[{"c":"Revenue $4.2B","t":0.98,"src":"SEC 10-Q"}]}

DOCX, PDF, Excel, PowerPoint, images, HTML, Markdown — 20+ formats.
No sidecars. The metadata travels with the file.

4/ Not all sources are equal. AKF's trust model knows this.

SEC filing at 0.98 confidence → trust stays ~0.98
AI inference at 0.98 confidence → drops to ~0.29

10 detection classes catch: hallucination risk, knowledge laundering,
stale claims, provenance gaps, classification downgrades.

5/ Zero-touch mode. One line in your shell config:

eval "$(akf shell-hook)"

Every file Claude, ChatGPT, OpenClaw, Aider, or Ollama touches gets
stamped automatically.

Upload to Google Workspace, Box, or Dropbox via CLI? Pre-stamped before
it leaves your machine.

6/ Compliance is the killer feature.

• EU AI Act Art. 50 — AI labeling (Aug 2, 2026)
• Colorado SB 205 — first US state AI law (Jun 30, 2026)
• DORA — financial sector (enforced)
• NIST AI RMF, SOX, ISO 42001

One command: akf audit report.akf --regulation eu_ai_act

7/ Open source. MIT license. Python + TypeScript.

MCP server with 9 tools — works with any agent.
Integrations: LangChain, LlamaIndex, CrewAI.
VS Code extension for Copilot/Cursor.

pip install akf
npm install akf-format

github.com/HMAKT99/AKF
akf.dev

The AI era finally has its file format. The law says it needs one.
```

### Thread B — Era narrative (classic)

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
automatically. Upload to Google Drive or Box? Pre-stamped before it
leaves your machine.

6/ Maps directly to compliance frameworks:

• EU AI Act Art. 50 (AI labeling — Aug 2026)
• Colorado SB 205 (first US state AI law — Jun 2026)
• DORA (financial sector — enforced)
• SOX 302/404, NIST AI RMF, ISO 42001

akf audit report.akf --regulation eu_ai_act

7/ Open source. MIT license. Python + TypeScript SDKs.

MCP server with 9 tools. Integrations for LangChain, LlamaIndex, CrewAI.
VS Code extension for Copilot/Cursor auto-stamping.

pip install akf
npm install akf-format

GitHub: github.com/HMAKT99/AKF
Docs: akf.dev

The AI era finally has its file format.
```

---

## 4. LinkedIn Post

### Post A — Compliance urgency (recommended for enterprise audience)

```
On August 2, 2026, the EU AI Act's Article 50 takes effect.

Every AI-generated document published for public interest must be labeled as
AI-generated. Fines: up to EUR 35 million or 7% of global annual turnover.

Colorado's AI Act (SB 205) kicks in June 30, 2026 — the first US state law
requiring AI impact assessments. DORA is already enforced for financial services.

Most organizations have no standard way to label AI content. It's scattered
across Word docs, PDFs, and reports with zero provenance.

We built AKF (Agent Knowledge Format) to solve this.

AKF is an open file format that embeds trust scores, source provenance, and
AI-generated flags directly into the files organizations already use — Word,
Excel, PowerPoint, PDF, and 20+ others. No sidecars. No databases. The
metadata lives inside the file and travels with it.

For technical teams: `pip install akf` and you're up in 30 seconds.
`eval "$(akf shell-hook)"` auto-stamps every file Claude, ChatGPT, OpenClaw,
or Copilot touches. Pre-stamps before uploads to Google Workspace, Box,
M365, or Dropbox — so trust metadata arrives with the file.

For compliance teams: `akf audit report.akf --regulation eu_ai_act` gives
you an actionable compliance report. Pre-mapped to EU AI Act, Colorado SB 205,
SOX, DORA, NIST AI RMF, and ISO 42001.

For CISOs: 10 detection classes catch hallucination risk, knowledge laundering,
and classification downgrades before they reach stakeholders.

Open source (MIT). Python + TypeScript SDKs. MCP server with 9 tools.
Integrations for LangChain, LlamaIndex, and CrewAI.

The clock is ticking. The AI era needs its file format.

→ github.com/HMAKT99/AKF
→ akf.dev

#EUAIAct #AIGovernance #AICompliance #OpenSource #TrustInAI #Article50
```

### Post B — Era narrative (broader audience)

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

For compliance teams: AKF maps directly to EU AI Act Article 50, Colorado
SB 205, SOX, DORA, and NIST AI RMF. One command gives you an actionable
compliance report.

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

#AIGovernance #OpenSource #TrustInAI #AICompliance #LLM #EUAIAct
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

COMPLIANCE — THE CLOCK IS TICKING
EU AI Act Article 50 takes effect August 2, 2026 — AI content must be
labeled. Colorado SB 205 kicks in June 30, 2026. DORA already enforced
for financial services. AKF maps to all of them plus SOX, NIST AI RMF,
and ISO 42001.

ZERO-TOUCH MODE
One line in your shell config and every AI-generated file gets stamped
automatically. Smart context detection infers git author, download source,
and project classification rules.

    eval "$(akf shell-hook)"    # Intercepts claude, chatgpt, openclaw, aider, ollama
    akf install                 # Background daemon for ~/Downloads, ~/Desktop

INSTALL
pip install akf          # Python
npm install akf-format   # TypeScript

PRE-UPLOAD STAMPING
Upload to Google Workspace, Box, M365, or Dropbox via CLI? AKF stamps
the file before it leaves your machine. Trust metadata arrives with the file.

INTEGRATIONS
LangChain, LlamaIndex, CrewAI, MCP server (9 tools), VS Code AI monitor,
GitHub Action, Office Add-in, Google Workspace Add-on.

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

The timing is right: EU AI Act Article 50 requires AI content labeling by
August 2, 2026. Colorado's SB 205 hits June 30, 2026. Most organizations
have no standard way to do this. AKF gives them one — open source, embeds
into the files they already produce.

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

**Pre-upload stamping** — the shell hook also intercepts content platform CLIs
(`gws upload`, `box files:upload`, `rclone copy`, `m365 spo file add`) and stamps
files *before* they leave your machine. Trust metadata arrives at Google
Workspace, Box, M365, or Dropbox with the file.

**VS Code extension** — detects large AI-style insertions from Copilot, Cursor,
and other AI coding tools, and stamps on save.

The goal: if AI touched it, AKF knows about it. No manual intervention.

## Compliance built in — and the clock is ticking

EU AI Act Article 50 takes effect **August 2, 2026**. AI-generated text
published for public interest must be labeled. Fines: up to EUR 35 million
or 7% of global annual turnover. Colorado's AI Act (SB 205) kicks in
**June 30, 2026** — the first US state law requiring AI impact assessments.
DORA is already enforced for financial services.

AKF maps directly to all of them:

| Regulation | Deadline | AKF Field |
|------------|----------|-----------|
| EU AI Act Art. 50 | Aug 2, 2026 | `ai`, `src`, `provenance` |
| EU AI Act Art. 14 | Aug 2, 2026 | `ver`, `ver_by` |
| Colorado SB 205 | Jun 30, 2026 | `risk`, `tier`, `classification` |
| SOX 302/404 | Enforced | `classification`, `tier`, audit trail |
| DORA | Enforced | `confidence`, `verified`, audit trail |
| NIST AI RMF | Framework | `risk`, `t`, `security` |

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
SDKs. Compliance mapping for EU AI Act Art. 50, Colorado SB 205, SOX, DORA,
NIST AI RMF, and ISO 42001. MCP server with 9 tools. MIT licensed.
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

### awesome-mcp / MCP server registries

```markdown
## [AKF MCP Server](https://github.com/HMAKT99/AKF/tree/main/packages/mcp-server-akf)

MCP server for AI trust metadata. 9 tools: stamp, audit, embed, extract,
detect, validate, scan, trust, create. Any MCP-compatible agent can create,
read, and validate trust provenance. Maps to EU AI Act, NIST AI RMF.
`pip install mcp-server-akf`. MIT licensed.
```

### awesome-compliance / awesome-ai-governance

```markdown
## [AKF — Agent Knowledge Format](https://github.com/HMAKT99/AKF)

Open file format for AI content trust and provenance. Pre-mapped to EU AI Act
Article 50, Colorado SB 205, SOX, DORA, NIST AI RMF, and ISO 42001.
`akf audit --regulation eu_ai_act` generates actionable compliance reports.
Embeds directly into DOCX, PDF, and 20+ formats. MIT licensed.
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
ai-safety, python, typescript, open-standard, eu-ai-act, mcp, ai-governance
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

### OpenClaw Community

```
AKF now supports OpenClaw — one line in your shell config and every file
OpenClaw generates gets trust-stamped automatically.

eval "$(akf shell-hook)"

AKF (Agent Knowledge Format) embeds trust scores and provenance into the
files AI agents create — DOCX, PDF, Markdown, images, and 20+ formats.
It also pre-stamps files before you upload them to Google Workspace, Box,
or Dropbox via CLI, so the metadata travels with the file.

Why now: EU AI Act Article 50 requires AI content labeling by August 2,
2026. AKF gives you compliance out of the box.

pip install akf
GitHub: https://github.com/HMAKT99/AKF
Docs: https://akf.dev
```

### Anthropic Community / Claude Forums

```
Built an MCP server for AKF (Agent Knowledge Format) — 9 tools for AI
trust metadata that any MCP agent can use: stamp, audit, embed, extract,
detect, validate, scan, trust, create.

Use case: Claude Code reads your CLAUDE.md and stamps every file it creates
with confidence scores and evidence. The AKF shell hook intercepts the
claude CLI and auto-stamps any new or modified files. Pre-stamps before
uploads to Google Workspace, Box, or M365.

The metadata embeds directly into DOCX, PDF, Markdown — no sidecars.
Trust scores use weighted source tiers so an SEC filing (tier 1) keeps
its confidence but an AI inference (tier 5) gets penalized.

pip install akf
pip install mcp-server-akf

GitHub: https://github.com/HMAKT99/AKF
```

---

## 10. Reddit — Compliance-Specific Posts

### r/gdpr / r/europrivacy

**Title:** `EU AI Act Article 50 takes effect Aug 2, 2026 — open-source format for AI content labeling`

**Body:**

```
Article 50 requires that AI-generated text published for public interest
be labeled as AI-generated. Fines: up to EUR 35M or 7% of global turnover.

Most organizations have no standard way to do this. AI content lives inside
Word docs and PDFs with zero provenance metadata.

AKF (Agent Knowledge Format) is an open file format that embeds AI labeling
and trust metadata directly into DOCX, PDF, HTML, images, and 20+ formats.
No sidecars, no external databases — the metadata lives inside the file.

Key fields for Article 50 compliance:
- `ai` — boolean flag: was this AI-generated?
- `src` — source provenance chain
- `provenance` — full derivation history
- `ver` / `ver_by` — human verification status (Art. 14)

One command generates a compliance report:

    akf audit report.docx --regulation eu_ai_act

Also maps to DORA (enforced for financial entities), NIST AI RMF,
SOX, and ISO 42001.

Open source, MIT licensed. Python + TypeScript SDKs.

GitHub: https://github.com/HMAKT99/AKF
Docs: https://akf.dev
```

### r/cybersecurity

**Title:** `AKF — open format for detecting knowledge laundering, hallucination risk, and AI provenance gaps in documents`

**Body:**

```
10 detection classes for AI content security, running on trust metadata
embedded directly in files:

1. AI Content Without Review — no human verification stamp
2. Trust Below Threshold — scores below your org's minimum
3. Hallucination Risk — weak evidence grounding
4. Knowledge Laundering — AI content repackaged as human-written
5. Classification Downgrade — AI lowering document sensitivity
6. Stale Claims — temporal decay past threshold
7. Excessive AI Concentration — too many AI-sourced claims
8. Provenance Gap — missing source chain
9. Ungrounded AI Claims — AI assertions without supporting evidence
10. Trust Degradation Chain — cascading low-trust sources

The metadata is ~15 tokens of JSON per claim, embedded into DOCX, PDF,
HTML, images — no sidecars. A shell hook auto-stamps files from Claude,
ChatGPT, OpenClaw, and other AI tools. Pre-stamps before uploads to
cloud platforms so metadata travels with the file.

    pip install akf
    akf scan ./documents/ --recursive
    akf audit report.docx --regulation eu_ai_act

Maps to EU AI Act (Aug 2026), Colorado SB 205 (Jun 2026), DORA (enforced),
NIST AI RMF, and ISO 42001. MCP server with 9 tools for agent integration.

GitHub: https://github.com/HMAKT99/AKF
```

---

## 11. SEO Content Briefs

### Brief 1: "How to Comply with EU AI Act Article 50"

```
Target keywords: EU AI Act Article 50, AI content labeling, AI transparency
                 requirements 2026, Article 50 compliance

Publish on: akf.dev/blog, cross-post to dev.to and Medium

Structure:
1. What Article 50 requires (AI text labeling, deepfake disclosure)
2. Who it applies to (deployers of AI systems generating public content)
3. Penalties (EUR 35M / 7% turnover)
4. Timeline (Code of Practice Jun 2026, enforcement Aug 2, 2026)
5. How to implement (AKF as the metadata standard)
6. Step-by-step: pip install akf → akf stamp → akf audit → akf embed
7. Comparison: AKF vs manual labeling vs C2PA vs watermarking

CTA: pip install akf && akf audit report.docx --regulation eu_ai_act
```

### Brief 2: "Colorado AI Act SB 205: Developer's Compliance Guide"

```
Target keywords: Colorado AI Act, SB 205 compliance, AI impact assessment
                 Colorado, AI risk management affirmative defense

Structure:
1. What SB 205 requires (impact assessments, consumer notices)
2. High-risk AI system definition
3. NIST/ISO compliance as affirmative defense
4. How AKF provides the evidence (trust scores, audit trail, risk field)
5. Step-by-step: akf audit --regulation nist_ai_rmf

CTA: akf audit --regulation nist_ai_rmf
```

### Brief 3: "DORA Compliance for AI in Financial Services"

```
Target keywords: DORA AI compliance, digital operational resilience AI,
                 financial AI governance

Structure:
1. How DORA applies to AI as ICT
2. Third-party risk management for AI services
3. Audit trail requirements
4. AKF trust metadata as documentation evidence
5. Integration with existing GRC tooling
```

---

## 12. Dev.to Tags & Metadata

```yaml
title: "The File Format for the AI Era: Why AI-Generated Content Needs Its Own Standard"
published: true
tags: ai, opensource, python, typescript
canonical_url: https://akf.dev/blog/file-format-for-ai
cover_image: # Use akf.dev og:image or a custom banner
series: # leave empty unless doing a series
```

**Alternative dev.to post (compliance angle):**

```yaml
title: "EU AI Act Article 50 Requires AI Content Labeling by August 2026. Here's an Open Format for It."
published: true
tags: ai, compliance, opensource, python
canonical_url: https://akf.dev/blog/eu-ai-act-article-50
```

---

## Launch Sequencing

| Phase | Timing | Actions |
|-------|--------|---------|
| **Pre-launch** | 1-2 weeks before | Homebrew formula, MCP registry listings, demo video, SEO articles queued |
| **Launch day** | Day 0 | Repo goes public → HN Show HN → Reddit (r/programming, r/MachineLearning) → Twitter Thread A |
| **Day 1-2** | Day 1-2 | Product Hunt, r/LocalLLaMA, r/cybersecurity, LinkedIn Post A |
| **Week 1** | Day 3-7 | dev.to blog, awesome-list PRs, Discord posts (LangChain, LlamaIndex, CrewAI, OpenClaw) |
| **Week 2** | Day 8-14 | r/europrivacy, Anthropic community, MCP community, compliance SEO articles |
| **Month 1** | Day 15-30 | SEO content (Article 50 guide, Colorado SB 205 guide), integration partner listings |
| **Month 2** | Day 31-60 | EU AI Office Code of Practice consultation, conference talk submissions |
| **Month 3+** | Ongoing | Standards body engagement, GRC partnerships, analyst briefings |

**Key timing note:** Every marketing piece should reference the Article 50 countdown. Update the day count in posts before publishing. The urgency window closes August 2, 2026 — maximize it.

---

## Quick Reference — Key URLs & Install Commands

| Item | Value |
|------|-------|
| GitHub | `https://github.com/HMAKT99/AKF` |
| Website | `https://akf.dev` |
| Python install | `pip install akf` |
| TypeScript install | `npm install akf-format` |
| MCP server | `pip install mcp-server-akf` |
| PyPI | `https://pypi.org/project/akf/` |
| npm | `https://www.npmjs.com/package/akf-format` |
| License | MIT |
| Primary tagline | "The file format for the AI era" |
| Urgency tagline | "Article 50 compliance in one line of code" |
| Closing line | "Every era gets its file format. The AI era finally has one." |

## Channel Checklist

| Channel | Post Ready | Priority |
|---------|-----------|----------|
| Hacker News (Show HN) | Yes (2 title options) | P0 — Launch day |
| Reddit r/programming | Yes | P0 — Launch day |
| Reddit r/MachineLearning | Yes | P0 — Launch day |
| Reddit r/LocalLLaMA | Yes | P1 — Day 1-2 |
| Reddit r/cybersecurity | Yes | P1 — Day 1-2 |
| Reddit r/europrivacy | Yes | P2 — Week 2 |
| Twitter/X | Yes (2 thread options) | P0 — Launch day |
| LinkedIn | Yes (2 post options) | P1 — Day 1-2 |
| Product Hunt | Yes | P1 — Day 1-2 |
| dev.to / Medium | Yes (2 article options) | P1 — Week 1 |
| Discord: LangChain | Yes | P1 — Week 1 |
| Discord: LlamaIndex | Yes | P1 — Week 1 |
| Discord: CrewAI | Yes | P1 — Week 1 |
| OpenClaw community | Yes | P1 — Week 1 |
| Anthropic community | Yes | P2 — Week 2 |
| MCP registries | Yes | P0 — Pre-launch |
| awesome-ai list PR | Yes | P1 — Week 1 |
| awesome-llm list PR | Yes | P1 — Week 1 |
| awesome-mcp list PR | Yes | P1 — Week 1 |
| awesome-compliance PR | Yes | P2 — Week 2 |
| SEO: Article 50 guide | Brief ready | P2 — Month 1 |
| SEO: Colorado SB 205 | Brief ready | P2 — Month 1 |
| SEO: DORA + AI | Brief ready | P3 — Month 1 |
| EU AI Office consultation | Not yet | P1 — Month 2 |
| Homebrew formula | Not yet | P0 — Pre-launch |
