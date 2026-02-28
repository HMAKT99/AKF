"""AKF v1.0 — Core API: create, load, validate."""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from .models import AKF, Claim


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def create(content: str, t: float, **kwargs) -> AKF:
    """Create a single-claim AKF unit."""
    claim = Claim(c=content, t=t, **kwargs)
    return AKF(v="1.0", claims=[claim])


def create_multi(claims: List[dict], **envelope) -> AKF:
    """Create a multi-claim AKF unit."""
    claim_objects = [Claim(**c) for c in claims]
    return AKF(v="1.0", claims=claim_objects, **envelope)


# ---------------------------------------------------------------------------
# Load / Save
# ---------------------------------------------------------------------------

def load(path: Union[str, Path]) -> AKF:
    """Load .akf file from disk."""
    with open(path) as f:
        data = json.load(f)
    return AKF(**data)


def loads(json_str: str) -> AKF:
    """Load .akf from a JSON string."""
    return AKF(**json.loads(json_str))


# ---------------------------------------------------------------------------
# Validate
# ---------------------------------------------------------------------------

VALID_LABELS = {"public", "internal", "confidential", "highly-confidential", "restricted"}
LABEL_RANK = {
    "public": 0, "internal": 1, "confidential": 2,
    "highly-confidential": 3, "restricted": 4,
}


@dataclass
class ValidationResult:
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    level: int = 0  # 0=invalid, 1=minimal, 2=practical, 3=full

    def __bool__(self) -> bool:
        return self.valid


def validate(target: Union[AKF, str, Path]) -> ValidationResult:
    """Validate an AKF unit, file path, or JSON string.

    Returns a ValidationResult with .valid, .errors, .warnings, .level.
    """
    result = ValidationResult()

    # Load the unit
    unit: Optional[AKF] = None
    if isinstance(target, AKF):
        unit = target
    elif isinstance(target, (str, Path)):
        path = Path(target)
        if path.exists():
            try:
                unit = load(path)
            except Exception as exc:
                result.valid = False
                result.errors.append("Failed to load file: {}".format(exc))
                return result
        else:
            # Try as JSON string
            try:
                unit = loads(str(target))
            except Exception as exc:
                result.valid = False
                result.errors.append("Invalid JSON: {}".format(exc))
                return result
    else:
        result.valid = False
        result.errors.append("Unsupported target type: {}".format(type(target)))
        return result

    # RULE 1: v must be present
    if not unit.v:
        result.valid = False
        result.errors.append("RULE 1: 'v' (version) is required")

    # RULE 2: claims must be non-empty
    if not unit.claims:
        result.valid = False
        result.errors.append("RULE 2: 'claims' must be a non-empty array")

    # RULE 3: Each claim must have c and t in range
    for i, claim in enumerate(unit.claims):
        if not isinstance(claim.t, (int, float)) or not (0.0 <= claim.t <= 1.0):
            result.valid = False
            result.errors.append(
                "RULE 3: claim[{}].t must be float 0.0-1.0, got {}".format(i, claim.t)
            )

    # RULE 4: tier must be 1-5
    for i, claim in enumerate(unit.claims):
        if claim.tier is not None and not (1 <= claim.tier <= 5):
            result.valid = False
            result.errors.append(
                "RULE 4: claim[{}].tier must be 1-5, got {}".format(i, claim.tier)
            )

    # RULE 5: label must be valid
    if unit.label is not None and unit.label not in VALID_LABELS:
        result.valid = False
        result.errors.append("RULE 5: invalid label '{}'".format(unit.label))

    # RULE 7: provenance hops sequential
    if unit.prov:
        for i, hop in enumerate(unit.prov):
            if hop.hop != i:
                result.valid = False
                result.errors.append(
                    "RULE 7: provenance hop[{}] has hop={}, expected {}".format(i, hop.hop, i)
                )

    # RULE 8: pen must be negative
    if unit.prov:
        for i, hop in enumerate(unit.prov):
            if hop.pen is not None and hop.pen >= 0:
                result.valid = False
                result.errors.append(
                    "RULE 8: provenance hop[{}].pen must be negative, got {}".format(i, hop.pen)
                )

    # RULE 9: AI + tier 5 should have risk (warning)
    for i, claim in enumerate(unit.claims):
        if claim.ai and claim.tier == 5 and not claim.risk:
            result.warnings.append(
                "RULE 9: claim[{}] is AI-generated tier 5 but has no risk description".format(i)
            )

    # RULE 10: hash prefix
    if unit.hash is not None:
        if not re.match(r"^(sha256|sha3-512|blake3):.*$", unit.hash):
            result.valid = False
            result.errors.append(
                "RULE 10: hash must be prefixed with algorithm, got '{}'".format(unit.hash)
            )

    # RULE 11: timestamps valid ISO-8601
    if unit.at:
        try:
            _parse_iso(unit.at)
        except ValueError:
            result.valid = False
            result.errors.append("RULE 11: invalid timestamp '{}'".format(unit.at))

    if unit.prov:
        for i, hop in enumerate(unit.prov):
            try:
                _parse_iso(hop.at)
            except ValueError:
                result.valid = False
                result.errors.append(
                    "RULE 11: invalid timestamp in prov[{}].at '{}'".format(i, hop.at)
                )

    # Determine level
    if result.valid:
        has_prov = bool(unit.prov)
        has_sources = any(c.src for c in unit.claims)
        has_label = unit.label is not None
        has_hash = unit.hash is not None

        if has_prov and has_hash and has_label and has_sources:
            result.level = 3  # Full
        elif has_sources or has_label:
            result.level = 2  # Practical
        else:
            result.level = 1  # Minimal

    return result


def _parse_iso(s: str) -> None:
    """Quick ISO-8601 validation."""
    s = s.replace("Z", "+00:00")
    datetime.fromisoformat(s)
