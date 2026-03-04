"""AKF v1.0 — Agent-native utilities.

Functions for LLMs and AI agents to produce, consume, and validate AKF.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .core import ValidationResult, create, load, loads, validate
from .models import AKF, Claim
from .provenance import add_hop, compute_integrity_hash
from .trust import effective_trust


def consume(
    target: Union[str, Path, AKF],
    agent_id: str,
    trust_threshold: float = 0.6,
    transform_penalty: float = -0.03,
) -> AKF:
    """Consume an AKF unit as an agent.

    Loads the unit, filters claims by trust threshold, applies penalty,
    and adds a provenance hop.

    Args:
        target: File path, JSON string, or AKF object.
        agent_id: Identifier for the consuming agent.
        trust_threshold: Minimum effective trust to retain a claim.
        transform_penalty: Penalty applied to retained claims.

    Returns:
        Derived AKF unit with provenance.
    """
    from .transform import AKFTransformer

    if isinstance(target, AKF):
        unit = target
    elif isinstance(target, (str, Path)):
        path = Path(target)
        if path.exists():
            unit = load(path)
        else:
            unit = loads(str(target))
    else:
        raise TypeError("Expected AKF, file path, or JSON string")

    derived = (
        AKFTransformer(unit)
        .filter(trust_min=trust_threshold)
        .penalty(transform_penalty)
        .by(agent_id)
        .build()
    )
    return derived


def derive(
    parent: Union[str, Path, AKF],
    agent_id: str,
    claims: Optional[List[Dict[str, Any]]] = None,
    trust_threshold: float = 0.6,
    transform_penalty: float = -0.05,
) -> AKF:
    """Create a derived AKF unit from a parent.

    Similar to consume but allows adding new claims.

    Args:
        parent: Parent AKF unit (file path, JSON string, or AKF object).
        agent_id: Identifier for the deriving agent.
        claims: Optional new claims to add as dicts.
        trust_threshold: Minimum effective trust for parent claims.
        transform_penalty: Penalty applied to inherited claims.

    Returns:
        Derived AKF unit with provenance chain.
    """
    from .transform import AKFTransformer
    from .security import inherit_label

    if isinstance(parent, (str, Path)):
        path = Path(parent)
        if path.exists():
            parent_unit = load(path)
        else:
            parent_unit = loads(str(parent))
    else:
        parent_unit = parent

    transformer = AKFTransformer(parent_unit).filter(trust_min=trust_threshold)
    if transform_penalty:
        transformer = transformer.penalty(transform_penalty)
    transformer = transformer.by(agent_id)
    derived = transformer.build()

    # Add new claims if provided
    if claims:
        new_claim_objs = [Claim(**c) for c in claims]
        all_claims = list(derived.claims) + new_claim_objs
        derived = derived.model_copy(update={"claims": all_claims})
        new_ids = [c.id for c in new_claim_objs if c.id]
        derived = add_hop(derived, by=agent_id, action="enriched", adds=new_ids)

    return derived


def generation_prompt() -> str:
    """Return a one-shot system prompt for any LLM to generate AKF.

    Returns:
        System prompt string suitable for LLM context.
    """
    return '''You are an AI agent that produces structured knowledge in AKF (Agent Knowledge Format).

When generating claims, output valid AKF JSON with this structure:
{
  "v": "1.0",
  "claims": [
    {
      "c": "<claim text>",
      "t": <confidence 0.0-1.0>,
      "src": "<source>",
      "tier": <1-5>,
      "ai": true,
      "risk": "<optional risk description>"
    }
  ]
}

Authority tiers: 1=primary source, 2=secondary, 3=tertiary, 4=speculative, 5=AI inference.
Always set "ai": true and be conservative with trust scores.
Include "risk" for tier 4-5 claims explaining limitations.'''


def validate_output(llm_response: str) -> ValidationResult:
    """Validate LLM-generated text as AKF.

    Attempts to extract JSON from the response and validate it.

    Args:
        llm_response: Raw text from an LLM.

    Returns:
        ValidationResult with details.
    """
    # Try to find JSON in the response
    text = llm_response.strip()

    # Try direct parse
    try:
        data = json.loads(text)
        unit = AKF(**data)
        return validate(unit)
    except (json.JSONDecodeError, Exception):
        pass

    # Try to extract JSON from markdown code block
    import re
    json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', text, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            unit = AKF(**data)
            return validate(unit)
        except (json.JSONDecodeError, Exception):
            pass

    # Try to find JSON object in text
    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        try:
            data = json.loads(brace_match.group())
            unit = AKF(**data)
            return validate(unit)
        except (json.JSONDecodeError, Exception):
            pass

    result = ValidationResult(valid=False)
    result.errors.append("Could not extract valid AKF JSON from response")
    return result


def response_schema(level: str = "standard") -> dict:
    """Return a JSON Schema for structured LLM outputs.

    Args:
        level: "minimal", "standard", or "full".

    Returns:
        JSON Schema dict suitable for structured output APIs.
    """
    claim_schema: Dict[str, Any] = {
        "type": "object",
        "required": ["c", "t"],
        "properties": {
            "c": {"type": "string", "description": "Claim content"},
            "t": {"type": "number", "minimum": 0, "maximum": 1, "description": "Trust score"},
        },
    }

    if level in ("standard", "full"):
        claim_schema["properties"].update({
            "src": {"type": "string", "description": "Source attribution"},
            "tier": {"type": "integer", "minimum": 1, "maximum": 5},
            "ai": {"type": "boolean", "description": "AI-generated flag"},
        })

    if level == "full":
        claim_schema["properties"].update({
            "risk": {"type": "string", "description": "Risk description"},
            "ver": {"type": "boolean"},
            "tags": {"type": "array", "items": {"type": "string"}},
        })

    return {
        "type": "object",
        "required": ["v", "claims"],
        "properties": {
            "v": {"type": "string", "const": "1.0"},
            "claims": {
                "type": "array",
                "minItems": 1,
                "items": claim_schema,
            },
        },
    }


def from_tool_call(params: dict) -> Claim:
    """Create a Claim from function/tool call parameters.

    Normalizes common parameter names to AKF fields.

    Args:
        params: Tool call parameters dict.

    Returns:
        A Claim object.
    """
    normalized: Dict[str, Any] = {}

    # Content normalization
    for key in ("content", "c", "text", "message", "result", "answer"):
        if key in params:
            normalized["content"] = params[key]
            break

    # Confidence normalization
    for key in ("confidence", "t", "trust", "score", "probability"):
        if key in params:
            val = params[key]
            if isinstance(val, (int, float)) and val > 1.0:
                val = val / 100.0  # Treat as percentage
            normalized["confidence"] = val
            break

    if "content" not in normalized:
        raise ValueError("No content field found in params")
    if "confidence" not in normalized:
        normalized["confidence"] = 0.5  # Default for tool calls

    # Pass through other recognized fields
    for key in ("source", "src", "authority_tier", "tier", "verified", "ver",
                "ai_generated", "ai", "risk", "tags"):
        if key in params and key not in normalized:
            normalized[key] = params[key]

    # Always mark as AI-generated
    normalized.setdefault("ai_generated", True)

    return Claim(**normalized)


def to_context(
    unit: Union[str, Path, AKF],
    max_tokens: int = 2000,
    sort_by: str = "confidence",
) -> str:
    """Format an AKF unit for injection into an LLM context window.

    Args:
        unit: AKF unit, file path, or JSON string.
        max_tokens: Approximate maximum tokens (chars / 4).
        sort_by: "confidence" or "authority_tier".

    Returns:
        Formatted string suitable for system/user prompt injection.
    """
    if isinstance(unit, (str, Path)):
        path = Path(unit)
        if path.exists():
            akf = load(path)
        else:
            akf = loads(str(unit))
    else:
        akf = unit

    max_chars = max_tokens * 4  # Rough approximation

    # Sort claims
    claims = list(akf.claims)
    if sort_by == "confidence":
        claims.sort(key=lambda c: c.confidence, reverse=True)
    elif sort_by == "authority_tier":
        claims.sort(key=lambda c: c.authority_tier or 3)

    lines = ["[AKF Knowledge Context]"]
    if akf.classification:
        lines.append(f"Classification: {akf.classification}")
    lines.append("")

    char_count = sum(len(l) for l in lines)
    for claim in claims:
        trust_label = "HIGH" if claim.confidence >= 0.8 else "MED" if claim.confidence >= 0.5 else "LOW"
        ai_flag = " [AI]" if claim.ai_generated else ""
        line = f"- [{trust_label} {claim.confidence:.2f}] {claim.content}"
        if claim.source:
            line += f" (source: {claim.source})"
        line += ai_flag

        if char_count + len(line) > max_chars:
            lines.append("... (truncated)")
            break
        lines.append(line)
        char_count += len(line)

    return "\n".join(lines)


def detect(target: Union[str, Path, dict]) -> Optional[dict]:
    """Auto-detect AKF in files, strings, or dicts.

    Args:
        target: A file path, JSON string, or dict to check.

    Returns:
        Dict with 'format' and 'unit' if AKF detected, None otherwise.
    """
    if isinstance(target, dict):
        if "v" in target or "version" in target:
            if "claims" in target:
                try:
                    unit = AKF(**target)
                    return {"format": "dict", "unit": unit}
                except Exception:
                    pass
        return None

    if isinstance(target, (str, Path)):
        path = Path(target)
        if path.exists():
            if path.suffix == ".akf":
                try:
                    unit = load(path)
                    return {"format": "akf_file", "unit": unit}
                except Exception:
                    pass
            # Try extracting from supported formats
            try:
                from .universal import extract
                meta = extract(str(path))
                if meta is not None:
                    return {"format": "embedded", "metadata": meta}
            except Exception:
                pass
        else:
            # Try as JSON string
            try:
                unit = loads(str(target))
                return {"format": "json_string", "unit": unit}
            except Exception:
                pass

    return None
