"""AKF v1.0 — One-line stamp API for AI agents.

Usage:
    import akf
    akf.stamp("Fixed auth bypass", kind="code_change",
              evidence=["42/42 tests passed", "mypy: 0 errors"],
              agent="claude-code", model="claude-sonnet-4-20250514")
"""

import re
from datetime import datetime, timezone
from typing import List, Optional, Union

from .models import AKF, Claim, Evidence


# ---------------------------------------------------------------------------
# Evidence string parser — auto-detects evidence type from plain text
# ---------------------------------------------------------------------------

_EVIDENCE_PATTERNS = [
    (r"\d+/\d+\s*tests?\s*pass", "test_pass"),
    (r"all\s*tests?\s*pass", "test_pass"),
    (r"tests?\s*pass", "test_pass"),
    (r"pytest.*pass", "test_pass"),
    (r"mypy.*0\s*error", "type_check"),
    (r"type.?check.*pass", "type_check"),
    (r"type.?check.*clean", "type_check"),
    (r"0\s*type\s*error", "type_check"),
    (r"lint.*clean", "lint_clean"),
    (r"lint.*pass", "lint_clean"),
    (r"eslint.*0", "lint_clean"),
    (r"ruff.*0", "lint_clean"),
    (r"0\s*lint\s*error", "lint_clean"),
    (r"ci\s*pass", "ci_pass"),
    (r"ci.*green", "ci_pass"),
    (r"pipeline.*pass", "ci_pass"),
    (r"build.*pass", "ci_pass"),
    (r"build.*success", "ci_pass"),
    (r"human.*review", "human_review"),
    (r"code.*review", "human_review"),
    (r"approved\s*by", "human_review"),
    (r"peer.*review", "human_review"),
]


def parse_evidence_string(s: str) -> Evidence:
    """Parse a plain-text evidence string into an Evidence object.

    Auto-detects type from common patterns (test_pass, type_check,
    lint_clean, ci_pass, human_review). Falls back to 'other'.
    """
    lower = s.lower()
    ev_type = "other"
    for pattern, etype in _EVIDENCE_PATTERNS:
        if re.search(pattern, lower):
            ev_type = etype
            break

    return Evidence(
        type=ev_type,
        detail=s,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def _to_evidence_list(evidence: list) -> List[Evidence]:
    """Convert mixed evidence list (Evidence, dict, str) to Evidence objects."""
    result = []
    for item in evidence:
        if isinstance(item, Evidence):
            result.append(item)
        elif isinstance(item, dict):
            result.append(Evidence(**item))
        elif isinstance(item, str):
            result.append(parse_evidence_string(item))
        else:
            raise TypeError(f"Unsupported evidence type: {type(item)}")
    return result


# ---------------------------------------------------------------------------
# stamp() — the one-liner
# ---------------------------------------------------------------------------

def stamp(
    content: str,
    *,
    confidence: float = 0.7,
    kind: str = "claim",
    evidence: Optional[list] = None,
    agent: Optional[str] = None,
    model: Optional[str] = None,
    tools: Optional[List[str]] = None,
    session: Optional[str] = None,
    ai_generated: bool = True,
    **kwargs,
) -> AKF:
    """One-line API for AI agents to create an AKF unit.

    Args:
        content: What the agent did or claims.
        confidence: Trust score 0.0-1.0 (default 0.7).
        kind: Kind of claim (claim, code_change, decision, suggestion,
              review, test_result, diagnosis). Default "claim".
        evidence: List of evidence — strings, dicts, or Evidence objects.
        agent: Agent identifier (e.g. "claude-code").
        model: Model identifier (e.g. "claude-sonnet-4-20250514").
        tools: Tools used during the action.
        session: Session identifier for grouping stamps.
        ai_generated: Whether AI-generated (default True).
        **kwargs: Extra fields passed to Claim.

    Returns:
        AKF unit with a single claim.
    """
    # Process evidence
    evidence_objects = None
    if evidence is not None:
        evidence_objects = _to_evidence_list(evidence)

    # Build claim
    claim_kwargs = {
        "ai_generated": ai_generated,
        "kind": kind,
        "source": kwargs.pop("source", "unspecified"),
        "authority_tier": kwargs.pop("authority_tier", 5 if ai_generated else 3),
        "verified": kwargs.pop("verified", False),
    }
    claim_kwargs.update(kwargs)
    if evidence_objects:
        claim_kwargs["evidence"] = evidence_objects

    claim = Claim(content=content, confidence=confidence, **claim_kwargs)

    # Build envelope
    unit = AKF(
        version="1.0",
        claims=[claim],
        agent=agent,
        model=model,
        tools=tools,
        session=session,
        classification="internal",
        inherit_classification=True,
        allow_external=False,
    )

    return unit
