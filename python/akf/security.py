"""AKF v1.0 — Security classification and inheritance."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import AKF

HIERARCHY: dict[str, int] = {
    "public": 0,
    "internal": 1,
    "confidential": 2,
    "highly-confidential": 3,
    "restricted": 4,
}


def label_rank(label: str | None) -> int:
    """Return numeric rank for a classification label. Defaults to 0 (public)."""
    if label is None:
        return 0
    return HIERARCHY.get(label, 0)


def validate_inheritance(parent: AKF, child: AKF) -> bool:
    """Check child classification >= parent classification when parent.inherit_classification is true.

    Returns True if inheritance is valid, False if child is less restrictive.
    """
    if parent.inherit_classification is False:
        return True  # No inheritance constraint
    return label_rank(child.classification) >= label_rank(parent.classification)


def can_share_external(unit: AKF) -> bool:
    """Check if the unit can be shared externally."""
    if unit.allow_external is True:
        return True
    if unit.classification in ("confidential", "highly-confidential", "restricted"):
        return False
    return unit.allow_external is not False and label_rank(unit.classification) <= HIERARCHY["internal"]


def inherit_label(parent: AKF) -> dict:
    """Return security fields to copy to a derived .akf."""
    fields: dict = {}
    if parent.inherit_classification is not False and parent.classification:
        fields["classification"] = parent.classification
        fields["inherit_classification"] = parent.inherit_classification
    if parent.allow_external is not None:
        fields["allow_external"] = parent.allow_external
    return fields


@dataclass
class SecurityScore:
    """Result of security scoring."""

    score: float  # 0-10
    checks: list[dict] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    @property
    def grade(self) -> str:
        if self.score >= 8:
            return "A"
        elif self.score >= 6:
            return "B"
        elif self.score >= 4:
            return "C"
        elif self.score >= 2:
            return "D"
        return "F"


def security_score(unit: AKF) -> SecurityScore:
    """Compute a 0-10 security score for an AKF unit."""
    checks = []
    issues = []
    points = 0.0

    # Check 1: Classification set (2 points)
    has_label = unit.classification is not None
    checks.append({"check": "classification", "passed": has_label})
    if has_label:
        points += 2.0
    else:
        issues.append("No classification label set")

    # Check 2: Inherit classification enabled (1 point)
    has_inherit = unit.inherit_classification is True
    checks.append({"check": "inherit_classification", "passed": has_inherit})
    if has_inherit:
        points += 1.0

    # Check 3: External sharing disabled (1 point)
    no_ext = unit.allow_external is not True
    checks.append({"check": "external_restricted", "passed": no_ext})
    if no_ext:
        points += 1.0
    else:
        issues.append("External sharing is enabled")

    # Check 4: Has provenance (2 points)
    has_prov = unit.prov is not None and len(unit.prov) > 0
    checks.append({"check": "provenance", "passed": has_prov})
    if has_prov:
        points += 2.0
    else:
        issues.append("No provenance chain")

    # Check 5: Integrity hash (2 points)
    has_hash = unit.integrity_hash is not None
    checks.append({"check": "integrity_hash", "passed": has_hash})
    if has_hash:
        points += 2.0
    else:
        issues.append("No integrity hash")

    # Check 6: All claims sourced (1 point)
    all_sourced = all(
        c.source and c.source != "unspecified" for c in unit.claims
    ) if unit.claims else False
    checks.append({"check": "all_claims_sourced", "passed": all_sourced})
    if all_sourced:
        points += 1.0

    # Check 7: AI claims labeled (1 point)
    ai_claims = [c for c in unit.claims if c.ai_generated]
    ai_labeled = all(c.risk or c.source for c in ai_claims) if ai_claims else True
    checks.append({"check": "ai_claims_labeled", "passed": ai_labeled})
    if ai_labeled:
        points += 1.0

    return SecurityScore(score=min(10.0, points), checks=checks, issues=issues)


def purview_signals(unit: AKF) -> dict:
    """Generate Microsoft Purview DLP-compatible signals from an AKF unit."""
    signals: dict = {
        "sensitivity_label": unit.classification or "unclassified",
        "sensitivity_rank": label_rank(unit.classification),
        "external_sharing_allowed": can_share_external(unit),
        "claim_count": len(unit.claims),
        "ai_generated_count": sum(1 for c in unit.claims if c.ai_generated),
        "verified_count": sum(1 for c in unit.claims if c.verified),
        "has_provenance": unit.prov is not None and len(unit.prov) > 0,
        "has_integrity_hash": unit.integrity_hash is not None,
    }
    if unit.claims:
        signals["min_trust"] = min(c.confidence for c in unit.claims)
        signals["max_trust"] = max(c.confidence for c in unit.claims)
        signals["avg_trust"] = sum(c.confidence for c in unit.claims) / len(unit.claims)
    return signals


def detect_laundering(unit: AKF) -> list[str]:
    """Detect potential classification laundering in an AKF unit's provenance chain.

    Laundering occurs when classification is downgraded across provenance hops,
    or when high-classification claims exist in a low-classification unit.
    """
    warnings: list[str] = []

    # Check 1: High-confidence claims in low-classification unit
    if unit.classification in ("public", None):
        high_tier = [c for c in unit.claims if c.authority_tier and c.authority_tier <= 2]
        if high_tier:
            warnings.append(
                f"Unit is '{unit.classification or 'unclassified'}' but contains "
                f"{len(high_tier)} high-authority (tier 1-2) claims"
            )

    # Check 2: AI claims in public unit without risk descriptions
    if unit.classification in ("public", None):
        ai_no_risk = [c for c in unit.claims if c.ai_generated and not c.risk]
        if ai_no_risk:
            warnings.append(
                f"{len(ai_no_risk)} AI-generated claims in public unit without risk descriptions"
            )

    # Check 3: Provenance shows classification downgrade
    if unit.prov and len(unit.prov) >= 2:
        for i in range(1, len(unit.prov)):
            prev_hop = unit.prov[i - 1]
            curr_hop = unit.prov[i]
            if curr_hop.action in ("downgraded", "declassified", "reclassified"):
                warnings.append(
                    f"Provenance hop {i} by '{curr_hop.actor}' shows "
                    f"classification change action: '{curr_hop.action}'"
                )

    # Check 4: External sharing enabled on high-classification unit
    if unit.allow_external and label_rank(unit.classification) >= HIERARCHY["confidential"]:
        warnings.append(
            f"External sharing enabled on '{unit.classification}' unit"
        )

    return warnings
