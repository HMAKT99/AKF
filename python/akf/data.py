"""AKF v1.0 — Data utilities for working with claims and units.

Filtering, merging, quality reporting, and optional pandas integration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .core import load, loads
from .models import AKF, Claim
from .trust import effective_trust


def _resolve(target: Union[str, Path, AKF]) -> AKF:
    """Resolve target to an AKF unit."""
    if isinstance(target, AKF):
        return target
    path = Path(target)
    if path.exists():
        return load(path)
    return loads(str(target))


def load_dataset(
    paths: List[Union[str, Path]],
    filters: Optional[Dict[str, Any]] = None,
) -> List[Claim]:
    """Load claims from multiple AKF files.

    Args:
        paths: List of .akf file paths.
        filters: Optional dict with keys like 'min_trust', 'verified_only', etc.

    Returns:
        Flat list of Claim objects.
    """
    all_claims: List[Claim] = []
    for p in paths:
        try:
            unit = load(p)
            all_claims.extend(unit.claims)
        except Exception:
            continue

    if filters:
        all_claims = _apply_filters(all_claims, filters)

    return all_claims


def _apply_filters(claims: List[Claim], filters: Dict[str, Any]) -> List[Claim]:
    """Apply filters to a list of claims."""
    result = list(claims)

    if "min_trust" in filters:
        min_t = filters["min_trust"]
        result = [c for c in result if c.confidence >= min_t]

    if filters.get("verified_only"):
        result = [c for c in result if c.verified]

    if filters.get("exclude_ai"):
        result = [c for c in result if not c.ai_generated]

    if "max_tier" in filters:
        max_tier = filters["max_tier"]
        result = [c for c in result if (c.authority_tier or 3) <= max_tier]

    if "tags" in filters:
        required_tags = set(filters["tags"])
        result = [c for c in result if c.tags and required_tags & set(c.tags)]

    return result


def quality_report(target: Union[str, Path, AKF]) -> Dict[str, Any]:
    """Generate a quality report for an AKF unit.

    Args:
        target: AKF unit, file path, or JSON string.

    Returns:
        Dict with quality metrics.
    """
    unit = _resolve(target)
    claims = unit.claims
    total = len(claims)

    if total == 0:
        return {"total_claims": 0, "quality_score": 0.0}

    avg_trust = sum(c.confidence for c in claims) / total
    sourced = sum(1 for c in claims if c.source and c.source != "unspecified")
    verified = sum(1 for c in claims if c.verified)
    ai_count = sum(1 for c in claims if c.ai_generated)
    with_risk = sum(1 for c in claims if c.risk)
    high_trust = sum(1 for c in claims if c.confidence >= 0.8)
    low_trust = sum(1 for c in claims if c.confidence < 0.5)

    # Quality score: weighted average of various metrics
    source_ratio = sourced / total
    verify_ratio = verified / total
    trust_quality = avg_trust
    quality_score = (trust_quality * 0.4 + source_ratio * 0.3 + verify_ratio * 0.3)

    return {
        "total_claims": total,
        "average_trust": round(avg_trust, 4),
        "high_trust_claims": high_trust,
        "low_trust_claims": low_trust,
        "sourced_claims": sourced,
        "verified_claims": verified,
        "ai_generated_claims": ai_count,
        "claims_with_risk": with_risk,
        "source_coverage": round(source_ratio, 4),
        "verification_coverage": round(verify_ratio, 4),
        "quality_score": round(quality_score, 4),
    }


def to_pandas(target: Union[str, Path, AKF]):
    """Convert an AKF unit's claims to a pandas DataFrame.

    Requires pandas to be installed.

    Args:
        target: AKF unit, file path, or JSON string.

    Returns:
        pandas.DataFrame with one row per claim.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required: pip install pandas")

    unit = _resolve(target)
    rows = []
    for claim in unit.claims:
        row = {
            "id": claim.id,
            "content": claim.content,
            "confidence": claim.confidence,
            "source": claim.source,
            "authority_tier": claim.authority_tier,
            "verified": claim.verified,
            "ai_generated": claim.ai_generated,
            "risk": claim.risk,
            "tags": ",".join(claim.tags) if claim.tags else None,
        }
        # Add effective trust
        result = effective_trust(claim)
        row["effective_trust"] = result.score
        row["trust_decision"] = result.decision
        rows.append(row)

    return pd.DataFrame(rows)


def merge(units: List[AKF]) -> AKF:
    """Merge multiple AKF units into one.

    Takes the highest classification, combines all claims,
    and creates a merged provenance note.

    Args:
        units: List of AKF units.

    Returns:
        Merged AKF unit.
    """
    if not units:
        raise ValueError("Cannot merge empty list of units")

    from .security import label_rank

    all_claims: List[Claim] = []
    seen_ids: set = set()
    highest_class = None
    highest_rank = -1

    for unit in units:
        for claim in unit.claims:
            if claim.id not in seen_ids:
                all_claims.append(claim)
                seen_ids.add(claim.id)
        rank = label_rank(unit.classification)
        if rank > highest_rank:
            highest_rank = rank
            highest_class = unit.classification

    if not all_claims:
        raise ValueError("No claims to merge")

    merged = AKF(
        version="1.0",
        claims=all_claims,
        classification=highest_class,
        meta={"merged_from": [u.id for u in units]},
    )

    return merged


def filter_claims(
    target: Union[str, Path, AKF],
    min_trust: float = 0.0,
    verified_only: bool = False,
    exclude_ai: bool = False,
) -> AKF:
    """Filter claims in an AKF unit.

    Args:
        target: AKF unit, file path, or JSON string.
        min_trust: Minimum confidence threshold.
        verified_only: Only keep verified claims.
        exclude_ai: Exclude AI-generated claims.

    Returns:
        New AKF unit with filtered claims.
    """
    unit = _resolve(target)
    claims = list(unit.claims)

    if min_trust > 0:
        claims = [c for c in claims if c.confidence >= min_trust]
    if verified_only:
        claims = [c for c in claims if c.verified]
    if exclude_ai:
        claims = [c for c in claims if not c.ai_generated]

    if not claims:
        raise ValueError("No claims match the filter criteria")

    return unit.model_copy(update={"claims": claims})
