"""AKF — Enterprise Report: aggregate trust insights across AKF files."""

from __future__ import annotations

import csv
import html as _html
import io
import json
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union


# ---------------------------------------------------------------------------
# Renderer registry — extensible via @register_renderer("name")
# ---------------------------------------------------------------------------

RENDERERS: Dict[str, Callable[["EnterpriseReport"], Union[str, bytes, bytearray]]] = {}


def register_renderer(name: str):
    """Register a custom report renderer.

    Usage::

        from akf.report import register_renderer

        @register_renderer("xml")
        def _xml(report):
            return "<report/>"
    """
    def decorator(fn: Callable[["EnterpriseReport"], Union[str, bytes, bytearray]]):
        RENDERERS[name] = fn
        return fn
    return decorator


@dataclass
class FileReport:
    """Per-file breakdown included in the enterprise report."""

    path: str
    claims: int
    avg_trust: float
    ai_claims: int
    human_claims: int
    security_grade: str
    security_score: float
    compliant: bool
    classification: str
    detections: int
    critical: int
    high: int
    quality_score: float


@dataclass
class EnterpriseReport:
    """Aggregated enterprise trust posture report."""

    generated_at: str
    total_files: int
    total_claims: int
    # Trust
    avg_trust: float
    trust_distribution: dict  # {high: n, moderate: n, low: n}
    # AI/Human
    ai_claims: int
    human_claims: int
    ai_ratio: float
    # Model/Provider tracking
    models_used: dict
    providers_used: dict
    untracked_claims: int
    # Security
    avg_security_score: float
    security_grade: str
    security_distribution: dict  # {"A": n, "B": n, ...}
    # Compliance
    compliance_rate: float
    compliant_files: int
    non_compliant_files: int
    # Classification
    classification_distribution: dict
    # Risk
    total_detections: int
    critical_risks: int
    high_risks: int
    top_risks: list
    # Quality
    avg_quality_score: float
    # Recommendations
    recommendations: list
    # Per-file
    file_reports: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def render(self, format: str = "markdown") -> Union[str, bytes, bytearray]:
        """Render the report in the given format.

        Returns str for text formats, bytes for binary formats (e.g. PDF).
        """
        renderer = RENDERERS.get(format)
        if renderer is None:
            available = ", ".join(sorted(RENDERERS)) or "(none)"
            raise ValueError(
                f"Unknown report format {format!r}. "
                f"Available: {available}. "
                f"Register custom formats with @register_renderer()."
            )
        return renderer(self)


