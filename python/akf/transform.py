"""AKF v1.0 — AKFTransformer: filter, derive, and transform AKF units."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .models import AKF, Claim
from .provenance import add_hop
from .security import inherit_label
from .trust import effective_trust


class AKFTransformer:
    """Transform a parent .akf into a derived .akf."""

    def __init__(self, parent: AKF) -> None:
        self._parent = parent
        self._claims: list[Claim] = list(parent.claims)
        self._penalty: float = 0
        self._agent: str | None = None
        self._accepted: list[str] = []
        self._rejected: list[str] = []
        self._trust_min: float | None = None

    def filter(self, trust_min: float = 0.6) -> AKFTransformer:
        """Keep only claims above trust threshold (based on effective trust)."""
        self._trust_min = trust_min
        kept: list[Claim] = []
        for claim in self._claims:
            result = effective_trust(claim)
            if result.score >= trust_min:
                kept.append(claim)
                if claim.id:
                    self._accepted.append(claim.id)
            else:
                if claim.id:
                    self._rejected.append(claim.id)
        self._claims = kept
        return self

    def penalty(self, pen: float = -0.03) -> AKFTransformer:
        """Apply transform penalty to all retained claims."""
        self._penalty = pen
        adjusted: list[Claim] = []
        for claim in self._claims:
            new_t = max(0.0, claim.confidence + pen)
            adjusted.append(claim.model_copy(update={"confidence": round(new_t, 4)}))
        self._claims = adjusted
        return self

    def by(self, agent: str) -> AKFTransformer:
        """Set the transforming agent."""
        self._agent = agent
        return self

    def build(self) -> AKF:
        """Build derived .akf with inherited classification and provenance."""
        if not self._claims:
            raise ValueError("No claims survived filtering — cannot build empty AKF")

        now = datetime.now(timezone.utc).isoformat()
        new_id = f"akf-{uuid.uuid4().hex[:12]}"

        # Inherit security from parent
        security = inherit_label(self._parent)

        # Build the derived unit (without provenance first)
        derived = AKF(
            version="1.0",
            id=new_id,
            claims=self._claims,
            author=self._agent,
            created=now,
            prov=list(self._parent.prov) if self._parent.prov else [],
            meta={"parent_id": self._parent.id},
            **security,
        )

        # Add the consumption/transform hop
        actor = self._agent or "unknown"
        derived = add_hop(
            derived,
            by=actor,
            action="consumed",
            adds=self._accepted if self._accepted else None,
            drops=self._rejected if self._rejected else None,
            penalty=self._penalty if self._penalty else None,
        )

        return derived
