"""AKF v1.0 — Trust computation engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

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

    Formula: effective_trust = confidence * authority_weight * temporal_decay * (1 + cumulative_penalty)
    """
    conf = claim.confidence
    tier = claim.authority_tier if claim.authority_tier is not None else 3
    authority = AUTHORITY_WEIGHTS.get(tier, 0.70)

    # Temporal decay: 0.5^(age_days / half_life_days)
    half_life = claim.decay_half_life if claim.decay_half_life else None
    if half_life and half_life > 0 and age_days > 0:
        decay = 0.5 ** (age_days / half_life)
    else:
        decay = 1.0

    # Penalty factor: (1 + cumulative_penalty) where penalty is negative
    penalty_factor = 1.0 + penalty

    score = conf * authority * decay * penalty_factor
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
            "decay": round(decay, 4),
            "penalty": penalty,
            "penalty_factor": round(penalty_factor, 4),
        },
    )


def explain_trust(claim: Claim, age_days: float = 0, penalty: float = 0) -> str:
    """Return a human-readable explanation of trust computation for a claim."""
    result = effective_trust(claim, age_days=age_days, penalty=penalty)
    b = result.breakdown

    lines = [f'Trust Analysis for "{claim.content}"', "=" * 40]
    lines.append(f"  Base confidence:    {b['confidence']:.2f}")
    lines.append(f"  Authority tier:     {b['tier']} (weight: {b['authority']:.2f})")
    if b["decay"] < 1.0:
        half_life = claim.decay_half_life or "N/A"
        lines.append(f"  Temporal decay:     {b['decay']:.4f} (half-life: {half_life}d, age: {age_days}d)")
    if b["penalty"] != 0:
        lines.append(f"  Penalty:            {b['penalty']:+.4f} (factor: {b['penalty_factor']:.4f})")
    lines.append(f"  ─────────────────────────────────")
    lines.append(f"  Effective trust:    {result.score:.4f}")
    lines.append(f"  Decision:           {result.decision}")

    if result.decision == "ACCEPT":
        lines.append("  → Claim meets trust threshold for use.")
    elif result.decision == "LOW":
        lines.append("  → Claim has low trust. Use with caution.")
    else:
        lines.append("  → Claim does not meet minimum trust. Consider discarding.")

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
