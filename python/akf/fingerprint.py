"""Content fingerprint that survives stamping and fresh checkouts.

`akf check` used to call a file STALE whenever its mtime was newer than the
stamp, but `git clone` resets every mtime. The fingerprint is a hash of the
file's own content with any embedded AKF stamp removed, recorded at stamp
time (``meta.content_hash``) and recomputed at check time, so a file whose
content is unchanged is not reported STALE.

What counts as "content" per format:
    Markdown      frontmatter minus the akf entries, plus the body
    DOCX/XLSX/PPTX every ZIP part except the ones stamping rewrites
    PDF           page boxes, decoded page content streams, image XObjects
    PNG           mode, size, palette and decoded pixels
    sidecar types the raw bytes (stamping never touches the file)
Anything else returns None and the caller keeps the mtime comparison.
"""

from __future__ import annotations

import hashlib
import os
from typing import Optional

_MARKDOWN_EXTS = (".md", ".markdown")
_OOXML_EXTS = (".docx", ".xlsx", ".pptx")

# Parts `embed_in_ooxml` rewrites or removes when stamping.
_OOXML_STAMP_PARTS = frozenset({
    "docProps/custom.xml",
    "[Content_Types].xml",
    "_rels/.rels",
    "customXml/akf-metadata.json",
    "customXml/akf-item.xml",
    "akf/metadata.json",
    "akf/metadata.xml",
})


def _markdown_canonical(text: str) -> str:
    """Frontmatter minus the akf entries, then the body.

    Stamping rewrites the frontmatter, so only the non-AKF fields and the
    body are hashed. A file with no frontmatter hashes the same before and
    after stamping (empty preserved block).
    """
    from .formats.markdown import _FRONTMATTER_RE, _strip_akf_from_frontmatter

    m = _FRONTMATTER_RE.match(text)
    if m is None:
        return "\0" + text
    preserved = _strip_akf_from_frontmatter(m.group(1)).strip("\n")
    return preserved + "\0" + text[m.end():]


def _ooxml_digest(filepath: str) -> bytes:
    import zipfile

    h = hashlib.sha256()
    with zipfile.ZipFile(filepath, "r") as z:
        for info in sorted(z.infolist(), key=lambda i: i.filename):
            if info.is_dir() or info.filename in _OOXML_STAMP_PARTS:
                continue
            data = z.read(info.filename)
            h.update(info.filename.encode("utf-8") + b"\0" + str(len(data)).encode() + b"\0")
            h.update(data)
    return h.digest()


def _pdf_digest(filepath: str) -> Optional[bytes]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return None

    h = hashlib.sha256()
    reader = PdfReader(filepath)
    for page in reader.pages:
        h.update(repr([float(v) for v in page.mediabox]).encode())
        contents = page.get_contents()
        h.update(contents.get_data() if contents is not None else b"")
        resources = page["/Resources"].get_object() if "/Resources" in page else {}
        xobjects = resources["/XObject"].get_object() if "/XObject" in resources else {}
        for name in sorted(xobjects):
            xo = xobjects[name].get_object()
            h.update(str(name).encode() + b"\0")
            if hasattr(xo, "get_data"):
                h.update(xo.get_data())
        h.update(b"\x01")
    return h.digest()


def _png_digest(filepath: str) -> Optional[bytes]:
    try:
        from PIL import Image
    except ImportError:
        return None

    h = hashlib.sha256()
    with Image.open(filepath) as img:
        img.load()
        h.update(repr((img.mode, img.size)).encode())
        h.update(bytes(img.getpalette() or []))
        h.update(img.tobytes())
    return h.digest()


# The image handler only embeds into PNG; these fall back to a sidecar.
_SIDECAR_IMAGE_EXTS = (".jpg", ".jpeg", ".webp", ".tiff")


def _sidecar_mode(filepath: str) -> bool:
    """True when stamping leaves the file itself untouched."""
    from . import universal

    if filepath.lower().endswith(_SIDECAR_IMAGE_EXTS):
        return True
    handler = universal._resolve_handler(filepath)
    return handler is None or handler.MODE == "sidecar"


def content_fingerprint(filepath: str) -> Optional[str]:
    """Return ``sha256:<16 hex>`` of the file content ignoring its stamp.

    None when the format embeds its stamp in a way we cannot strip (the
    caller then falls back to the mtime comparison).
    """
    lower = filepath.lower()
    try:
        if lower.endswith(_MARKDOWN_EXTS):
            with open(filepath, "r", encoding="utf-8") as fh:
                data = _markdown_canonical(fh.read()).encode("utf-8")
        elif lower.endswith(_OOXML_EXTS):
            data = _ooxml_digest(filepath)
        elif lower.endswith(".pdf"):
            data = _pdf_digest(filepath)
        elif lower.endswith(".png"):
            data = _png_digest(filepath)
        elif _sidecar_mode(filepath):
            with open(filepath, "rb") as fh:
                data = fh.read()
        else:
            return None
    except Exception:
        # Corrupt or unreadable file: no fingerprint, caller uses mtime.
        return None
    if data is None:
        return None
    return "sha256:" + hashlib.sha256(data).hexdigest()[:16]


def content_unchanged(filepath: str, meta: Optional[dict], integrity_hash: Optional[str]) -> bool:
    """True only when we can prove the content matches what was stamped."""
    current = content_fingerprint(filepath)
    if current is None:
        return False
    stored = (meta or {}).get("content_hash")
    if stored:
        return stored == current
    # Stamps from before content_hash: sidecar-mode files are never rewritten,
    # so integrity_hash is a plain hash of the file (full or truncated).
    if integrity_hash and _sidecar_mode(filepath):
        with open(filepath, "rb") as fh:
            full = hashlib.sha256(fh.read()).hexdigest()
        want = integrity_hash.split(":", 1)[-1]
        return bool(want) and full.startswith(want)
    return False
