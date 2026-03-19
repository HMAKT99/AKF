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
    """Render as professional, executive-ready HTML report."""
    gc = {"A": "#22c55e", "B": "#3b82f6", "C": "#eab308", "D": "#f97316", "F": "#ef4444"}
    grade_color = gc.get(report.security_grade, "#6b7280")

    td = report.trust_distribution
    total_td = sum(td.values()) or 1
    high_pct = round(td.get("high", 0) / total_td * 100)
    mod_pct = round(td.get("moderate", 0) / total_td * 100)
    low_pct = round(td.get("low", 0) / total_td * 100)

    _e = _html.escape

    # KPI card color helpers
    def _trust_color(v):
        if v >= 0.7:
            return "#22c55e"
        if v >= 0.4:
            return "#eab308"
        return "#ef4444"

    def _compliance_color(v):
        if v >= 0.8:
            return "#22c55e"
        if v >= 0.5:
            return "#eab308"
        return "#ef4444"

    # File rows
    file_rows = ""
    for fr in report.file_reports:
        name = _e(Path(fr.path).name)
        tc = _trust_color(fr.avg_trust)
        sc = gc.get(fr.security_grade[0], "#6b7280") if fr.security_grade else "#6b7280"
        comp_badge = ('<span style="background:#dcfce7;color:#166534;padding:2px 8px;'
                      'border-radius:9999px;font-size:0.8em">Compliant</span>' if fr.compliant
                      else '<span style="background:#fef2f2;color:#991b1b;padding:2px 8px;'
                      'border-radius:9999px;font-size:0.8em">Non-compliant</span>')
        file_rows += (
            f'<tr><td style="font-weight:500">{name}</td><td>{fr.claims}</td>'
            f'<td style="color:{tc};font-weight:600">{fr.avg_trust:.2f}</td>'
            f'<td><span style="color:{sc};font-weight:700">{_e(fr.security_grade)}</span>'
            f' <span style="color:#6b7280;font-size:0.85em">({fr.security_score:.0f})</span></td>'
            f'<td>{comp_badge}</td><td>{fr.detections}</td>'
            f'<td>{fr.quality_score:.2f}</td></tr>'
        )

    # Model rows
    model_rows = ""
    for m, c in sorted(report.models_used.items(), key=lambda x: -x[1]):
        model_rows += f"<tr><td>{_e(m)}</td><td>{c}</td></tr>"

    # Risk rows
    risk_rows = ""
    for r in report.top_risks:
        risk_rows += (
            f'<tr><td><code style="background:#f1f5f9;padding:2px 6px;border-radius:4px">'
            f'{_e(r["class"])}</code></td><td>{r["count"]}</td></tr>'
        )

    # Recommendation items
    rec_items = "".join(
        f'<li style="margin:6px 0;padding:8px 12px;background:#f0f9ff;border-left:3px solid #3b82f6;'
        f'border-radius:0 4px 4px 0">{_e(r)}</li>' for r in report.recommendations
    )

    # Security grade badges
    grade_badges = ""
    for g in ["A", "B", "C", "D", "F"]:
        cnt = report.security_distribution.get(g, 0)
        if cnt:
            bg = gc.get(g, "#6b7280")
            grade_badges += (
                f'<span style="display:inline-block;background:{bg};color:#fff;'
                f'padding:4px 12px;border-radius:9999px;margin:0 4px;font-weight:600">'
                f'{g}: {cnt}</span>'
            )

    # AI vs Human bar
    ai_total = report.ai_claims + report.human_claims
    ai_pct = round(report.ai_claims / ai_total * 100) if ai_total else 0
    human_pct = 100 - ai_pct

    # Compliance bar
    comp_total = report.compliant_files + report.non_compliant_files
    comp_pct = round(report.compliant_files / comp_total * 100) if comp_total else 0

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AKF Trust Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
               background: #f8fafc; color: #1e293b; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
                   color: #fff; padding: 32px 40px; }}
        .header h1 {{ font-size: 1.75em; font-weight: 700; letter-spacing: -0.02em; }}
        .header .subtitle {{ color: #94a3b8; font-size: 0.9em; margin-top: 4px; }}
        .container {{ max-width: 1000px; margin: 0 auto; padding: 24px 40px 48px; }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px;
                     margin: -40px 0 32px; position: relative; z-index: 1; }}
        .kpi {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
                padding: 20px 16px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }}
        .kpi .val {{ font-size: 1.8em; font-weight: 700; line-height: 1.2; }}
        .kpi .lbl {{ color: #64748b; font-size: 0.8em; margin-top: 4px; text-transform: uppercase;
                     letter-spacing: 0.05em; }}
        details {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
                   margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
        summary {{ padding: 16px 20px; font-weight: 600; font-size: 1.05em; cursor: pointer;
                   list-style: none; display: flex; align-items: center; gap: 8px; }}
        summary::-webkit-details-marker {{ display: none; }}
        summary::before {{ content: "\\25B6"; font-size: 0.7em; color: #94a3b8;
                          transition: transform 0.2s; }}
        details[open] summary::before {{ transform: rotate(90deg); }}
        .section-body {{ padding: 0 20px 20px; }}
        .stacked-bar {{ display: flex; height: 28px; border-radius: 6px; overflow: hidden;
                        margin: 8px 0; }}
        .stacked-bar span {{ display: flex; align-items: center; justify-content: center;
                            font-size: 0.75em; font-weight: 600; color: #fff;
                            min-width: 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 8px 0; font-size: 0.9em; }}
        th {{ background: #f8fafc; padding: 10px 12px; text-align: left; font-weight: 600;
              color: #475569; border-bottom: 2px solid #e2e8f0; font-size: 0.85em;
              text-transform: uppercase; letter-spacing: 0.04em; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; }}
        tr:hover td {{ background: #f8fafc; }}
        .bar-label {{ display: flex; justify-content: space-between; font-size: 0.85em;
                      color: #64748b; margin-top: 4px; }}
        .rec-list {{ list-style: none; padding: 0; }}
        .footer {{ text-align: center; color: #94a3b8; font-size: 0.8em; margin-top: 40px;
                   padding-top: 20px; border-top: 1px solid #e2e8f0; }}
        .footer a {{ color: #3b82f6; text-decoration: none; }}
        @media print {{
            body {{ background: #fff; }}
            .header {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
            .kpi-grid {{ margin-top: 16px; }}
            .kpi, details {{ box-shadow: none; border: 1px solid #d1d5db; }}
            details {{ break-inside: avoid; }}
            details[open] {{ break-inside: auto; }}
            summary {{ break-after: avoid; }}
            table {{ break-inside: auto; font-size: 0.8em; }}
            tr {{ break-inside: avoid; }}
            .stacked-bar span {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
            .footer {{ break-before: avoid; }}
        }}
        @media (max-width: 768px) {{
            .kpi-grid {{ grid-template-columns: repeat(3, 1fr); }}
            .container {{ padding: 16px 20px 32px; }}
            .header {{ padding: 24px 20px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>AKF Trust Report</h1>
        <div class="subtitle">Generated {report.generated_at} &middot; {report.total_files} files &middot; {report.total_claims} claims</div>
    </div>

    <div class="container">
        <div class="kpi-grid">
            <div class="kpi"><div class="val">{report.total_files}</div><div class="lbl">Files</div></div>
            <div class="kpi"><div class="val">{report.total_claims}</div><div class="lbl">Claims</div></div>
            <div class="kpi"><div class="val" style="color:{_trust_color(report.avg_trust)}">{report.avg_trust:.2f}</div><div class="lbl">Avg Trust</div></div>
            <div class="kpi"><div class="val" style="color:{grade_color};font-size:2.2em">{report.security_grade}</div><div class="lbl">Security ({report.avg_security_score:.1f}/10)</div></div>
            <div class="kpi"><div class="val" style="color:{_compliance_color(report.compliance_rate)}">{report.compliance_rate:.0%}</div><div class="lbl">Compliance</div></div>
            <div class="kpi"><div class="val">{report.avg_quality_score:.2f}</div><div class="lbl">Quality</div></div>
        </div>

        <details open>
            <summary>Trust Distribution</summary>
            <div class="section-body">
                <div class="stacked-bar">
                    <span style="width:{high_pct}%;background:#22c55e">{high_pct}%</span>
                    <span style="width:{mod_pct}%;background:#eab308">{mod_pct}%</span>
                    <span style="width:{low_pct}%;background:#ef4444">{low_pct}%</span>
                </div>
                <div class="bar-label">
                    <span>High: {td.get('high', 0)}</span>
                    <span>Moderate: {td.get('moderate', 0)}</span>
                    <span>Low: {td.get('low', 0)}</span>
                </div>
            </div>
        </details>

        <details>
            <summary>AI vs Human Breakdown</summary>
            <div class="section-body">
                <div class="stacked-bar">
                    <span style="width:{ai_pct}%;background:#3b82f6">{ai_pct}% AI</span>
                    <span style="width:{human_pct}%;background:#8b5cf6">{human_pct}% Human</span>
                </div>
                <div class="bar-label">
                    <span>AI: {report.ai_claims}</span>
                    <span>Human: {report.human_claims}</span>
                    {f'<span>Untracked: {report.untracked_claims}</span>' if report.untracked_claims else ''}
                </div>
                {('<p style="margin-top:12px;font-size:0.9em"><strong>Models:</strong> ' + ', '.join(f'{_e(m)} ({c})' for m, c in sorted(report.models_used.items(), key=lambda x: -x[1])) + '</p>') if report.models_used else ''}
            </div>
        </details>

        <details>
            <summary>Security Posture</summary>
            <div class="section-body">
                <p style="margin-bottom:12px">{grade_badges}</p>
            </div>
        </details>

        <details>
            <summary>Compliance</summary>
            <div class="section-body">
                <div class="stacked-bar" style="height:22px">
                    <span style="width:{comp_pct}%;background:#22c55e">{report.compliant_files} compliant</span>
                    <span style="width:{100 - comp_pct}%;background:#ef4444">{report.non_compliant_files} non-compliant</span>
                </div>
            </div>
        </details>

        {'<details><summary>Risk Summary</summary><div class="section-body">' +
         f'<p style="margin-bottom:8px">Total: <strong>{report.total_detections}</strong> &middot; Critical: <strong>{report.critical_risks}</strong> &middot; High: <strong>{report.high_risks}</strong></p>' +
         ('<table><tr><th>Risk Class</th><th>Count</th></tr>' + risk_rows + '</table>' if report.top_risks else '') +
         '</div></details>' if report.total_detections else ''}

        {'<details><summary>Recommendations</summary><div class="section-body"><ul class="rec-list">' + rec_items + '</ul></div></details>' if report.recommendations else ''}

        <details>
            <summary>Per-File Breakdown ({report.total_files} files)</summary>
            <div class="section-body">
                <table>
                    <tr><th>File</th><th>Claims</th><th>Trust</th><th>Security</th><th>Status</th><th>Detections</th><th>Quality</th></tr>
                    {file_rows}
                </table>
            </div>
        </details>

        <div class="footer">Generated by AKF v1.1 &mdash; <a href="https://akf.dev">akf.dev</a></div>
    </div>
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
