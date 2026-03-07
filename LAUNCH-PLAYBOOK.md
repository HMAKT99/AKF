# AKF Launch Playbook

## The One-Line Pitch

> AKF is EXIF for AI — trust metadata that embeds natively into every file AI touches.

---

## Phase 1: Pre-Launch (1-2 weeks before)

### Build the Arsenal

- [ ] **Demo video** (30-60s) — cinematic, Apple-style, shows the problem → solution → proof
- [ ] **Launch blog post** (800-1200 words) — "Why we built AKF" origin story
- [ ] **Twitter/X thread** (10-12 tweets) — the hook thread that goes viral
- [ ] **HN post draft** — Show HN title + first comment ready to paste
- [ ] **README polish** — hero GIF, badges, quickstart that works in 30 seconds
- [ ] **Landing page live** — akf.dev with clear CTA, install command front and center

### Seed the Ground

- [ ] DM 10-15 devs you respect — give them early access, ask for honest feedback
- [ ] Get 3-5 people to star the repo before launch (social proof)
- [ ] Prepare answers for obvious objections:
  - "How is this different from C2PA?" → C2PA is for media authenticity. AKF is for all AI content — docs, code, data, streaming.
  - "Why not just use metadata headers?" → AKF embeds inside the file. It survives email, Slack, downloads. Headers don't.
  - "Who needs this?" → Anyone whose AI output goes to a human who needs to decide whether to trust it.

### Content Bank (write all of these before launch day)

1. **The Problem Post** — "AI generates 2.4M documents per day. None of them tell you how much to trust them."
2. **The Technical Post** — "How AKF embeds trust metadata in 15 tokens"
3. **The Compliance Post** — "EU AI Act requires AI transparency. Here's how to comply in one line of code."
4. **The Comparison Post** — "AKF vs C2PA vs IPTC vs Watermarking — what each actually solves"
5. **The Integration Post** — "We added trust metadata to our LangChain pipeline in 10 minutes"

---

## Phase 2: Launch Day

### Hour-by-Hour

**T-1h: Final checks**
- Repo is public, README looks perfect
- akf.dev loads fast, install commands work
- `pip install akf` and `npm install akf-format` both install clean
- Demo video uploaded and embedded

**T+0: Go live**
1. Post on Hacker News: **"Show HN: AKF — EXIF for AI (trust metadata for every file AI touches)"**
   - First comment: explain what it does, why you built it, and a 3-line code example
2. Post Twitter/X thread simultaneously
3. Post on Reddit: r/MachineLearning, r/artificial, r/Python, r/opensource
4. Post on LinkedIn (different tone — enterprise/compliance angle)

**T+1h onward:**
- Monitor HN comments — respond to every single one within 15 minutes
- Retweet/share anyone who mentions AKF
- If HN gets traction, post the blog link in a follow-up comment

### The HN First Comment (template)

```
Hey HN, I built AKF because I kept seeing AI-generated reports
with no way to know how trustworthy they were.

AKF embeds trust metadata — confidence scores, model provenance,
source references — directly inside files. DOCX, PDF, images,
code, Markdown. It survives copy-paste, email, Slack.

    pip install akf
    akf stamp report.pdf --confidence 0.92 --model gpt-4o
    akf read report.pdf   # → trust: 0.92, model: gpt-4o
    akf audit ./reports/ --framework eu-ai-act

~15 tokens overhead per stamp. Open format, MIT licensed.

Happy to answer any questions about the design decisions.
```

### The Twitter/X Thread (template)

```
1/ AI generates millions of documents every day.

   Not one of them tells you how much to trust it.

   We built something to fix that. Meet .akf →

2/ AKF = "EXIF for AI"

   Trust metadata that embeds natively into files.
   Confidence scores. Model provenance. Source references.

   It lives INSIDE the file — survives email, Slack, downloads.

3/ One command:

   pip install akf
   akf stamp report.pdf --confidence 0.92 --model gpt-4o

   That's it. Your PDF now carries its own trust receipt.

4/ Reading it back is just as simple:

   akf read report.pdf
   → Trust: 0.92 | Model: gpt-4o | Source: finance-db | Reviewed: Yes

5/ Works with everything:

   .docx .pdf .xlsx .pptx .md .html .png .json .csv .py

   20+ formats. ~15 tokens overhead. 0.1s streaming.

6/ Compliance built in:

   akf audit ./reports/ --framework eu-ai-act

   EU AI Act, HIPAA, SOX, GDPR — one command.

7/ Why not C2PA / watermarking / metadata headers?

   C2PA = media authenticity (photos, video)
   Watermarking = detection ("is this AI?")
   AKF = trust layer for ALL AI content (docs, code, data, streams)

   Different problem. Different solution.

8/ Enterprise-ready:

   10 AI-specific detection classes
   Microsoft Purview integration
   MCP server for AI agents
   LangChain + LlamaIndex plugins

9/ Open format. MIT licensed.
   Python SDK + TypeScript SDK.

   pip install akf
   npm install akf-format

10/ The file format for the AI era.

    akf.dev
    github.com/HMAKT99/AKF

    Star it if this resonates. We're just getting started.
```

