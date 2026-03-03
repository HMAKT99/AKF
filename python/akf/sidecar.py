"""AKF v1.0 — Universal sidecar module.

Works with ANY file format by storing AKF metadata in a companion
.akf.json file alongside the original.

Sidecar discovery order:
  1. {filepath}.akf.json           (same directory)
  2. .akf/{filename}.akf.json      (hidden .akf directory)
  3. .akf-manifest.json            (directory-level manifest)
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def sidecar_path(filepath: str) -> str:
    """Return the primary sidecar path for a file.

    This is ``{filepath}.akf.json`` in the same directory as the original.
    """
    return filepath + ".akf.json"


def _discover_sidecar(filepath: str) -> Optional[str]:
    """Find the sidecar file using the discovery order.

    Returns the path to the sidecar file, or None if not found.
    """
    # 1. {filepath}.akf.json
    primary = sidecar_path(filepath)
    if os.path.isfile(primary):
        return primary

    # 2. .akf/{filename}.akf.json
    dirpath = os.path.dirname(os.path.abspath(filepath))
    filename = os.path.basename(filepath)
    hidden = os.path.join(dirpath, ".akf", filename + ".akf.json")
    if os.path.isfile(hidden):
        return hidden

    # 3. .akf-manifest.json (directory-level manifest)
    manifest = os.path.join(dirpath, ".akf-manifest.json")
    if os.path.isfile(manifest):
        return manifest

    return None


def _compute_file_hash(filepath: str) -> str:
    """Compute SHA-256 hash of a file, prefixed with algorithm."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def create(filepath: str, metadata: Dict[str, Any]) -> str:
    """Create a sidecar file for the given filepath.

    Computes the integrity hash of the original file and writes the
    sidecar JSON. Returns the path to the created sidecar file.

    Args:
        filepath: Path to the original file.
        metadata: AKF metadata dict (claims, provenance, etc.).

    Returns:
        Path to the created sidecar file.
    """
    now = datetime.now(timezone.utc).isoformat()
    file_hash = _compute_file_hash(filepath)

    sidecar_data: Dict[str, Any] = {
        "akf": "1.0",
        "mode": "sidecar",
        "target_file": os.path.basename(filepath),
        "generated_at": now,
    }

    # Merge user metadata, but preserve our envelope fields
    for key, value in metadata.items():
        if key not in ("akf", "mode", "target_file", "generated_at"):
            sidecar_data[key] = value

    # Always set integrity_hash from the actual file
    sidecar_data["integrity_hash"] = file_hash

    sc_path = sidecar_path(filepath)
    with open(sc_path, "w", encoding="utf-8") as f:
        json.dump(sidecar_data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return sc_path


def read(filepath: str) -> Optional[Dict[str, Any]]:
    """Read and return sidecar metadata for a file.

    Uses the sidecar discovery order. Returns None if no sidecar exists.

    Args:
        filepath: Path to the original file.

    Returns:
        Metadata dict, or None if no sidecar found.
    """
    sc = _discover_sidecar(filepath)
    if sc is None:
        return None

    with open(sc, "r", encoding="utf-8") as f:
        data = json.load(f)

    # If reading from a manifest, extract entry for this file
    if sc.endswith(".akf-manifest.json") and isinstance(data, dict):
        filename = os.path.basename(filepath)
        if "files" in data and filename in data["files"]:
            return data["files"][filename]
        # Manifest exists but no entry for this file
        return None

    return data


def verify_integrity(filepath: str) -> Optional[bool]:
    """Verify file integrity against its sidecar hash.

    Returns:
        True if hash matches, False if mismatch, None if no sidecar.
    """
    meta = read(filepath)
    if meta is None:
        return None

    stored_hash = meta.get("integrity_hash")
    if stored_hash is None:
        return None

    current_hash = _compute_file_hash(filepath)
    return current_hash == stored_hash


def list_enriched(directory: str) -> List[str]:
    """Find all files with AKF sidecars in a directory.

    Returns a list of original file paths (not the sidecar paths).

    Args:
        directory: Directory to scan.

    Returns:
        List of file paths that have AKF sidecars.
    """
    enriched: List[str] = []

    if not os.path.isdir(directory):
        return enriched

    for entry in sorted(os.listdir(directory)):
        # Skip sidecar files and hidden dirs
        if entry.endswith(".akf.json"):
            continue
        if entry.startswith("."):
            continue

        full_path = os.path.join(directory, entry)
        if not os.path.isfile(full_path):
            continue

        if _discover_sidecar(full_path) is not None:
            enriched.append(full_path)

    return enriched


def remove(filepath: str) -> bool:
    """Delete the sidecar for a file.

    Args:
        filepath: Path to the original file.

    Returns:
        True if a sidecar was found and deleted, False otherwise.
    """
    sc = _discover_sidecar(filepath)
    if sc is None:
        return False

    # Don't delete manifest files, only dedicated sidecars
    if sc.endswith(".akf-manifest.json"):
        return False

    os.remove(sc)
    return True