def enterprise_report(
    paths_or_dir: Union[str, Path, List[Union[str, Path]]],
    *,
    format: str = "markdown",
    top: int = 5,
) -> EnterpriseReport:
    """Generate an enterprise-level aggregate report across AKF files.

    Args:
        paths_or_dir: A directory path, a single file, or list of .akf paths.
        format: Output format hint (stored but rendering is via .render()).
        top: Number of top risks to include.

    Returns:
        EnterpriseReport with aggregated metrics.
    """
    from .core import load
    from .trust import effective_trust
    from .data import quality_report
    from .security import security_score
    from .compliance import audit
    from .detection import run_all_detections

    # Resolve paths
    paths = _resolve_paths(paths_or_dir)

    if not paths:
        return _empty_report()

    # Accumulators
    all_trust_scores: list[float] = []
    trust_dist = Counter({"high": 0, "moderate": 0, "low": 0})
    ai_count = 0
    human_count = 0
    models = Counter()
    providers = Counter()
    untracked = 0
    security_scores: list[float] = []
    sec_grade_dist = Counter()
    compliant_count = 0
    non_compliant_count = 0
    class_dist = Counter()
    total_detections = 0
    critical_total = 0
    high_total = 0
    risk_classes = Counter()
    quality_scores: list[float] = []
    all_recommendations: list[str] = []
    file_reports: list[FileReport] = []
    total_claims = 0
    skipped_files: list[str] = []

    for p in paths:
        try:
            unit = load(p)
        except Exception:
            skipped_files.append(str(p))
            continue

        n_claims = len(unit.claims)
        total_claims += n_claims

        # Classification
        label = unit.classification or "unclassified"
        class_dist[label] += 1

        # Trust per claim
        file_trusts = []
        file_ai = 0
        file_human = 0
        for claim in unit.claims:
            try:
                tr = effective_trust(claim)
                score = tr.score
            except Exception:
                score = claim.confidence or 0.0

            all_trust_scores.append(score)
            file_trusts.append(score)

            if score >= 0.7:
                trust_dist["high"] += 1
            elif score >= 0.4:
                trust_dist["moderate"] += 1
            else:
                trust_dist["low"] += 1

            if claim.ai_generated:
                ai_count += 1
                file_ai += 1
            else:
                human_count += 1
                file_human += 1

            # Model/provider from origin
            origin = getattr(claim, "origin", None)
            if origin:
                m = getattr(origin, "model", None)
                prov = getattr(origin, "provider", None)
                if m:
                    models[m] += 1
                if prov:
                    providers[prov] += 1
                if not m and not prov:
                    untracked += 1
            else:
                if claim.ai_generated:
                    untracked += 1


        file_avg_trust = sum(file_trusts) / len(file_trusts) if file_trusts else 0.0

        # Unit-level model (counted once per file, not per claim)
        unit_model = getattr(unit, "model", None)
        if unit_model:
            has_claim_model = any(
                getattr(getattr(c, "origin", None), "model", None)
                for c in unit.claims
            )
            if not has_claim_model:
                models[unit_model] += 1

        # Security
        try:
            sec = security_score(unit)
            sec_score = sec.score
            sec_grade = sec.grade
        except Exception:
            sec_score = 0.0
            sec_grade = "F"
        security_scores.append(sec_score)
        sec_grade_dist[sec_grade] += 1

        # Compliance
        try:
            aud = audit(unit)
            is_compliant = aud.compliant
            all_recommendations.extend(aud.recommendations)
        except Exception:
            is_compliant = False
        if is_compliant:
            compliant_count += 1
        else:
            non_compliant_count += 1

        # Detections
        try:
            det = run_all_detections(unit)
            file_det = det.triggered_count
            file_crit = det.critical_count
            file_high = det.high_count
            total_detections += file_det
            critical_total += file_crit
            high_total += file_high
            for r in det.results:
                if r.triggered:
                    risk_classes[r.detection_class] += 1
        except Exception:
            file_det = 0
            file_crit = 0
            file_high = 0

        # Quality
        try:
            qr = quality_report(unit)
            qs = qr.get("quality_score", 0.0)
        except Exception:
            qs = 0.0
        quality_scores.append(qs)

        file_reports.append(FileReport(
            path=str(p),
            claims=n_claims,
            avg_trust=round(file_avg_trust, 3),
            ai_claims=file_ai,
            human_claims=file_human,
            security_grade=sec_grade,
            security_score=round(sec_score, 1),
            compliant=is_compliant,
            classification=label,
            detections=file_det,
            critical=file_crit,
            high=file_high,
            quality_score=round(qs, 3),
        ))

    # Aggregate
    avg_trust = sum(all_trust_scores) / len(all_trust_scores) if all_trust_scores else 0.0
    avg_sec = sum(security_scores) / len(security_scores) if security_scores else 0.0
    avg_qual = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    total_files = len(file_reports)
    comp_rate = compliant_count / total_files if total_files else 0.0
    ai_ratio = ai_count / total_claims if total_claims else 0.0

    # Overall security grade
    if avg_sec >= 9:
        overall_grade = "A"
    elif avg_sec >= 7:
        overall_grade = "B"
    elif avg_sec >= 5:
        overall_grade = "C"
    elif avg_sec >= 3:
        overall_grade = "D"
    else:
        overall_grade = "F"

    # Top risks
    top_risks = [{"class": cls, "count": cnt} for cls, cnt in risk_classes.most_common(top)]

    # Deduplicate recommendations
    seen = set()
    deduped_recs = []
    for r in all_recommendations:
        if r not in seen:
            seen.add(r)
            deduped_recs.append(r)

    if skipped_files:
        deduped_recs.insert(0, f"{len(skipped_files)} file(s) could not be loaded and were skipped")

    return EnterpriseReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_files=total_files,
        total_claims=total_claims,
        avg_trust=round(avg_trust, 3),
        trust_distribution=dict(trust_dist),
        ai_claims=ai_count,
        human_claims=human_count,
        ai_ratio=round(ai_ratio, 3),
        models_used=dict(models),
        providers_used=dict(providers),
        untracked_claims=untracked,
        avg_security_score=round(avg_sec, 1),
        security_grade=overall_grade,
        security_distribution=dict(sec_grade_dist),
        compliance_rate=round(comp_rate, 3),
        compliant_files=compliant_count,
        non_compliant_files=non_compliant_count,
        classification_distribution=dict(class_dist),
        total_detections=total_detections,
        critical_risks=critical_total,
        high_risks=high_total,
        top_risks=top_risks,
        avg_quality_score=round(avg_qual, 3),
        recommendations=deduped_recs,
        file_reports=file_reports,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_paths(paths_or_dir) -> list[Path]:
    """Normalize input to a list of .akf file paths."""
    if isinstance(paths_or_dir, (str, Path)):
        p = Path(paths_or_dir)
        if p.is_dir():
            return sorted(p.glob("**/*.akf"))
        elif p.is_file() and p.suffix == ".akf":
            return [p]
        return []

    result = []
    for item in paths_or_dir:
        ip = Path(item)
        if ip.is_dir():
            result.extend(sorted(ip.glob("**/*.akf")))
        elif ip.is_file() and ip.suffix == ".akf":
            result.append(ip)
    return result


