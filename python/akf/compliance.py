"""AKF v1.0 — Compliance auditing and regulatory mapping.

Supports EU AI Act, SOX, HIPAA, GDPR, NIST AI RMF.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .core import load, loads, validate
from .models import AKF


@dataclass
class AuditResult:
    """Result of a compliance audit."""

    compliant: bool
    score: float  # 0.0-1.0
    checks: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    regulation: str = ""

    def __bool__(self) -> bool:
        return self.compliant


def _load_unit(target: Union[str, Path, AKF]) -> AKF:
    """Resolve target to an AKF unit."""
    if isinstance(target, AKF):
        return target
    path = Path(target)
    if path.exists():
        return load(path)
    return loads(str(target))


def audit(target: Union[str, Path, AKF]) -> AuditResult:
    """Run a general compliance audit on an AKF unit.

    Checks for: provenance, trust scores, AI labeling, classification,
    integrity hash, source attribution.

    Args:
        target: AKF unit, file path, or JSON string.

    Returns:
        AuditResult with compliance score and recommendations.
    """
    unit = _load_unit(target)
    checks: List[Dict[str, Any]] = []
    score_points = 0
    max_points = 0

    # Check 1: Has provenance
    max_points += 1
    has_prov = bool(unit.prov) and len(unit.prov) > 0
    checks.append({"check": "provenance_present", "passed": has_prov})
    if has_prov:
        score_points += 1

    # Check 2: Has integrity hash
    max_points += 1
    has_hash = unit.integrity_hash is not None
    checks.append({"check": "integrity_hash", "passed": has_hash})
    if has_hash:
        score_points += 1

    # Check 3: Classification set
    max_points += 1
    has_class = unit.classification is not None
    checks.append({"check": "classification_set", "passed": has_class})
    if has_class:
        score_points += 1

    # Check 4: All claims have sources
    max_points += 1
    all_sourced = all(
        c.source and c.source != "unspecified" for c in unit.claims
    )
    checks.append({"check": "all_claims_sourced", "passed": all_sourced})
    if all_sourced:
        score_points += 1

    # Check 5: AI claims labeled
    max_points += 1
    ai_claims = [c for c in unit.claims if c.ai_generated]
    ai_labeled = all(c.ai_generated is not None for c in unit.claims)
    checks.append({"check": "ai_claims_labeled", "passed": ai_labeled})
    if ai_labeled:
        score_points += 1

    # Check 6: High-risk AI claims have risk descriptions
    max_points += 1
    risky_ai = [c for c in unit.claims if c.ai_generated and (c.authority_tier or 3) >= 4]
    all_risky_described = all(c.risk for c in risky_ai) if risky_ai else True
    checks.append({"check": "ai_risk_described", "passed": all_risky_described})
    if all_risky_described:
        score_points += 1

    # Check 7: Valid structure
    max_points += 1
    vr = validate(unit)
    checks.append({"check": "valid_structure", "passed": vr.valid})
    if vr.valid:
        score_points += 1

    score = score_points / max_points if max_points > 0 else 0.0
    compliant = score >= 0.7

    recommendations: List[str] = []
    if not has_prov:
        recommendations.append("Add provenance to track data lineage")
    if not has_hash:
        recommendations.append("Compute integrity hash for tamper detection")
    if not has_class:
        recommendations.append("Set security classification")
    if not all_sourced:
        recommendations.append("Add source attribution to all claims")
    if not all_risky_described:
        recommendations.append("Add risk descriptions to AI-generated speculative claims")

    return AuditResult(
        compliant=compliant,
        score=round(score, 2),
        checks=checks,
        recommendations=recommendations,
        regulation="general",
    )


def check_regulation(
    target: Union[str, Path, AKF],
    regulation: str = "eu_ai_act",
) -> AuditResult:
    """Check compliance with a specific regulation.

    Supported regulations: eu_ai_act, sox, hipaa, gdpr, nist_ai.

    Args:
        target: AKF unit, file path, or JSON string.
        regulation: Regulation identifier.

    Returns:
        AuditResult with regulation-specific checks.
    """
    unit = _load_unit(target)
    checks: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    score_points = 0
    max_points = 0

    if regulation == "eu_ai_act":
        # Article 13: Transparency — AI outputs must be labeled
        max_points += 1
        ai_labeled = all(c.ai_generated is not None for c in unit.claims)
        checks.append({"check": "eu_ai_transparency", "passed": ai_labeled,
                       "article": "Art. 13 Transparency"})
        if ai_labeled:
            score_points += 1
        else:
            recommendations.append("EU AI Act Art. 13: Label all AI-generated claims")

        # Article 14: Human oversight — verified flag or human in provenance
        max_points += 1
        has_human = (unit.prov and any(
            h.action in ("reviewed", "created") and not h.actor.startswith("ai-")
            for h in unit.prov
        )) or any(c.verified for c in unit.claims)
        checks.append({"check": "eu_ai_human_oversight", "passed": has_human,
                       "article": "Art. 14 Human Oversight"})
        if has_human:
            score_points += 1
        else:
            recommendations.append("EU AI Act Art. 14: Ensure human oversight in provenance")

        # Article 15: Accuracy — risk descriptions for low-confidence AI
        max_points += 1
        risky = [c for c in unit.claims if c.ai_generated and c.confidence < 0.7]
        risks_noted = all(c.risk for c in risky) if risky else True
        checks.append({"check": "eu_ai_accuracy", "passed": risks_noted,
                       "article": "Art. 15 Accuracy"})
        if risks_noted:
            score_points += 1
        else:
            recommendations.append("EU AI Act Art. 15: Add risk notes for low-confidence AI claims")

        # Traceability — provenance chain
        max_points += 1
        has_prov = bool(unit.prov)
        checks.append({"check": "eu_ai_traceability", "passed": has_prov,
                       "article": "Art. 12 Record-keeping"})
        if has_prov:
            score_points += 1
        else:
            recommendations.append("EU AI Act Art. 12: Add provenance for traceability")

    elif regulation == "sox":
        # SOX compliance checks
        max_points += 3
        has_hash = unit.integrity_hash is not None
        has_prov = bool(unit.prov)
        has_class = unit.classification is not None

        checks.append({"check": "sox_integrity", "passed": has_hash, "section": "Section 302"})
        checks.append({"check": "sox_audit_trail", "passed": has_prov, "section": "Section 404"})
        checks.append({"check": "sox_classification", "passed": has_class, "section": "Section 802"})

        score_points += sum([has_hash, has_prov, has_class])
        if not has_hash:
            recommendations.append("SOX Section 302: Add integrity hash")
        if not has_prov:
            recommendations.append("SOX Section 404: Add provenance audit trail")
        if not has_class:
            recommendations.append("SOX Section 802: Set information classification")

    elif regulation == "hipaa":
        max_points += 3
        has_class = unit.classification is not None and unit.classification != "public"
        has_hash = unit.integrity_hash is not None
        no_external = unit.allow_external is not True

        checks.append({"check": "hipaa_access_control", "passed": has_class})
        checks.append({"check": "hipaa_integrity", "passed": has_hash})
        checks.append({"check": "hipaa_transmission_security", "passed": no_external})

        score_points += sum([has_class, has_hash, no_external])
        if not has_class:
            recommendations.append("HIPAA: Set non-public classification for PHI")
        if not has_hash:
            recommendations.append("HIPAA: Add integrity hash for data integrity")
        if not no_external:
            recommendations.append("HIPAA: Restrict external sharing for PHI")

    elif regulation == "gdpr":
        max_points += 2
        has_prov = bool(unit.prov)
        ai_labeled = all(c.ai_generated is not None for c in unit.claims)

        checks.append({"check": "gdpr_data_lineage", "passed": has_prov, "article": "Art. 5(2)"})
        checks.append({"check": "gdpr_automated_decision", "passed": ai_labeled, "article": "Art. 22"})

        score_points += sum([has_prov, ai_labeled])
        if not has_prov:
            recommendations.append("GDPR Art. 5(2): Add provenance for accountability")
        if not ai_labeled:
            recommendations.append("GDPR Art. 22: Label automated decision-making")

    elif regulation == "nist_ai":
        max_points += 3
        has_prov = bool(unit.prov)
        all_sourced = all(c.source and c.source != "unspecified" for c in unit.claims)
        ai_risks = [c for c in unit.claims if c.ai_generated and (c.authority_tier or 3) >= 4]
        risks_described = all(c.risk for c in ai_risks) if ai_risks else True

        checks.append({"check": "nist_governance", "passed": has_prov})
        checks.append({"check": "nist_map", "passed": all_sourced})
        checks.append({"check": "nist_manage", "passed": risks_described})

        score_points += sum([has_prov, all_sourced, risks_described])
        if not has_prov:
            recommendations.append("NIST AI RMF: Add governance through provenance")
        if not all_sourced:
            recommendations.append("NIST AI RMF: Map all claims to sources")
        if not risks_described:
            recommendations.append("NIST AI RMF: Document AI risk factors")

    else:
        return AuditResult(
            compliant=False, score=0.0,
            checks=[{"check": "unknown_regulation", "passed": False}],
            recommendations=[f"Unknown regulation: {regulation}"],
            regulation=regulation,
        )

    score = score_points / max_points if max_points > 0 else 0.0
    return AuditResult(
        compliant=score >= 0.7,
        score=round(score, 2),
        checks=checks,
        recommendations=recommendations,
        regulation=regulation,
    )


def audit_trail(
    target: Union[str, Path, AKF],
    format: str = "text",
) -> str:
    """Generate a human-readable audit trail.

    Args:
        target: AKF unit, file path, or JSON string.
        format: "text" or "markdown".

    Returns:
        Formatted audit trail string.
    """
    unit = _load_unit(target)
    lines: List[str] = []

    if format == "markdown":
        lines.append(f"# Audit Trail: {unit.id}")
        lines.append("")
        lines.append(f"**Version**: {unit.version}")
        if unit.author:
            lines.append(f"**Author**: {unit.author}")
        if unit.classification:
            lines.append(f"**Classification**: {unit.classification}")
        lines.append(f"**Claims**: {len(unit.claims)}")
        lines.append("")

        if unit.prov:
            lines.append("## Provenance Chain")
            for hop in unit.prov:
                ai_flag = ""
                lines.append(f"- **Hop {hop.hop}**: {hop.actor} — {hop.action} @ {hop.timestamp}{ai_flag}")
                if hop.claims_added:
                    lines.append(f"  - Added: {len(hop.claims_added)} claims")
                if hop.claims_removed:
                    lines.append(f"  - Removed: {len(hop.claims_removed)} claims")
        else:
            lines.append("## Provenance Chain\n*No provenance recorded*")
    else:
        lines.append(f"Audit Trail: {unit.id}")
        lines.append(f"  Version: {unit.version}")
        if unit.author:
            lines.append(f"  Author: {unit.author}")
        if unit.classification:
            lines.append(f"  Classification: {unit.classification}")
        lines.append(f"  Claims: {len(unit.claims)}")

        if unit.prov:
            lines.append("  Provenance:")
            for hop in unit.prov:
                lines.append(f"    Hop {hop.hop}: {hop.actor} — {hop.action} @ {hop.timestamp}")
        else:
            lines.append("  Provenance: none")

    return "\n".join(lines)


def verify_human_oversight(target: Union[str, Path, AKF]) -> dict:
    """Check if human oversight is present in the provenance chain.

    Args:
        target: AKF unit, file path, or JSON string.

    Returns:
        Dict with 'has_human_oversight', 'human_actors', 'ai_actors'.
    """
    unit = _load_unit(target)

    human_actors = set()
    ai_actors = set()
    has_review = False

    if unit.prov:
        for hop in unit.prov:
            if hop.action == "reviewed":
                has_review = True
                human_actors.add(hop.actor)
            elif hop.action in ("created",) and "@" in hop.actor:
                human_actors.add(hop.actor)
            elif hop.action in ("enriched", "consumed", "transformed"):
                ai_actors.add(hop.actor)

    verified_claims = [c for c in unit.claims if c.verified]

    return {
        "has_human_oversight": has_review or len(verified_claims) > 0,
        "human_actors": sorted(human_actors),
        "ai_actors": sorted(ai_actors),
        "verified_claims": len(verified_claims),
        "reviewed": has_review,
    }
