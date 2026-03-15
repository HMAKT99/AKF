# Twitter/X Launch Thread

---

## Tweet 1 (Hook)

Every photo has EXIF — who took it, when, what camera.

Every AI output has... nothing.

No confidence score. No source. No way to tell if it came from a verified SEC filing or a hallucination.

We built AKF to fix that. Here's what it does 🧵

---

## Tweet 2 (The Problem)

AI agents are writing financial reports, legal memos, medical summaries.

But there's zero metadata attached to any of it.

A claim with 0.95 confidence from an expert source looks identical to a speculative guess from an unverified model.

That's insane.

---

## Tweet 3 (The Solution)

AKF = Agent Knowledge Format.

~15 tokens of JSON that travel with every AI output:

→ Trust score (how much should you trust this?)
→ Source provenance (where did it come from?)
→ Security classification (who can see it?)

Think EXIF, but for AI.

---

## Tweet 4 (Code — keep it simple)

```python
import akf

akf.stamp(
    "Revenue was $4.2B, up 12% YoY",
    confidence=0.98,
    source="SEC 10-Q",
    model="gpt-4o"
)
```

That's it. One function call. 0.2ms. 7KB memory.

Works with DOCX, PDF, Excel, images, code, HTML — 20+ formats.

---

## Tweet 5 (Security Detections)

AKF also catches bad actors:

→ Confidence laundering (low-confidence claim presented as certain)
→ Authority inflation (Tier 5 speculation stamped as Tier 1 expert)
→ Classification drift (confidential data leaking to public docs)

10 detection classes. Built-in.

---

## Tweet 6 (The Daemon)

One command:

```
akf install
```

Now every file AI touches on your machine gets trust metadata. Automatically. Survives reboots.

0% idle CPU. Zero performance impact.

---

## Tweet 7 (Integrations)

Works with the tools you already use:

→ LangChain
→ CrewAI
→ LlamaIndex
→ Claude (MCP server)
→ VS Code
→ Office (Word/Excel/PowerPoint)
→ Google Workspace
→ GitHub Actions

pip install akf
npm install akf-format

---

## Tweet 8 (Why It Matters)

By 2028, the EU AI Act will require provenance metadata on high-risk AI outputs.

Insurance companies will require trust scores for AI liability coverage.

The question isn't IF trust metadata becomes mandatory.

It's which format becomes the standard.

---

## Tweet 9 (CTA)

AKF is MIT licensed. Free and open — forever.

Try it:
→ pip install akf
→ npm install akf-format
→ Live demo: [HuggingFace Space]
→ Website: akf.dev

If AI generated it, AKF should stamp it.

---

## Tweet 10 (Tag / Amplify)

Tagging people who should care about this:

@LangChainAI @llaboratory @AndrewYNg @kaboroevich @jerryjliu0 @jobergum @hardmaru

If you're building with AI agents, your outputs need trust metadata.

EXIF took 30 years. AKF ships today.

---

# NOTES FOR POSTING

- Post Tweet 1 as standalone. Wait for engagement. Thread the rest as replies.
- Tweet 4 (code) will get the most developer engagement — the code block renders well on X.
- Tweet 10 tags should be updated to real handles of people you want to reach.
- Add a screenshot of `akf quickstart` terminal output or the HuggingFace Space as media on Tweet 1.
- Best posting times: Tuesday–Thursday, 9am–11am PST (peak dev Twitter).
- Cross-post the hook tweet (Tweet 1) to LinkedIn with a longer-form version.