def _empty_report() -> EnterpriseReport:
    return EnterpriseReport(
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_files=0,
        total_claims=0,
        avg_trust=0.0,
        trust_distribution={"high": 0, "moderate": 0, "low": 0},
        ai_claims=0,
        human_claims=0,
        ai_ratio=0.0,
        models_used={},
        providers_used={},
        untracked_claims=0,
        avg_security_score=0.0,
        security_grade="N/A",
        security_distribution={},
        compliance_rate=0.0,
        compliant_files=0,
        non_compliant_files=0,
        classification_distribution={},
        total_detections=0,
        critical_risks=0,
        high_risks=0,
        top_risks=[],
        avg_quality_score=0.0,
        recommendations=[],
        file_reports=[],
    )


def _bar(value: float, max_val: float, width: int = 20) -> str:
    """Render an ASCII bar chart segment."""
    if max_val <= 0:
        return ""
    filled = min(int(round(value / max_val * width)), width)
    return "\u2588" * filled + "\u2591" * (width - filled)


@register_renderer("json")
def _render_json(report: EnterpriseReport) -> str:
    """Render as JSON."""
    return report.to_json()


@register_renderer("markdown")
def _render_markdown(report: EnterpriseReport) -> str:
    """Render as executive Markdown briefing."""
    lines = [
        "# AI Governance Report",
        "",
        f"*Generated: {report.generated_at}*",
        "",
        "---",
        "",
        "## Overview",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total files | {report.total_files} |",
        f"| Total claims | {report.total_claims} |",
        f"| Average trust | {report.avg_trust:.2f} |",
        f"| Security grade | **{report.security_grade}** ({report.avg_security_score:.1f}/10) |",
        f"| Compliance rate | {report.compliance_rate:.0%} |",
        f"| Quality score | {report.avg_quality_score:.2f} |",
        "",
        "## Trust Distribution",
        "",
    ]

    # Trust bar chart
    td = report.trust_distribution
    max_t = max(td.values()) if td.values() else 1
    lines.append("```")
    lines.append(f"  High     [{_bar(td.get('high', 0), max_t)}] {td.get('high', 0)}")
    lines.append(f"  Moderate [{_bar(td.get('moderate', 0), max_t)}] {td.get('moderate', 0)}")
    lines.append(f"  Low      [{_bar(td.get('low', 0), max_t)}] {td.get('low', 0)}")
    lines.append("```")
    lines.append("")

    # AI vs Human
    lines.append("## AI vs Human Content")
    lines.append("")
    lines.append(f"- AI-generated claims: **{report.ai_claims}** ({report.ai_ratio:.0%})")
    lines.append(f"- Human claims: **{report.human_claims}**")
    if report.untracked_claims > 0:
        lines.append(f"- Untracked (no origin metadata): **{report.untracked_claims}**")
    lines.append("")

    # Model/Provider usage
    if report.models_used:
        lines.append("## Model Usage")
        lines.append("")
        lines.append("| Model | Claims |")
        lines.append("|-------|--------|")
        for model, count in sorted(report.models_used.items(), key=lambda x: -x[1]):
            lines.append(f"| {model} | {count} |")
        lines.append("")

    if report.providers_used:
        lines.append("## Provider Usage")
        lines.append("")
        lines.append("| Provider | Claims |")
        lines.append("|----------|--------|")
        for prov, count in sorted(report.providers_used.items(), key=lambda x: -x[1]):
            lines.append(f"| {prov} | {count} |")
        lines.append("")

    # Security
    lines.append("## Security Posture")
    lines.append("")
    if report.security_distribution:
        lines.append("| Grade | Files |")
        lines.append("|-------|-------|")
        for grade in ["A", "B", "C", "D", "F"]:
            if grade in report.security_distribution:
                lines.append(f"| {grade} | {report.security_distribution[grade]} |")
        lines.append("")

    # Compliance
    lines.append("## Compliance")
    lines.append("")
    lines.append(f"- Compliant: **{report.compliant_files}** / {report.total_files}")
    lines.append(f"- Non-compliant: **{report.non_compliant_files}**")
    lines.append("")

    # Classification
    if report.classification_distribution:
        lines.append("## Classification Distribution")
        lines.append("")
        lines.append("| Label | Files |")
        lines.append("|-------|-------|")
        for label, count in sorted(report.classification_distribution.items(), key=lambda x: -x[1]):
            lines.append(f"| {label} | {count} |")
        lines.append("")

    # Risk
    lines.append("## Risk Summary")
    lines.append("")
    lines.append(f"- Total detections: **{report.total_detections}**")
    lines.append(f"- Critical: **{report.critical_risks}**")
    lines.append(f"- High: **{report.high_risks}**")
    if report.top_risks:
        lines.append("")
        lines.append("**Top Risks:**")
        lines.append("")
        for r in report.top_risks:
            lines.append(f"1. `{r['class']}` ({r['count']} occurrences)")
    lines.append("")

    # Recommendations
    if report.recommendations:
        lines.append("## Recommendations")
        lines.append("")
        for rec in report.recommendations:
            lines.append(f"- {rec}")
        lines.append("")

    # Per-file table
    if report.file_reports:
        lines.append("## Per-File Breakdown")
        lines.append("")
        lines.append("| File | Claims | Trust | Security | Compliant | Detections |")
        lines.append("|------|--------|-------|----------|-----------|------------|")
        for fr in report.file_reports:
            name = Path(fr.path).name
            comp = "Yes" if fr.compliant else "No"
            lines.append(
                f"| {name} | {fr.claims} | {fr.avg_trust:.2f} | "
                f"{fr.security_grade} ({fr.security_score:.0f}) | {comp} | {fr.detections} |"
            )
        lines.append("")

    return "\n".join(lines)


