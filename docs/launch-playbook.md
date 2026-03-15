# AKF Launch Playbook

> Internal document — not for public distribution.

---

## Phase 1: Ship-Ready (Week 1)

**Goal:** Remove all friction from install-to-first-use.

- [x] PyPI/npm/CI/license badges on READMEs
- [x] Fix TypeScript circular self-dependency
- [x] `akf doctor` command (PATH check + platform-specific fix)
- [x] `akf quickstart` command (one-command demo)
- [x] PATH troubleshooting in READMEs
- [ ] Clean venv test: `pip install akf` → `akf quickstart`
- [ ] Clean node test: `npm install akf-format` → import works
- [ ] Terminal GIF recorded

---

## Phase 2: Content & Positioning (Week 2)

**Goal:** Give people a reason to care before they see the code.

### 2.1 The pitch (pick ONE lead narrative)

| Audience | Lead with | Hook |
|----------|-----------|------|
| AI engineers | "Stop re-processing files your LLM already analyzed" | Token burn / cost |
| Enterprise / GRC | "AI governance in one command" | Compliance (EU AI Act, SOX) |
| Indie devs | "EXIF for AI — trust metadata that travels with your files" | Simplicity |

**Recommendation:** Lead with **indie/developer** narrative for launch. Enterprise sells itself once developers adopt. "EXIF for AI" is your strongest one-liner.

### 2.2 Launch blog post (publish on your site + dev.to + Medium)

Structure:
1. The problem in 2 sentences (AI content has no trust metadata)
2. What AKF is in 1 sentence (EXIF for AI)
3. Live demo: `akf create --demo` → `akf inspect` → `akf trust` (terminal screenshots)
4. The "aha" moment: embed into a DOCX, open in Word, see metadata in Properties
5. Where it's going (token burn reduction, trust-aware routing)
6. `pip install akf` CTA

### 2.3 README rewrite (root)

Current README is solid but reads like docs. For launch, restructure:

```
# AKF — EXIF for AI

[One-sentence description]
[3 badges: PyPI version, npm version, tests passing]
[Terminal GIF: create → inspect → trust in 10 seconds]

## Install
pip install akf    # Python
npm i akf-format   # TypeScript

## 30-Second Demo
[4 commands with output]

## Why
[3 bullet points, not paragraphs]

## Docs
[Link to akf.dev]
```

### 2.4 Terminal GIF

