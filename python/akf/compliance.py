"""AKF v1.1 — Compliance auditing and regulatory mapping.

Supports EU AI Act, SOX, HIPAA, GDPR, NIST AI RMF, ISO 42001.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    """Resolve target to an AKF unit.

    For .akf files, loads directly. For other formats (PDF, DOCX, MD, etc.),
    extracts metadata via universal.extract() and builds an AKF unit from it.
    """
    if isinstance(target, AKF):
        return target
    path = Path(target)
    if path.exists():
        if path.suffix == ".akf":
            return load(path)
        # Non-AKF file: extract metadata via universal API
        from . import universal as akf_u
        meta = akf_u.extract(str(path))
        if meta is not None:
            from .core import create_multi
            claims = meta.get("claims", [])
            envelope: Dict[str, Any] = {}
            if meta.get("classification"):
                envelope["label"] = meta["classification"]
            unit = create_multi(claims if claims else [], **envelope)
            # Copy provenance if present
            if meta.get("provenance"):
                from .models import ProvHop
                hops = []
                for i, p in enumerate(meta["provenance"]):
                    hop_data: Dict[str, Any] = {
                        "hop": i,
                        "actor": p.get("actor", p.get("by", "unknown")),
                        "action": p.get("action", p.get("do", "unknown")),
                        "timestamp": p.get("at", p.get("timestamp", "")),
                    }
                    if p.get("hash") or p.get("h"):
                        hop_data["hash"] = p.get("hash", p.get("h"))
                    hops.append(ProvHop(**hop_data))
                unit = unit.model_copy(update={"prov": hops})
            return unit
        raise ValueError(f"No AKF metadata found in {path}")
    return loads(str(target))


def audit(
    target: Union[str, Path, AKF],
    regulation: Optional[str] = None,
) -> AuditResult:
    """Run a compliance audit on an AKF unit.

    Checks for: provenance, trust scores, AI labeling, classification,
    integrity hash, source attribution, origin tracking, reviews, freshness.

    If a regulation is specified, delegates to ``check_regulation()`` for
    a regulation-specific audit instead.

    Args:
        target: AKF unit, file path, or JSON string.
        regulation: Optional regulation code (e.g. "eu_ai_act", "hipaa",
            "sox", "gdpr", "nist_ai", "iso_42001"). If provided, runs
            regulation-specific checks instead of the general audit.

    Returns:
        AuditResult with compliance score and recommendations.
    """
    if regulation is not None:
        return check_regulation(target, regulation)
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

    # Check 8 (v1.1): Origin tracking — all AI claims have origin field
    max_points += 1
    ai_claims = [c for c in unit.claims if c.ai_generated]
    origin_tracked = all(c.origin is not None for c in ai_claims) if ai_claims else True
    checks.append({"check": "origin_tracking", "passed": origin_tracked})
    if origin_tracked:
        score_points += 1

    # Check 9 (v1.1): Reviews present — unit or claims have reviews
    max_points += 1
    has_reviews = bool(unit.reviews) or any(c.reviews for c in unit.claims if c.reviews)
    checks.append({"check": "review_present", "passed": has_reviews})
    if has_reviews:
        score_points += 1

    # Check 10 (v1.1): Freshness valid — claims with freshness haven't expired
    max_points += 1
    freshness_valid = True
    now = datetime.now(timezone.utc)
    for c in unit.claims:
        if c.freshness and c.freshness.valid_until:
            try:
                vu = c.freshness.valid_until
                # Handle trailing Z for Python 3.9 compatibility
                if vu.endswith("Z"):
                    vu = vu[:-1] + "+00:00"
                valid_until = datetime.fromisoformat(vu)
                if valid_until.tzinfo is None:
                    valid_until = valid_until.replace(tzinfo=timezone.utc)
                if valid_until < now:
                    freshness_valid = False
                    break
            except (ValueError, TypeError):
                pass
    checks.append({"check": "freshness_valid", "passed": freshness_valid})
    if freshness_valid:
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
    if not origin_tracked:
        recommendations.append("Add origin fields to AI-generated claims for transparency")
    if not has_reviews:
        recommendations.append("Add reviews for human oversight verification")
    if not freshness_valid:
        recommendations.append("Refresh or remove expired claims")

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

    Supported regulations: eu_ai_act, sox, hipaa, gdpr, nist_ai, iso_42001.

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

    elif regulation == "iso_42001":
        # ISO 42001 — AI management system standard
        max_points += 4

        # 1. AI governance: provenance and authorship
        has_prov = bool(unit.prov)
        checks.append({"check": "iso42001_governance", "passed": has_prov,
                       "clause": "Clause 5 Leadership"})
        if has_prov:
            score_points += 1
        else:
            recommendations.append("ISO 42001: Add provenance for AI governance")

        # 2. Risk management: AI claims have risk descriptions
        ai_claims = [c for c in unit.claims if c.ai_generated]
        risks_managed = all(c.risk for c in ai_claims) if ai_claims else True
        checks.append({"check": "iso42001_risk_management", "passed": risks_managed,
                       "clause": "Clause 6.1 Risk Assessment"})
        if risks_managed:
            score_points += 1
        else:
            recommendations.append("ISO 42001: Document risk for all AI-generated claims")

        # 3. Explainability: AI claims have origin or reasoning
        ai_explained = all(
            c.origin is not None or c.reasoning is not None
            for c in ai_claims
        ) if ai_claims else True
        checks.append({"check": "iso42001_explainability", "passed": ai_explained,
                       "clause": "Clause 8.4 AI System Development"})
        if ai_explained:
            score_points += 1
        else:
            recommendations.append("ISO 42001: Add origin/reasoning for AI explainability")

        # 4. Continuous improvement: integrity hash for monitoring
        has_hash = unit.integrity_hash is not None
        checks.append({"check": "iso42001_monitoring", "passed": has_hash,
                       "clause": "Clause 10 Improvement"})
        if has_hash:
            score_points += 1
        else:
            recommendations.append("ISO 42001: Add integrity hash for monitoring")

    else:
        valid = ["eu_ai_act", "sox", "hipaa", "gdpr", "nist_ai", "iso_42001"]
        # Suggest closest match
        suggestions = [v for v in valid if regulation.lower() in v or v in regulation.lower()]
        hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else f" Available: {', '.join(valid)}"
        return AuditResult(
            compliant=False, score=0.0,
            checks=[{"check": "unknown_regulation", "passed": False}],
            recommendations=[f"Unknown regulation: {regulation}.{hint}"],
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
                lines.append(f"- **Hop {hop.hop}**: {hop.actor} \u2014 {hop.action} @ {hop.timestamp}{ai_flag}")
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
                lines.append(f"    Hop {hop.hop}: {hop.actor} \u2014 {hop.action} @ {hop.timestamp}")
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


# ---------------------------------------------------------------------------
# v1.1 — New compliance functions
# ---------------------------------------------------------------------------

def check_explainability(target: Union[str, Path, AKF]) -> AuditResult:
    """Check that AI claims have reasoning chains, origin fields, and risk descriptions.

    Args:
        target: AKF unit, file path, or JSON string.

    Returns:
        AuditResult for explainability compliance.
    """
    unit = _load_unit(target)
    checks: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    score_points = 0
    max_points = 0

    ai_claims = [c for c in unit.claims if c.ai_generated or (c.origin and c.origin.type in ("ai", "ai_chain"))]

    # Check 1: AI claims have origin fields
    max_points += 1
    has_origin = all(c.origin is not None for c in ai_claims) if ai_claims else True
    checks.append({"check": "ai_origin_present", "passed": has_origin})
    if has_origin:
        score_points += 1
    else:
        recommendations.append("Add origin fields to all AI-generated claims")

    # Check 2: AI claims have reasoning chains
    max_points += 1
    has_reasoning = all(c.reasoning is not None for c in ai_claims) if ai_claims else True
    checks.append({"check": "ai_reasoning_present", "passed": has_reasoning})
    if has_reasoning:
        score_points += 1
    else:
        recommendations.append("Add reasoning chains for AI explainability")

    # Check 3: AI claims have risk descriptions
    max_points += 1
    has_risk = all(c.risk for c in ai_claims) if ai_claims else True
    checks.append({"check": "ai_risk_described", "passed": has_risk})
    if has_risk:
        score_points += 1
    else:
        recommendations.append("Add risk descriptions to AI claims")

    score = score_points / max_points if max_points > 0 else 0.0
    return AuditResult(
        compliant=score >= 0.7,
        score=round(score, 2),
        checks=checks,
        recommendations=recommendations,
        regulation="explainability",
    )


def check_fairness(target: Union[str, Path, AKF]) -> AuditResult:
    """Check for bias indicators in AI claims.

    Checks: diverse sources, no single-source dominance, multiple evidence types.

    Args:
        target: AKF unit, file path, or JSON string.

    Returns:
        AuditResult for fairness compliance.
    """
    unit = _load_unit(target)
    checks: List[Dict[str, Any]] = []
    recommendations: List[str] = []
    score_points = 0
    max_points = 0

    ai_claims = [c for c in unit.claims if c.ai_generated or (c.origin and c.origin.type in ("ai", "ai_chain"))]

    # Check 1: Source diversity — not all from same source
    max_points += 1
    sources = [c.source for c in unit.claims if c.source and c.source != "unspecified"]
    diverse_sources = len(set(sources)) > 1 if len(sources) > 1 else True
    checks.append({"check": "source_diversity", "passed": diverse_sources})
    if diverse_sources:
        score_points += 1
    else:
        recommendations.append("Diversify claim sources to reduce single-source bias")

    # Check 2: No single-source dominance (no source > 80% of claims)
    max_points += 1
    no_dominance = True
    if sources:
        from collections import Counter
        source_counts = Counter(sources)
        max_count = max(source_counts.values())
        if max_count / len(unit.claims) > 0.8:
            no_dominance = False
    checks.append({"check": "no_source_dominance", "passed": no_dominance})
    if no_dominance:
        score_points += 1
    else:
        recommendations.append("Reduce single-source dominance (>80% from one source)")

    # Check 3: AI claims have evidence
    max_points += 1
    ai_grounded = all(c.evidence and len(c.evidence) > 0 for c in ai_claims) if ai_claims else True
    checks.append({"check": "ai_claims_grounded", "passed": ai_grounded})
    if ai_grounded:
        score_points += 1
    else:
        recommendations.append("Ground AI claims with evidence to reduce bias risk")

    score = score_points / max_points if max_points > 0 else 0.0
    return AuditResult(
        compliant=score >= 0.7,
        score=round(score, 2),
        checks=checks,
        recommendations=recommendations,
        regulation="fairness",
    )


def export_audit(result: AuditResult, format: str = "json") -> str:
    """Export audit result as JSON, markdown, or CSV.

    Args:
        result: AuditResult to export.
        format: "json", "markdown", or "csv".

    Returns:
        Formatted string.
    """
    if format == "json":
        return json.dumps({
            "compliant": result.compliant,
            "score": result.score,
            "regulation": result.regulation,
            "checks": result.checks,
            "recommendations": result.recommendations,
        }, indent=2, ensure_ascii=False)

    elif format == "markdown":
        status = "COMPLIANT" if result.compliant else "NON-COMPLIANT"
        lines = [
            f"# Audit Report: {result.regulation}",
            "",
            f"**Status**: {status}",
            f"**Score**: {result.score:.2f}",
            "",
            "## Checks",
        ]
        for check in result.checks:
            icon = "\u2705" if check["passed"] else "\u274c"
            lines.append(f"- {icon} {check['check']}")
        if result.recommendations:
            lines.append("")
            lines.append("## Recommendations")
            for rec in result.recommendations:
                lines.append(f"- {rec}")
        return "\n".join(lines)

    elif format == "csv":
        lines = ["check,passed"]
        for check in result.checks:
            lines.append(f"{check['check']},{check['passed']}")
        return "\n".join(lines)

    return json.dumps({"error": f"Unknown format: {format}"})


def continuous_audit(
    target: Union[str, Path, AKF],
    regulations: List[str],
) -> dict:
    """Run all specified regulation checks and return a combined report.

    Args:
        target: AKF unit, file path, or JSON string.
        regulations: List of regulation identifiers to check.

    Returns:
        Dict with 'overall_compliant', 'overall_score', 'results' (per regulation).
    """
    unit = _load_unit(target)
    results: Dict[str, Any] = {}
    all_scores: List[float] = []
    all_compliant = True

    for reg in regulations:
        result = check_regulation(unit, reg)
        results[reg] = {
            "compliant": result.compliant,
            "score": result.score,
            "checks": result.checks,
            "recommendations": result.recommendations,
        }
        all_scores.append(result.score)
        if not result.compliant:
            all_compliant = False

    overall_score = sum(all_scores) / len(all_scores) if all_scores else 0.0

    return {
        "overall_compliant": all_compliant,
        "overall_score": round(overall_score, 2),
        "results": results,
    }
