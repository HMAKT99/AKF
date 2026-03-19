"""Cross-platform agent identity for AKF.

Provides AgentCard (rich agent identity with hash verification) and
AgentRegistry (persistent registry backed by .akf/agents.json).
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class AgentCard(BaseModel):
    """Rich agent identity card with integrity verification."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    name: str
    capabilities: Optional[List[str]] = Field(
        default=None, validation_alias=AliasChoices("capabilities", "caps")
    )
    trust_ceiling: Optional[float] = Field(
        default=None,
        validation_alias=AliasChoices("trust_ceiling", "ceil"),
        ge=0.0,
        le=1.0,
    )
    platform: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("platform", "plat")
    )
    model: Optional[str] = Field(default=None)
    version: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("version", "ver")
    )
    provider: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("provider", "prov")
    )
    created_at: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("created_at", "at")
    )
    card_hash: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("card_hash", "h")
    )


class AgentRegistry:
    """Registry backed by .akf/agents.json."""

    def __init__(self, base_dir: str = ".akf"):
        self.base_dir = base_dir
        self.registry_path = os.path.join(base_dir, "agents.json")

    def register(self, card: AgentCard) -> AgentCard:
        """Register an agent card. Computes hash and saves."""
        data = self._load()
        data[card.id] = card.model_dump(exclude_none=True)
        self._save(data)
        return card

    def get(self, agent_id: str) -> Optional[AgentCard]:
        """Get an agent card by ID."""
        data = self._load()
        entry = data.get(agent_id)
        if entry is None:
            return None
        return AgentCard.model_validate(entry)

    def list(self) -> List[AgentCard]:
        """List all registered agent cards."""
        data = self._load()
        return [AgentCard.model_validate(v) for v in data.values()]

    def remove(self, agent_id: str) -> bool:
        """Remove an agent card by ID."""
        data = self._load()
        if agent_id not in data:
            return False
        del data[agent_id]
        self._save(data)
        return True

    def _load(self) -> Dict[str, dict]:
        if not os.path.exists(self.registry_path):
            return {}
        with open(self.registry_path, "r") as f:
            return json.load(f)

    def _save(self, data: Dict[str, dict]) -> None:
        os.makedirs(self.base_dir, exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")


def _compute_card_hash(card: AgentCard) -> str:
    """Compute SHA-256 hash of card contents (excluding the hash field itself)."""
    d = card.model_dump(exclude_none=True)
    d.pop("card_hash", None)
    canonical = json.dumps(d, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def create_agent_card(
    name: str,
    platform: Optional[str] = None,
    capabilities: Optional[List[str]] = None,
    trust_ceiling: Optional[float] = None,
    model: Optional[str] = None,
    version: Optional[str] = None,
    provider: Optional[str] = None,
) -> AgentCard:
    """Create a new agent card with auto-generated ID and hash."""
    now = datetime.now(timezone.utc).isoformat()
    raw_id = f"{name}-{now}"
    agent_id = hashlib.sha256(raw_id.encode("utf-8")).hexdigest()[:16]

    card = AgentCard(
        id=agent_id,
        name=name,
        platform=platform,
        capabilities=capabilities,
        trust_ceiling=trust_ceiling,
        model=model,
        version=version,
        provider=provider,
        created_at=now,
    )
    card.card_hash = _compute_card_hash(card)
    return card


def verify_agent_card(card: AgentCard) -> bool:
    """Verify the integrity of an agent card by recomputing its hash."""
    if card.card_hash is None:
        return False
    expected = _compute_card_hash(card)
    return card.card_hash == expected


def to_agent_profile(card: AgentCard):
    """Convert AgentCard to AgentProfile (from models.py) for use in AKF units."""
    from .models import AgentProfile

    return AgentProfile(
        id=card.id,
        name=card.name,
        model=card.model,
        version=card.version,
        capabilities=card.capabilities,
        trust_ceiling=card.trust_ceiling,
    )
