"""AKF v1.1 — Trust computation engine."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from .models import AKF, Claim

AUTHORITY_WEIGHTS: dict[int, float] = {
    1: 1.00,
    2: 0.85,
    3: 0.70,
    4: 0.50,
    5: 0.30,
}

DECAY_PRESETS: dict[str, float] = {
    "realtime": 0.001,
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
    "quarterly": 90,
    "annual": 365,
    "legal": 1825,
    "scientific": 3650,
    "permanent": 365000,
}

# v1.1 trust constants
ORIGIN_WEIGHTS: dict[str, float] = {
    "human": 1.0,
    "ai_supervised_by_human": 0.9,
    "collaboration": 0.85,
    "human_assisted_by_ai": 0.85,
    "ai": 0.7,
    "multi_agent": 0.60,
    "ai_chain": 0.5,
}

GROUNDING_BONUS = 0.05  # per evidence piece, max 0.15
REVIEW_BONUS: dict[str, float] = {
    "approved": 0.1,
    "needs_changes": 0.0,
    "rejected": -0.2,
}
CHAIN_PENALTY_PER_HOP = -0.02


class TrustLevel(Enum):
    """Trust decision levels with thresholds."""

    ACCEPT = "ACCEPT"
    LOW = "LOW"
    REJECT = "REJECT"

    @staticmethod
    def from_score(score: float) -> "TrustLevel":
        if score >= 0.7:
            return TrustLevel.ACCEPT
        elif score >= 0.4:
            return TrustLevel.LOW
        return TrustLevel.REJECT

    @property
    def threshold(self) -> float:
        return {TrustLevel.ACCEPT: 0.7, TrustLevel.LOW: 0.4, TrustLevel.REJECT: 0.0}[self]


@dataclass
class TrustResult:
    """Result of trust computation for a single claim."""

    score: float
    decision: str  # "ACCEPT" | "LOW" | "REJECT"
    breakdown: dict
    grounded: bool = False
    evidence_count: int = 0

    @property
    def accepted(self) -> bool:
        return self.decision == "ACCEPT"

    @property
    def level(self) -> TrustLevel:
        return TrustLevel.from_score(self.score)


def effective_trust(
    claim: Claim,
    age_days: float = 0,
    penalty: float = 0,
) -> TrustResult:
    """Compute effective trust for a single claim.

    Enhanced formula (v1.1):
        score = confidence * authority_weight * origin_weight * temporal_decay * penalty_factor
                + grounding_bonus + review_bonus + chain_penalty
    """
    conf = claim.confidence
    tier = claim.authority_tier if claim.authority_tier is not None else 3
    authority = AUTHORITY_WEIGHTS.get(tier, 0.70)

    # Origin weight (v1.1)
    origin_weight = 1.0
    if claim.origin is not None:
        origin_weight = ORIGIN_WEIGHTS.get(claim.origin.type, 0.7)

    # Temporal decay: 0.5^(age_days / half_life_days)
    half_life = claim.decay_half_life if claim.decay_half_life else None
    if half_life and half_life > 0 and age_days > 0:
        decay = 0.5 ** (age_days / half_life)
    else:
        decay = 1.0

    # Penalty factor: (1 + cumulative_penalty) where penalty is negative
    penalty_factor = 1.0 + penalty

    base_score = conf * authority * origin_weight * decay * penalty_factor

    # Grounding bonus (v1.1): +0.05 per evidence, max 0.15
    ev_count = len(claim.evidence) if claim.evidence else 0
    is_grounded = ev_count > 0
    grounding_bonus = min(ev_count * GROUNDING_BONUS, 0.15)

    # Review bonus (v1.1)
    review_bonus = 0.0
    if claim.reviews:
        for review in claim.reviews:
            review_bonus += REVIEW_BONUS.get(review.verdict, 0.0)

    # Chain penalty (v1.1) — not applicable at claim level, but available
    chain_penalty = 0.0

    score = base_score + grounding_bonus + review_bonus + chain_penalty
    score = max(0.0, min(1.0, score))  # clamp

    if score >= 0.7:
        decision = "ACCEPT"
    elif score >= 0.4:
        decision = "LOW"
    else:
        decision = "REJECT"

    return TrustResult(
        score=round(score, 4),
        decision=decision,
        breakdown={
            "confidence": conf,
            "authority": authority,
            "tier": tier,
            "origin_weight": origin_weight,
            "decay": round(decay, 4),
            "penalty": penalty,
            "penalty_factor": round(penalty_factor, 4),
            "grounding_bonus": round(grounding_bonus, 4),
            "review_bonus": round(review_bonus, 4),
            "chain_penalty": chain_penalty,
        },
        grounded=is_grounded,
        evidence_count=ev_count,
    )


def explain_trust(claim: Claim, age_days: float = 0, penalty: float = 0) -> str:
    """Return a human-readable explanation of trust computation for a claim."""
    result = effective_trust(claim, age_days=age_days, penalty=penalty)
    b = result.breakdown

    lines = [f'Trust Analysis for "{claim.content}"', "=" * 40]
    lines.append(f"  Base confidence:    {b['confidence']:.2f}")
    lines.append(f"  Authority tier:     {b['tier']} (weight: {b['authority']:.2f})")
    if b.get("origin_weight", 1.0) != 1.0:
        origin_type = claim.origin.type if claim.origin else "unknown"
        lines.append(f"  Origin weight:      {b['origin_weight']:.2f} ({origin_type})")
    if b["decay"] < 1.0:
        half_life = claim.decay_half_life or "N/A"
        lines.append(f"  Temporal decay:     {b['decay']:.4f} (half-life: {half_life}d, age: {age_days}d)")
    if b["penalty"] != 0:
        lines.append(f"  Penalty:            {b['penalty']:+.4f} (factor: {b['penalty_factor']:.4f})")
    if b.get("grounding_bonus", 0) > 0:
        lines.append(f"  Grounding bonus:    +{b['grounding_bonus']:.4f}")
    if b.get("review_bonus", 0) != 0:
        lines.append(f"  Review bonus:       {b['review_bonus']:+.4f}")
    lines.append(f"  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500")
    lines.append(f"  Effective trust:    {result.score:.4f}")
    lines.append(f"  Decision:           {result.decision}")

    if result.evidence_count > 0:
        lines.append(f"  Evidence:           {result.evidence_count} piece(s) \u2014 grounded")
    else:
        lines.append(f"  Evidence:           none \u2014 ungrounded")

    if result.decision == "ACCEPT":
        lines.append("  \u2192 Claim meets trust threshold for use.")
    elif result.decision == "LOW":
        lines.append("  \u2192 Claim has low trust. Use with caution.")
    else:
        lines.append("  \u2192 Claim does not meet minimum trust. Consider discarding.")

    return "\n".join(lines)


def compute_all(
    unit: AKF,
    age_days: float = 0,
    penalty: float = 0,
    threshold: float = 0.6,
) -> list[TrustResult]:
    """Compute trust for all claims in an AKF unit."""
    results = []
    for claim in unit.claims:
        result = effective_trust(claim, age_days=age_days, penalty=penalty)
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# v1.1 — New trust functions
# ---------------------------------------------------------------------------

def calibrated_trust(
    claim: Claim,
    references: List[Claim],
    age_days: float = 0,
    penalty: float = 0,
) -> TrustResult:
    """Cross-reference calibration.

    If the claim contradicts higher-trust claims in references, penalize.
    If it aligns with high-trust references, the score is unchanged.
    """
    result = effective_trust(claim, age_days=age_days, penalty=penalty)
    calibration_penalty = 0.0

    if claim.contradicts:
        for ref in references:
            if ref.id == claim.contradicts:
                ref_result = effective_trust(ref, age_days=age_days)
                if ref_result.score > result.score:
                    calibration_penalty = -0.15
                break

    if calibration_penalty != 0:
        adjusted = max(0.0, min(1.0, result.score + calibration_penalty))
        if adjusted >= 0.7:
            decision = "ACCEPT"
        elif adjusted >= 0.4:
            decision = "LOW"
        else:
            decision = "REJECT"
        result = TrustResult(
            score=round(adjusted, 4),
            decision=decision,
            breakdown={**result.breakdown, "calibration_penalty": calibration_penalty},
            grounded=result.grounded,
            evidence_count=result.evidence_count,
        )

    return result


def resolve_conflict(claims: List[Claim]) -> dict:
    """Given claims where some contradict others, return winner + explanation.

    Returns:
        Dict with 'winner' (Claim), 'explanation' (str), 'scores' (list of dicts).
    """
    if not claims:
        return {"winner": None, "explanation": "No claims provided", "scores": []}

    scored = []
    for c in claims:
        result = effective_trust(c)
        scored.append({"claim": c, "score": result.score, "decision": result.decision})

    scored.sort(key=lambda x: x["score"], reverse=True)
    winner = scored[0]["claim"]

    explanation_parts = []
    for i, entry in enumerate(scored):
        marker = " (winner)" if i == 0 else ""
        explanation_parts.append(
            f"  [{entry['claim'].id}] score={entry['score']:.4f} "
            f'"{entry["claim"].content}"{marker}'
        )

    explanation = "Conflict resolution by trust score:\n" + "\n".join(explanation_parts)

    return {
        "winner": winner,
        "explanation": explanation,
        "scores": [{"id": e["claim"].id, "score": e["score"], "decision": e["decision"]} for e in scored],
    }


def trust_summary(unit: AKF) -> dict:
    """Compute summary trust statistics for a unit.

    Returns:
        Dict with min, max, mean, median, grounded_pct, ai_pct.
    """
    if not unit.claims:
        return {"min": 0, "max": 0, "mean": 0, "median": 0, "grounded_pct": 0, "ai_pct": 0}

    results = compute_all(unit)
    scores = [r.score for r in results]

    grounded_count = sum(1 for r in results if r.grounded)
    ai_count = sum(1 for c in unit.claims if c.ai_generated or (c.origin and c.origin.type in ("ai", "ai_chain")))

    return {
        "min": round(min(scores), 4),
        "max": round(max(scores), 4),
        "mean": round(statistics.mean(scores), 4),
        "median": round(statistics.median(scores), 4),
        "grounded_pct": round(grounded_count / len(unit.claims), 4),
        "ai_pct": round(ai_count / len(unit.claims), 4),
    }


# ---------------------------------------------------------------------------
# v1.1 — Claim freshness helpers
# ---------------------------------------------------------------------------

def is_expired(claim: Claim) -> bool:
    """Check if a claim has passed its expiry date."""
    expires = getattr(claim, "expires_at", None)
    if not expires:
        return False
    try:
        expiry_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) > expiry_dt
    except (ValueError, TypeError):
        return False


def freshness_status(claim: Claim) -> str:
    """Returns: 'fresh', 'stale', 'expired', or 'no_expiry'."""
    if not getattr(claim, "expires_at", None):
        return "no_expiry"
    if is_expired(claim):
        return "expired"
    verified = getattr(claim, "verified_at", None)
    if not verified:
        return "stale"
    return "fresh"
