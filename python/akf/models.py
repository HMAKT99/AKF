"""AKF v1.0 — Pydantic v2 models for Agent Knowledge Format.

Field names are descriptive by default (content, confidence, source, etc.).
Compact wire-format names (c, t, src, etc.) are accepted on input via
AliasChoices and emitted via to_dict(compact=True).
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Compact alias maps — used for serialization
# ---------------------------------------------------------------------------

_FIDELITY_COMPACT = {"headline": "h", "summary": "s", "full": "f"}
_CLAIM_COMPACT = {
    "content": "c",
    "confidence": "t",
    "source": "src",
    "authority_tier": "tier",
    "verified": "ver",
    "verified_by": "ver_by",
    "ai_generated": "ai",
    "decay_half_life": "decay",
    "expires": "exp",
    "contradicts": "contra",
}
_PROVHOP_COMPACT = {
    "actor": "by",
    "action": "do",
    "timestamp": "at",
    "hash": "h",
    "penalty": "pen",
    "claims_added": "adds",
    "claims_removed": "drops",
}
_AKF_COMPACT = {
    "version": "v",
    "author": "by",
    "created": "at",
    "classification": "label",
    "inherit_classification": "inherit",
    "allow_external": "ext",
    "integrity_hash": "hash",
}


class Fidelity(BaseModel):
    """Multi-resolution fidelity for a claim."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    headline: Optional[str] = Field(None, validation_alias=AliasChoices("h", "headline"))
    summary: Optional[str] = Field(None, validation_alias=AliasChoices("s", "summary"))
    full: Optional[str] = Field(None, validation_alias=AliasChoices("f", "full"))

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _FIDELITY_COMPACT)
        return d


class Claim(BaseModel):
    """A single knowledge claim with trust metadata."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    content: str = Field(validation_alias=AliasChoices("c", "content"))
    confidence: float = Field(ge=0.0, le=1.0, validation_alias=AliasChoices("t", "confidence"))
    id: Optional[str] = None
    source: Optional[str] = Field(None, validation_alias=AliasChoices("src", "source"))
    uri: Optional[str] = None
    authority_tier: Optional[int] = Field(
        None, ge=1, le=5, validation_alias=AliasChoices("tier", "authority_tier")
    )
    verified: Optional[bool] = Field(None, validation_alias=AliasChoices("ver", "verified"))
    verified_by: Optional[str] = Field(
        None, validation_alias=AliasChoices("ver_by", "verified_by")
    )
    ai_generated: Optional[bool] = Field(None, validation_alias=AliasChoices("ai", "ai_generated"))
    risk: Optional[str] = None
    decay_half_life: Optional[int] = Field(
        None, validation_alias=AliasChoices("decay", "decay_half_life")
    )
    expires: Optional[str] = Field(None, validation_alias=AliasChoices("exp", "expires"))
    tags: Optional[List[str]] = None
    contradicts: Optional[str] = Field(
        None, validation_alias=AliasChoices("contra", "contradicts")
    )
    fidelity: Optional[Fidelity] = None

    @model_validator(mode="before")
    @classmethod
    def _auto_id(cls, data: Any) -> Any:
        if isinstance(data, dict) and not data.get("id"):
            data["id"] = str(uuid.uuid4())[:8]
        return data

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if self.fidelity is not None:
            d["fidelity"] = self.fidelity.to_dict(compact=compact)
        if compact:
            d = _remap_keys(d, _CLAIM_COMPACT)
        return d


class ProvHop(BaseModel):
    """A single hop in the provenance chain."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    hop: int
    actor: str = Field(validation_alias=AliasChoices("by", "actor"))
    action: str = Field(validation_alias=AliasChoices("do", "action"))
    timestamp: str = Field(validation_alias=AliasChoices("at", "timestamp"))
    hash: Optional[str] = Field(None, validation_alias=AliasChoices("h", "hash"))
    penalty: Optional[float] = Field(None, validation_alias=AliasChoices("pen", "penalty"))
    claims_added: Optional[List[str]] = Field(
        None, validation_alias=AliasChoices("adds", "claims_added")
    )
    claims_removed: Optional[List[str]] = Field(
        None, validation_alias=AliasChoices("drops", "claims_removed")
    )

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _PROVHOP_COMPACT)
        return d

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        return super().model_dump(**kwargs)


