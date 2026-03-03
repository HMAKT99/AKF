"""AKF v1.0 — Abstract base class for format-specific handlers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ScanReport:
    """Security scan result for any file."""

    enriched: bool = False
    classification: Optional[str] = None
    overall_trust: Optional[float] = None
    ai_contribution: Optional[float] = None
    claim_count: int = 0
    ai_claim_count: int = 0
    verified_claim_count: int = 0
    risk_claims: List[str] = field(default_factory=list)
    provenance_depth: int = 0
    integrity_valid: Optional[bool] = None
    warnings: List[str] = field(default_factory=list)
    format: str = ""
    mode: str = ""  # "embedded", "sidecar", "native"


class AKFFormatHandler(ABC):
    """Base class for format-specific AKF handlers.

    Subclasses must implement embed(), extract(), and is_enriched().
    The base class provides default implementations for scan() and auto_enrich().
    """

    FORMAT_NAME: str = ""
    EXTENSIONS: List[str] = []
    MODE: str = "embedded"  # "embedded" or "sidecar"
    MECHANISM: str = ""
    DEPENDENCIES: List[str] = []  # Optional pip packages needed

    @abstractmethod
    def embed(self, filepath: str, metadata: dict) -> None:
        """Embed AKF metadata into a file."""

    @abstractmethod
    def extract(self, filepath: str) -> Optional[dict]:
        """Extract AKF metadata from a file. Returns None if not enriched."""

    @abstractmethod
    def is_enriched(self, filepath: str) -> bool:
        """Check if file has AKF metadata."""

    def scan(self, filepath: str) -> ScanReport:
        """Security scan. Default: extract then analyze."""
        meta = self.extract(filepath)
        if meta is None:
            return ScanReport(enriched=False, format=self.FORMAT_NAME, mode=self.MODE)
        return self._scan_metadata(meta)

    def auto_enrich(
        self,
        filepath: str,
        agent_id: str,
        default_tier: int = 3,
        classification: Optional[str] = None,
    ) -> None:
        """Auto-add AKF metadata to an AI-generated file. Default implementation."""
        meta = self._build_auto_metadata(filepath, agent_id, default_tier, classification)
        self.embed(filepath, meta)

    def _build_auto_metadata(
        self,
        filepath: str,
        agent_id: str,
        default_tier: int = 3,
        classification: Optional[str] = None,
    ) -> dict:
        """Build default AKF metadata for auto-enrichment."""
        import hashlib
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()

        # Compute file hash
        with open(filepath, "rb") as f:
            file_hash = "sha256:" + hashlib.sha256(f.read()).hexdigest()

        meta: Dict[str, Any] = {
            "akf": "1.0",
            "generated_at": now,
            "ai_contribution": 1.0,
            "overall_trust": 0.7,
            "provenance": [
                {"actor": agent_id, "action": "generated", "at": now, "hash": file_hash}
            ],
            "claims": [],
            "integrity_hash": file_hash,
        }
        if classification:
            meta["classification"] = classification
        return meta

    def _scan_metadata(self, meta: dict) -> ScanReport:
        """Analyze extracted metadata into a ScanReport."""
        claims = meta.get("claims", [])
        ai_claims = [c for c in claims if c.get("ai")]
        verified = [c for c in claims if c.get("ver")]
        risks = [c.get("c", "") for c in claims if c.get("risk")]
        prov = meta.get("provenance", [])

        trust_values = [c.get("t", 0) for c in claims]
        avg_trust = sum(trust_values) / len(trust_values) if trust_values else None

        ai_contrib = meta.get("ai_contribution")
        if ai_contrib is None and claims:
            ai_contrib = len(ai_claims) / len(claims)

        return ScanReport(
            enriched=True,
            classification=meta.get("classification"),
            overall_trust=meta.get("overall_trust", avg_trust),
            ai_contribution=ai_contrib,
            claim_count=len(claims),
            ai_claim_count=len(ai_claims),
            verified_claim_count=len(verified),
            risk_claims=risks,
            provenance_depth=len(prov),
            integrity_valid=None,  # Would need file hash check
            format=self.FORMAT_NAME,
            mode=self.MODE,
        )

    def _check_dependency(self, package: str, install_name: str) -> None:
        """Check if optional dependency is available."""
        try:
            __import__(package)
        except ImportError:
            raise ImportError(
                "{} support requires {}. Install with: pip install akf[{}]".format(
                    self.FORMAT_NAME, install_name, self.FORMAT_NAME.lower()
                )
            )