@register_renderer("html")
def _render_html(report: EnterpriseReport) -> str:
    """Render as styled HTML report."""
    # Grade color
    gc = {"A": "#22c55e", "B": "#3b82f6", "C": "#eab308", "D": "#f97316", "F": "#ef4444"}
    grade_color = gc.get(report.security_grade, "#6b7280")

    # Trust distribution for chart
    td = report.trust_distribution
    total_td = sum(td.values()) or 1

    _e = _html.escape

    # File rows
    file_rows = ""
    for fr in report.file_reports:
        name = _e(Path(fr.path).name)
        sc = gc.get(fr.security_grade[0], "#6b7280") if fr.security_grade else "#6b7280"
        comp_badge = '<span style="color:#22c55e">Yes</span>' if fr.compliant else '<span style="color:#ef4444">No</span>'
        file_rows += f"""<tr>
            <td>{name}</td><td>{fr.claims}</td><td>{fr.avg_trust:.2f}</td>
            <td><span style="color:{sc};font-weight:bold">{_e(fr.security_grade)}</span></td>
            <td>{comp_badge}</td><td>{fr.detections}</td>
        </tr>"""

    # Model rows
    model_rows = ""
    for m, c in sorted(report.models_used.items(), key=lambda x: -x[1]):
        model_rows += f"<tr><td>{_e(m)}</td><td>{c}</td></tr>"

    # Risk rows
    risk_rows = ""
    for r in report.top_risks:
        risk_rows += f"<tr><td><code>{_e(r['class'])}</code></td><td>{r['count']}</td></tr>"

    # Recommendation items
    rec_items = "".join(f"<li>{_e(r)}</li>" for r in report.recommendations)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Governance Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 960px; margin: 0 auto; padding: 20px; color: #1f2937; }}
        h1 {{ border-bottom: 2px solid #e5e7eb; padding-bottom: 12px; }}
        h2 {{ color: #374151; margin-top: 32px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin: 20px 0; }}
        .card {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; text-align: center; }}
        .card .value {{ font-size: 2em; font-weight: bold; }}
        .card .label {{ color: #6b7280; font-size: 0.85em; margin-top: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
        th, td {{ padding: 8px 12px; border: 1px solid #e5e7eb; text-align: left; }}
        th {{ background: #f3f4f6; font-weight: 600; }}
        .bar {{ height: 20px; border-radius: 4px; display: inline-block; }}
        .bar-high {{ background: #22c55e; }}
        .bar-mod {{ background: #eab308; }}
        .bar-low {{ background: #ef4444; }}
        .grade {{ font-size: 2.5em; font-weight: bold; color: {grade_color}; }}
        .meta {{ color: #6b7280; font-size: 0.85em; }}
        @media print {{
            body {{ color: #000; max-width: 100%; padding: 0; }}
            .card {{ break-inside: avoid; border: 1px solid #ccc; }}
            .grid {{ break-inside: avoid; }}
            table {{ break-inside: auto; }}
            tr {{ break-inside: avoid; }}
            h2 {{ break-after: avoid; }}
            .bar {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
            .grade {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
        }}
    </style>
</head>
<body>
    <h1>AI Governance Report</h1>
    <p class="meta">Generated: {report.generated_at}</p>

    <div class="grid">
        <div class="card"><div class="value">{report.total_files}</div><div class="label">Files</div></div>
        <div class="card"><div class="value">{report.total_claims}</div><div class="label">Claims</div></div>
        <div class="card"><div class="value">{report.avg_trust:.2f}</div><div class="label">Avg Trust</div></div>
        <div class="card"><div class="grade">{report.security_grade}</div><div class="label">Security ({report.avg_security_score:.1f}/10)</div></div>
        <div class="card"><div class="value">{report.compliance_rate:.0%}</div><div class="label">Compliance</div></div>
        <div class="card"><div class="value">{report.avg_quality_score:.2f}</div><div class="label">Quality</div></div>
    </div>

    <h2>Trust Distribution</h2>
    <div style="margin:12px 0">
        <div style="margin:4px 0">High <span class="bar bar-high" style="width:{td.get('high',0)/total_td*300}px"></span> {td.get('high',0)}</div>
        <div style="margin:4px 0">Moderate <span class="bar bar-mod" style="width:{td.get('moderate',0)/total_td*300}px"></span> {td.get('moderate',0)}</div>
        <div style="margin:4px 0">Low <span class="bar bar-low" style="width:{td.get('low',0)/total_td*300}px"></span> {td.get('low',0)}</div>
    </div>

    <h2>AI vs Human</h2>
    <p>AI-generated: <strong>{report.ai_claims}</strong> ({report.ai_ratio:.0%}) | Human: <strong>{report.human_claims}</strong>{f' | Untracked: <strong>{report.untracked_claims}</strong>' if report.untracked_claims else ''}</p>

    {'<h2>Model Usage</h2><table><tr><th>Model</th><th>Claims</th></tr>' + model_rows + '</table>' if report.models_used else ''}

    <h2>Security Posture</h2>
    <table><tr><th>Grade</th><th>Files</th></tr>
    {''.join(f"<tr><td>{g}</td><td>{report.security_distribution.get(g, 0)}</td></tr>" for g in ["A","B","C","D","F"] if report.security_distribution.get(g))}
    </table>

    <h2>Compliance</h2>
    <p>Compliant: <strong>{report.compliant_files}</strong> / {report.total_files} | Non-compliant: <strong>{report.non_compliant_files}</strong></p>

    <h2>Risk Summary</h2>
    <p>Total: <strong>{report.total_detections}</strong> | Critical: <strong>{report.critical_risks}</strong> | High: <strong>{report.high_risks}</strong></p>
    {'<table><tr><th>Risk Class</th><th>Count</th></tr>' + risk_rows + '</table>' if report.top_risks else ''}

    {'<h2>Recommendations</h2><ul>' + rec_items + '</ul>' if report.recommendations else ''}

    <h2>Per-File Breakdown</h2>
    <table>
        <tr><th>File</th><th>Claims</th><th>Trust</th><th>Security</th><th>Compliant</th><th>Detections</th></tr>
        {file_rows}
    </table>
</body>
</html>"""


@register_renderer("csv")
def _render_csv(report: EnterpriseReport) -> str:
    """Render per-file breakdown as CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "file", "claims", "avg_trust", "ai_claims", "human_claims",
        "security_grade", "security_score", "compliant", "classification",
        "detections", "critical", "high", "quality_score",
    ])
    for fr in report.file_reports:
        writer.writerow([
            fr.path, fr.claims, fr.avg_trust, fr.ai_claims, fr.human_claims,
            fr.security_grade, fr.security_score, fr.compliant, fr.classification,
            fr.detections, fr.critical, fr.high, fr.quality_score,
        ])
    return buf.getvalue()


@register_renderer("pdf")
def _render_pdf(report: EnterpriseReport) -> bytes:
    """Render as PDF using fpdf2 (optional dependency)."""
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError(
            "fpdf2 is required for PDF export: pip install akf[report]"
        )

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "AI Governance Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Generated: {report.generated_at}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # KPI row
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Key Metrics", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    kpis = [
        f"Files: {report.total_files}",
        f"Claims: {report.total_claims}",
        f"Avg Trust: {report.avg_trust:.2f}",
        f"Security: {report.security_grade} ({report.avg_security_score:.1f}/10)",
        f"Compliance: {report.compliance_rate:.0%}",
        f"Quality: {report.avg_quality_score:.2f}",
    ]
    pdf.cell(0, 6, "  |  ".join(kpis), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Trust distribution
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Trust Distribution", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    td = report.trust_distribution
    pdf.cell(0, 6, f"  High: {td.get('high', 0)}  |  Moderate: {td.get('moderate', 0)}  |  Low: {td.get('low', 0)}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # AI vs Human
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "AI vs Human Content", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"  AI: {report.ai_claims} ({report.ai_ratio:.0%})  |  Human: {report.human_claims}  |  Untracked: {report.untracked_claims}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Model usage table
    if report.models_used:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Model Usage", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(95, 6, "Model", border=1)
        pdf.cell(30, 6, "Claims", border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for m, c in sorted(report.models_used.items(), key=lambda x: -x[1]):
            display_m = m if len(m) <= 38 else m[:35] + "..."
            pdf.cell(95, 6, display_m, border=1)
            pdf.cell(30, 6, str(c), border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # Provider usage
    if report.providers_used:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Provider Usage", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(95, 6, "Provider", border=1)
        pdf.cell(30, 6, "Claims", border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for prov, c in sorted(report.providers_used.items(), key=lambda x: -x[1]):
            pdf.cell(95, 6, prov, border=1)
            pdf.cell(30, 6, str(c), border=1, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # Compliance
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Compliance", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"  Compliant: {report.compliant_files} / {report.total_files}  |  Non-compliant: {report.non_compliant_files}  |  Rate: {report.compliance_rate:.0%}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Classification distribution
    if report.classification_distribution:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Classification Distribution", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        parts = [f"{label}: {cnt}" for label, cnt in sorted(report.classification_distribution.items(), key=lambda x: -x[1])]
        pdf.cell(0, 6, "  " + "  |  ".join(parts), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # Risk summary
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Risk Summary", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"  Total: {report.total_detections}  |  Critical: {report.critical_risks}  |  High: {report.high_risks}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Recommendations
    if report.recommendations:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Recommendations", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        for rec in report.recommendations:
            display_rec = rec if len(rec) <= 90 else rec[:87] + "..."
            pdf.cell(0, 5, f"  - {display_rec}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # Per-file table
    if report.file_reports:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, "Per-File Breakdown", new_x="LMARGIN", new_y="NEXT")

        col_w = [55, 18, 18, 22, 22, 22, 18]
        headers = ["File", "Claims", "Trust", "Security", "Compliant", "Detect.", "Quality"]
        pdf.set_font("Helvetica", "B", 8)
        for i, h in enumerate(headers):
            pdf.cell(col_w[i], 5, h, border=1)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for fr in report.file_reports:
            name = Path(fr.path).name
            if len(name) > 22:
                name = name[:19] + "..."
            comp = "Yes" if fr.compliant else "No"
            row = [name, str(fr.claims), f"{fr.avg_trust:.2f}",
                   f"{fr.security_grade} ({fr.security_score:.0f})",
                   comp, str(fr.detections), f"{fr.quality_score:.2f}"]
            for i, val in enumerate(row):
                pdf.cell(col_w[i], 5, val, border=1)
            pdf.ln()

    return pdf.output()
