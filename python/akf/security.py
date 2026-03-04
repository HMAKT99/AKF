"""AKF v1.1 — Security classification, inheritance, and access control."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

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
    """Compute a 0-10 security score for an AKF unit.

    Enhanced in v1.1: 15 raw points, normalized to 0-10 scale.
    """
    checks = []
    issues = []
    points = 0.0
    max_points = 15.0

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

    # Check 8 (v1.1): Origin tracking — AI claims have origin field (2 points)
    ai_with_origin = all(
        c.origin is not None for c in unit.claims if c.ai_generated
    ) if ai_claims else True
    checks.append({"check": "origin_tracking", "passed": ai_with_origin})
    if ai_with_origin:
        points += 2.0
    else:
        issues.append("AI claims missing origin tracking")

    # Check 9 (v1.1): Reviews present (1 point)
    has_reviews = bool(unit.reviews) or any(c.reviews for c in unit.claims if c.reviews)
    checks.append({"check": "reviews_present", "passed": has_reviews})
    if has_reviews:
        points += 1.0

    # Check 10 (v1.1): Trust anchor verification (1 point)
    has_anchor = False
    if has_prov and unit.prov:
        first_actor = unit.prov[0].actor
        has_anchor = not first_actor.startswith("ai-") and "@" in first_actor
    checks.append({"check": "trust_anchor", "passed": has_anchor})
    if has_anchor:
        points += 1.0

    # Normalize to 0-10 scale
    normalized = (points / max_points) * 10.0

    return SecurityScore(score=round(min(10.0, normalized), 1), checks=checks, issues=issues)


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


# ---------------------------------------------------------------------------
# v1.1 — New security functions
# ---------------------------------------------------------------------------

def check_access(unit: AKF, actor: str, required_level: str = "internal") -> bool:
    """Check if an actor meets the classification level for the unit.

    Uses unit.security.access_control if present, otherwise falls back
    to comparing the required_level against the unit's classification.

    Args:
        unit: AKF unit.
        actor: Actor identifier (email, agent ID).
        required_level: Minimum classification level the actor needs.

    Returns:
        True if actor has sufficient access.
    """
    # Check unit.security.access_control if present
    if unit.security and "access_control" in unit.security:
        ac = unit.security["access_control"]
        allowed = ac.get("allowed_actors", [])
        denied = ac.get("denied_actors", [])
        if actor in denied:
            return False
        if allowed and actor not in allowed:
            return False
        return True

    # Fallback: compare classification levels
    unit_rank = label_rank(unit.classification)
    required_rank = label_rank(required_level)
    return required_rank >= unit_rank


def verify_trust_anchor(unit: AKF, trusted_actors: List[str]) -> dict:
    """Verify that the provenance chain starts from a trusted actor.

    Args:
        unit: AKF unit.
        trusted_actors: List of trusted actor identifiers.

    Returns:
        Dict with 'anchored' (bool), 'anchor_actor' (str), 'chain_length' (int).
    """
    if not unit.prov or len(unit.prov) == 0:
        return {"anchored": False, "anchor_actor": None, "chain_length": 0}

    first_actor = unit.prov[0].actor
    anchored = first_actor in trusted_actors

    return {
        "anchored": anchored,
        "anchor_actor": first_actor,
        "chain_length": len(unit.prov),
    }


def redaction_report(unit: AKF) -> dict:
    """Identify claims that should be redacted based on classification and sharing rules.

    Args:
        unit: AKF unit.

    Returns:
        Dict with 'redact' (list of claim IDs), 'reason' (list of reasons), 'total'.
    """
    redact_ids: list[str] = []
    reasons: list[str] = []

    for claim in unit.claims:
        # Claims with high authority in externally-shared units
        if unit.allow_external and claim.authority_tier and claim.authority_tier <= 2:
            cid = claim.id or "unknown"
            redact_ids.append(cid)
            reasons.append(f"[{cid}] High-authority claim in externally-shared unit")

        # AI claims without risk in confidential+ units
        if (claim.ai_generated and not claim.risk
                and label_rank(unit.classification) >= HIERARCHY.get("confidential", 2)):
            cid = claim.id or "unknown"
            if cid not in redact_ids:
                redact_ids.append(cid)
                reasons.append(f"[{cid}] Undisclosed AI risk in classified unit")

    return {
        "redact": redact_ids,
        "reasons": reasons,
        "total": len(redact_ids),
    }


def compute_security_hash(unit: AKF) -> str:
    """Compute SHA-256 of canonical sorted JSON (excluding hash field itself).

    Args:
        unit: AKF unit.

    Returns:
        Hash string with 'sha256:' prefix.
    """
    d = unit.to_dict(compact=False)
    # Exclude the hash field itself
    d.pop("integrity_hash", None)
    d.pop("hash", None)

    canonical = json.dumps(d, sort_keys=True, ensure_ascii=False)
    hash_hex = hashlib.sha256(canonical.encode()).hexdigest()
    return f"sha256:{hash_hex}"
