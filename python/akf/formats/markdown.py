"""AKF v1.0 -- Markdown format handler.

Embeds AKF metadata as native YAML frontmatter under the ``akf:`` key.
Also reads the legacy ``_akf: '{JSON}'`` format for backwards compatibility.
Supports HTML comment annotations for inline claims.

No external dependencies -- uses stdlib json module only.
"""

import json
import re
from typing import Any, Dict, List, Optional, Union

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


def _parse_frontmatter_raw(text: str) -> Optional[str]:
    """Extract the raw frontmatter block (without delimiters)."""
    m = _FRONTMATTER_RE.match(text)
    return m.group(1) if m else None


def _parse_frontmatter_simple(block: str) -> Dict[str, str]:
    """Parse frontmatter into a simple key: value dict (top-level scalars only).

    Used for non-akf keys that we want to preserve.
    """
    result: Dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        # Skip indented lines (part of nested YAML)
        if line[0] in (" ", "\t"):
            continue
        colon_idx = stripped.find(":")
        if colon_idx < 0:
            continue
        key = stripped[:colon_idx].strip()
        val = stripped[colon_idx + 1:].strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        result[key] = val
    return result


def _extract_akf_from_frontmatter(block: str) -> Optional[dict]:
    """Extract AKF metadata from a frontmatter block.

    Supports two formats:
    1. Native YAML (new): ``akf:`` key with indented YAML structure
    2. Legacy JSON string: ``_akf: '{...}'``
    """
    lines = block.splitlines()

    # Try native YAML format: "akf:" followed by indented lines
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "akf:" or stripped.startswith("akf: "):
            # Check if there's an inline value (legacy-ish)
            inline = stripped[4:].strip()
            if inline and not inline.startswith("{"):
                # Simple scalar value after "akf:", not our nested format
                continue
            if inline:
                # Inline JSON: akf: {"v":"1.0",...}
                try:
                    return json.loads(inline)
                except json.JSONDecodeError:
                    pass

            # Collect indented block
            if stripped == "akf:":
                yaml_lines = []
                for j in range(i + 1, len(lines)):
                    if lines[j] and lines[j][0] in (" ", "\t"):
                        yaml_lines.append(lines[j])
                    else:
                        break
                if yaml_lines:
                    return _parse_yaml_block(yaml_lines)

    # Try legacy format: _akf: '{...}'
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("_akf:"):
            val = stripped[5:].strip()
            if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
                val = val[1:-1]
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                pass

    return None


def _parse_yaml_block(lines: List[str]) -> dict:
    """Parse an indented YAML block into a Python dict.

    Minimal YAML parser supporting:
    - Scalars: ``key: value``
    - Booleans: true/false
    - Numbers: int and float
    - Quoted strings: ``'value'`` or ``"value"``
    - Lists of dicts (``- key: value`` sequences)
    - Nested objects (further indentation)

    This is intentionally limited to AKF's data shapes.
    """
    result: Dict[str, Any] = {}
    i = 0
    base_indent = _indent_level(lines[0]) if lines else 0

    while i < len(lines):
        line = lines[i]
        indent = _indent_level(line)
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        if indent < base_indent:
            break

        if ":" not in stripped and not stripped.startswith("- "):
            i += 1
            continue

        colon_idx = stripped.find(":")
        if colon_idx < 0:
            i += 1
            continue

        key = stripped[:colon_idx].strip()
        val_str = stripped[colon_idx + 1:].strip()

        if val_str == "" or val_str is None:
            # Could be a list or nested object — look at next lines
            child_lines = []
            for j in range(i + 1, len(lines)):
                if _indent_level(lines[j]) > indent and lines[j].strip():
                    child_lines.append(lines[j])
                elif not lines[j].strip():
                    child_lines.append(lines[j])
                else:
                    break

            if child_lines and child_lines[0].strip().startswith("- "):
                result[key] = _parse_yaml_list(child_lines)
            elif child_lines:
                result[key] = _parse_yaml_block(child_lines)
            i += 1 + len(child_lines)
        else:
            result[key] = _parse_yaml_value(val_str)
            i += 1

    return result


