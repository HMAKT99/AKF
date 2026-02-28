"""AKF v1.0 — Pydantic v2 models for Agent Knowledge Format."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class Fidelity(BaseModel):
    """Multi-resolution fidelity for a claim."""

    model_config = {"extra": "allow"}

    h: Optional[str] = None  # headline (~5 tokens)
    s: Optional[str] = None  # summary (~50 tokens)
    f: Optional[str] = None  # full detail (~2000 tokens)


class Claim(BaseModel):
    """A single knowledge claim with trust metadata."""

    model_config = {"extra": "allow"}

    c: str  # content (required)
    t: float = Field(ge=0.0, le=1.0)  # trust score (required)
    id: Optional[str] = None
    src: Optional[str] = None
    uri: Optional[str] = None
    tier: Optional[int] = Field(None, ge=1, le=5)
    ver: Optional[bool] = None
    ver_by: Optional[str] = None
    ai: Optional[bool] = None
    risk: Optional[str] = None
    decay: Optional[int] = None
    exp: Optional[str] = None
    tags: Optional[List[str]] = None
    contra: Optional[str] = None
    fidelity: Optional[Fidelity] = None

    @model_validator(mode="before")
    @classmethod
    def _auto_id(cls, data: Any) -> Any:
        if isinstance(data, dict) and not data.get("id"):
            data["id"] = str(uuid.uuid4())[:8]
        return data


class ProvHop(BaseModel):
    """A single hop in the provenance chain."""

    model_config = {"extra": "allow", "populate_by_name": True}

    hop: int
    by: str
    do: str = Field(alias="do")
    at: str
    h: Optional[str] = None
    pen: Optional[float] = None
    adds: Optional[List[str]] = None
    drops: Optional[List[str]] = None

    def model_dump(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


class AKF(BaseModel):
    """Root AKF envelope — the top-level knowledge unit."""

    model_config = {"extra": "allow"}

    v: str  # version (required)
    claims: List[Claim] = Field(min_length=1)  # non-empty
    id: Optional[str] = None
    by: Optional[str] = None
    agent: Optional[str] = None
    at: Optional[str] = None
    label: Optional[str] = None
    inherit: Optional[bool] = None
    ext: Optional[bool] = None
    ttl: Optional[int] = None
    prov: Optional[List[ProvHop]] = None
    hash: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

    @model_validator(mode="before")
    @classmethod
    def _auto_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("id"):
                data["id"] = "akf-{}".format(uuid.uuid4().hex[:12])
            if not data.get("at"):
                data["at"] = datetime.now(timezone.utc).isoformat()
        return data

    # --- Convenience methods ---

    def to_dict(self) -> dict:
        """Serialize to dict, excluding None fields."""
        return _strip_none(self.model_dump(by_alias=True))

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize to compact JSON string, excluding None fields."""
        import json

        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save(self, path: str) -> None:
        """Save to .akf file (compact JSON, no None fields)."""
        import json

        with open(path, "w") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False)
            f.write("\n")

    def inspect(self) -> str:
        """Pretty-print with trust indicators."""
        lines: list = []
        lines.append("AKF {} | {}".format(self.v, self.id))
        if self.by:
            lines.append("  by: {}".format(self.by))
        if self.label:
            lines.append("  label: {}".format(self.label))
        lines.append("  claims: {}".format(len(self.claims)))
        lines.append("")
        for claim in self.claims:
            icon = (
                "\u2705" if claim.t >= 0.8 else "\u26a0\ufe0f " if claim.t >= 0.5 else "\u274c"
            )
            tier_str = "Tier {}".format(claim.tier) if claim.tier else ""
            src_str = claim.src or ""
            ver_str = " verified" if claim.ver else ""
            ai_str = " [AI]" if claim.ai else ""
            lines.append(
                '  {} {:.2f}  "{}"  {}  {}{}{}'.format(
                    icon, claim.t, claim.c, src_str, tier_str, ver_str, ai_str
                )
            )
        if self.prov:
            lines.append("")
            lines.append("  Provenance:")
            for hop in self.prov:
                h_short = hop.h[:15] + "..." if hop.h else ""
                lines.append(
                    "    hop {}: {} {} @ {}  {}".format(hop.hop, hop.by, hop.do, hop.at, h_short)
                )
        return "\n".join(lines)


def _strip_none(obj: Any) -> Any:
    """Recursively remove None values from dicts."""
    if isinstance(obj, dict):
        return {k: _strip_none(v) for k, v in obj.items() if v is not None}
    if isinstance(obj, list):
        return [_strip_none(item) for item in obj]
    return obj
