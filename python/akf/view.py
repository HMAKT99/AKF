"""AKF v1.0 — View and display utilities.

Pretty-print, HTML, Markdown, and executive summary outputs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

from .core import load, loads
from .models import AKF
from .trust import effective_trust


def _resolve(target: Union[str, Path, AKF]) -> AKF:
    """Resolve target to an AKF unit."""
    if isinstance(target, AKF):
        return target
    path = Path(target)
    if path.exists():
        return load(path)
    return loads(str(target))


def show(target: Union[str, Path, AKF]) -> None:
    """Pretty-print an AKF unit to the terminal."""
    unit = _resolve(target)
    print(unit.inspect())


def to_html(target: Union[str, Path, AKF]) -> str:
    """Generate standalone HTML with trust badges.

    Args:
        target: AKF unit, file path, or JSON string.

    Returns:
        Complete HTML document string.
    """
    unit = _resolve(target)

    claims_html = []
    for claim in unit.claims:
        result = effective_trust(claim)
        if result.score >= 0.7:
            badge_color = "#22c55e"
            badge_text = "HIGH"
        elif result.score >= 0.4:
            badge_color = "#eab308"
            badge_text = "MED"
        else:
            badge_color = "#ef4444"
            badge_text = "LOW"

        ai_badge = ""
        if claim.ai_generated:
            ai_badge = ' <span style="background:#6366f1;color:white;padding:2px 6px;border-radius:4px;font-size:0.75em">AI</span>'

        verified_badge = ""
        if claim.verified:
            verified_badge = ' <span style="background:#22c55e;color:white;padding:2px 6px;border-radius:4px;font-size:0.75em">Verified</span>'

        source_str = ""
        if claim.source and claim.source != "unspecified":
            source_str = f'<div style="color:#6b7280;font-size:0.85em">Source: {claim.source}</div>'

        claims_html.append(f'''
        <div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin:8px 0">
            <div style="display:flex;align-items:center;gap:8px">
                <span style="background:{badge_color};color:white;padding:2px 8px;border-radius:4px;font-size:0.85em;font-weight:bold">{badge_text} {claim.confidence:.2f}</span>
                {ai_badge}{verified_badge}
            </div>
            <div style="margin-top:8px">{claim.content}</div>
            {source_str}
        </div>''')

    class_badge = ""
    if unit.classification:
        class_colors = {
            "public": "#22c55e", "internal": "#3b82f6",
            "confidential": "#f59e0b", "highly-confidential": "#ef4444",
            "restricted": "#dc2626",
        }
        cc = class_colors.get(unit.classification, "#6b7280")
        class_badge = f'<span style="background:{cc};color:white;padding:4px 12px;border-radius:4px">{unit.classification}</span>'

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AKF: {unit.id}</title>
    <style>body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}</style>
</head>
<body>
    <h1>AKF {unit.version} <small style="color:#6b7280">{unit.id}</small></h1>
    {class_badge}
    {f'<p>Author: {unit.author}</p>' if unit.author else ''}
    <h2>Claims ({len(unit.claims)})</h2>
    {"".join(claims_html)}
</body>
</html>'''


def to_markdown(target: Union[str, Path, AKF]) -> str:
    """Generate Markdown representation.

    Args:
        target: AKF unit, file path, or JSON string.

    Returns:
        Markdown string.
    """
    unit = _resolve(target)

    lines = [f"# AKF {unit.version} | {unit.id}", ""]
    if unit.author:
        lines.append(f"**Author**: {unit.author}")
    if unit.classification:
        lines.append(f"**Classification**: {unit.classification}")
    lines.append(f"**Claims**: {len(unit.claims)}")
    lines.append("")

    for i, claim in enumerate(unit.claims, 1):
        trust_icon = "+" if claim.confidence >= 0.8 else "~" if claim.confidence >= 0.5 else "-"
        ai_flag = " `[AI]`" if claim.ai_generated else ""
        ver_flag = " `[Verified]`" if claim.verified else ""
        lines.append(f"{i}. [{trust_icon} {claim.confidence:.2f}] {claim.content}{ai_flag}{ver_flag}")
        if claim.source and claim.source != "unspecified":
            lines.append(f"   - Source: {claim.source}")
        if claim.risk:
            lines.append(f"   - Risk: {claim.risk}")
        lines.append("")

    if unit.prov:
        lines.append("## Provenance")
        for hop in unit.prov:
            lines.append(f"- Hop {hop.hop}: **{hop.actor}** {hop.action} @ {hop.timestamp}")

    return "\n".join(lines)


def executive_summary(target: Union[str, Path, AKF]) -> str:
    """Generate a plain-English executive summary.

    Designed for non-technical stakeholders.

    Args:
        target: AKF unit, file path, or JSON string.

    Returns:
        Plain English summary string.
    """
    unit = _resolve(target)

    total = len(unit.claims)
    ai_count = sum(1 for c in unit.claims if c.ai_generated)
    verified_count = sum(1 for c in unit.claims if c.verified)
    avg_trust = sum(c.confidence for c in unit.claims) / total if total > 0 else 0
    high_trust = sum(1 for c in unit.claims if c.confidence >= 0.8)
    low_trust = sum(1 for c in unit.claims if c.confidence < 0.5)

    lines = ["Executive Summary", "=" * 40, ""]

    # Overall assessment
    if avg_trust >= 0.8:
        lines.append("Overall: This knowledge unit has HIGH confidence.")
    elif avg_trust >= 0.5:
        lines.append("Overall: This knowledge unit has MODERATE confidence.")
    else:
        lines.append("Overall: This knowledge unit has LOW confidence and should be used with caution.")

    lines.append("")
    lines.append(f"Contains {total} knowledge claims:")
    lines.append(f"  - {high_trust} high confidence (>= 0.8)")
    lines.append(f"  - {total - high_trust - low_trust} moderate confidence")
    lines.append(f"  - {low_trust} low confidence (< 0.5)")

    if ai_count > 0:
        pct = ai_count / total * 100
        lines.append(f"\n{ai_count} of {total} claims ({pct:.0f}%) are AI-generated.")
        risky = [c for c in unit.claims if c.ai_generated and c.risk]
        if risky:
            lines.append(f"  {len(risky)} AI claims have risk advisories.")

    if verified_count > 0:
        lines.append(f"\n{verified_count} claims have been human-verified.")

    if unit.classification:
        lines.append(f"\nClassification: {unit.classification}")
        if unit.allow_external:
            lines.append("External sharing: allowed")
        else:
            lines.append("External sharing: restricted")

    if unit.prov:
        lines.append(f"\nProvenance: {len(unit.prov)} recorded steps in the data chain.")

    return "\n".join(lines)
