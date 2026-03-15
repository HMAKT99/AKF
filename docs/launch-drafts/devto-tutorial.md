# Dev.to Tutorial

---
title: "Add trust metadata to your AI app in 5 minutes"
published: false
tags: python, ai, langchain, security
---

## The Problem Nobody's Talking About

Every photo you take has EXIF metadata — who took it, when, with what camera, GPS coordinates. It's invisible but always there.

Every AI output has... nothing.

When GPT-4 writes a financial report, there's no metadata saying:
- How confident the model was
- Where the data came from
- Whether it's safe to share externally

A hallucinated number looks identical to a verified fact.

## The Fix: 3 Lines of Python

```bash
pip install akf
```

```python
import akf

unit = akf.stamp(
    "Revenue was $4.2B, up 12% YoY",
    confidence=0.98,
    source="SEC 10-Q",
    model="gpt-4o"
)
```

That's it. `unit` now carries trust metadata:

```python
print(unit.inspect())
```

```
AKF Unit (v1.1) — 1 claim, public

  Claim #1
    Content:     Revenue was $4.2B, up 12% YoY
    Confidence:  0.98
    Authority:   Tier 3 (domain expert)
    Source:      SEC 10-Q
    AI-generated: Yes (gpt-4o)
    Trust score: 0.88 → ACCEPT
```

## Embed Into Real Files

AKF doesn't just create metadata — it embeds it directly into documents:

```python
# Stamp a Word doc
akf.stamp_file("report.docx", confidence=0.9, source="analyst-review")

# Stamp a PDF
akf.stamp_file("summary.pdf", confidence=0.7, source="ai-summary")

# Stamp an image
akf.stamp_file("chart.png", confidence=0.95, source="data-pipeline")
```

The metadata lives inside the file. Open the DOCX in Word — it's in the custom properties. Open the PNG — it's in the EXIF. It travels with the file.

## Catch Bad Actors: Security Detections

AKF includes 10 security detection classes that catch manipulation:

```python
import akf, json

# A suspicious unit: high confidence + low authority + AI-generated
sus = {
    "version": "1.1",
    "claims": [{
        "content": "Revenue will reach $50B next quarter",
        "confidence": 0.95,
        "authority_tier": 1,
        "ai_generated": True,
        "source": "unspecified"
    }]
}

unit = akf.loads(json.dumps(sus))
report = akf.run_all_detections(unit)

print(f"Triggered: {report.triggered_count}")
# → Triggered: 3 (confidence laundering, authority inflation, missing provenance)
```

## One Command: Auto-Stamp Everything

```bash
akf install
```

Now every new file in `~/Downloads`, `~/Desktop`, and `~/Documents` gets trust metadata automatically. The daemon runs in the background, survives reboots, and uses 0% idle CPU.

## Works With Your Stack

AKF integrates with the tools you already use:

| Tool | How |
|------|-----|
| **LangChain** | Stamp chain outputs with provenance |
| **CrewAI** | Track trust across multi-agent crews |
| **LlamaIndex** | Add trust to RAG pipeline outputs |
| **Claude** | MCP server for native tool use |
| **VS Code** | Extension for in-editor trust badges |
| **GitHub Actions** | Stamp artifacts in CI/CD |

## Why This Matters

The EU AI Act (enforcement starting 2025) requires provenance metadata on high-risk AI outputs. Insurance companies are starting to ask about AI liability coverage. Multi-agent systems need a way to reason about trust across hops.

Trust metadata will be as fundamental to AI content as HTTPS became to the web. The question is when, not if.

```bash
pip install akf        # Python
npm install akf-format # TypeScript
```

MIT licensed. Free and open — forever.

**Links:**
- [PyPI](https://pypi.org/project/akf/)
- [npm](https://www.npmjs.com/package/akf-format)
- [Website](https://akf.dev)
- [Try it live on HuggingFace](link)
