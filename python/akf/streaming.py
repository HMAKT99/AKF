"""AKF v1.1 — Streaming .akfl support (JSON Lines format).

Enables incremental claim emission for long-running agent sessions.
Each line is a self-contained JSON object with a type field.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from .models import AKF, Claim


@dataclass
class StreamSession:
    """Active streaming session state."""

    session_id: str
    started_at: str
    agent: Optional[str] = None
    claims: List[Claim] = field(default_factory=list)
    output_path: Optional[str] = None
    _file_handle: Any = field(default=None, repr=False)


def stream_start(
    agent_id: Optional[str] = None,
    output_path: Optional[str] = None,
    **envelope_kwargs: Any,
) -> StreamSession:
    """Start a streaming session, optionally writing to an .akfl file.

    Args:
        agent_id: Identifier for the streaming agent.
        output_path: Path to .akfl file for incremental writes.
        **envelope_kwargs: Extra fields for the start header.

    Returns:
        StreamSession object for subsequent stream_claim/stream_end calls.
    """
    session_id = str(uuid.uuid4())[:12]
    started_at = datetime.now(timezone.utc).isoformat()

    session = StreamSession(
        session_id=session_id,
        started_at=started_at,
        agent=agent_id,
        output_path=output_path,
    )

    header = {
        "type": "start",
        "session": session_id,
        "agent": agent_id,
        "at": started_at,
        **envelope_kwargs,
    }

    if output_path:
        fh = open(output_path, "w")
        fh.write(json.dumps(header, ensure_ascii=False) + "\n")
        fh.flush()
        session._file_handle = fh

    return session


def stream_claim(
    session: StreamSession,
    content: str,
    confidence: float,
    **kwargs: Any,
) -> Claim:
    """Emit a single claim into the stream.

    Args:
        session: Active StreamSession.
        content: Claim content text.
        confidence: Trust score 0.0-1.0.
        **kwargs: Additional Claim fields.

    Returns:
        The created Claim object.
    """
    claim = Claim(content=content, confidence=confidence, **kwargs)
    session.claims.append(claim)

    line = {
        "type": "claim",
        "c": claim.content,
        "t": claim.confidence,
        "id": claim.id,
    }
    # Include optional fields
    if claim.source:
        line["src"] = claim.source
    if claim.ai_generated:
        line["ai"] = True
    if claim.authority_tier:
        line["tier"] = claim.authority_tier

    if session._file_handle:
        session._file_handle.write(json.dumps(line, ensure_ascii=False) + "\n")
        session._file_handle.flush()

    return claim


def stream_end(
    session: StreamSession,
    output_path: Optional[str] = None,
) -> AKF:
    """End a streaming session and collect into an AKF unit.

    Args:
        session: Active StreamSession.
        output_path: Optional path to save the final .akf file.

    Returns:
        Collected AKF unit.
    """
    # Compute content hash
    content_str = json.dumps(
        [c.to_dict(compact=True) for c in session.claims],
        sort_keys=True, ensure_ascii=False,
    )
    content_hash = "sha256:" + hashlib.sha256(content_str.encode()).hexdigest()

    footer = {
        "type": "end",
        "count": len(session.claims),
        "hash": content_hash,
        "at": datetime.now(timezone.utc).isoformat(),
    }

    if session._file_handle:
        session._file_handle.write(json.dumps(footer, ensure_ascii=False) + "\n")
        session._file_handle.close()
        session._file_handle = None

    unit = AKF(
        version="1.0",
        claims=session.claims,
        agent=session.agent,
        session=session.session_id,
        integrity_hash=content_hash,
    )

    if output_path:
        unit.save(output_path)

    return unit


def collect_stream(akfl_path: str) -> AKF:
    """Read an .akfl file and collect all claims into an AKF unit.

    Args:
        akfl_path: Path to .akfl JSON Lines file.

    Returns:
        AKF unit with all collected claims.

    Raises:
        ValueError: If the file is malformed or missing required lines.
    """
    path = Path(akfl_path)
    if not path.exists():
        raise FileNotFoundError(f"Stream file not found: {akfl_path}")

    claims: List[Claim] = []
    session_id = None
    agent = None
    end_found = False

    with open(path) as f:
        for line_num, raw_line in enumerate(f, 1):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                obj = json.loads(raw_line)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON on line {line_num}: {raw_line[:80]}")

            line_type = obj.get("type")

            if line_type == "start":
                session_id = obj.get("session")
                agent = obj.get("agent")
            elif line_type == "claim":
                claim_data: Dict[str, Any] = {}
                claim_data["content"] = obj.get("c", obj.get("content", ""))
                claim_data["confidence"] = obj.get("t", obj.get("confidence", 0.5))
                if "id" in obj:
                    claim_data["id"] = obj["id"]
                if "src" in obj:
                    claim_data["source"] = obj["src"]
                if "ai" in obj:
                    claim_data["ai_generated"] = obj["ai"]
                if "tier" in obj:
                    claim_data["authority_tier"] = obj["tier"]
                claims.append(Claim(**claim_data))
            elif line_type == "end":
                end_found = True

    if not claims:
        raise ValueError(f"No claims found in stream file: {akfl_path}")

    return AKF(
        version="1.0",
        claims=claims,
        agent=agent,
        session=session_id,
    )


def iter_stream(akfl_path: str) -> Generator[dict, None, None]:
    """Generator yielding parsed lines from an .akfl file.

    Args:
        akfl_path: Path to .akfl JSON Lines file.

    Yields:
        Parsed dict for each line (with 'type' field: start, claim, end).
    """
    with open(akfl_path) as f:
        for raw_line in f:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            yield json.loads(raw_line)
