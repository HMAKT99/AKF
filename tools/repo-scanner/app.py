"""
AI Trust Report Card — Scan any GitHub repo for provenance.
Powered by AKF — The AI Native File Format.
"""

import gradio as gr
import subprocess
import tempfile
import os
import shutil
import json


def scan_repo(repo_url):
    if not repo_url or not repo_url.strip():
        return "Enter a GitHub repo URL.", "", ""

    repo_url = repo_url.strip()
    if not repo_url.startswith("http"):
        repo_url = f"https://github.com/{repo_url}"

    # Clone repo
    tmpdir = tempfile.mkdtemp()
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, tmpdir + "/repo"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return f"Failed to clone: {result.stderr[:200]}", "", ""

        repo_path = tmpdir + "/repo"

        # Count files by type
        file_counts = {}
        total_files = 0
        stamped_files = 0
        unstamped_files = 0

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if f.startswith('.'):
                    continue
                ext = os.path.splitext(f)[1].lower()
                if ext in ['.md', '.yaml', '.yml', '.json', '.py', '.js', '.ts',
                          '.html', '.go', '.rs', '.toml', '.csv', '.docx', '.pdf']:
                    filepath = os.path.join(root, f)
                    file_counts[ext] = file_counts.get(ext, 0) + 1
                    total_files += 1

                    # Check for AKF metadata
                    try:
                        from akf import universal as akf_u
                        meta = akf_u.extract(filepath)
                        if meta:
                            stamped_files += 1
                        else:
                            unstamped_files += 1
                    except Exception:
                        unstamped_files += 1

        # Has CLAUDE.md, AGENTS.md, .cursorrules?
        has_claude = os.path.exists(os.path.join(repo_path, "CLAUDE.md"))
        has_agents = os.path.exists(os.path.join(repo_path, "AGENTS.md"))
        has_cursor = os.path.exists(os.path.join(repo_path, ".cursorrules"))
        has_precommit = os.path.exists(os.path.join(repo_path, ".pre-commit-config.yaml"))

        # Calculate grade
        provenance_pct = (stamped_files / max(total_files, 1)) * 100
        if provenance_pct >= 80:
            grade = "A"
            grade_color = "🟢"
        elif provenance_pct >= 60:
            grade = "B"
            grade_color = "🟢"
        elif provenance_pct >= 40:
            grade = "C"
            grade_color = "🟡"
        elif provenance_pct >= 20:
            grade = "D"
            grade_color = "🟡"
        else:
            grade = "F"
            grade_color = "🔴"

        # Report card
        report = f"# {grade_color} Trust Grade: {grade}\n\n"
        report += f"**{stamped_files}/{total_files}** files carry provenance metadata ({provenance_pct:.0f}%)\n\n"
        report += "## File Breakdown\n\n"
        report += "| Format | Count |\n|--------|-------|\n"
        for ext, count in sorted(file_counts.items(), key=lambda x: -x[1]):
            report += f"| {ext} | {count} |\n"

        # Agent readiness
        agent_report = "## Agent Readiness\n\n"
        agent_report += f"{'✅' if has_claude else '❌'} CLAUDE.md (Claude Code)\n"
        agent_report += f"{'✅' if has_agents else '❌'} AGENTS.md (Codex/Copilot)\n"
        agent_report += f"{'✅' if has_cursor else '❌'} .cursorrules (Cursor)\n"
        agent_report += f"{'✅' if has_precommit else '❌'} .pre-commit-config.yaml\n"

        # Compliance
        compliance = "## EU AI Act Readiness\n\n"
        if provenance_pct >= 80:
            compliance += "✅ **LIKELY COMPLIANT** — Most files carry transparency metadata.\n"
        elif provenance_pct >= 40:
            compliance += "⚠️ **PARTIALLY COMPLIANT** — Some files need provenance.\n"
        else:
            compliance += "❌ **NOT COMPLIANT** — AI-generated files lack required transparency metadata.\n"
        compliance += f"\n*EU AI Act Article 50 takes effect August 2, 2026.*\n\n"
        compliance += "**Fix it:**\n```bash\npip install akf\nakf scan . --stamp --agent your-name\n```\n"

        # Badge
        badge_url = f"https://img.shields.io/badge/Trust_Grade-{grade}-{'green' if grade in 'AB' else 'yellow' if grade in 'CD' else 'red'}?style=flat-square"
        compliance += f"\n**Add this badge to your README:**\n"
        compliance += f"```markdown\n![Trust Grade](/{badge_url})\n```\n"

        return report, agent_report, compliance

    except subprocess.TimeoutExpired:
        return "Clone timed out — repo may be too large.", "", ""
    except Exception as e:
        return f"Error: {e}", "", ""
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


with gr.Blocks(
    title="AI Trust Report Card — AKF Repo Scanner",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown("""
    # 📊 AI Trust Report Card
    ### Enter any GitHub repo — get a trust score instantly.
    *How much of your codebase carries AI provenance?*

    *Powered by [AKF — The AI Native File Format](https://akf.dev)*
    """)

    with gr.Row():
        repo_input = gr.Textbox(
            label="GitHub Repo URL",
            placeholder="https://github.com/owner/repo or owner/repo",
            scale=4
        )
        scan_btn = gr.Button("Scan", variant="primary", scale=1)

    with gr.Row():
        report_out = gr.Markdown(label="Trust Report")
        agent_out = gr.Markdown(label="Agent Readiness")
        compliance_out = gr.Markdown(label="Compliance")

    scan_btn.click(scan_repo, inputs=repo_input, outputs=[report_out, agent_out, compliance_out])

    gr.Markdown("""
    ---
    **Improve your score:**
    ```bash
    pip install akf
    akf scan . --stamp --agent your-team --evidence "code reviewed"
    akf audit . --regulation eu_ai_act
    ```
    [akf.dev](https://akf.dev) · [GitHub](https://github.com/HMAKT99/AKF)
    """)

demo.launch()
