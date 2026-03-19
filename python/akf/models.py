"""AKF v1.1 — Pydantic v2 models for Agent Knowledge Format.

Field names are descriptive by default (content, confidence, source, etc.).
Compact wire-format names (c, t, src, etc.) are accepted on input via
AliasChoices and emitted via to_dict(compact=True).
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Compact alias maps — used for serialization
# ---------------------------------------------------------------------------

_FIDELITY_COMPACT = {"headline": "h", "summary": "s", "full": "f"}
_EVIDENCE_COMPACT = {
    "type": "type",
    "detail": "detail",
    "timestamp": "at",
    "tool": "tool",
}
_GENERATION_PARAMS_COMPACT = {
    "temperature": "temp",
    "top_p": "top_p",
    "max_tokens": "max_tok",
    "tokens_input": "in_tok",
    "tokens_output": "out_tok",
    "tokens_total": "tot_tok",
    "cost_usd": "cost",
    "prompt_hash": "p_hash",
    "system_prompt_hash": "sys_hash",
    "tools_used": "tools_used",
    "tool_names": "tools",
    "context_sources": "ctx_src",
    "context_window_used_pct": "ctx_pct",
    "cached_tokens": "cache_tok",
    "latency_ms": "lat_ms",
}
_ORIGIN_COMPACT = {
    "type": "type",
    "model": "model",
    "version": "ver",
    "provider": "prov",
    "parameters": "params",
}
_MADE_BY_COMPACT = {
    "actor": "by",
    "role": "role",
    "at": "at",
}
_REVIEW_COMPACT = {
    "reviewer": "by",
    "verdict": "v",
    "comment": "msg",
    "at": "at",
}
_SOURCE_DETAIL_COMPACT = {
    "uri": "uri",
    "retrieved_at": "at",
    "hash": "h",
    "page": "pg",
    "section": "sec",
}
_REASONING_CHAIN_COMPACT = {
    "steps": "steps",
    "conclusion": "end",
    "model": "model",
    "token_count": "tok",
}
_ANNOTATION_COMPACT = {
    "key": "k",
    "value": "val",
    "scope": "scope",
    "at": "at",
}
_FRESHNESS_COMPACT = {
    "retrieved_at": "at",
    "valid_until": "until",
    "refresh_url": "url",
    "stale_after_hours": "stale_h",
}
_COST_METADATA_COMPACT = {
    "input_tokens": "in_tok",
    "output_tokens": "out_tok",
    "model": "model",
    "cost_usd": "cost",
}
_AGENT_PROFILE_COMPACT = {
    "id": "id",
    "name": "name",
    "model": "model",
    "version": "ver",
    "capabilities": "caps",
    "trust_ceiling": "ceil",
}
_CALIBRATION_COMPACT = {
    "method": "method",
    "verifier": "verifier",
    "verified_at": "ver_at",
}
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
    "supersedes": "sup",
    "expires_at": "exp_at",
    "verified_at": "ver_at",
    "depends_on": "deps",
    "relationship": "rel",
    "calibration": "cal",
}
_DELEGATION_POLICY_COMPACT = {
    "delegator": "from",
    "delegate": "to",
    "trust_ceiling": "ceil",
    "allowed_actions": "actions",
    "expires": "exp",
    "scope": "scope",
}
_PROVHOP_COMPACT = {
    "actor": "by",
    "action": "do",
    "timestamp": "at",
    "hash": "h",
    "penalty": "pen",
    "claims_added": "adds",
    "claims_removed": "drops",
    "model": "m",
    "input_hash": "in_h",
    "output_hash": "out_h",
    "duration_ms": "dur",
    "tool_calls": "tools",
    "delegation_policy": "deleg",
}
_AKF_COMPACT = {
    "version": "v",
    "author": "by",
    "created": "at",
    "classification": "label",
    "inherit_classification": "inherit",
    "allow_external": "ext",
    "integrity_hash": "hash",
    "schema_version": "sv",
    "parent_id": "parent",
    "signature": "sig",
    "signature_algorithm": "sig_algo",
    "public_key_id": "key_id",
    "signed_at": "sig_at",
    "signed_by": "sig_by",
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


class Evidence(BaseModel):
    """A piece of evidence supporting a claim."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type: str
    detail: str
    timestamp: Optional[str] = Field(None, validation_alias=AliasChoices("at", "timestamp"))
    tool: Optional[str] = None

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _EVIDENCE_COMPACT)
        return d


