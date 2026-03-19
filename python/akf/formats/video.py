"""AKF v1.0 -- Video format handler.

Embeds AKF metadata into video files via sidecar .akf.json files.
"""

import os
from typing import Dict, List, Optional

from .base import AKFFormatHandler, ScanReport


class VideoHandler(AKFFormatHandler):
    """Handler for video files (MP4, MOV, WebM, MKV).

    Video files always use sidecar .akf.json files for metadata storage.
    """

    FORMAT_NAME = "Video"
    EXTENSIONS = [".mp4", ".mov", ".webm", ".mkv"]  # type: List[str]
    MODE = "sidecar"
    MECHANISM = "sidecar .akf.json"
    DEPENDENCIES = []  # type: List[str]

    def embed(self, filepath: str, metadata: dict) -> None:
        """Embed AKF metadata into a video file via sidecar."""
        from ..sidecar import create as create_sidecar

        create_sidecar(filepath, metadata)

    def extract(self, filepath: str) -> Optional[dict]:
        """Extract AKF metadata from a video file's sidecar."""
        from ..sidecar import read as read_sidecar

        return read_sidecar(filepath)

    def is_enriched(self, filepath: str) -> bool:
        """Return True if the video has AKF metadata."""
        return self.extract(filepath) is not None

    def scan_directory(self, dirpath: str) -> List[Dict[str, object]]:
        """Walk *dirpath* and check each video for AKF metadata.

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

_handler = VideoHandler()


def embed(filepath: str, metadata: dict) -> None:
    """Embed AKF metadata into a video file."""
    _handler.embed(filepath, metadata)


def extract(filepath: str) -> Optional[dict]:
    """Extract AKF metadata from a video file."""
    return _handler.extract(filepath)


def is_enriched(filepath: str) -> bool:
    """Check whether a video file has AKF metadata."""
    return _handler.is_enriched(filepath)


def scan(filepath: str) -> ScanReport:
    """Run a security scan on a video file."""
    return _handler.scan(filepath)


def scan_directory(dirpath: str) -> List[Dict[str, object]]:
    """Scan a directory for videos and check AKF metadata."""
    return _handler.scan_directory(dirpath)


def auto_enrich(
    filepath: str,
    agent_id: str,
    default_tier: int = 3,
    classification: Optional[str] = None,
) -> None:
    """Auto-enrich a video with AKF metadata."""
    _handler.auto_enrich(filepath, agent_id, default_tier, classification)
