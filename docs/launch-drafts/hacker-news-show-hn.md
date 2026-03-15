# Show HN: AKF – EXIF for AI (trust metadata for every file AI touches)

Every photo carries EXIF — who took it, when, with what camera. But when AI generates a financial report, a legal memo, or a medical summary, the output carries nothing. No confidence score. No source provenance. No way to tell if the claim came from a verified SEC filing or a hallucinated guess.

AKF (Agent Knowledge Format) fixes this. It's a lightweight JSON metadata standard (~15 tokens) that embeds trust scores, source provenance, and security classification directly into files — DOCX, PDF, XLSX, images, code, and 20+ formats.

```python
import akf

unit = akf.stamp(
    "Revenue was $4.2B, up 12% YoY",
    confidence=0.98,
    source="SEC 10-Q",
    model="gpt-4o"
)
print(unit.inspect())
# → trust=0.88  confidence=0.98  tier=3  source=SEC 10-Q
```

What it does:

- **Stamps** any AI output with trust metadata (confidence 0–1, authority tiers 1–5, source chain)
- **Embeds** metadata natively into Office docs, PDFs, images, HTML, code files
- **Detects** 10 security patterns: confidence laundering, authority inflation, classification drift, provenance gaps
- **Audits** against 6 regulatory frameworks (EU AI Act, HIPAA, SOX, GDPR, NIST AI, ISO 42001)
- **Zero overhead** — 0.2ms per stamp, 7KB memory, 0% idle CPU

Works as: Python SDK (`pip install akf`), TypeScript SDK (`npm install akf-format`), CLI, MCP server, LangChain/CrewAI/LlamaIndex integrations, VS Code extension, Office Add-in, GitHub Action.

The daemon (`akf install`) auto-stamps every new file in watched directories and survives reboots. Once installed, every file AI touches gets trust metadata — silently, with zero performance impact.

MIT licensed. Free and open — forever.

- PyPI: https://pypi.org/project/akf/
- npm: https://www.npmjs.com/package/akf-format
- Try it live: [HuggingFace Space] (link)
- Website: https://akf.dev

We built this because we believe trust metadata will be as fundamental to AI content as HTTPS became to the web. Happy to answer any questions about the format, the trust model, or the architecture.