def _parse_yaml_list(lines: List[str]) -> List[Any]:
    """Parse a YAML list (sequence of ``- `` items)."""
    items: List[Any] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if not stripped.startswith("- "):
            i += 1
            continue

        item_indent = _indent_level(line)
        # First line of list item: "- key: val" or "- scalar"
        first = stripped[2:].strip()

        if ":" in first:
            # Dict item starting on this line
            obj: Dict[str, Any] = {}
            k, v = first.split(":", 1)
            obj[k.strip()] = _parse_yaml_value(v.strip())
            # Collect continuation lines at deeper indent
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if not next_line.strip():
                    j += 1
                    continue
                if _indent_level(next_line) > item_indent and not next_line.strip().startswith("- "):
                    ns = next_line.strip()
                    if ":" in ns:
                        ck, cv = ns.split(":", 1)
                        obj[ck.strip()] = _parse_yaml_value(cv.strip())
                    j += 1
                else:
                    break
            items.append(obj)
            i = j
        else:
            items.append(_parse_yaml_value(first))
            i += 1

    return items


def _parse_yaml_value(val: str) -> Any:
    """Parse a YAML scalar value."""
    if not val:
        return ""
    # Quoted string
    if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
        return val[1:-1]
    # Boolean
    if val.lower() == "true":
        return True
    if val.lower() == "false":
        return False
    # Null
    if val.lower() in ("null", "~"):
        return None
    # Number
    try:
        if "." in val:
            return float(val)
        return int(val)
    except ValueError:
        pass
    # Inline list [a, b, c]
    if val.startswith("[") and val.endswith("]"):
        inner = val[1:-1].strip()
        if not inner:
            return []
        return [_parse_yaml_value(x.strip()) for x in inner.split(",")]
    # Plain string
    return val


def _indent_level(line: str) -> int:
    """Count leading spaces."""
    return len(line) - len(line.lstrip())


# ---------------------------------------------------------------------------
# YAML serializer for AKF metadata
# ---------------------------------------------------------------------------


def _akf_to_yaml(metadata: dict, indent: int = 2) -> str:
    """Serialize AKF metadata dict as native YAML under the ``akf:`` key.

    Produces human-readable, Obsidian/Dataview-friendly YAML.
    """
    lines = ["akf:"]
    _dict_to_yaml(metadata, lines, indent, indent)
    return "\n".join(lines)


def _dict_to_yaml(d: dict, lines: List[str], base: int, step: int) -> None:
    """Recursively serialize a dict to YAML lines."""
    prefix = " " * base
    for key, val in d.items():
        if val is None:
            continue
        if isinstance(val, dict):
            lines.append("{}{}:".format(prefix, key))
            _dict_to_yaml(val, lines, base + step, step)
        elif isinstance(val, list):
            if not val:
                lines.append("{}{}: []".format(prefix, key))
            elif isinstance(val[0], dict):
                lines.append("{}{}:".format(prefix, key))
                _list_of_dicts_to_yaml(val, lines, base + step, step)
            else:
                # Inline list for simple scalars
                items = ", ".join(_yaml_scalar(v) for v in val)
                lines.append("{}{}: [{}]".format(prefix, key, items))
        else:
            lines.append("{}{}: {}".format(prefix, key, _yaml_scalar(val)))


