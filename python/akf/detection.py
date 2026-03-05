"""AKF v1.1 — 10 AI-specific detection classes for enterprise security.

Each detection class examines an AKF unit for a specific category of AI
content risk and returns structured findings. These power DLP policies
in enterprise security platforms.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from .core import load, loads
from .models import AKF
from .trust import effective_trust, freshness_status


@dataclass
class DetectionResult:
    """Result of a single detection class evaluation."""

    detection_class: str
    triggered: bool
    severity: str  # "critical", "high", "medium", "low", "info"
    findings: List[str] = field(default_factory=list)
    affected_claims: List[str] = field(default_factory=list)
    recommendation: str = ""

    def to_dict(self) -> dict:
        return {
            "detection_class": self.detection_class,
            "triggered": self.triggered,
            "severity": self.severity,
            "findings": self.findings,
            "affected_claims": self.affected_claims,
            "recommendation": self.recommendation,
        }


@dataclass
class DetectionReport:
    """Aggregate result of running all detection classes."""

    results: List[DetectionResult] = field(default_factory=list)
    triggered_count: int = 0
    critical_count: int = 0
    high_count: int = 0

    @property
    def clean(self) -> bool:
        return self.triggered_count == 0

    def to_dict(self) -> dict:
        return {
            "results": [r.to_dict() for r in self.results],
            "triggered_count": self.triggered_count,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "clean": self.clean,
        }


def _load_unit(target: Union[str, "AKF"]) -> AKF:
    """Resolve target to an AKF unit."""
    if isinstance(target, AKF):
        return target
    from pathlib import Path

    path = Path(target)
    if path.exists():
        return load(path)
    return loads(str(target))


# ---------------------------------------------------------------------------
# Detection Class 1: AI Content Without Review
# ---------------------------------------------------------------------------

def detect_ai_without_review(unit: AKF) -> DetectionResult:
    """Flag documents where AI-generated content lacks a human review stamp.

    Triggers when AI-generated claims have no associated review records
    indicating human verification.
    """
    findings: List[str] = []
    affected: List[str] = []

    ai_claims = [c for c in unit.claims if c.ai_generated]
    if not ai_claims:
        return DetectionResult(
            detection_class="ai_content_without_review",
            triggered=False,
            severity="info",
            findings=["No AI-generated claims found"],
        )

    # Check unit-level reviews
    unit_has_review = bool(unit.reviews)

    for claim in ai_claims:
        claim_has_review = bool(claim.reviews) if hasattr(claim, "reviews") and claim.reviews else False
        if not claim_has_review and not unit_has_review:
            cid = claim.id or "unknown"
            affected.append(cid)
            preview = (claim.content[:60] + "...") if len(claim.content) > 60 else claim.content
            findings.append(f"AI claim [{cid}] has no human review: \"{preview}\"")

    triggered = len(affected) > 0
    return DetectionResult(
        detection_class="ai_content_without_review",
        triggered=triggered,
        severity="high" if triggered else "info",
        findings=findings if findings else ["All AI content has been reviewed"],
        affected_claims=affected,
        recommendation="Add human review stamps to AI-generated claims before distribution." if triggered else "",
    )


# ---------------------------------------------------------------------------
# Detection Class 2: Trust Below Threshold
# ---------------------------------------------------------------------------

def detect_trust_below_threshold(
    unit: AKF, threshold: float = 0.7
) -> DetectionResult:
    """Detect content with trust scores below the organizational minimum.

    Args:
        unit: AKF unit to evaluate.
        threshold: Minimum acceptable trust score (default 0.7).
    """
    findings: List[str] = []
    affected: List[str] = []

    for claim in unit.claims:
        trust = effective_trust(claim)
        if trust.score < threshold:
            cid = claim.id or "unknown"
            affected.append(cid)
            findings.append(
                f"Claim [{cid}] trust {trust.score:.2f} < threshold {threshold} "
                f"(decision: {trust.decision})"
            )

    triggered = len(affected) > 0
    return DetectionResult(
        detection_class="trust_below_threshold",
        triggered=triggered,
        severity="high" if triggered else "info",
        findings=findings if findings else [f"All claims meet trust threshold {threshold}"],
        affected_claims=affected,
        recommendation="Review low-trust claims and add evidence or human verification." if triggered else "",
    )


# ---------------------------------------------------------------------------
# Detection Class 3: Hallucination Risk
# ---------------------------------------------------------------------------

def detect_hallucination_risk(unit: AKF) -> DetectionResult:
    """Identify claims with weak evidence grounding or low confidence scores.

    Flags AI-generated claims that lack evidence, have low confidence,
    or are missing source attribution — indicators of potential hallucination.
    """
    findings: List[str] = []
    affected: List[str] = []

    for claim in unit.claims:
        risks: List[str] = []
        cid = claim.id or "unknown"

        # AI-generated with low confidence
        if claim.ai_generated and claim.confidence < 0.5:
            risks.append(f"low confidence ({claim.confidence:.2f})")

        # No evidence backing
        if claim.ai_generated and (not claim.evidence or len(claim.evidence) == 0):
            risks.append("no evidence grounding")

        # No source attribution
        if claim.ai_generated and (not claim.source or claim.source == "unspecified"):
            risks.append("no source attribution")

        # High authority tier (5 = lowest authority) with AI
        if claim.ai_generated and claim.authority_tier and claim.authority_tier >= 5:
            risks.append(f"lowest authority tier ({claim.authority_tier})")

        if risks:
            affected.append(cid)
            preview = (claim.content[:50] + "...") if len(claim.content) > 50 else claim.content
            findings.append(f"Claim [{cid}] \"{preview}\": {', '.join(risks)}")

    triggered = len(affected) > 0
    return DetectionResult(
        detection_class="hallucination_risk",
        triggered=triggered,
        severity="critical" if triggered else "info",
        findings=findings if findings else ["No hallucination risk indicators found"],
        affected_claims=affected,
        recommendation="Add evidence grounding, source attribution, and human review to flagged claims." if triggered else "",
    )


# ---------------------------------------------------------------------------
# Detection Class 4: Knowledge Laundering
# ---------------------------------------------------------------------------

def detect_knowledge_laundering(unit: AKF) -> DetectionResult:
    """Detect AI content repackaged to obscure its machine-generated origin.

    Triggers when AI-generated content is in a public unit without proper
    labeling, risk descriptions, or when provenance shows suspicious
    reclassification actions.
    """
    findings: List[str] = []
    affected: List[str] = []

    # Check 1: AI claims in public unit without AI labeling
    if unit.classification in ("public", None):
        for claim in unit.claims:
            if claim.ai_generated and not claim.risk:
                cid = claim.id or "unknown"
                affected.append(cid)
                findings.append(
                    f"AI claim [{cid}] in public unit without risk disclosure"
                )

    # Check 2: High-authority claims from AI without origin tracking
    for claim in unit.claims:
        if (claim.ai_generated
                and claim.authority_tier is not None
                and claim.authority_tier <= 2
                and not getattr(claim, "origin", None)):
            cid = claim.id or "unknown"
            if cid not in affected:
                affected.append(cid)
                findings.append(
                    f"AI claim [{cid}] has high authority (tier {claim.authority_tier}) "
                    f"but no origin tracking"
                )

    # Check 3: Provenance shows reclassification/downgrade actions
    if unit.prov:
        for hop in unit.prov:
            if hop.action in ("downgraded", "declassified", "reclassified"):
                findings.append(
                    f"Provenance hop by '{hop.actor}' shows suspicious action: '{hop.action}'"
                )

    # Check 4: AI-generated flag missing entirely
    unlabeled = [
        c for c in unit.claims
        if c.ai_generated is None or c.ai_generated is False
    ]
    if unlabeled and unit.agent:
        # Agent-produced unit but claims not labeled as AI
        for claim in unlabeled:
            cid = claim.id or "unknown"
            if cid not in affected:
                affected.append(cid)
                findings.append(
                    f"Unit has agent '{unit.agent}' but claim [{cid}] not labeled as AI-generated"
                )

    triggered = len(findings) > 0
    return DetectionResult(
        detection_class="knowledge_laundering",
        triggered=triggered,
        severity="critical" if triggered else "info",
        findings=findings if findings else ["No knowledge laundering indicators found"],
        affected_claims=affected,
        recommendation="Ensure all AI content is properly labeled with origin tracking and risk descriptions." if triggered else "",
    )


# ---------------------------------------------------------------------------
# Detection Class 5: Classification Downgrade
# ---------------------------------------------------------------------------

def detect_classification_downgrade(unit: AKF) -> DetectionResult:
    """Prevent AI from lowering document classification or sensitivity levels.

    Checks provenance for classification changes and verifies inheritance
    constraints are maintained.
    """
    findings: List[str] = []

    # Check provenance for downgrade actions
    if unit.prov:
        for i, hop in enumerate(unit.prov):
            if hop.action in ("downgraded", "declassified", "reclassified"):
                findings.append(
                    f"Hop {i} by '{hop.actor}': classification action '{hop.action}'"
                )

    # Check if inherit_classification is disabled
    if unit.inherit_classification is False and unit.classification in ("public", "internal"):
        findings.append(
            f"Classification inheritance disabled on '{unit.classification}' unit — "
            f"derived documents can downgrade freely"
        )

    # Check for external sharing on restricted content
    from .security import HIERARCHY, label_rank
    if unit.allow_external and label_rank(unit.classification) >= HIERARCHY.get("confidential", 2):
        findings.append(
            f"External sharing enabled on '{unit.classification}' unit"
        )

    triggered = len(findings) > 0
    return DetectionResult(
        detection_class="classification_downgrade",
        triggered=triggered,
        severity="critical" if triggered else "info",
        findings=findings if findings else ["Classification integrity maintained"],
        recommendation="Enable inherit_classification and review provenance for unauthorized changes." if triggered else "",
    )


# ---------------------------------------------------------------------------
# Detection Class 6: Stale Claims
# ---------------------------------------------------------------------------

def detect_stale_claims(unit: AKF) -> DetectionResult:
    """Flag content with outdated evidence or expired trust attestations.

    Checks freshness metadata and claim timestamps against current time.
    """
    findings: List[str] = []
    affected: List[str] = []
    now = datetime.now(timezone.utc)

    for claim in unit.claims:
        cid = claim.id or "unknown"
        status = freshness_status(claim)

        if status == "expired":
            affected.append(cid)
            findings.append(f"Claim [{cid}] has expired freshness")
        elif status == "stale":
            affected.append(cid)
            findings.append(f"Claim [{cid}] is stale (past recommended refresh)")

    # Check unit-level TTL
    if unit.ttl is not None and unit.created:
        try:
            created_str = unit.created
            if created_str.endswith("Z"):
                created_str = created_str[:-1] + "+00:00"
            created_dt = datetime.fromisoformat(created_str)
            if created_dt.tzinfo is None:
                created_dt = created_dt.replace(tzinfo=timezone.utc)
            age_hours = (now - created_dt).total_seconds() / 3600
            if age_hours > unit.ttl:
                findings.append(f"Unit TTL ({unit.ttl}h) exceeded — age is {age_hours:.1f}h")
        except (ValueError, TypeError):
            pass

    triggered = len(findings) > 0
    return DetectionResult(
        detection_class="stale_claims",
        triggered=triggered,
        severity="medium" if triggered else "info",
        findings=findings if findings else ["All claims are fresh"],
        affected_claims=affected,
        recommendation="Refresh expired claims or remove stale content before distribution." if triggered else "",
    )


# ---------------------------------------------------------------------------
# Detection Class 7: Ungrounded AI Claims
# ---------------------------------------------------------------------------

def detect_ungrounded_claims(unit: AKF) -> DetectionResult:
    """Identify AI assertions lacking source references or evidence backing.

    Flags AI claims that make assertions without any evidence objects,
    source references, or reasoning chains to support them.
    """
    findings: List[str] = []
    affected: List[str] = []

    for claim in unit.claims:
        if not claim.ai_generated:
            continue

        cid = claim.id or "unknown"
        grounding_issues: List[str] = []

        # No evidence at all
        if not claim.evidence or len(claim.evidence) == 0:
            grounding_issues.append("no evidence")

        # No source reference
        if not claim.source or claim.source == "unspecified":
            grounding_issues.append("no source")

        # No reasoning chain (if available)
        if hasattr(claim, "reasoning") and not claim.reasoning:
            grounding_issues.append("no reasoning chain")

        if grounding_issues:
            affected.append(cid)
            preview = (claim.content[:50] + "...") if len(claim.content) > 50 else claim.content
            findings.append(f"Claim [{cid}] \"{preview}\": {', '.join(grounding_issues)}")

    triggered = len(affected) > 0
    return DetectionResult(
        detection_class="ungrounded_ai_claims",
        triggered=triggered,
        severity="high" if triggered else "info",
        findings=findings if findings else ["All AI claims have grounding"],
        affected_claims=affected,
        recommendation="Add evidence, source references, or reasoning chains to ungrounded claims." if triggered else "",
    )


# ---------------------------------------------------------------------------
# Detection Class 8: Trust Degradation Chain
# ---------------------------------------------------------------------------

def detect_trust_degradation_chain(unit: AKF) -> DetectionResult:
    """Track cascading trust loss across document transformation pipelines.

    Checks provenance hops for cumulative penalties that significantly
    degrade trust from the original source.
    """
    findings: List[str] = []

    if not unit.prov or len(unit.prov) < 2:
        return DetectionResult(
            detection_class="trust_degradation_chain",
            triggered=False,
            severity="info",
            findings=["No multi-hop provenance chain to evaluate"],
        )

    # Calculate cumulative penalty
    total_penalty = 0.0
    for hop in unit.prov:
        if hop.penalty is not None:
            total_penalty += hop.penalty

    if total_penalty < -0.1:
        findings.append(
            f"Cumulative provenance penalty: {total_penalty:.2f} across {len(unit.prov)} hops"
        )

    # Check for large single-hop penalties
    for i, hop in enumerate(unit.prov):
        if hop.penalty is not None and hop.penalty < -0.1:
            findings.append(
                f"Hop {i} by '{hop.actor}' has significant penalty: {hop.penalty:.2f}"
            )

    # Check if claims have degraded below threshold after chain
    for claim in unit.claims:
        trust = effective_trust(claim)
        if trust.score < 0.4 and claim.confidence >= 0.7:
            cid = claim.id or "unknown"
            findings.append(
                f"Claim [{cid}] original confidence {claim.confidence:.2f} "
                f"degraded to effective trust {trust.score:.2f}"
            )

    triggered = len(findings) > 0
    return DetectionResult(
        detection_class="trust_degradation_chain",
        triggered=triggered,
        severity="high" if triggered else "info",
        findings=findings if findings else ["Trust chain is healthy"],
        recommendation="Review provenance chain for unnecessary transformations that degrade trust." if triggered else "",
    )


# ---------------------------------------------------------------------------
# Detection Class 9: Excessive AI Concentration
# ---------------------------------------------------------------------------

def detect_excessive_ai_concentration(
    unit: AKF, max_ai_ratio: float = 0.8
) -> DetectionResult:
    """Alert when documents exceed acceptable ratios of AI-generated content.

    Args:
        unit: AKF unit to evaluate.
        max_ai_ratio: Maximum acceptable ratio of AI claims (default 0.8).
    """
    total = len(unit.claims)
    ai_count = sum(1 for c in unit.claims if c.ai_generated)
    ai_ratio = ai_count / total if total > 0 else 0.0

    findings: List[str] = []

    if ai_ratio > max_ai_ratio:
        findings.append(
            f"AI content ratio {ai_ratio:.0%} exceeds threshold {max_ai_ratio:.0%} "
            f"({ai_count}/{total} claims are AI-generated)"
        )

    # Check if all claims are from the same AI model
    if ai_count > 1 and unit.model:
        findings_extra = f"All AI claims attributed to single model: {unit.model}"
        if ai_ratio > max_ai_ratio:
            findings.append(findings_extra)

    # No human claims at all
    human_count = sum(1 for c in unit.claims if not c.ai_generated)
    if human_count == 0 and total > 0:
        findings.append("No human-authored claims — document is entirely AI-generated")

    triggered = len(findings) > 0
    return DetectionResult(
        detection_class="excessive_ai_concentration",
        triggered=triggered,
        severity="medium" if triggered else "info",
        findings=findings if findings else [f"AI concentration {ai_ratio:.0%} is within acceptable range"],
        recommendation="Add human-authored or human-reviewed claims to balance AI concentration." if triggered else "",
    )


# ---------------------------------------------------------------------------
# Detection Class 10: Provenance Gap
# ---------------------------------------------------------------------------

def detect_provenance_gap(unit: AKF) -> DetectionResult:
    """Detect breaks in the content lineage chain where origin is unknown.

    Checks for missing provenance, gaps in hop numbering, and claims
    without any traceability to their source.
    """
    findings: List[str] = []

    # No provenance at all
    if not unit.prov or len(unit.prov) == 0:
        findings.append("No provenance chain — content origin is untraceable")
    else:
        # Check for gaps in hop numbering
        for i, hop in enumerate(unit.prov):
            if hop.hop != i:
                findings.append(f"Provenance gap: expected hop {i}, found hop {hop.hop}")

        # Check first hop has a meaningful actor
        first_actor = unit.prov[0].actor
        if not first_actor or first_actor in ("unknown", "unspecified"):
            findings.append("Provenance origin actor is unknown or unspecified")

        # Check for hops with no actor
        for i, hop in enumerate(unit.prov):
            if not hop.actor:
                findings.append(f"Provenance hop {i} has no actor")

    # Check claims without origin tracking
    ai_without_origin = [
        c for c in unit.claims
        if c.ai_generated and not getattr(c, "origin", None)
    ]
    if ai_without_origin:
        findings.append(
            f"{len(ai_without_origin)} AI claims lack origin tracking"
        )

    triggered = len(findings) > 0
    return DetectionResult(
        detection_class="provenance_gap",
        triggered=triggered,
        severity="high" if triggered else "info",
        findings=findings if findings else ["Complete provenance chain with origin tracking"],
        recommendation="Add provenance chain and origin tracking to establish content lineage." if triggered else "",
    )


# ---------------------------------------------------------------------------
# Aggregate: Run all 10 detection classes
# ---------------------------------------------------------------------------

ALL_DETECTION_CLASSES = [
    detect_ai_without_review,
    detect_trust_below_threshold,
    detect_hallucination_risk,
    detect_knowledge_laundering,
    detect_classification_downgrade,
    detect_stale_claims,
    detect_ungrounded_claims,
    detect_trust_degradation_chain,
    detect_excessive_ai_concentration,
    detect_provenance_gap,
]


def run_all_detections(
    target: Union[str, AKF],
    *,
    trust_threshold: float = 0.7,
    max_ai_ratio: float = 0.8,
) -> DetectionReport:
    """Run all 10 detection classes against an AKF unit.

    Args:
        target: AKF unit, file path, or JSON string.
        trust_threshold: Minimum trust score for detection class 2.
        max_ai_ratio: Maximum AI concentration for detection class 9.

    Returns:
        DetectionReport with all results aggregated.
    """
    unit = _load_unit(target)
    results: List[DetectionResult] = []

    results.append(detect_ai_without_review(unit))
    results.append(detect_trust_below_threshold(unit, threshold=trust_threshold))
    results.append(detect_hallucination_risk(unit))
    results.append(detect_knowledge_laundering(unit))
    results.append(detect_classification_downgrade(unit))
    results.append(detect_stale_claims(unit))
    results.append(detect_ungrounded_claims(unit))
    results.append(detect_trust_degradation_chain(unit))
    results.append(detect_excessive_ai_concentration(unit, max_ai_ratio=max_ai_ratio))
    results.append(detect_provenance_gap(unit))

    triggered = [r for r in results if r.triggered]
    critical = [r for r in triggered if r.severity == "critical"]
    high = [r for r in triggered if r.severity == "high"]

    return DetectionReport(
        results=results,
        triggered_count=len(triggered),
        critical_count=len(critical),
        high_count=len(high),
    )
