"""AKF v1.0 -- CSV format handler.

Embeds AKF metadata as a ``# _akf: {...}`` comment on the first line
of any CSV file.  Most CSV parsers treat lines starting with ``#`` as
comments, so the metadata is invisible to downstream consumers.

No external dependencies -- uses stdlib json module only.
"""

import json
import re
from typing import List, Optional

from .base import AKFFormatHandler, ScanReport

# Pattern to detect the AKF comment line at the top of a CSV file
_AKF_COMMENT_RE = re.compile(r"^#\s*_akf:\s*(\{.*\})\s*$")


class CSVHandler(AKFFormatHandler):
    """CSV format handler -- ``# _akf: {...}`` comment as first line."""

    FORMAT_NAME = "CSV"
    EXTENSIONS = [".csv"]
    MODE = "embedded"
    MECHANISM = "# _akf: {...} comment"
    DEPENDENCIES: List[str] = []

    def embed(self, filepath: str, metadata: dict) -> None:
        """Embed AKF metadata into a CSV file as a comment on the first line."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

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
        """Extract AKF metadata from the first-line comment of a CSV file."""
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
        """Return True if the CSV file contains an AKF comment."""
        return self.extract(filepath) is not None


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_handler = CSVHandler()
embed = _handler.embed
extract = _handler.extract
is_enriched = _handler.is_enriched
scan = _handler.scan
auto_enrich = _handler.auto_enrich
