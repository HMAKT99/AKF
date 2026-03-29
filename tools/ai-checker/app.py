"""
Is This AI-Generated? — Drop any file, get a trust report.
Powered by AKF — The AI Native File Format.
"""

import gradio as gr
import json
import tempfile
import os

# Try importing akf
try:
    from akf import universal as akf_u
    from akf.detection import detect_all
    from akf.trust import effective_trust
    from akf.models import AKF, Claim
    AKF_AVAILABLE = True
except ImportError:
    AKF_AVAILABLE = False


def analyze_file(file):
    if file is None:
        return "Upload a file to analyze.", "", ""

    filepath = file.name if hasattr(file, 'name') else str(file)

    # 1. Check for existing AKF metadata
    metadata_report = "## Existing Provenance\n\n"
    meta = None
    if AKF_AVAILABLE:
        try:
            meta = akf_u.extract(filepath)
        except Exception:
            meta = None

    if meta:
        metadata_report += "**✅ This file carries AKF trust metadata:**\n\n"
        claims = meta.get("claims", [])
        agent = meta.get("agent", "unknown")
        timestamp = meta.get("at", "unknown")
        label = meta.get("label", meta.get("classification", "unknown"))
        integrity = meta.get("hash", "none")

        metadata_report += f"- **Agent:** {agent}\n"
        metadata_report += f"- **Stamped:** {timestamp}\n"
        metadata_report += f"- **Classification:** {label}\n"
        metadata_report += f"- **Integrity hash:** {integrity}\n"
        metadata_report += f"- **Claims:** {len(claims)}\n\n"

        for i, claim in enumerate(claims):
            c = claim.get("c", claim.get("content", ""))
            t = claim.get("t", claim.get("confidence", 0))
            src = claim.get("src", claim.get("source", "unspecified"))
            ai = claim.get("ai", claim.get("ai_generated", False))
            tier = claim.get("tier", claim.get("authority_tier", "?"))

            icon = "🟢" if t >= 0.8 else "🟡" if t >= 0.5 else "🔴"
            metadata_report += f"{icon} **Claim {i+1}:** {c}\n"
            metadata_report += f"   Trust: {t:.2f} | Source: {src} | Tier: {tier} | AI: {'Yes' if ai else 'No'}\n\n"
    else:
        metadata_report += "**❌ No provenance metadata found.**\n\n"
        metadata_report += "This file carries no record of who created it, "
        metadata_report += "what model was used, or whether it was verified.\n\n"
        metadata_report += "*EU AI Act Article 50 (Aug 2, 2026) will require transparency metadata on AI-generated content.*\n"

    # 2. Run security detections
    detection_report = "## Security Detections\n\n"
    if AKF_AVAILABLE and meta:
        try:
            unit = AKF(**meta)
            results = detect_all(unit)
            passed = sum(1 for r in results if r.passed)
            total = len(results)
            grade = "A" if passed >= 9 else "B" if passed >= 7 else "C" if passed >= 5 else "D" if passed >= 3 else "F"

            detection_report += f"**Security Grade: {grade}** ({passed}/{total} checks passed)\n\n"
            for r in results:
                icon = "✅" if r.passed else "❌"
                detection_report += f"{icon} {r.name}\n"
        except Exception as e:
            detection_report += f"Could not run detections: {e}\n"
    else:
        detection_report += "No metadata to analyze. Stamp the file first:\n\n"
        detection_report += "```bash\npip install akf\nakf stamp your-file --agent your-name --evidence 'your sources'\n```\n"

    # 3. Trust summary
    trust_summary = "## Trust Summary\n\n"
    if meta and meta.get("claims"):
        scores = [c.get("t", c.get("confidence", 0)) for c in meta["claims"]]
        avg = sum(scores) / len(scores) if scores else 0
        ai_claims = sum(1 for c in meta["claims"] if c.get("ai", c.get("ai_generated", False)))

        if avg >= 0.8:
            trust_summary += "🟢 **HIGH TRUST** — This content has strong provenance.\n"
        elif avg >= 0.5:
            trust_summary += "🟡 **MODERATE TRUST** — Some claims need verification.\n"
        else:
            trust_summary += "🔴 **LOW TRUST** — This content needs human review.\n"

        trust_summary += f"\n- Average trust score: **{avg:.2f}**\n"
        trust_summary += f"- AI-generated claims: **{ai_claims}/{len(scores)}**\n"
    else:
        trust_summary += "⚠️ **UNKNOWN** — No trust metadata present.\n\n"
        trust_summary += "Without provenance, there's no way to verify this content's origin.\n"

    return metadata_report, detection_report, trust_summary