---

## Phase 3: Distribution Channels

### Tier 1 — Launch day (highest impact)
| Channel | Angle | Format |
|---------|-------|--------|
| Hacker News | Technical + "Show HN" | Link post + first comment |
| Twitter/X | Developer hook | 10-tweet thread |
| Reddit r/MachineLearning | Research/technical angle | Text post with examples |
| LinkedIn | Enterprise/compliance angle | Long-form post |

### Tier 2 — Week 1 (sustain momentum)
| Channel | Angle | Format |
|---------|-------|--------|
| Dev.to | Tutorial: "Add trust metadata to your AI pipeline" | Blog post |
| Hashnode | "Why AI needs EXIF" | Blog post |
| Reddit r/Python | Python SDK showcase | Text post |
| Reddit r/node | TypeScript SDK showcase | Text post |
| Product Hunt | Launch (schedule for a Tuesday) | Product page |
| YouTube | Demo video + walkthrough | Short-form |

### Tier 3 — Weeks 2-4 (build authority)
| Channel | Angle | Format |
|---------|-------|--------|
| Podcasts (Changelog, PythonBytes, etc.) | Pitch as guest | Email pitch |
| AI newsletters (TLDR AI, The Batch, etc.) | Submit for inclusion | Submission form |
| Conference CFPs (PyCon, AI Engineer, etc.) | Talk proposal | Abstract |
| InfoSec channels | 10 detection classes angle | Blog + demo |

---

## Phase 4: Messaging by Audience

### Developers
- **Hook:** "pip install, import, trust metadata in 5 minutes"
- **Proof:** Code examples, quickstart, SDK docs
- **CTA:** Star the repo, try the quickstart

### Security / CISOs
- **Hook:** "10 AI-specific threats your DLP can't catch"
- **Proof:** Detection classes, Purview integration, audit trails
- **CTA:** Read the security whitepaper, book a demo

### Compliance / Governance
- **Hook:** "EU AI Act requires AI transparency. One command."
- **Proof:** Audit output, framework coverage, machine-readable trails
- **CTA:** Run `akf audit` on your AI output folder

### Knowledge Workers
- **Hook:** "That report your AI wrote? Now you can see exactly how trustworthy each claim is."
- **Proof:** Trust scores, provenance chains, review status
- **CTA:** Install the Office add-in / VS Code extension

---

## Phase 5: Metrics to Track

### Week 1 targets
- [ ] GitHub stars: 100+
- [ ] PyPI downloads: 500+
- [ ] npm downloads: 200+
- [ ] HN upvotes: 50+ (front page = 100+)
- [ ] Twitter impressions: 50K+
- [ ] akf.dev unique visitors: 2K+

### Month 1 targets
- [ ] GitHub stars: 500+
- [ ] PyPI downloads: 2K+
- [ ] npm downloads: 1K+
- [ ] Contributors: 3+
- [ ] Integration PRs from community: 1+

### Track daily
- GitHub stars + forks + issues
- PyPI/npm download counts
- akf.dev traffic (add Plausible or similar)
- Social mentions (search "akf" + "agent knowledge format")

---

## Phase 6: Post-Launch Momentum

### Week 2-4: Content drip
- Publish one post per week from the content bank
- Share user examples / testimonials as they come in
- Post "how we built X with AKF" tutorials

### Month 2: Community
- Create Discord / GitHub Discussions
- Write a CONTRIBUTING.md
- Tag "good first issues" for new contributors
- Reach out to LangChain / LlamaIndex maintainers for official integration

### Month 3: Enterprise
- Publish compliance whitepaper
- Build case study with one design partner
- Launch enterprise tier or support offering (if applicable)

---

## The One Thing That Matters Most

Everything above is noise if the **quickstart doesn't work in 30 seconds**.

Before you launch, have 5 people who've never seen AKF run:
```
pip install akf
```
and get to a working trust stamp in under a minute. If they can't, fix that first. Everything else follows.

---

## Launch Checklist (final go/no-go)

- [ ] `pip install akf` works clean on fresh Python 3.10+
- [ ] `npm install akf-format` works clean on Node 18+
- [ ] README quickstart runs without errors
- [ ] akf.dev loads in <2s, install command is above the fold
- [ ] Demo video is uploaded and plays
- [ ] HN post + first comment are drafted
- [ ] Twitter thread is drafted
- [ ] 3+ people have tested the install flow
- [ ] You've set aside 4 hours post-launch to respond to everything
