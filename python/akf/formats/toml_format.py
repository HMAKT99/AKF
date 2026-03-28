"""AKF v1.0 -- TOML format handler.

Embeds AKF metadata under a reserved ``_akf`` table at the top level of
any TOML document.  Uses a ``# _akf: {...}`` comment as the first line
so the metadata survives round-trip parsing by any TOML library.

No external dependencies -- uses stdlib tomllib (Python 3.11+) for
reading.  Writing is handled with a simple JSON comment prefix so
no third-party TOML writer is needed.
"""

import json
import re
from typing import List, Optional

from .base import AKFFormatHandler, ScanReport

# Pattern to detect the AKF comment line at the top of a TOML file
_AKF_COMMENT_RE = re.compile(r"^#\s*_akf:\s*(\{.*\})\s*$")


class TOMLHandler(AKFFormatHandler):
    """TOML format handler -- ``# _akf: {...}`` comment as first line."""

    FORMAT_NAME = "TOML"
    EXTENSIONS = [".toml"]
    MODE = "embedded"
    MECHANISM = "# _akf: {...} comment"
    DEPENDENCIES: List[str] = []

    def embed(self, filepath: str, metadata: dict) -> None:
        """Embed AKF metadata into a TOML file as a comment on the first line."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Serialize metadata as compact JSON on one line
        akf_line = "# _akf: {}\n".format(json.dumps(metadata, ensure_ascii=False))

        # Replace existing AKF comment if present, otherwise prepend
        lines = content.splitlines(True)
        if lines and _AKF_COMMENT_RE.match(lines[0]):
            lines[0] = akf_line
            new_content = "".join(lines)
        else:
            new_content = akf_line + content

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)

    def extract(self, filepath: str) -> Optional[dict]:
        """Extract AKF metadata from the first-line comment of a TOML file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                first_line = f.readline()
        except (OSError, UnicodeDecodeError):
            return None

        match = _AKF_COMMENT_RE.match(first_line.strip())
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
        return None

    def is_enriched(self, filepath: str) -> bool:
        """Return True if the TOML file contains an AKF comment."""
        return self.extract(filepath) is not None


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_handler = TOMLHandler()
embed = _handler.embed
extract = _handler.extract
is_enriched = _handler.is_enriched
scan = _handler.scan
auto_enrich = _handler.auto_enrich