# ---------------------------------------------------------------------------
# New v1.1 models
# ---------------------------------------------------------------------------

class GenerationParams(BaseModel):
    """Parameters used during AI generation (Pillar 3)."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    temperature: Optional[float] = Field(None, validation_alias=AliasChoices("temp", "temperature"))
    top_p: Optional[float] = None
    max_tokens: Optional[int] = Field(None, validation_alias=AliasChoices("max_tok", "max_tokens"))
    tokens_input: Optional[int] = Field(None, validation_alias=AliasChoices("in_tok", "tokens_input"))
    tokens_output: Optional[int] = Field(None, validation_alias=AliasChoices("out_tok", "tokens_output"))
    tokens_total: Optional[int] = Field(None, validation_alias=AliasChoices("tot_tok", "tokens_total"))
    cost_usd: Optional[float] = Field(None, validation_alias=AliasChoices("cost", "cost_usd"))
    prompt_hash: Optional[str] = Field(None, validation_alias=AliasChoices("p_hash", "prompt_hash"))
    system_prompt_hash: Optional[str] = Field(
        None, validation_alias=AliasChoices("sys_hash", "system_prompt_hash")
    )
    tools_used: Optional[List[str]] = Field(
        None, validation_alias=AliasChoices("tools_used",)
    )
    tool_names: Optional[List[str]] = Field(
        None, validation_alias=AliasChoices("tools", "tool_names")
    )
    context_sources: Optional[List[str]] = Field(None, validation_alias=AliasChoices("ctx_src", "context_sources"))
    context_window_used_pct: Optional[float] = Field(
        None, validation_alias=AliasChoices("ctx_pct", "context_window_used_pct")
    )
    cached_tokens: Optional[int] = Field(None, validation_alias=AliasChoices("cache_tok", "cached_tokens"))
    latency_ms: Optional[float] = Field(None, validation_alias=AliasChoices("lat_ms", "latency_ms"))

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _GENERATION_PARAMS_COMPACT)
        return d


class Origin(BaseModel):
    """Origin tracking — who/what produced this content and how."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    type: Literal["human", "ai", "human_assisted_by_ai", "ai_supervised_by_human", "ai_chain",
                   "collaboration", "multi_agent"] = Field(
        validation_alias=AliasChoices("type",)
    )
    model: Optional[str] = None
    version: Optional[str] = Field(None, validation_alias=AliasChoices("ver", "version"))
    provider: Optional[str] = Field(None, validation_alias=AliasChoices("prov", "provider"))
    parameters: Optional[GenerationParams] = Field(
        None, validation_alias=AliasChoices("params", "parameters")
    )
    generation: Optional[GenerationParams] = Field(
        None, validation_alias=AliasChoices("generation",)
    )

    @model_validator(mode="before")
    @classmethod
    def _unify_generation(cls, data: Any) -> Any:
        """Accept 'generation' as alias for 'parameters' — merge into parameters."""
        if isinstance(data, dict):
            gen = data.pop("generation", None)
            if gen is not None and data.get("parameters") is None and data.get("params") is None:
                data["parameters"] = gen
        return data

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        # Remove the generation field from output — parameters is canonical
        d.pop("generation", None)
        if self.parameters is not None:
            d["parameters"] = self.parameters.to_dict(compact=compact)
        if compact:
            d = _remap_keys(d, _ORIGIN_COMPACT)
        return d


