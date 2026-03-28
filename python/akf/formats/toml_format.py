"""AKF v1.0 — TOML format handler.

Embeds AKF metadata as a ``[_akf]`` table appended to any TOML document.
Uses stdlib ``tomllib`` (Python 3.11+) for reading; writes with a minimal
serialiser to avoid external dependencies.

Works with any TOML file: ``pyproject.toml``, ``Cargo.toml``, config files.
"""

import json
import re
import sys
from typing import Any, Dict, List, Optional

from .base import AKFFormatHandler, ScanReport

_AKF_TABLE_RE = re.compile(
    r"\n?\[_akf\]\n.*?(?=\n\[|\Z)",
    re.DOTALL,
)

_AKF_KEY_RE = re.compile(r"^\[_akf\]", re.MULTILINE)


def _load_toml(text: str) -> Dict[str, Any]:
    if sys.version_info >= (3, 11):
        import tomllib
        return tomllib.loads(text)
    try:
        import tomli
        return tomli.loads(text)
    except ImportError:
        raise ImportError(
            "TOML reading requires Python 3.11+ or 'tomli'. "
            "Install with: pip install tomli"
        )


def _dict_to_toml_table(d: Dict[str, Any], indent: str = "") -> str:
    lines: List[str] = []
    for k, v in d.items():
        key = k if re.match(r"^[A-Za-z0-9_-]+$", k) else '"{}"'.format(k)
        if isinstance(v, bool):
            lines.append("{}{}  = {}".format(indent, key, "true" if v else "false"))
        elif isinstance(v, int):
            lines.append("{}{}  = {}".format(indent, key, v))
        elif isinstance(v, float):
            lines.append("{}{}  = {}".format(indent, key, v))
        elif isinstance(v, str):
            escaped = v.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            lines.append('{}{}  = "{}"'.format(indent, key, escaped))
        elif isinstance(v, list):
            items = json.dumps(v, ensure_ascii=False)
            lines.append("{}{}  = {}".format(indent, key, items))
        elif isinstance(v, dict):
            lines.append("")
            lines.append("{}[_akf.{}]".format(indent, key))
            lines.extend(_dict_to_toml_table(v, indent).splitlines())
        else:
            lines.append('{}{}  = "{}"'.format(indent, key, str(v)))
    return "\n".join(lines)


def _remove_akf_table(text: str) -> str:
    cleaned = _AKF_TABLE_RE.sub("", text)
    return cleaned.rstrip() + "\n"


class TOMLHandler(AKFFormatHandler):
    """TOML format handler — ``[_akf]`` table."""

    FORMAT_NAME = "TOML"
    EXTENSIONS = [".toml"]
    MODE = "embedded"
    MECHANISM = "[_akf] table"
    DEPENDENCIES: List[str] = []

    def embed(self, filepath: str, metadata: dict) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()

        try:
            _load_toml(raw)
        except Exception:
            from ..sidecar import create as create_sidecar
            create_sidecar(filepath, metadata)
            return

        cleaned = _remove_akf_table(raw)
        akf_block = "\n[_akf]\n" + _dict_to_toml_table(metadata) + "\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cleaned + akf_block)

    def extract(self, filepath: str) -> Optional[dict]:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = f.read()
            data = _load_toml(raw)
            return data.get("_akf")
        except Exception:
            return None

    def is_enriched(self, filepath: str) -> bool:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return bool(_AKF_KEY_RE.search(content))
        except OSError:
            return False


_handler = TOMLHandler()
embed = _handler.embed
extract = _handler.extract
is_enriched = _handler.is_enriched
scan = _handler.scan
auto_enrich = _handler.auto_enrich
