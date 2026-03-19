"""AKF v1.1 -- Agent-to-agent trust delegation.

Enables one agent to delegate work to another with a trust ceiling cap,
ensuring the delegate's output never exceeds the delegator's policy limit.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import AKF, Claim, DelegationPolicy
from .agent import derive


def validate_delegation(policy: DelegationPolicy) -> List[str]:
    """Validate a delegation policy.

    Args:
        policy: The delegation policy to validate.

    Returns:
        List of warning messages. Empty list if valid.
    """
    warnings: List[str] = []

    # Check ceiling in valid range (already enforced by Pydantic, but belt-and-suspenders)
    if policy.trust_ceiling < 0.0 or policy.trust_ceiling > 1.0:
        warnings.append(
            f"trust_ceiling {policy.trust_ceiling} is outside valid range [0.0, 1.0]"
        )

    # Check if expired
    if policy.expires:
        try:
            expiry_dt = datetime.fromisoformat(
                policy.expires.replace("Z", "+00:00")
            )
            if datetime.now(timezone.utc) > expiry_dt:
                warnings.append(
                    f"delegation policy expired at {policy.expires}"
                )
        except (ValueError, TypeError):
            warnings.append(
                f"invalid expires format: {policy.expires}"
            )

    return warnings


def delegate(
    parent: AKF,
    policy: DelegationPolicy,
    claims: Optional[List[Dict[str, Any]]] = None,
    transform_penalty: float = -0.05,
) -> AKF:
    """Delegate work from parent agent to delegate agent with trust ceiling.

    Uses the existing ``derive()`` flow but caps all claim confidences at
    ``policy.trust_ceiling`` and records the delegation policy in the
    provenance hop.

    Args:
        parent: The parent AKF unit being delegated.
        policy: Delegation policy defining ceiling and constraints.
        claims: Optional new claims to add (as dicts).
        transform_penalty: Penalty applied to inherited claims.

    Returns:
        Derived AKF unit with trust-capped claims and delegation provenance.

    Raises:
        ValueError: If the delegation policy is expired.
    """
    # Validate policy first
    warnings = validate_delegation(policy)
    for w in warnings:
        if "expired" in w:
            raise ValueError(w)

    # Use derive() to create the delegated unit
    derived = derive(
        parent,
        agent_id=policy.delegate,
        claims=claims,
        transform_penalty=transform_penalty,
    )

    # Cap all claim confidences at trust_ceiling
    capped_claims = []
    for claim in derived.claims:
        if claim.confidence > policy.trust_ceiling:
            claim_dict = claim.model_dump()
            claim_dict["confidence"] = policy.trust_ceiling
            capped_claims.append(Claim(**claim_dict))
        else:
            capped_claims.append(claim)

    derived = derived.model_copy(update={"claims": capped_claims})

    # Attach delegation_policy to the last provenance hop
    if derived.prov:
        from .models import ProvHop

        last_hop = derived.prov[-1]
        last_hop_dict = last_hop.model_dump()
        last_hop_dict["delegation_policy"] = policy
        updated_hop = ProvHop(**last_hop_dict)
        derived = derived.model_copy(
            update={"prov": list(derived.prov[:-1]) + [updated_hop]}
        )

    return derived
