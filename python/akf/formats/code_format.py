"""AKF v1.0 -- Code format handler.

Embeds AKF metadata as a comment header (first line starting with // _akf: or # _akf:).

No external dependencies -- uses stdlib json module only.
"""

import json
import os
from typing import Dict, List, Optional

from .base import AKFFormatHandler


class CodeHandler(AKFFormatHandler):
    """Code format handler -- comment header."""

    FORMAT_NAME = "Code"
    EXTENSIONS = [".py", ".js", ".ts", ".go", ".c", ".cpp", ".rs", ".rb", ".sh"]
    MODE = "embedded"
    MECHANISM = "comment header"
    DEPENDENCIES: List[str] = []  # stdlib only

    _COMMENT_STYLES = {
        "py": "#",
        "sh": "#",
        "rb": "#",
        "js": "//",
        "ts": "//",
        "go": "//",
        "c": "//",
        "cpp": "//",
        "rs": "//",
    }

    def _get_comment_style(self, filepath: str) -> str:
        ext = os.path.splitext(filepath)[1].lstrip(".").lower()
        return self._COMMENT_STYLES.get(ext, "#")

    def embed(self, filepath: str, metadata: dict) -> None:
        """Embed AKF metadata into a code file via comment header."""
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                lines = f.readlines()
            except UnicodeDecodeError:
                f.seek(0)
                lines = f.readlines()

        akf_json = json.dumps(metadata, separators=(",", ":"), ensure_ascii=False)
        comment = self._get_comment_style(filepath)
        header = "{} _akf: {}\n".format(comment, akf_json)

        # Check if already has an AKF header
        if lines and (lines[0].startswith("// _akf:") or lines[0].startswith("# _akf:")):
            lines[0] = header
        else:
            lines.insert(0, header)

        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def extract(self, filepath: str) -> Optional[dict]:
        """Extract AKF metadata from a code file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                # Only check the first few lines for performance
                for _ in range(5):
                    line = f.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line.startswith("// _akf:") or line.startswith("# _akf:"):
                        try:
                            # Strip the comment prefix and leading/trailing whitespace
                            prefix_len = 8 if line.startswith("//") else 7
                            return json.loads(line[prefix_len:].strip())  # type: ignore[no-any-return]
                        except json.JSONDecodeError:
                            pass
        except (UnicodeDecodeError, IOError):
            pass
        return None

    def is_enriched(self, filepath: str) -> bool:
        """Return True if the file contains AKF metadata."""
        return self.extract(filepath) is not None
