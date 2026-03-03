"""AKF v1.0 -- PDF format handler.

Embeds AKF metadata into PDF files using pypdf (XMP/custom metadata).
Falls back to sidecar .akf.json when pypdf is not installed.

Metadata is stored as a base64-encoded JSON string in the PDF Info dict
under the ``/AKF`` key, with ``/AKFVersion`` set to ``"1.0"``.
"""

import base64
import json
import logging
import os
from typing import Dict, List, Optional

from .base import AKFFormatHandler, ScanReport

logger = logging.getLogger(__name__)

_HAS_PYPDF: Optional[bool] = None


def _check_pypdf() -> bool:
    """Lazily check whether pypdf is importable."""
    global _HAS_PYPDF
    if _HAS_PYPDF is None:
        try:
            import pypdf  # noqa: F401
            _HAS_PYPDF = True
        except ImportError:
            _HAS_PYPDF = False
    return _HAS_PYPDF


class PDFHandler(AKFFormatHandler):
    """Handler for PDF files.

    Uses pypdf to embed metadata in the PDF Info dictionary when available.
    Falls back to a sidecar ``.akf.json`` file when pypdf is not installed.
    """

    FORMAT_NAME = "PDF"
    EXTENSIONS = [".pdf"]  # type: List[str]
    MODE = "embedded"
    MECHANISM = "XMP Metadata"
    DEPENDENCIES = ["pypdf"]  # type: List[str]

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    def embed(self, filepath: str, metadata: dict) -> None:
        """Embed AKF metadata into a PDF.

        When *pypdf* is available the metadata is written directly into the
        PDF's Info dictionary under ``/AKF`` (base64-encoded JSON).  When
        *pypdf* is not installed the metadata is persisted as a sidecar file
        instead.
        """
        if _check_pypdf():
            self._embed_native(filepath, metadata)
        else:
            logger.info(
                "pypdf not available -- falling back to sidecar for %s", filepath
            )
            from ..sidecar import create as create_sidecar

            create_sidecar(filepath, metadata)

    def extract(self, filepath: str) -> Optional[dict]:
        """Extract AKF metadata from a PDF.

        Tries the embedded approach first, then falls back to sidecar.
        """
        if _check_pypdf():
            result = self._extract_native(filepath)
            if result is not None:
                return result

        # Sidecar fallback
        from ..sidecar import read as read_sidecar

        return read_sidecar(filepath)

    def is_enriched(self, filepath: str) -> bool:
        """Return True if the PDF carries AKF metadata (embedded or sidecar)."""
        return self.extract(filepath) is not None

    # ------------------------------------------------------------------
    # Native (pypdf) helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _embed_native(filepath: str, metadata: dict) -> None:
        from pypdf import PdfReader, PdfWriter

        reader = PdfReader(filepath)
        writer = PdfWriter()
        writer.append_pages_from_reader(reader)

        json_bytes = json.dumps(metadata, ensure_ascii=False).encode("utf-8")
        encoded = base64.b64encode(json_bytes).decode("ascii")

        writer.add_metadata({"/AKF": encoded, "/AKFVersion": "1.0"})

        with open(filepath, "wb") as fh:
            writer.write(fh)

    @staticmethod
    def _extract_native(filepath: str) -> Optional[dict]:
        from pypdf import PdfReader

        reader = PdfReader(filepath)
        info = reader.metadata
        if info is None:
            return None

        raw = info.get("/AKF")
        if raw is None:
            return None

        try:
            decoded = base64.b64decode(raw)
            return json.loads(decoded)  # type: ignore[no-any-return]
        except (ValueError, json.JSONDecodeError):
            logger.warning("Corrupted AKF payload in PDF %s", filepath)
            return None


# ------------------------------------------------------------------
# Module-level convenience functions
# ------------------------------------------------------------------

_handler = PDFHandler()


def embed(filepath: str, metadata: dict) -> None:
    """Embed AKF metadata into a PDF file."""
    _handler.embed(filepath, metadata)


def extract(filepath: str) -> Optional[dict]:
    """Extract AKF metadata from a PDF file."""
    return _handler.extract(filepath)


def is_enriched(filepath: str) -> bool:
    """Check whether a PDF file has AKF metadata."""
    return _handler.is_enriched(filepath)


def scan(filepath: str) -> ScanReport:
    """Run a security scan on a PDF file."""
    return _handler.scan(filepath)


def auto_enrich(
    filepath: str,
    agent_id: str,
    default_tier: int = 3,
    classification: Optional[str] = None,
) -> None:
    """Auto-enrich a PDF with AKF metadata."""
    _handler.auto_enrich(filepath, agent_id, default_tier, classification)
