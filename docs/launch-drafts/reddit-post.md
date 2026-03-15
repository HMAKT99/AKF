# Reddit Posts (3 subreddits, tailored for each)

---

## r/Python — Title: "I built a trust metadata library for AI outputs — like EXIF for photos, but for anything AI generates"

Hey r/Python,

I've been working on a problem that's been bugging me: when AI generates a financial report or a legal memo, the output carries zero metadata about how trustworthy it is.

Photos have had EXIF for decades — who took it, when, with what camera. AI outputs have nothing.

So I built **AKF** (Agent Knowledge Format) — a Python library that stamps trust metadata onto any AI output:

```python
import akf

unit = akf.stamp(
    "Revenue was $4.2B, up 12% YoY",
    confidence=0.98,
    source="SEC 10-Q",
    model="gpt-4o"
)
print(unit.inspect())
# trust=0.88  confidence=0.98  tier=3  source=SEC 10-Q
```

**What makes it interesting technically:**

- Pydantic v2 models with compact wire format (~15 tokens) + descriptive aliases
- Embeds metadata natively into 20+ formats (DOCX, PDF, XLSX, PNG, HTML, code files) — not sidecar files, actually inside the document
- 10 security detection classes (confidence laundering, authority inflation, etc.)
- File watcher daemon that auto-stamps new files (launchd/systemd, survives reboots)
- 0.2ms per stamp, 7KB memory overhead

```bash
pip install akf
akf quickstart  # full demo in one command
```

MIT licensed. Would love feedback on the API design and the trust model.

- PyPI: https://pypi.org/project/akf/
- Also on npm as `akf-format` for TypeScript

---

## r/MachineLearning — Title: "[P] AKF: Trust metadata standard for AI agent outputs — confidence scores, source provenance, security classification"

**Problem:** AI agents produce outputs with no standardised way to express confidence, source provenance, or classification. A claim with 0.95 confidence from a verified source is indistinguishable from a hallucinated guess.

**Solution:** AKF (Agent Knowledge Format) — a lightweight metadata standard (~15 tokens of JSON) that attaches trust scores to any AI output and embeds them directly into files.

**Key features:**
- Trust scoring with confidence (0–1), authority tiers (1–5), and trust decay across agent hops
- Provenance chain tracking across multi-agent systems
- 10 security detection classes (confidence laundering, authority inflation, classification drift)
- Regulatory audit against EU AI Act, HIPAA, SOX, GDPR, NIST AI, ISO 42001
- Native embedding into DOCX, PDF, XLSX, images, HTML, code — 20+ formats
- Integrations: LangChain, CrewAI, LlamaIndex, MCP server

**Why this matters for ML:**
As we move from single-model inference to multi-agent systems, trust degradation across agent hops becomes a real problem. Agent A's 0.7 confidence output shouldn't be treated as ground truth by Agent B. AKF's trust decay formula (`effective_trust = confidence × authority_weight × decay_factor`) gives agents a principled way to reason about how much to trust upstream outputs.

```bash
pip install akf  # Python
npm install akf-format  # TypeScript
```

MIT licensed. Paper on the trust model coming soon.

---

## r/LangChain — Title: "Built an integration that adds trust metadata to every LangChain output — source provenance, confidence scores, security classification"

If you're using LangChain in production, your chain outputs have no metadata about how trustworthy they are.

AKF (Agent Knowledge Format) adds trust scores, source provenance, and security classification to any AI output — including LangChain chains.

**Quick integration:**

```python
import akf
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")
response = llm.invoke("What was Apple's Q3 revenue?")

# Stamp with trust metadata
unit = akf.stamp(
    content=response.content,
    confidence=0.85,
    source="langchain-rag",
    model="gpt-4o",
    agent="financial-analyst-chain"
)

# Now this output carries provenance everywhere it goes
akf.embed("report.docx", unit=unit)
```

Also ships with:
- 10 security detection classes (catches confidence laundering, authority inflation)
- Regulatory audit (EU AI Act, HIPAA, SOX)
- MCP server for Claude integration
- `akf install` daemon that auto-stamps files

`pip install akf` — MIT licensed.
