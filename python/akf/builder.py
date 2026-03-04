"""AKF v1.0 — Fluent builder API."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from .models import AKF, Claim, ProvHop
from .provenance import compute_integrity_hash


class AKFBuilder:
    """Fluent builder for constructing AKF units."""

    def __init__(self) -> None:
        self._claims: List[Claim] = []
        self._by: Optional[str] = None
        self._agent_id: Optional[str] = None
        self._label: Optional[str] = None
        self._inherit: Optional[bool] = None
        self._ext: Optional[bool] = None
        self._ttl: Optional[int] = None
        self._meta: Optional[dict] = None

    def claim(self, content: str, trust: float, **kwargs) -> "AKFBuilder":
        """Add a claim."""
        self._claims.append(Claim(content=content, confidence=trust, **kwargs))
        return self

    def by(self, author: str) -> "AKFBuilder":
        """Set author."""
        self._by = author
        return self

    def agent(self, agent_id: str) -> "AKFBuilder":
        """Set AI agent."""
        self._agent_id = agent_id
        return self

    def label(self, classification: str) -> "AKFBuilder":
        """Set security classification."""
        self._label = classification
        return self

    def inherit(self, value: bool = True) -> "AKFBuilder":
        """Set inheritance flag."""
        self._inherit = value
        return self

    def ext(self, value: bool = True) -> "AKFBuilder":
        """Set external sharing flag."""
        self._ext = value
        return self

    def ttl(self, days: int) -> "AKFBuilder":
        """Set retention period in days."""
        self._ttl = days
        return self

    def tag(self, *tags: str) -> "AKFBuilder":
        """Add tags to the last claim."""
        if not self._claims:
            raise ValueError("No claims to tag — add a claim first")
        last = self._claims[-1]
        existing = list(last.tags) if last.tags else []
        existing.extend(tags)
        self._claims[-1] = last.model_copy(update={"tags": existing})
        return self

    def meta(self, **kwargs) -> "AKFBuilder":
        """Set free-form metadata."""
        self._meta = kwargs
        return self

    def build(self) -> AKF:
        """Build the AKF unit."""
        if not self._claims:
            raise ValueError("At least one claim is required")

        now = datetime.now(timezone.utc).isoformat()
        unit_id = "akf-{}".format(uuid.uuid4().hex[:12])

        # Auto-create provenance hop 0
        prov: Optional[List[ProvHop]] = None
        if self._by or self._agent_id:
            actor = self._by or self._agent_id or "unknown"
            prov = [
                ProvHop(
                    hop=0,
                    actor=actor,
                    action="created",
                    timestamp=now,
                    claims_added=[c.id for c in self._claims if c.id],
                )
            ]

        unit = AKF(
            version="1.0",
            id=unit_id,
            claims=self._claims,
            author=self._by,
            agent=self._agent_id,
            created=now,
            classification=self._label if self._label is not None else "internal",
            inherit_classification=self._inherit if self._inherit is not None else True,
            allow_external=self._ext if self._ext is not None else False,
            ttl=self._ttl,
            prov=prov,
            meta=self._meta,
        )

        # Auto-compute integrity hash
        integrity = compute_integrity_hash(unit)
        unit = unit.model_copy(update={"integrity_hash": integrity})

        return unit
