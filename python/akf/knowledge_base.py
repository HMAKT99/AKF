"""AKF v1.0 — Knowledge Base: persistent, queryable claim store.

A directory-backed collection of AKF units with topic-based organization,
querying, pruning, and context generation.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .core import create, load
from .models import AKF, Claim


class KnowledgeBase:
    """Directory-backed knowledge base for AKF claims.

    Each topic is stored as a separate .akf file in the directory.
    """

    def __init__(self, directory: str) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)

    @property
    def directory(self) -> str:
        return str(self._dir)

    def add(
        self,
        content: str,
        confidence: float,
        source: Optional[str] = None,
        topic: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Add a claim to the knowledge base.

        Args:
            content: Claim text.
            confidence: Trust score 0.0-1.0.
            source: Source attribution.
            topic: Topic category (used as filename prefix).
            **kwargs: Additional claim fields.

        Returns:
            ID of the created claim.
        """
        topic = topic or "general"
        topic_file = self._topic_path(topic)

        claim_kwargs: Dict[str, Any] = {}
        if source:
            claim_kwargs["source"] = source
        claim_kwargs.update(kwargs)

        new_claim = Claim(content=content, confidence=confidence, **claim_kwargs)

        if topic_file.exists():
            unit = load(topic_file)
            claims = list(unit.claims) + [new_claim]
            unit = unit.model_copy(update={"claims": claims})
        else:
            unit = create(content, confidence=confidence, source=source, **kwargs)
            # Replace the auto-created claim with our new_claim to preserve ID
            unit = unit.model_copy(update={"claims": [new_claim]})

        unit.save(str(topic_file))
        return new_claim.id

    def query(
        self,
        topic: Optional[str] = None,
        min_trust: float = 0.0,
        max_age_days: Optional[int] = None,
    ) -> List[Claim]:
        """Query claims from the knowledge base.

        Args:
            topic: Filter by topic. None for all topics.
            min_trust: Minimum confidence threshold.
            max_age_days: Maximum age in days (based on unit creation time).

        Returns:
            List of matching Claims.
        """
        claims: List[Claim] = []

        if topic:
            paths = [self._topic_path(topic)]
        else:
            paths = list(self._dir.glob("*.akf"))

        now = datetime.now(timezone.utc)

        for path in paths:
            if not path.exists():
                continue
            try:
                unit = load(path)
            except Exception:
                continue

            # Age filter
            if max_age_days is not None and unit.created:
                try:
                    created = datetime.fromisoformat(unit.created.replace("Z", "+00:00"))
                    age = (now - created).days
                    if age > max_age_days:
                        continue
                except (ValueError, TypeError):
                    pass

            for claim in unit.claims:
                if claim.confidence >= min_trust:
                    claims.append(claim)

        return claims

    def to_context(self, max_tokens: int = 2000) -> str:
        """Format the knowledge base for LLM context injection.

        Args:
            max_tokens: Approximate maximum tokens.

        Returns:
            Formatted string.
        """
        all_claims = self.query()
        all_claims.sort(key=lambda c: c.confidence, reverse=True)

        max_chars = max_tokens * 4
        lines = ["[Knowledge Base Context]", ""]
        char_count = sum(len(l) for l in lines)

        for claim in all_claims:
            line = f"- [{claim.confidence:.2f}] {claim.content}"
            if claim.source and claim.source != "unspecified":
                line += f" ({claim.source})"
            if char_count + len(line) > max_chars:
                lines.append("... (truncated)")
                break
            lines.append(line)
            char_count += len(line)

        return "\n".join(lines)

    def prune(
        self,
        max_age_days: int = 90,
        min_trust: float = 0.3,
    ) -> int:
        """Remove old or low-trust claims.

        Args:
            max_age_days: Remove claims from units older than this.
            min_trust: Remove claims below this confidence.

        Returns:
            Number of claims pruned.
        """
        pruned = 0
        now = datetime.now(timezone.utc)

        for path in list(self._dir.glob("*.akf")):
            try:
                unit = load(path)
            except Exception:
                continue

            original_count = len(unit.claims)

            # Filter out low-trust claims
            kept = [c for c in unit.claims if c.confidence >= min_trust]

            # Check age
            if unit.created:
                try:
                    created = datetime.fromisoformat(unit.created.replace("Z", "+00:00"))
                    age = (now - created).days
                    if age > max_age_days:
                        # Remove entire unit
                        pruned += len(unit.claims)
                        os.remove(path)
                        continue
                except (ValueError, TypeError):
                    pass

            if len(kept) < original_count:
                pruned += original_count - len(kept)
                if kept:
                    unit = unit.model_copy(update={"claims": kept})
                    unit.save(str(path))
                else:
                    os.remove(path)

        return pruned

    def stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics.

        Returns:
            Dict with topic count, claim count, average trust, etc.
        """
        topics = list(self._dir.glob("*.akf"))
        total_claims = 0
        total_trust = 0.0
        ai_count = 0
        verified_count = 0

        for path in topics:
            try:
                unit = load(path)
                for claim in unit.claims:
                    total_claims += 1
                    total_trust += claim.confidence
                    if claim.ai_generated:
                        ai_count += 1
                    if claim.verified:
                        verified_count += 1
            except Exception:
                continue

        return {
            "topics": len(topics),
            "total_claims": total_claims,
            "average_trust": round(total_trust / total_claims, 4) if total_claims else 0.0,
            "ai_generated": ai_count,
            "verified": verified_count,
            "directory": str(self._dir),
        }

    def history(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get history of claims, sorted by creation time.

        Args:
            topic: Filter by topic. None for all.

        Returns:
            List of dicts with claim info and timestamps.
        """
        entries: List[Dict[str, Any]] = []

        if topic:
            paths = [self._topic_path(topic)]
        else:
            paths = list(self._dir.glob("*.akf"))

        for path in paths:
            if not path.exists():
                continue
            try:
                unit = load(path)
            except Exception:
                continue

            topic_name = path.stem
            for claim in unit.claims:
                entries.append({
                    "topic": topic_name,
                    "content": claim.content,
                    "confidence": claim.confidence,
                    "source": claim.source,
                    "created": unit.created,
                })

        entries.sort(key=lambda e: e.get("created", ""), reverse=True)
        return entries

    def _topic_path(self, topic: str) -> Path:
        """Get the file path for a topic."""
        safe = topic.replace("/", "_").replace("\\", "_").replace(" ", "_")
        return self._dir / f"{safe}.akf"
