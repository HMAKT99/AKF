"""
EU AI Act Compliance Check — Paste any AI content, get a compliance report.
Powered by AKF — The AI Native File Format.
"""

import gradio as gr
import json
from datetime import datetime, timezone

try:
    from akf.compliance import check_regulation
    from akf.models import AKF, Claim
    from akf import stamp as akf_stamp
    AKF_AVAILABLE = True
except ImportError:
    AKF_AVAILABLE = False


REGULATIONS = {
    "EU AI Act (Article 50)": "eu_ai_act",
    "SOX (Financial)": "sox",
    "HIPAA (Healthcare)": "hipaa",
    "GDPR (Data Privacy)": "gdpr",
    "NIST AI RMF": "nist_ai",
    "ISO 42001": "iso_42001",
}


def days_until_deadline():
    deadline = datetime(2026, 8, 2, tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return max(0, (deadline - now).days)


def check_compliance(text, regulation, is_ai_generated, agent_name, source_description):
    if not text or not text.strip():
        return "Enter content to check.", "", ""

    reg_key = REGULATIONS.get(regulation, "eu_ai_act")

    # Create AKF unit from the content
    confidence = 0.30 if is_ai_generated else 0.70
    tier = 5 if is_ai_generated else 3

    claims = [{
        "c": text[:100] + ("..." if len(text) > 100 else ""),
        "t": confidence,
        "src": source_description or ("AI inference" if is_ai_generated else "human authored"),
        "tier": tier,
        "ai": is_ai_generated,
        "ver": not is_ai_generated,
    }]

    meta = {
        "v": "1.0",
        "claims": claims,
        "agent": agent_name or ("ai-agent" if is_ai_generated else "human"),
        "at": datetime.now(timezone.utc).isoformat(),
        "label": "internal",
    }

    # Run compliance check
    compliance_report = f"# {regulation} Compliance Report\n\n"
    compliance_report += f"**📅 Days until deadline: {days_until_deadline()}**\n\n"

    if AKF_AVAILABLE:
        try:
            unit = AKF(**meta)
            result = check_regulation(unit, reg_key)

            if result.compliant:
                compliance_report += "## ✅ COMPLIANT\n\n"
                compliance_report += f"Score: **{result.score:.0%}**\n\n"
            else:
                compliance_report += "## ❌ NON-COMPLIANT\n\n"
                compliance_report += f"Score: **{result.score:.0%}**\n\n"

            compliance_report += "### Checks\n\n"
            for check in result.checks:
                icon = "✅" if check["passed"] else "❌"
                compliance_report += f"{icon} {check['check']}\n"

            if result.recommendations:
                compliance_report += "\n### Recommendations\n\n"
                for rec in result.recommendations:
                    compliance_report += f"- {rec}\n"
        except Exception as e:
            compliance_report += f"Error running check: {e}\n"
    else:
        # Fallback without akf installed
        compliance_report += "## ⚠️ Manual Assessment\n\n"
        checks = {
            "eu_ai_act": [
                ("AI-generated disclosure", is_ai_generated and agent_name),
                ("Human oversight marker", not is_ai_generated or source_description),
                ("Transparency metadata present", bool(agent_name and source_description)),
                ("Source traceability", bool(source_description)),
            ],
            "sox": [
                ("Integrity controls", False),
                ("Audit trail", bool(agent_name)),
                ("Classification", True),
            ],
            "hipaa": [
                ("Access control metadata", False),
                ("Data integrity", bool(source_description)),
                ("Audit logging", bool(agent_name)),
            ],
        }
        for name, passed in checks.get(reg_key, checks["eu_ai_act"]):
            icon = "✅" if passed else "❌"
            compliance_report += f"{icon} {name}\n"

    # What's missing
    gaps = "## What's Missing\n\n"
    if not agent_name:
        gaps += "❌ **Agent identity** — who/what generated this content?\n"
    if not source_description:
        gaps += "❌ **Source provenance** — what sources were used?\n"
    if is_ai_generated and not source_description:
        gaps += "❌ **Evidence chain** — no verifiable sources referenced\n"
    if not is_ai_generated:
        gaps += "✅ Human-authored content has lower compliance requirements\n"

    gaps += "\n### Fix it\n"
    gaps += "```bash\npip install akf\n"
    gaps += f'akf stamp your-file --agent "{agent_name or "your-agent"}" --evidence "{source_description or "your sources"}"\n'
    gaps += f"akf audit your-file --regulation {reg_key}\n```\n"

    # Shareable metadata
    shareable = "## Provenance Metadata\n\n"
    shareable += "This is what the compliance metadata looks like:\n\n"
    shareable += "```json\n"
    shareable += json.dumps(meta, indent=2, default=str)
    shareable += "\n```\n\n"
    shareable += f"~{len(json.dumps(meta))} characters of JSON — embeds into any file format.\n"

    return compliance_report, gaps, shareable


with gr.Blocks(
    title="EU AI Act Compliance Check — AKF",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown(f"""
    # 🇪🇺 EU AI Act Compliance Check
    ### Is your AI content compliant? Check in 5 seconds.
    **⏰ {days_until_deadline()} days until Article 50 takes effect (August 2, 2026)**

    *Powered by [AKF — The AI Native File Format](https://akf.dev)*
    """)

    with gr.Row():
        with gr.Column(scale=3):
            text_input = gr.Textbox(
                label="Paste AI-generated content",
                lines=6,
                placeholder="Paste any text, report, code, or document content here..."
            )
        with gr.Column(scale=1):
            regulation = gr.Dropdown(
                choices=list(REGULATIONS.keys()),
                value="EU AI Act (Article 50)",
                label="Regulation"
            )
            is_ai = gr.Checkbox(label="AI-generated?", value=True)
            agent = gr.Textbox(label="Agent/model name", placeholder="claude, gpt-4, etc.")
            source = gr.Textbox(label="Source description", placeholder="SEC filing, internal data, etc.")

    check_btn = gr.Button("Check Compliance", variant="primary", size="lg")

    with gr.Row():
        report_out = gr.Markdown(label="Compliance Report")
        gaps_out = gr.Markdown(label="Gaps")
        meta_out = gr.Markdown(label="Metadata")

    check_btn.click(
        check_compliance,
        inputs=[text_input, regulation, is_ai, agent, source],
        outputs=[report_out, gaps_out, meta_out]
    )

    gr.Markdown("""
    ---
    ### Supported Regulations
    | Regulation | Deadline | Penalty |
    |-----------|----------|---------|
    | EU AI Act Article 50 | August 2, 2026 | €35M / 7% turnover |
    | Colorado SB 205 | June 30, 2026 | State enforcement |
    | SOX | Active | Criminal penalties |
    | HIPAA | Active | $50K per violation |
    | GDPR | Active | €20M / 4% turnover |

    [akf.dev](https://akf.dev) · [GitHub](https://github.com/HMAKT99/AKF) · `pip install akf`
    """)

demo.launch()