Record with [asciinema](https://asciinema.org/) or [vhs](https://github.com/charmbracelet/vhs):

```
akf create report.akf --demo
akf inspect report.akf
akf trust report.akf
akf security report.akf
```

Embed in README and homepage hero.

---

## Phase 3: Distribution (Week 3)

**Goal:** Get AKF in front of people who build with LLMs.

### 3.1 Hacker News

- Post as "Show HN: AKF — EXIF for AI (trust metadata for LLM-generated content)"
- Best time: Tuesday-Thursday, 9-11am ET
- Be online for 2 hours to answer comments
- Have the demo flow, Word Properties screenshot, and governance report ready as follow-ups

### 3.2 Reddit

- r/MachineLearning (research angle: trust-aware routing)
- r/LocalLLaMA (practical angle: tag your local model outputs)
- r/Python (tool announcement)

### 3.3 Twitter/X thread

```
1/ Every photo has EXIF. Every AI-generated file has... nothing.

We built AKF — trust metadata that travels with your files.

pip install akf

2/ One command tells you what to trust: [screenshot of akf inspect]

3/ Works inside Word, Excel, PowerPoint: [screenshot of Properties panel]

4/ Your LLM can read it too: [code snippet]

5/ Open source, zero vendor lock-in. https://akf.dev
```

### 3.4 GitHub ecosystem

- Add `topics` to repo: `ai`, `trust`, `metadata`, `governance`, `llm`, `file-format`
- Create a GitHub Discussion for "Show what you built with AKF"
- File issues tagged `good first issue` (3-5 of them) to attract contributors

### 3.5 Agent framework communities

- Post in CrewAI Discord/GitHub showing the integration
- Post in LangChain Discord showing the callback handler
- Post in LlamaIndex Discord showing the trust filter
- These are high-signal, low-noise communities

---

## Phase 4: Credibility (Week 4)

**Goal:** Make AKF look like a standard, not a side project.

### 4.1 Spec as a standalone artifact

- Host the JSON Schema at `https://akf.dev/schema/v1.1.json` (stable URL)
- Add `$schema` reference to all example files
- This lets anyone validate AKF files without installing the SDK

### 4.2 Interop proof points

Create 3 demos that show AKF working across boundaries:
1. **Python → TypeScript:** Create in Python, consume in Node.js
2. **CLI → Word:** Embed metadata, open in Word Properties
3. **Model A → Model B:** GPT generates a file, Claude reads the trust scores

### 4.3 Compliance mapping doc

Publish a page on akf.dev mapping AKF fields to regulation requirements:

| Regulation | Requirement | AKF Field |
|------------|-------------|-----------|
| EU AI Act Art. 13 | Transparency | `ai`, `src`, `provenance` |
| EU AI Act Art. 14 | Human oversight | `ver`, `ver_by` |
| SOX 302/404 | Internal controls | `classification`, `tier`, audit trail |
| NIST AI RMF | Risk management | `risk`, `t`, `security` |

This is what enterprise buyers Google. Have it indexed.

### 4.4 "Awesome AKF" list

Create `awesome-akf` repo with:
- Links to integrations (CrewAI, LangChain, LlamaIndex, MCP)
- Example workflows
- Community tools
- Blog posts / talks

---

## Phase 5: Adoption Loops (Ongoing)

### 5.1 Git hooks (already built)

`akf init --git-hooks` should add pre-commit validation. This creates a viral loop: one person on a team adds it, everyone has to use AKF.

### 5.2 CI/CD template

Publish a reusable GitHub Action:

```yaml
- uses: HMAKT99/akf-action@v1
  with:
    command: audit
    format: report
```

This makes AKF show up in PR checks — visible to entire teams.

### 5.3 VS Code extension (future)

- Inline trust score decorations on AKF files
- "AKF: Inspect" command palette action
- Gutter icons for claim trust levels
- This is a high-effort, high-reward item for later

---

## Launch Day Checklist

- [ ] Repo is public
- [ ] `pip install akf` works from PyPI (clean venv test)
- [ ] `npm install akf-format` works (clean project test)
- [ ] `akf create --demo` → `akf inspect` flow is flawless
- [ ] README has terminal GIF, badges, 30-second demo
- [ ] akf.dev is live and loads fast
- [ ] Blog post is published
- [ ] HN post is ready (title + first comment drafted)
- [ ] Twitter thread is queued
- [ ] 3 "good first issue" GitHub issues exist
- [ ] Schema hosted at stable URL
- [ ] You have 2 hours blocked to respond to comments

---

## What NOT to Do at Launch

- **Don't lead with enterprise.** "Enterprise governance" scares indie devs. Lead with "EXIF for AI", let enterprises find the audit/compliance features themselves.
- **Don't show all 30 CLI commands.** Show 4: `create`, `inspect`, `trust`, `embed`. Discovery comes later.
- **Don't compare to competitors on day 1.** The comparison pages exist on akf.dev for SEO — don't make them the launch story.
- **Don't ask for contributions before adoption.** First get users, then get contributors.
- **Don't launch on Friday.** Tuesday-Thursday for HN/Reddit engagement.

---

## Success Metrics (30 days post-launch)

| Metric | Target |
|--------|--------|
| GitHub stars | 500+ |
| PyPI installs/week | 200+ |
| npm installs/week | 100+ |
| HN upvotes | 100+ |
| Blog post views | 2,000+ |
| First external PR | 1+ |
| First "I built X with AKF" post | 1+ |
