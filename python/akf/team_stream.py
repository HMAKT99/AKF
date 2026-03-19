"""AKF v1.1 — Team-aware streaming for multi-agent sessions.

Enables multiple agents to emit claims into a shared stream with
per-agent attribution and team-level trust aggregation.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import AKF, Claim
from .streaming import StreamSession, stream_claim, stream_end, stream_start


@dataclass
class TeamStreamSession:
    """Active team streaming session state."""

    team_id: str
    started_at: str
    agents: Dict[str, StreamSession] = field(default_factory=dict)
    output_path: Optional[str] = None
    _file_handle: Any = field(default=None, repr=False)


@dataclass
class TeamTrustResult:
    """Aggregated trust result for a team session."""

    team_id: str
    team_avg_trust: float
    agent_scores: Dict[str, float]  # agent_id -> avg confidence
    total_claims: int
    claims_per_agent: Dict[str, int]


def team_stream_start(
    agent_ids: List[str],
    output_path: Optional[str] = None,
    **kwargs: Any,
) -> TeamStreamSession:
    """Start a team streaming session.

    Args:
        agent_ids: List of agent identifiers participating in the session.
        output_path: Path to .akfl file for incremental writes.
        **kwargs: Extra fields for the start header.

    Returns:
        TeamStreamSession for subsequent operations.
    """
    team_id = str(uuid.uuid4())[:12]
    started_at = datetime.now(timezone.utc).isoformat()

    session = TeamStreamSession(
        team_id=team_id,
        started_at=started_at,
        output_path=output_path,
    )

    # Create sub-sessions for each agent (no individual file output)
    for agent_id in agent_ids:
        sub = stream_start(agent_id=agent_id)
        session.agents[agent_id] = sub

    # Write team header to file
    if output_path:
        header = {
            "type": "team_start",
            "team": team_id,
            "agents": agent_ids,
            "at": started_at,
            **kwargs,
        }
        fh = open(output_path, "w")
        fh.write(json.dumps(header, ensure_ascii=False) + "\n")
        fh.flush()
        session._file_handle = fh

    return session


def team_stream_claim(
    session: TeamStreamSession,
    agent_id: str,
    content: str,
    confidence: float,
    **kwargs: Any,
) -> Claim:
    """Emit a claim attributed to a specific agent in the team.

    Args:
        session: Active TeamStreamSession.
        agent_id: The agent emitting this claim.
        content: Claim content text.
        confidence: Trust score 0.0-1.0.
        **kwargs: Additional Claim fields.

    Returns:
        The created Claim object.

    Raises:
        ValueError: If agent_id is not part of the team session.
    """
    if agent_id not in session.agents:
        raise ValueError(
            f"Agent '{agent_id}' not in team session. "
            f"Registered agents: {list(session.agents.keys())}"
        )

    sub = session.agents[agent_id]
    claim = stream_claim(sub, content=content, confidence=confidence, **kwargs)

    # Write to team file with agent attribution
    if session._file_handle:
        line = {
            "type": "claim",
            "agent": agent_id,
            "c": claim.content,
            "t": claim.confidence,
            "id": claim.id,
        }
        if claim.source:
            line["src"] = claim.source
        if claim.ai_generated:
            line["ai"] = True
        if claim.authority_tier:
            line["tier"] = claim.authority_tier
        session._file_handle.write(json.dumps(line, ensure_ascii=False) + "\n")
        session._file_handle.flush()

    return claim


def team_stream_end(
    session: TeamStreamSession,
) -> AKF:
    """End a team streaming session and collect into an AKF unit.

    All agent claims are merged into a single AKF unit with team metadata.

    Returns:
        Collected AKF unit with all team claims.
    """
    all_claims: List[Claim] = []
    for agent_id, sub in session.agents.items():
        all_claims.extend(sub.claims)

    # Compute content hash
    content_str = json.dumps(
        [c.to_dict(compact=True) for c in all_claims],
        sort_keys=True,
        ensure_ascii=False,
    )
    content_hash = "sha256:" + hashlib.sha256(content_str.encode()).hexdigest()

    # Write team footer
    if session._file_handle:
        footer = {
            "type": "team_end",
            "team": session.team_id,
            "count": len(all_claims),
            "hash": content_hash,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        session._file_handle.write(json.dumps(footer, ensure_ascii=False) + "\n")
        session._file_handle.close()
        session._file_handle = None

    if not all_claims:
        # AKF requires at least one claim; create a placeholder
        all_claims = [Claim(content="(empty team session)", confidence=0.0)]

    return AKF(
        version="1.0",
        claims=all_claims,
        session=session.team_id,
        integrity_hash=content_hash,
    )


def team_trust_aggregate(session: TeamStreamSession) -> TeamTrustResult:
    """Compute per-agent and team-level trust scores.

    Args:
        session: Active or completed TeamStreamSession.

    Returns:
        TeamTrustResult with per-agent and aggregate scores.
    """
    agent_scores: Dict[str, float] = {}
    claims_per_agent: Dict[str, int] = {}
    all_confidences: List[float] = []

    for agent_id, sub in session.agents.items():
        if sub.claims:
            scores = [c.confidence for c in sub.claims]
            agent_scores[agent_id] = sum(scores) / len(scores)
            claims_per_agent[agent_id] = len(sub.claims)
            all_confidences.extend(scores)
        else:
            agent_scores[agent_id] = 0.0
            claims_per_agent[agent_id] = 0

    team_avg = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

    return TeamTrustResult(
        team_id=session.team_id,
        team_avg_trust=round(team_avg, 4),
        agent_scores={k: round(v, 4) for k, v in agent_scores.items()},
        total_claims=len(all_confidences),
        claims_per_agent=claims_per_agent,
    )


class TeamStream:
    """Context manager for multi-agent streaming.

    Usage::

        with TeamStream(["agent-a", "agent-b"]) as ts:
            ts.write("agent-a", "First claim", confidence=0.9)
            ts.write("agent-b", "Second claim", confidence=0.8)
        # ts.unit contains the team-aggregated AKF unit
    """

    def __init__(
        self,
        agent_ids: List[str],
        output_path: Optional[str] = None,
        confidence: float = 0.7,
        **kwargs: Any,
    ) -> None:
        self.agent_ids = agent_ids
        self.output_path = output_path
        self.confidence = confidence
        self.extra = kwargs
        self._session: Optional[TeamStreamSession] = None
        self.unit: Optional[AKF] = None

    def __enter__(self) -> "TeamStream":
        akfl_path = None
        if self.output_path:
            akfl_path = self.output_path + ".team.akfl"
        self._session = team_stream_start(
            agent_ids=self.agent_ids,
            output_path=akfl_path,
            **self.extra,
        )
        return self

    def write(
        self,
        agent_id: str,
        content: str,
        confidence: Optional[float] = None,
        **kwargs: Any,
    ) -> Claim:
        """Write a claim attributed to a specific agent.

        Args:
            agent_id: The agent emitting this claim.
            content: The content text.
            confidence: Override default confidence.
            **kwargs: Additional claim fields.

        Returns:
            The created Claim.
        """
        if self._session is None:
            raise RuntimeError("TeamStream not started — use as context manager")
        return team_stream_claim(
            self._session,
            agent_id=agent_id,
            content=content,
            confidence=confidence if confidence is not None else self.confidence,
            **kwargs,
        )

    def aggregate(self) -> TeamTrustResult:
        """Get current team trust aggregation."""
        if self._session is None:
            raise RuntimeError("TeamStream not started — use as context manager")
        return team_trust_aggregate(self._session)

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self._session is not None:
            self.unit = team_stream_end(self._session)
        return None
