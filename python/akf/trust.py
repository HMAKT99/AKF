"""AKF v1.0 — Trust computation engine."""

from __future__ import annotations

from dataclasses import dataclass

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


@dataclass
class TrustResult:
    """Result of trust computation for a single claim."""

    score: float
    decision: str  # "ACCEPT" | "LOW" | "REJECT"
    breakdown: dict

    @property
    def accepted(self) -> bool:
        return self.decision == "ACCEPT"


def effective_trust(
    claim: Claim,
    age_days: float = 0,
    penalty: float = 0,
) -> TrustResult:
    """Compute effective trust for a single claim.

    Formula: effective_trust = t * authority_weight * temporal_decay * (1 + cumulative_penalty)
    """
    confidence = claim.t
    tier = claim.tier if claim.tier is not None else 3
    authority = AUTHORITY_WEIGHTS.get(tier, 0.70)

    # Temporal decay: 0.5^(age_days / half_life_days)
    half_life = claim.decay if claim.decay else None
    if half_life and half_life > 0 and age_days > 0:
        decay = 0.5 ** (age_days / half_life)
    else:
        decay = 1.0

    # Penalty factor: (1 + cumulative_penalty) where penalty is negative
    penalty_factor = 1.0 + penalty

    score = confidence * authority * decay * penalty_factor
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
            "confidence": confidence,
            "authority": authority,
            "tier": tier,
            "decay": round(decay, 4),
            "penalty": penalty,
            "penalty_factor": round(penalty_factor, 4),
        },
    )


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
