"""AKF v1.0 -- Email (.eml) format handler.

Embeds AKF metadata into RFC-5322 ``.eml`` files using custom X-headers.
No external dependencies are required -- the stdlib ``email`` module is
used for parsing and serialisation.

Headers added / replaced:

* ``X-AKF-Metadata`` -- base64-encoded JSON of the full AKF metadata dict
* ``X-AKF-Version``  -- always ``"1.0"``
* ``X-AKF-Classification`` -- present only when the metadata contains a
  ``classification`` key
"""

import base64
import email
import email.policy
import json
import logging
from typing import Dict, List, Optional

from .base import AKFFormatHandler, ScanReport

logger = logging.getLogger(__name__)


class EmailHandler(AKFFormatHandler):
    """Handler for RFC-5322 email files (``.eml``).

    All operations use the Python standard library so no optional
    dependencies are needed.
    """

    FORMAT_NAME = "Email"
    EXTENSIONS = [".eml"]  # type: List[str]
    MODE = "embedded"
    MECHANISM = "X-AKF custom header"
    DEPENDENCIES = []  # type: List[str]

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    def embed(self, filepath: str, metadata: dict) -> None:
        """Embed AKF metadata into an ``.eml`` file via custom headers."""
        with open(filepath, "rb") as fh:
            msg = email.message_from_bytes(fh.read(), policy=email.policy.default)

        json_bytes = json.dumps(metadata, ensure_ascii=False).encode("utf-8")
        encoded = base64.b64encode(json_bytes).decode("ascii")

        # Remove any existing AKF headers (safe even if absent)
        for hdr in ("X-AKF-Metadata", "X-AKF-Version", "X-AKF-Classification"):
            if hdr in msg:
                del msg[hdr]

        msg["X-AKF-Metadata"] = encoded
        msg["X-AKF-Version"] = "1.0"

        classification = metadata.get("classification")
        if classification:
            msg["X-AKF-Classification"] = str(classification)

        with open(filepath, "wb") as fh:
            fh.write(msg.as_bytes())

    def extract(self, filepath: str) -> Optional[dict]:
        """Extract AKF metadata from an ``.eml`` file.

        Returns the decoded metadata dict or ``None`` if the file does not
        contain AKF headers.
        """
        with open(filepath, "rb") as fh:
            msg = email.message_from_bytes(fh.read(), policy=email.policy.default)

        raw = msg.get("X-AKF-Metadata")
        if raw is None:
            return None

        try:
            decoded = base64.b64decode(raw)
            return json.loads(decoded)  # type: ignore[no-any-return]
        except (ValueError, json.JSONDecodeError):
            logger.warning("Corrupted AKF payload in EML %s", filepath)
            return None

    def is_enriched(self, filepath: str) -> bool:
        """Return True if the EML file carries AKF metadata."""
        return self.extract(filepath) is not None

    # ------------------------------------------------------------------
    # Email-specific helpers
    # ------------------------------------------------------------------

    def has_ai_content(self, filepath: str) -> bool:
        """Check if any claim in the AKF metadata is flagged as AI-generated.

        Returns ``False`` when no metadata is found or no claims have
        ``ai: True``.
        """
        meta = self.extract(filepath)
        if meta is None:
            return False
        claims = meta.get("claims", [])
        return any(c.get("ai") for c in claims)

    def get_classification(self, filepath: str) -> Optional[str]:
        """Return the AKF classification header value, or None."""
        with open(filepath, "rb") as fh:
            msg = email.message_from_bytes(fh.read(), policy=email.policy.default)
        return msg.get("X-AKF-Classification")


# ------------------------------------------------------------------
# Module-level convenience functions
# ------------------------------------------------------------------

_handler = EmailHandler()


def embed(filepath: str, metadata: dict) -> None:
    """Embed AKF metadata into an EML file."""
    _handler.embed(filepath, metadata)


def extract(filepath: str) -> Optional[dict]:
    """Extract AKF metadata from an EML file."""
    return _handler.extract(filepath)


def is_enriched(filepath: str) -> bool:
    """Check whether an EML file has AKF metadata."""
    return _handler.is_enriched(filepath)


def scan(filepath: str) -> ScanReport:
    """Run a security scan on an EML file."""
    return _handler.scan(filepath)


def has_ai_content(filepath: str) -> bool:
    """Check if any claim is flagged as AI-generated."""
    return _handler.has_ai_content(filepath)


def auto_enrich(
    filepath: str,
    agent_id: str,
    default_tier: int = 3,
    classification: Optional[str] = None,
) -> None:
    """Auto-enrich an EML file with AKF metadata."""
    _handler.auto_enrich(filepath, agent_id, default_tier, classification)