class AKF(BaseModel):
    """Root AKF envelope — the top-level knowledge unit."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    version: str = Field(validation_alias=AliasChoices("v", "version"))
    claims: List[Claim] = Field(min_length=1)
    id: Optional[str] = None
    author: Optional[str] = Field(None, validation_alias=AliasChoices("by", "author"))
    agent: Optional[str] = None
    created: Optional[str] = Field(None, validation_alias=AliasChoices("at", "created"))
    classification: Optional[str] = Field(
        None, validation_alias=AliasChoices("label", "classification")
    )
    inherit_classification: Optional[bool] = Field(
        None, validation_alias=AliasChoices("inherit", "inherit_classification")
    )
    allow_external: Optional[bool] = Field(
        None, validation_alias=AliasChoices("ext", "allow_external")
    )
    ttl: Optional[int] = None
    prov: Optional[List[ProvHop]] = None
    integrity_hash: Optional[str] = Field(
        None, validation_alias=AliasChoices("hash", "integrity_hash")
    )
    meta: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def _auto_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("id"):
                data["id"] = "akf-{}".format(uuid.uuid4().hex[:12])
            if not data.get("at") and not data.get("created"):
                data["created"] = datetime.now(timezone.utc).isoformat()
        return data

    # --- Convenience methods ---

    def to_dict(self, compact: bool = True) -> dict:
        """Serialize to dict, excluding None fields.

        Args:
            compact: If True (default), use compact wire-format names (c, t, src, ...).
                     If False, use descriptive names (content, confidence, source, ...).
        """
        d = _strip_none(self.model_dump())
        # Serialize nested objects
        d["claims"] = [c.to_dict(compact=compact) for c in self.claims]
        if self.prov:
            d["prov"] = [h.to_dict(compact=compact) for h in self.prov]
        if compact:
            d = _remap_keys(d, _AKF_COMPACT)
        return d

    def to_json(self, indent: Optional[int] = None, compact: bool = True) -> str:
        """Serialize to JSON string, excluding None fields.

        Args:
            indent: JSON indentation level. None for compact.
            compact: If True (default), use compact names. If False, descriptive.
        """
        import json

        return json.dumps(self.to_dict(compact=compact), indent=indent, ensure_ascii=False)

    def save(self, path: str, compact: bool = True) -> None:
        """Save to .akf file.

        Args:
            path: File path to save to.
            compact: If True (default), use compact wire-format names.
        """
        import json

        with open(path, "w") as f:
            json.dump(self.to_dict(compact=compact), f, ensure_ascii=False)
            f.write("\n")

    def inspect(self) -> str:
        """Pretty-print with trust indicators."""
        lines: list = []
        lines.append("AKF {} | {}".format(self.version, self.id))
        if self.author:
            lines.append("  by: {}".format(self.author))
        if self.classification:
            lines.append("  label: {}".format(self.classification))
        lines.append("  claims: {}".format(len(self.claims)))
        lines.append("")
        for claim in self.claims:
            icon = (
                "\u2705"
                if claim.confidence >= 0.8
                else "\u26a0\ufe0f " if claim.confidence >= 0.5 else "\u274c"
            )
            tier_str = "Tier {}".format(claim.authority_tier) if claim.authority_tier else ""
            src_str = claim.source or ""
            ver_str = " verified" if claim.verified else ""
            ai_str = " [AI]" if claim.ai_generated else ""
            lines.append(
                '  {} {:.2f}  "{}"  {}  {}{}{}'.format(
                    icon,
                    claim.confidence,
                    claim.content,
                    src_str,
                    tier_str,
                    ver_str,
                    ai_str,
                )
            )
        if self.prov:
            lines.append("")
            lines.append("  Provenance:")
            for hop in self.prov:
                h_short = hop.hash[:15] + "..." if hop.hash else ""
                lines.append(
                    "    hop {}: {} {} @ {}  {}".format(
                        hop.hop, hop.actor, hop.action, hop.timestamp, h_short
                    )
                )
        return "\n".join(lines)

    def __repr__(self) -> str:
        return "AKF(id={!r}, claims={}, classification={!r})".format(
            self.id, len(self.claims), self.classification
        )

    def __str__(self) -> str:
        return self.inspect()


def _strip_none(obj: Any) -> Any:
    """Recursively remove None values from dicts."""
    if isinstance(obj, dict):
        return {k: _strip_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_strip_none(item) for item in obj]
    return obj


def _remap_keys(d: dict, mapping: dict) -> dict:
    """Remap dict keys using a {descriptive: compact} mapping."""
    result = {}
    for k, v in d.items():
        new_key = mapping.get(k, k)
        result[new_key] = v
    return result