class MadeBy(BaseModel):
    """Authorship entry in the made_by chain."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    actor: str = Field(validation_alias=AliasChoices("by", "actor"))
    role: Literal["author", "reviewer", "editor", "approver", "system"] = "author"
    at: Optional[str] = None

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _MADE_BY_COMPACT)
        return d


class Review(BaseModel):
    """A review verdict on a claim or unit."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    reviewer: str = Field(validation_alias=AliasChoices("by", "reviewer"))
    verdict: Literal["approved", "rejected", "needs_changes"] = Field(
        validation_alias=AliasChoices("v", "verdict")
    )
    comment: Optional[str] = Field(None, validation_alias=AliasChoices("msg", "comment"))
    at: Optional[str] = None

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _REVIEW_COMPACT)
        return d


class SourceDetail(BaseModel):
    """Detailed source information for grounded claims."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    uri: str
    retrieved_at: Optional[str] = Field(None, validation_alias=AliasChoices("at", "retrieved_at"))
    hash: Optional[str] = Field(None, validation_alias=AliasChoices("h", "hash"))
    page: Optional[int] = Field(None, validation_alias=AliasChoices("pg", "page"))
    section: Optional[str] = Field(None, validation_alias=AliasChoices("sec", "section"))

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _SOURCE_DETAIL_COMPACT)
        return d


class ReasoningChain(BaseModel):
    """Explainability chain for AI-generated claims."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    steps: List[str]
    conclusion: Optional[str] = Field(None, validation_alias=AliasChoices("end", "conclusion"))
    model: Optional[str] = None
    token_count: Optional[int] = Field(None, validation_alias=AliasChoices("tok", "token_count"))

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _REASONING_CHAIN_COMPACT)
        return d


class Annotation(BaseModel):
    """Free-form annotation on a claim, unit, or provenance hop."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    key: str = Field(validation_alias=AliasChoices("k", "key"))
    value: Any = Field(validation_alias=AliasChoices("val", "value"))
    scope: Literal["claim", "unit", "provenance"] = "claim"
    at: Optional[str] = None

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _ANNOTATION_COMPACT)
        return d


class Freshness(BaseModel):
    """Time-sensitivity metadata for claims with expirable data."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    retrieved_at: Optional[str] = Field(None, validation_alias=AliasChoices("at", "retrieved_at"))
    valid_until: Optional[str] = Field(None, validation_alias=AliasChoices("until", "valid_until"))
    refresh_url: Optional[str] = Field(None, validation_alias=AliasChoices("url", "refresh_url"))
    stale_after_hours: Optional[int] = Field(
        None, validation_alias=AliasChoices("stale_h", "stale_after_hours")
    )

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _FRESHNESS_COMPACT)
        return d


class CostMetadata(BaseModel):
    """LLM cost tracking metadata."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    input_tokens: Optional[int] = Field(None, validation_alias=AliasChoices("in_tok", "input_tokens"))
    output_tokens: Optional[int] = Field(
        None, validation_alias=AliasChoices("out_tok", "output_tokens")
    )
    model: Optional[str] = None
    cost_usd: Optional[float] = Field(None, validation_alias=AliasChoices("cost", "cost_usd"))

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _COST_METADATA_COMPACT)
        return d


class AgentProfile(BaseModel):
    """Profile of an AI agent in the provenance chain."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    name: Optional[str] = None
    model: Optional[str] = None
    version: Optional[str] = Field(None, validation_alias=AliasChoices("ver", "version"))
    capabilities: Optional[List[str]] = Field(
        None, validation_alias=AliasChoices("caps", "capabilities")
    )
    trust_ceiling: Optional[float] = Field(
        None, validation_alias=AliasChoices("ceil", "trust_ceiling")
    )

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _AGENT_PROFILE_COMPACT)
        return d


