"""AKF v1.1 — A2A (Agent-to-Agent) Protocol Bridge.

Converts between AKF AgentCards and A2A-compatible agent card format
for cross-platform agent discovery and interoperability.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from .agent_card import AgentCard, AgentRegistry, create_agent_card


def to_a2a_card(card: AgentCard) -> Dict:
    """Export an AKF AgentCard as an A2A-compatible JSON dict.

    Maps AKF fields to A2A Agent Card schema:
    - name -> name
    - capabilities -> skills (list of {id, name})
    - provider -> provider.organization
    - model -> provider.model
    - platform -> provider.platform (AKF extension)
    - version -> version
    - trust_ceiling -> securityPolicy.trustCeiling (AKF extension)
    """
    a2a: Dict = {
        "name": card.name,
        "version": card.version or "1.0",
    }

    # Skills from capabilities
    if card.capabilities:
        a2a["skills"] = [
            {"id": cap, "name": cap} for cap in card.capabilities
        ]

    # Provider info
    provider: Dict = {}
    if card.provider:
        provider["organization"] = card.provider
    if card.model:
        provider["model"] = card.model
    if card.platform:
        provider["platform"] = card.platform
    if provider:
        a2a["provider"] = provider

    # AKF extensions
    if card.trust_ceiling is not None:
        a2a["securityPolicy"] = {"trustCeiling": card.trust_ceiling}

    # Metadata
    a2a["metadata"] = {
        "akf_id": card.id,
        "akf_hash": card.card_hash,
    }
    if card.created_at:
        a2a["metadata"]["created_at"] = card.created_at

    return a2a


def from_a2a_card(data: Dict) -> AgentCard:
    """Import an A2A-compatible agent card as an AKF AgentCard.

    Reverse mapping of to_a2a_card.
    """
    name = data.get("name", "unknown")
    version = data.get("version")

    # Extract capabilities from skills
    capabilities = None
    skills = data.get("skills")
    if skills:
        capabilities = [s.get("name", s.get("id", "")) for s in skills]

    # Extract provider info
    provider_data = data.get("provider", {})
    provider = provider_data.get("organization")
    model = provider_data.get("model")
    platform = provider_data.get("platform")

    # Trust ceiling from security policy
    trust_ceiling = None
    security = data.get("securityPolicy", {})
    if "trustCeiling" in security:
        trust_ceiling = security["trustCeiling"]

    # Check for existing AKF metadata
    metadata = data.get("metadata", {})
    akf_id = metadata.get("akf_id")
    created_at = metadata.get("created_at")
    card_hash = metadata.get("akf_hash")

    if akf_id:
        # Reconstruct from known AKF card
        card = AgentCard(
            id=akf_id,
            name=name,
            capabilities=capabilities,
            trust_ceiling=trust_ceiling,
            platform=platform,
            model=model,
            version=version,
            provider=provider,
            created_at=created_at,
            card_hash=card_hash,
        )
    else:
        # Create new card from A2A data
        card = create_agent_card(
            name=name,
            platform=platform,
            capabilities=capabilities,
            trust_ceiling=trust_ceiling,
            model=model,
            version=version,
            provider=provider,
        )

    return card


def save_a2a_card(
    card: AgentCard,
    path: Optional[str] = None,
) -> str:
    """Save an AgentCard as an A2A-compatible JSON file.

    Args:
        card: The AgentCard to export.
        path: Output file path. Defaults to .akf/agent-cards/<id>.json.

    Returns:
        Path to the saved file.
    """
    if path is None:
        cards_dir = os.path.join(".akf", "agent-cards")
        os.makedirs(cards_dir, exist_ok=True)
        path = os.path.join(cards_dir, f"{card.id}.json")

    a2a = to_a2a_card(card)

    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(path, "w") as f:
        json.dump(a2a, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return path


def discover_a2a_cards(
    directory: Optional[str] = None,
) -> List[AgentCard]:
    """Discover A2A agent cards in a directory.

    Scans for .json files and attempts to parse them as A2A cards.

    Args:
        directory: Directory to scan. Defaults to .akf/agent-cards/.

    Returns:
        List of AgentCards parsed from discovered files.
    """
    if directory is None:
        directory = os.path.join(".akf", "agent-cards")

    if not os.path.isdir(directory):
        return []

    cards: List[AgentCard] = []
    for fname in sorted(os.listdir(directory)):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(directory, fname)
        try:
            with open(fpath) as f:
                data = json.load(f)
            # Must have at least a name to be a valid card
            if "name" in data:
                cards.append(from_a2a_card(data))
        except (json.JSONDecodeError, KeyError, TypeError):
            continue

    return cards
