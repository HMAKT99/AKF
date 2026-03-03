"""AKF v1.0 — Shared OOXML (ZIP-based) helpers for DOCX/XLSX/PPTX.

All Office Open XML formats are ZIP archives. AKF metadata is stored as
a custom XML part inside the archive, which Office applications safely
ignore. This allows zero-dependency embed/extract using only stdlib zipfile.

Storage layout inside the ZIP:
  customXml/akf-metadata.json   — raw JSON metadata
  customXml/akf-item.xml        — XML wrapper with CDATA section
"""

import json
import os
import shutil
import tempfile
import zipfile
from typing import Optional

AKF_JSON_PATH = "customXml/akf-metadata.json"
AKF_XML_PATH = "customXml/akf-item.xml"
AKF_NAMESPACE = "https://akf.dev/v1"


def embed_in_ooxml(filepath: str, metadata: dict) -> None:
    """Embed AKF metadata JSON into an OOXML ZIP archive.

    Creates a temporary copy of the archive with existing AKF entries
    replaced (or added), then atomically replaces the original file.

    Args:
        filepath: Path to the OOXML file (.docx, .xlsx, .pptx).
        metadata: AKF metadata dict to embed.

    Raises:
        zipfile.BadZipFile: If the file is not a valid ZIP archive.
        OSError: If the file cannot be read or written.
    """
    json_bytes = json.dumps(metadata, indent=2, ensure_ascii=False).encode("utf-8")
    xml_content = _wrap_xml(json_bytes.decode("utf-8"))

    # Create temp file in same directory for safe atomic replace
    tmp_fd, tmp_path = tempfile.mkstemp(
        suffix=os.path.splitext(filepath)[1],
        dir=os.path.dirname(os.path.abspath(filepath)),
    )
    os.close(tmp_fd)

    try:
        with zipfile.ZipFile(filepath, "r") as zin:
            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    # Skip existing AKF entries — we'll write fresh ones
                    if item.filename in (AKF_JSON_PATH, AKF_XML_PATH):
                        continue
                    zout.writestr(item, zin.read(item.filename))

                # Add new AKF entries
                zout.writestr(AKF_JSON_PATH, json_bytes)
                zout.writestr(AKF_XML_PATH, xml_content.encode("utf-8"))

        # Atomic replace
        shutil.move(tmp_path, filepath)
    except Exception:
        # Clean up temp file on any failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def extract_from_ooxml(filepath: str) -> Optional[dict]:
    """Extract AKF metadata from an OOXML ZIP archive.

    Args:
        filepath: Path to the OOXML file.

    Returns:
        Parsed metadata dict, or None if no AKF metadata found.
    """
    try:
        with zipfile.ZipFile(filepath, "r") as z:
            if AKF_JSON_PATH in z.namelist():
                data = z.read(AKF_JSON_PATH)
                return json.loads(data)
    except (zipfile.BadZipFile, KeyError, json.JSONDecodeError, OSError):
        pass
    return None


def is_ooxml_enriched(filepath: str) -> bool:
    """Check if an OOXML file contains AKF metadata.

    Args:
        filepath: Path to the OOXML file.

    Returns:
        True if the file contains AKF metadata.
    """
    try:
        with zipfile.ZipFile(filepath, "r") as z:
            return AKF_JSON_PATH in z.namelist()
    except (zipfile.BadZipFile, OSError):
        return False


def list_ooxml_entries(filepath: str) -> Optional[list]:
    """List all entries in an OOXML ZIP archive.

    Useful for debugging and testing.

    Args:
        filepath: Path to the OOXML file.

    Returns:
        List of entry names, or None if not a valid ZIP.
    """
    try:
        with zipfile.ZipFile(filepath, "r") as z:
            return z.namelist()
    except zipfile.BadZipFile:
        return None


def _wrap_xml(json_str: str) -> str:
    """Wrap JSON metadata in an XML envelope with CDATA section."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<akf:metadata xmlns:akf="{ns}">\n'
        "<![CDATA[\n{json}\n]]>\n"
        "</akf:metadata>"
    ).format(ns=AKF_NAMESPACE, json=json_str)