class Calibration(BaseModel):
    """Trust calibration metadata for a claim."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    method: Literal["self_reported", "source_verified", "externally_audited"]
    verifier: Optional[str] = None
    verified_at: Optional[str] = Field(None, validation_alias=AliasChoices("ver_at", "verified_at"))

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _CALIBRATION_COMPACT)
        return d


# ---------------------------------------------------------------------------
# Enhanced existing models
# ---------------------------------------------------------------------------

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
    kind: Optional[str] = None
    evidence: Optional[List["Evidence"]] = None
    # v1.1 fields
    origin: Optional[Origin] = None
    reviews: Optional[List[Review]] = None
    source_detail: Optional[SourceDetail] = Field(
        None, validation_alias=AliasChoices("source_detail",)
    )
    reasoning: Optional[ReasoningChain] = None
    freshness: Optional[Freshness] = None
    annotations: Optional[List[Annotation]] = None
    cost: Optional[CostMetadata] = None
    supersedes: Optional[str] = Field(None, validation_alias=AliasChoices("sup", "supersedes"))
    # Freshness / dependency fields
    expires_at: Optional[str] = Field(None, validation_alias=AliasChoices("exp_at", "expires_at"))
    verified_at: Optional[str] = Field(None, validation_alias=AliasChoices("ver_at", "verified_at"))
    depends_on: Optional[List[str]] = Field(None, validation_alias=AliasChoices("deps", "depends_on"))
    relationship: Optional[str] = Field(None, validation_alias=AliasChoices("rel", "relationship"))
    calibration: Optional[Calibration] = Field(None, validation_alias=AliasChoices("cal", "calibration"))

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
        if self.evidence is not None:
            d["evidence"] = [e.to_dict(compact=compact) for e in self.evidence]
        if self.origin is not None:
            d["origin"] = self.origin.to_dict(compact=compact)
        if self.reviews is not None:
            d["reviews"] = [r.to_dict(compact=compact) for r in self.reviews]
        if self.source_detail is not None:
            d["source_detail"] = self.source_detail.to_dict(compact=compact)
        if self.reasoning is not None:
            d["reasoning"] = self.reasoning.to_dict(compact=compact)
        if self.freshness is not None:
            d["freshness"] = self.freshness.to_dict(compact=compact)
        if self.annotations is not None:
            d["annotations"] = [a.to_dict(compact=compact) for a in self.annotations]
        if self.cost is not None:
            d["cost"] = self.cost.to_dict(compact=compact)
        if self.calibration is not None:
            d["calibration"] = self.calibration.to_dict(compact=compact)
        if compact:
            d = _remap_keys(d, _CLAIM_COMPACT)
        return d


class DelegationPolicy(BaseModel):
    """Policy controlling agent-to-agent trust delegation."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    delegator: str = Field(validation_alias=AliasChoices("delegator", "from"))
    delegate: str = Field(validation_alias=AliasChoices("delegate", "to"))
    trust_ceiling: float = Field(
        validation_alias=AliasChoices("trust_ceiling", "ceil"), ge=0.0, le=1.0
    )
    allowed_actions: Optional[List[str]] = Field(
        default=None, validation_alias=AliasChoices("allowed_actions", "actions")
    )
    expires: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("expires", "exp")
    )
    scope: Optional[str] = Field(default=None)

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if compact:
            d = _remap_keys(d, _DELEGATION_POLICY_COMPACT)
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
    # v1.1 fields
    model: Optional[str] = Field(None, validation_alias=AliasChoices("m", "model"))
    input_hash: Optional[str] = Field(None, validation_alias=AliasChoices("in_h", "input_hash"))
    output_hash: Optional[str] = Field(None, validation_alias=AliasChoices("out_h", "output_hash"))
    agent_profile: Optional[AgentProfile] = None
    duration_ms: Optional[int] = Field(None, validation_alias=AliasChoices("dur", "duration_ms"))
    tool_calls: Optional[List[str]] = Field(
        None, validation_alias=AliasChoices("tools", "tool_calls")
    )
    delegation_policy: Optional[DelegationPolicy] = Field(
        None, validation_alias=AliasChoices("deleg", "delegation_policy")
    )

    def to_dict(self, compact: bool = False) -> dict:
        d = _strip_none(self.model_dump())
        if self.agent_profile is not None:
            d["agent_profile"] = self.agent_profile.to_dict(compact=compact)
        if self.delegation_policy is not None:
            d["delegation_policy"] = self.delegation_policy.to_dict(compact=compact)
        if compact:
            d = _remap_keys(d, _PROVHOP_COMPACT)
        return d