def _list_of_dicts_to_yaml(items: list, lines: List[str], base: int, step: int) -> None:
    """Serialize a list of dicts as YAML list items."""
    prefix = " " * base
    for item in items:
        if isinstance(item, dict):
            first = True
            for key, val in item.items():
                if val is None:
                    continue
                if first:
                    if isinstance(val, dict):
                        lines.append("{}- {}:".format(prefix, key))
                        _dict_to_yaml(val, lines, base + step + 2, step)
                    elif isinstance(val, list) and val and isinstance(val[0], dict):
                        lines.append("{}- {}:".format(prefix, key))
                        _list_of_dicts_to_yaml(val, lines, base + step + 2, step)
                    else:
                        lines.append("{}- {}: {}".format(prefix, key, _yaml_scalar(val)))
                    first = False
                else:
                    inner_prefix = " " * (base + 2)
                    if isinstance(val, dict):
                        lines.append("{}{}:".format(inner_prefix, key))
                        _dict_to_yaml(val, lines, base + step + 2, step)
                    elif isinstance(val, list) and val and isinstance(val[0], dict):
                        lines.append("{}{}:".format(inner_prefix, key))
                        _list_of_dicts_to_yaml(val, lines, base + step + 2, step)
                    elif isinstance(val, list):
                        items_str = ", ".join(_yaml_scalar(v) for v in val)
                        lines.append("{}{}: [{}]".format(inner_prefix, key, items_str))
                    else:
                        lines.append("{}{}: {}".format(inner_prefix, key, _yaml_scalar(val)))
        else:
            lines.append("{}- {}".format(prefix, _yaml_scalar(item)))


def _yaml_scalar(val: Any) -> str:
    """Format a scalar value for YAML output."""
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)
    if val is None:
        return "null"
    s = str(val)
    # Quote strings that look like numbers to prevent YAML type coercion
    try:
        float(s)
        return '"{}"'.format(s)
    except ValueError:
        pass
    # Quote strings that contain YAML-special characters
    if any(c in s for c in (":", "#", "{", "}", "[", "]", ",", "&", "*", "?", "|", "-", "<", ">", "=", "!", "%", "@", "`")):
        escaped = s.replace('"', '\\"')
        return '"{}"'.format(escaped)
    if s.lower() in ("true", "false", "null", "~", "yes", "no", "on", "off"):
        return '"{}"'.format(s)
    if not s:
        return '""'
    return s


def _build_frontmatter(akf_yaml: str, other_fields: Dict[str, str]) -> str:
    """Build a complete frontmatter block with AKF YAML and other preserved fields."""
    lines = ["---"]
    for key, val in other_fields.items():
        if key not in ("akf", "_akf"):
            lines.append("{}: {}".format(key, val))
    lines.append(akf_yaml)
    lines.append("---")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# MarkdownHandler
# ---------------------------------------------------------------------------


class MarkdownHandler(AKFFormatHandler):
    """Markdown format handler -- native YAML frontmatter + HTML comment annotations.

    Writes AKF metadata as native YAML under the ``akf:`` key.
    Reads both native YAML (``akf:``) and legacy JSON string (``_akf: '{...}'``).
    """

    FORMAT_NAME = "Markdown"
    EXTENSIONS = [".md", ".markdown"]
    MODE = "embedded"
    MECHANISM = "YAML frontmatter"
    DEPENDENCIES: List[str] = []  # stdlib only

    def embed(self, filepath: str, metadata: dict) -> None:
        """Embed AKF metadata into a Markdown file as native YAML frontmatter."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        akf_yaml = _akf_to_yaml(metadata)
        fm_block = _parse_frontmatter_raw(content)

        if fm_block is not None:
            # File already has frontmatter — preserve non-AKF keys, replace AKF
            other_fields = _parse_frontmatter_simple(fm_block)
            m = _FRONTMATTER_RE.match(content)
            assert m is not None
            body = content[m.end():]
            new_content = _build_frontmatter(akf_yaml, other_fields) + body
        else:
            # No frontmatter — add one
            new_content = _build_frontmatter(akf_yaml, {}) + content

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

    def extract(self, filepath: str) -> Optional[dict]:
        """Extract AKF metadata from a Markdown file.

        Reads native YAML (``akf:``) and legacy JSON string (``_akf: '{...}'``).
        Falls back to HTML comments.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Strategy 1: YAML frontmatter (native or legacy)
        fm_block = _parse_frontmatter_raw(content)
        if fm_block is not None:
            result = _extract_akf_from_frontmatter(fm_block)
            if result is not None:
                return result

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