def analyze_text(text):
    if not text or not text.strip():
        return "Enter text to analyze.", "", ""

    # Write to temp file and analyze
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(text)
        filepath = f.name

    # Check basic AI signals
    metadata_report = "## Text Analysis\n\n"
    metadata_report += "**❌ No provenance metadata found in plain text.**\n\n"
    metadata_report += "Plain text carries no embedded provenance. "
    metadata_report += "To add trust metadata:\n\n"
    metadata_report += "```bash\npip install akf\n"
    metadata_report += "echo 'your text' > output.md\n"
    metadata_report += "akf stamp output.md --agent your-name --evidence 'your sources'\n```\n"

    detection_report = "## AI Content Signals\n\n"
    word_count = len(text.split())
    avg_word_len = sum(len(w) for w in text.split()) / max(word_count, 1)
    sentence_count = text.count('.') + text.count('!') + text.count('?')
    avg_sent_len = word_count / max(sentence_count, 1)

    detection_report += f"- **Word count:** {word_count}\n"
    detection_report += f"- **Avg word length:** {avg_word_len:.1f} chars\n"
    detection_report += f"- **Avg sentence length:** {avg_sent_len:.1f} words\n\n"
    detection_report += "*Note: Text-based AI detection is unreliable. "
    detection_report += "Provenance metadata is the only reliable signal.*\n"

    trust_summary = "## Verdict\n\n"
    trust_summary += "⚠️ **Cannot determine origin without provenance metadata.**\n\n"
    trust_summary += "AKF solves this — every file carries its origin story.\n\n"
    trust_summary += "EU AI Act Article 50 takes effect **August 2, 2026**.\n"

    os.unlink(filepath)
    return metadata_report, detection_report, trust_summary


with gr.Blocks(
    title="Is This AI-Generated? — AKF Trust Checker",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown("""
    # 🛡️ Is This AI-Generated?
    ### Drop any file or paste text — get a trust report instantly.
    *Powered by [AKF — The AI Native File Format](https://akf.dev)*
    """)

    with gr.Tabs():
        with gr.Tab("📄 Check a File"):
            file_input = gr.File(label="Upload any file (PDF, DOCX, images, code, markdown...)")
            check_btn = gr.Button("Analyze", variant="primary")
            with gr.Row():
                meta_out = gr.Markdown(label="Provenance")
                detect_out = gr.Markdown(label="Security")
                trust_out = gr.Markdown(label="Trust")
            check_btn.click(analyze_file, inputs=file_input, outputs=[meta_out, detect_out, trust_out])

        with gr.Tab("📝 Check Text"):
            text_input = gr.Textbox(label="Paste any text", lines=8, placeholder="Paste AI-generated text here...")
            check_text_btn = gr.Button("Analyze", variant="primary")
            with gr.Row():
                meta_out2 = gr.Markdown(label="Provenance")
                detect_out2 = gr.Markdown(label="Signals")
                trust_out2 = gr.Markdown(label="Verdict")
            check_text_btn.click(analyze_text, inputs=text_input, outputs=[meta_out2, detect_out2, trust_out2])

    gr.Markdown("""
    ---
    **How to add provenance to your files:**
    ```bash
    pip install akf
    akf stamp your-file --agent your-name --evidence "your sources"
    akf audit your-file --regulation eu_ai_act
    ```
    [akf.dev](https://akf.dev) · [GitHub](https://github.com/HMAKT99/AKF) · [npm](https://www.npmjs.com/package/akf-format)
    """)

demo.launch()
