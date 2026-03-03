"""AKF v1.0 -- Image format handler.

Embeds AKF metadata into image files.  For PNG files Pillow is used to
store metadata in a ``tEXt`` chunk with key ``akf``.  For all other image
formats (JPEG, WebP, TIFF, ...) or when Pillow is not installed, a sidecar
``.akf.json`` file is used instead.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Tuple

from .base import AKFFormatHandler, ScanReport

logger = logging.getLogger(__name__)

_HAS_PILLOW: Optional[bool] = None


def _check_pillow() -> bool:
    """Lazily check whether Pillow is importable."""
    global _HAS_PILLOW
    if _HAS_PILLOW is None:
        try:
            from PIL import Image  # noqa: F401
            _HAS_PILLOW = True
        except ImportError:
            _HAS_PILLOW = False
    return _HAS_PILLOW


class ImageHandler(AKFFormatHandler):
    """Handler for image files (PNG, JPEG, WebP, TIFF).

    For PNG files with Pillow available the metadata is embedded directly
    in a ``tEXt`` chunk.  For JPEG and other raster formats, or when
    Pillow is not installed, a sidecar ``.akf.json`` file is created.
    """

    FORMAT_NAME = "Image"
    EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".tiff"]  # type: List[str]
    MODE = "embedded"
    MECHANISM = "EXIF/XMP metadata"
    DEPENDENCIES = ["Pillow"]  # type: List[str]

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    def embed(self, filepath: str, metadata: dict) -> None:
        """Embed AKF metadata into an image file.

        PNG files are handled natively via Pillow ``tEXt`` chunks.  All
        other formats (or when Pillow is missing) use a sidecar file.
        """
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".png" and _check_pillow():
            self._embed_png(filepath, metadata)
        else:
            if ext == ".png" and not _check_pillow():
                logger.info(
                    "Pillow not available -- falling back to sidecar for %s",
                    filepath,
                )
            from ..sidecar import create as create_sidecar

            create_sidecar(filepath, metadata)

    def extract(self, filepath: str) -> Optional[dict]:
        """Extract AKF metadata from an image file.

        Checks the embedded PNG approach first, then tries sidecar.
        """
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".png" and _check_pillow():
            result = self._extract_png(filepath)
            if result is not None:
                return result

        # Sidecar fallback
        from ..sidecar import read as read_sidecar

        return read_sidecar(filepath)

    def is_enriched(self, filepath: str) -> bool:
        """Return True if the image carries AKF metadata."""
        return self.extract(filepath) is not None

    # ------------------------------------------------------------------
    # PNG-specific helpers (Pillow)
    # ------------------------------------------------------------------

    @staticmethod
    def _embed_png(filepath: str, metadata: dict) -> None:
        from PIL import Image
        from PIL.PngImagePlugin import PngInfo

        img = Image.open(filepath)
        png_info = PngInfo()

        # Preserve existing text chunks (skip our own key)
        if hasattr(img, "text"):
            for k, v in img.text.items():
                if k != "akf":
                    png_info.add_text(k, v)

        png_info.add_text("akf", json.dumps(metadata, ensure_ascii=False))
        img.save(filepath, pnginfo=png_info)

    @staticmethod
    def _extract_png(filepath: str) -> Optional[dict]:
        from PIL import Image

        img = Image.open(filepath)
        if not hasattr(img, "text"):
            return None

        raw = img.text.get("akf")
        if raw is None:
            return None

        try:
            return json.loads(raw)  # type: ignore[no-any-return]
        except (ValueError, json.JSONDecodeError):
            logger.warning("Corrupted AKF payload in PNG %s", filepath)
            return None

    # ------------------------------------------------------------------
    # Directory scanning
    # ------------------------------------------------------------------

    def scan_directory(self, dirpath: str) -> List[Dict[str, object]]:
        """Walk *dirpath* and check each image for AKF metadata.

        Returns a list of dicts with ``file``, ``enriched``, and optional
        ``metadata`` keys.
        """
        results: List[Dict[str, object]] = []
        if not os.path.isdir(dirpath):
            return results

        for root, _dirs, files in os.walk(dirpath):
            for fname in sorted(files):
                ext = os.path.splitext(fname)[1].lower()
                if ext not in self.EXTENSIONS:
                    continue
                full_path = os.path.join(root, fname)
                meta = self.extract(full_path)
                entry: Dict[str, object] = {
                    "file": full_path,
                    "enriched": meta is not None,
                }
                if meta is not None:
                    entry["metadata"] = meta
                results.append(entry)
        return results


# ------------------------------------------------------------------
# Module-level convenience functions
# ------------------------------------------------------------------

_handler = ImageHandler()


def embed(filepath: str, metadata: dict) -> None:
    """Embed AKF metadata into an image file."""
    _handler.embed(filepath, metadata)


def extract(filepath: str) -> Optional[dict]:
    """Extract AKF metadata from an image file."""
    return _handler.extract(filepath)


def is_enriched(filepath: str) -> bool:
    """Check whether an image file has AKF metadata."""
    return _handler.is_enriched(filepath)


def scan(filepath: str) -> ScanReport:
    """Run a security scan on an image file."""
    return _handler.scan(filepath)


def scan_directory(dirpath: str) -> List[Dict[str, object]]:
    """Scan a directory for images and check AKF metadata."""
    return _handler.scan_directory(dirpath)


def auto_enrich(
    filepath: str,
    agent_id: str,
    default_tier: int = 3,
    classification: Optional[str] = None,
) -> None:
    """Auto-enrich an image with AKF metadata."""
    _handler.auto_enrich(filepath, agent_id, default_tier, classification)
