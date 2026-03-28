"""AKF v1.0 -- CSV format handler.

Embeds AKF metadata as a comment header (first line starting with # _akf:).

No external dependencies -- uses stdlib json module only.
"""

import json
from typing import List, Optional

from .base import AKFFormatHandler


class CSVHandler(AKFFormatHandler):
    """CSV format handler -- comment header."""

    FORMAT_NAME = "CSV"
    EXTENSIONS = [".csv"]
    MODE = "embedded"
    MECHANISM = "comment header"
    DEPENDENCIES: List[str] = []  # stdlib only

    def embed(self, filepath: str, metadata: dict) -> None:
        """Embed AKF metadata into a CSV file via comment header."""
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                lines = f.readlines()
            except UnicodeDecodeError:
                # Fallback to latin-1 if utf-8 fails
                f.seek(0)
                lines = f.readlines()

        akf_json = json.dumps(metadata, separators=(",", ":"), ensure_ascii=False)
        header = "# _akf: {}\n".format(akf_json)

        # Check if already has an AKF header
        if lines and lines[0].startswith("# _akf:"):
            lines[0] = header
        else:
            lines.insert(0, header)

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def extract(self, filepath: str) -> Optional[dict]:
        """Extract AKF metadata from a CSV file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                # Only check the first few lines for performance
                for _ in range(5):
                    line = f.readline()
                    if not line:
                        break
                    if line.startswith("# _akf:"):
                        try:
                            return json.loads(line[7:].strip())  # type: ignore[no-any-return]
                        except json.JSONDecodeError:
                            pass
        except (UnicodeDecodeError, IOError):
            pass
        return None

    def is_enriched(self, filepath: str) -> bool:
        """Return True if the file contains AKF metadata."""
        return self.extract(filepath) is not None