class AKF(BaseModel):
    """Root AKF envelope — the top-level knowledge unit."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    version: str = Field(validation_alias=AliasChoices("v", "version"))
    claims: List[Claim] = Field(min_length=1)
    id: Optional[str] = None
    author: Optional[str] = Field(None, validation_alias=AliasChoices("by", "author"))
    agent: Optional[str] = None
    model: Optional[str] = None
    tools: Optional[List[str]] = None
    session: Optional[str] = None
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
    # v1.1 fields
    made_by: Optional[List[MadeBy]] = None
    reviews: Optional[List[Review]] = None
    security: Optional[Dict[str, Any]] = None
    compliance: Optional[Dict[str, Any]] = None
    cost: Optional[CostMetadata] = None
    annotations: Optional[List[Annotation]] = None
    schema_version: Optional[str] = Field(
        "1.1", validation_alias=AliasChoices("sv", "schema_version")
    )
    parent_id: Optional[str] = Field(None, validation_alias=AliasChoices("parent", "parent_id"))
    # Cryptographic signing fields
    signature: Optional[str] = Field(None, validation_alias=AliasChoices("sig", "signature"))
    signature_algorithm: Optional[str] = Field(
        None, validation_alias=AliasChoices("sig_algo", "signature_algorithm")
    )
    public_key_id: Optional[str] = Field(
        None, validation_alias=AliasChoices("key_id", "public_key_id")
    )
    signed_at: Optional[str] = Field(None, validation_alias=AliasChoices("sig_at", "signed_at"))
    signed_by: Optional[str] = Field(None, validation_alias=AliasChoices("sig_by", "signed_by"))

    @model_validator(mode="before")
    @classmethod
    def _auto_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("id"):
                data["id"] = "akf-{}".format(uuid.uuid4().hex[:12])
            if not data.get("at") and not data.get("created"):
                data["created"] = datetime.now(timezone.utc).isoformat()
        return data

    # --- Convenience properties ---

    @property
    def trust_score(self) -> float:
        """Computed average confidence across all claims.

        Returns the mean confidence of all claims in the unit as a
        quick trust indicator. For detailed per-claim trust scores
        with authority weighting and decay, use ``effective_trust()``.
        """
        if not self.claims:
            return 0.0
        return sum(c.confidence for c in self.claims) / len(self.claims)

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
        if self.made_by:
            d["made_by"] = [m.to_dict(compact=compact) for m in self.made_by]
        if self.reviews:
            d["reviews"] = [r.to_dict(compact=compact) for r in self.reviews]
        if self.cost is not None:
            d["cost"] = self.cost.to_dict(compact=compact)
        if self.annotations:
            d["annotations"] = [a.to_dict(compact=compact) for a in self.annotations]
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
            kind_str = " ({})".format(claim.kind) if claim.kind else ""
            ev_str = " [{}ev]".format(len(claim.evidence)) if claim.evidence else ""
            origin_str = ""
            if claim.origin:
                origin_str = " [{}]".format(claim.origin.type)
            review_str = ""
            if claim.reviews:
                verdicts = [r.verdict for r in claim.reviews]
                review_str = " [reviewed:{}]".format(",".join(verdicts))
            lines.append(
                '  {} {:.2f}  "{}"  {}  {}{}{}{}{}{}{}'.format(
                    icon,
                    claim.confidence,
                    claim.content,
                    src_str,
                    tier_str,
                    ver_str,
                    ai_str,
                    kind_str,
                    ev_str,
                    origin_str,
                    review_str,
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
