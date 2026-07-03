"""Fast trust check for agent consumption.

`check_file` answers one question in one line: can an agent trust this
file's stamped verification state, or does it need to re-verify?

Statuses:
    OK        — fresh stamp, trust at or above threshold. Safe to build on.
    LOW       — stamped and fresh, but effective trust below threshold.
    STALE     — file modified after it was stamped, or claims expired.
    UNSTAMPED — no AKF metadata found.

Exit codes (CLI): OK=0, LOW/STALE=1, UNSTAMPED=2.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from .models import AKF, Claim
from .trust import effective_trust, is_expired

# Seconds of slack between the stamp timestamp and the file mtime — stamping
# rewrites the file, so the mtime always lands slightly after `created`.
_MTIME_TOLERANCE_S = 10

# Objective verification receipts upgrade a claim's authority tier: a stamp
# backed by a test run or a human review is no longer bare AI inference
# (tier 5), even though the content itself is AI-generated. Weak signals
# (lint, type check) alone don't clear the default threshold; test runs and
# human review do.
_EVIDENCE_TIER_FLOOR = {
    "human_review": 1,
    "test_pass": 2,
    "ci_pass": 2,
    "type_check": 3,
    "lint_clean": 3,
}


@dataclass
class CheckResult:
    """Result of a trust check on a single file."""

    file: str
    status: str  # OK | LOW | STALE | UNSTAMPED
    exit_code: int
    trust: Optional[float] = None
    threshold: float = 0.6
    agent: Optional[str] = None
    model: Optional[str] = None
    age_days: Optional[int] = None
    claims: int = 0
    evidence: List[str] = field(default_factory=list)
    reason: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "status": self.status,
            "exit_code": self.exit_code,
            "trust": self.trust,
            "threshold": self.threshold,
            "agent": self.agent,
            "model": self.model,
            "age_days": self.age_days,
            "claims": self.claims,
            "evidence": self.evidence,
            "reason": self.reason,
        }

    def summary_line(self) -> str:
        """One-line, ~20-token summary designed for agent context windows."""
        parts = [self.status]
        if self.trust is not None:
            parts.append(f"trust={self.trust:.2f}")
        if self.agent:
            parts.append(f"agent={self.agent}")
        if self.evidence:
            parts.append("evidence=" + ",".join(self.evidence))
        if self.age_days is not None:
            parts.append(f"age={self.age_days}d")
        if self.claims:
            parts.append(f"claims={self.claims}")
        if self.reason:
            parts.append(f"reason={self.reason}")
        return " ".join(parts)


def _parse_ts(value: str) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _evidence_types(unit: AKF) -> List[str]:
    types: List[str] = []
    for claim in unit.claims:
        for ev in claim.evidence or []:
            ev_type = getattr(ev, "type", None) or "other"
            if ev_type not in types:
                types.append(ev_type)
    return types


def _claim_score(claim: Claim, age_days: float = 0) -> float:
    """Effective trust with evidence-aware authority and temporal decay.

    Verification receipts (tests, type checks, human review) floor the
    authority tier — see _EVIDENCE_TIER_FLOOR. Stamp age drives decay for
    claims with a decay_half_life (e.g. memory stamps).
    """
    floors = [
        _EVIDENCE_TIER_FLOOR[ev.type]
        for ev in (claim.evidence or [])
        if getattr(ev, "type", None) in _EVIDENCE_TIER_FLOOR
    ]
    if floors:
        tier = claim.authority_tier if claim.authority_tier is not None else 3
        floored = min(min(floors), tier)
        if floored != tier:
            claim = claim.model_copy(update={"authority_tier": floored})
    return effective_trust(claim, age_days=age_days).score


def check_file(filepath: str, threshold: float = 0.6) -> CheckResult:
    """Check whether an agent can trust a file's stamped state.

    Reads AKF metadata (inline or sidecar), computes effective trust,
    and compares the stamp timestamp against the file's mtime to catch
    modifications made after stamping.
    """
    from . import universal
    from .core import load

    meta = universal.extract(filepath)
    if meta is not None:
        unit = AKF(**meta)
    elif filepath.endswith(".akf"):
        try:
            unit = load(filepath)
        except Exception:
            unit = None
    else:
        unit = None

    if unit is None:
        return CheckResult(
            file=filepath, status="UNSTAMPED", exit_code=2,
            threshold=threshold, reason="no_metadata",
        )

    stamped_at = _parse_ts(unit.created) if unit.created else None
    age_days: Optional[int] = None
    if stamped_at is not None:
        age_days = max(0, (datetime.now(timezone.utc) - stamped_at).days)

    scores = [_claim_score(claim, age_days=age_days or 0) for claim in unit.claims]
    overall = round(min(scores), 4) if scores else 0.0

    base = dict(
        file=filepath,
        trust=overall,
        threshold=threshold,
        agent=unit.agent,
        model=unit.model,
        age_days=age_days,
        claims=len(unit.claims),
        evidence=_evidence_types(unit),
    )

    # Staleness: the file changed after it was stamped, or claims expired.
    if stamped_at is not None:
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath), tz=timezone.utc)
            if (mtime - stamped_at).total_seconds() > _MTIME_TOLERANCE_S:
                return CheckResult(
                    status="STALE", exit_code=1,
                    reason="modified_after_stamp", **base,
                )
        except OSError:
            pass
    if any(is_expired(claim) for claim in unit.claims):
        return CheckResult(status="STALE", exit_code=1, reason="claims_expired", **base)

    # Transitive staleness: this file is unchanged, but a local dependency it
    # imports moved — what the stamp verified is no longer true (#124).
    recorded_deps = (unit.meta or {}).get("deps")
    if recorded_deps:
        from .deps import changed_deps
        if changed_deps(filepath, recorded_deps):
            return CheckResult(status="STALE", exit_code=1, reason="dependency_changed", **base)

    if overall < threshold:
        return CheckResult(status="LOW", exit_code=1, reason="below_threshold", **base)

    return CheckResult(status="OK", exit_code=0, **base)
