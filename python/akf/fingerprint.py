"""Content fingerprint that survives stamping and fresh checkouts.

`akf check` used to call a file STALE whenever its mtime was newer than the
stamp, but `git clone` resets every mtime. The fingerprint is a hash of the
file's own content with any embedded AKF stamp removed, recorded at stamp
time (``meta.content_hash``) and recomputed at check time, so a file whose
content is unchanged is not reported STALE.
"""

from __future__ import annotations

import hashlib
import os
from typing import Optional

_MARKDOWN_EXTS = (".md", ".markdown")


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


def _sidecar_mode(filepath: str) -> bool:
    """True when stamping leaves the file itself untouched."""
    from . import universal

    handler = universal._resolve_handler(filepath)
    return handler is None or handler.MODE == "sidecar"


def content_fingerprint(filepath: str) -> Optional[str]:
    """Return ``sha256:<16 hex>`` of the file content ignoring its stamp.

    None when the format embeds its stamp in a way we cannot strip (the
    caller then falls back to the mtime comparison).
    """
    try:
        if filepath.lower().endswith(_MARKDOWN_EXTS):
            with open(filepath, "r", encoding="utf-8") as fh:
                data = _markdown_canonical(fh.read()).encode("utf-8")
        elif _sidecar_mode(filepath):
            with open(filepath, "rb") as fh:
                data = fh.read()
        else:
            return None
    except (OSError, UnicodeDecodeError):
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
    if integrity_hash and not filepath.lower().endswith(_MARKDOWN_EXTS):
        with open(filepath, "rb") as fh:
            full = hashlib.sha256(fh.read()).hexdigest()
        want = integrity_hash.split(":", 1)[-1]
        return bool(want) and full.startswith(want)
    return False
