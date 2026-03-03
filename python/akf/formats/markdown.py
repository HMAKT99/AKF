"""AKF v1.0 -- Markdown format handler.

Embeds AKF metadata as YAML frontmatter (_akf key with JSON value)
and supports HTML comment annotations for inline claims.

No external dependencies -- uses stdlib json module only.
"""

import json
import re
from typing import Any, Dict, List, Optional

from .base import AKFFormatHandler, ScanReport


# ---------------------------------------------------------------------------
# Frontmatter helpers (no PyYAML dependency)
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\r?\n(.*?)^---[ \t]*\r?\n",
    re.MULTILINE | re.DOTALL,
)

_AKF_COMMENT_RE = re.compile(
    r"<!--\s*akf:(.*?)-->",
    re.DOTALL,
)

_AKF_FRONTMATTER_RE = re.compile(
    r"""^_akf:\s*'(.*?)'\s*$""",
    re.MULTILINE,
)


def _parse_frontmatter(text: str) -> Optional[Dict[str, str]]:
    """Parse YAML frontmatter into a simple key: value dict.

    Only supports top-level scalar values (string or single-quoted JSON).
    This is intentionally minimal to avoid a PyYAML dependency.
    """
    m = _FRONTMATTER_RE.match(text)
    if m is None:
        return None
    block = m.group(1)
    result: Dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        colon_idx = line.find(":")
        if colon_idx < 0:
            continue
        key = line[:colon_idx].strip()
        val = line[colon_idx + 1 :].strip()
        # Strip surrounding quotes
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        result[key] = val
    return result


def _serialize_frontmatter(fields: Dict[str, str]) -> str:
    """Serialize a dict back to YAML frontmatter string (simple scalars)."""
    lines = ["---"]
    for key, val in fields.items():
        # Always single-quote JSON values to keep them safe in YAML
        if key == "_akf":
            lines.append("_akf: '{}'".format(val))
        else:
            # Preserve other keys as-is
            lines.append("{}: {}".format(key, val))
    lines.append("---")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# MarkdownHandler
# ---------------------------------------------------------------------------


class MarkdownHandler(AKFFormatHandler):
    """Markdown format handler -- YAML frontmatter + HTML comment annotations."""

    FORMAT_NAME = "Markdown"
    EXTENSIONS = [".md", ".markdown"]
    MODE = "embedded"
    MECHANISM = "YAML frontmatter"
    DEPENDENCIES: List[str] = []  # stdlib only

    def embed(self, filepath: str, metadata: dict) -> None:
        """Embed AKF metadata into a Markdown file via YAML frontmatter."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        akf_json = json.dumps(metadata, separators=(",", ":"), ensure_ascii=False)
        fm = _parse_frontmatter(content)

        if fm is not None:
            # File already has frontmatter -- merge _akf key
            fm["_akf"] = akf_json
            m = _FRONTMATTER_RE.match(content)
            assert m is not None  # we just parsed it
            body = content[m.end() :]
            new_content = _serialize_frontmatter(fm) + body
        else:
            # No frontmatter -- add one
            fm_block = _serialize_frontmatter({"_akf": akf_json})
            new_content = fm_block + content

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

    def extract(self, filepath: str) -> Optional[dict]:
        """Extract AKF metadata from a Markdown file.

        Looks in YAML frontmatter first, then falls back to HTML comments.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Strategy 1: YAML frontmatter _akf key
        fm = _parse_frontmatter(content)
        if fm is not None and "_akf" in fm:
            try:
                return json.loads(fm["_akf"])  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                pass

        # Strategy 2: HTML comment <!-- akf:{...} -->
        m = _AKF_COMMENT_RE.search(content)
        if m:
            try:
                return json.loads(m.group(1).strip())  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                pass

        return None

    def is_enriched(self, filepath: str) -> bool:
        """Return True if the file contains AKF metadata."""
        return self.extract(filepath) is not None


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def render(akf_unit: dict, include_comments: bool = True) -> str:
    """Render an AKF unit as Markdown with optional trust annotations.

    Parameters
    ----------
    akf_unit : dict
        A dict with at minimum ``claims`` (list of claim dicts).
    include_comments : bool
        If True, emit ``<!-- akf:{...} -->`` HTML comments before each claim.

    Returns
    -------
    str
        Annotated Markdown text.
    """
    lines: List[str] = []
    claims = akf_unit.get("claims", [])

    for claim in claims:
        if include_comments:
            annotation: Dict[str, Any] = {}
            if "t" in claim:
                annotation["t"] = claim["t"]
            if "src" in claim:
                annotation["src"] = claim["src"]
            if "ver" in claim:
                annotation["ver"] = claim["ver"]
            if "ai" in claim:
                annotation["ai"] = claim["ai"]
            if "tier" in claim:
                annotation["tier"] = claim["tier"]
            comment_json = json.dumps(annotation, separators=(",", ":"), ensure_ascii=False)
            lines.append("<!-- akf:{} -->".format(comment_json))
        lines.append(claim.get("c", ""))
        lines.append("")  # blank line between claims

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_handler = MarkdownHandler()
embed = _handler.embed
extract = _handler.extract
is_enriched = _handler.is_enriched
scan = _handler.scan
auto_enrich = _handler.auto_enrich
