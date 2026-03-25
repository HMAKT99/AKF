"""AKF v1.0 -- JSON format handler.

Embeds AKF metadata under a reserved ``_akf`` key at the top level of any
JSON document.

No external dependencies -- uses stdlib json module only.
"""

import json
import re
from typing import Any, Dict, List, Optional

from .base import AKFFormatHandler, ScanReport


# ---------------------------------------------------------------------------
# Indentation detection
# ---------------------------------------------------------------------------


def _detect_indent(text: str) -> int:
    """Detect the indentation level used in a JSON file.

    Returns the number of spaces, defaulting to 2 if detection fails.
    """
    # Look for the first indented line
    for line in text.splitlines()[1:]:
        stripped = line.lstrip(" ")
        if stripped and not stripped.startswith("}") and not stripped.startswith("]"):
            indent = len(line) - len(stripped)
            if indent > 0:
                return indent
    return 2


# ---------------------------------------------------------------------------
# JSONHandler
# ---------------------------------------------------------------------------


class JSONHandler(AKFFormatHandler):
    """JSON format handler -- ``_akf`` key at top level."""

    FORMAT_NAME = "JSON"
    EXTENSIONS = [".json"]
    MODE = "embedded"
    MECHANISM = "_akf key"
    DEPENDENCIES: List[str] = []

    def embed(self, filepath: str, metadata: dict) -> None:
        """Embed AKF metadata into a JSON file under the ``_akf`` key."""
        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()

        try:
            indent = _detect_indent(raw)
            data = json.loads(raw)
        except json.JSONDecodeError:
            # File has .json extension but invalid content — fall back to sidecar
            from ..sidecar import create as create_sidecar
            create_sidecar(filepath, metadata)
            return

        if not isinstance(data, dict):
            raise TypeError(
                "Cannot embed AKF metadata in a non-object JSON file "
                "(top-level type is {})".format(type(data).__name__)
            )

        data["_akf"] = metadata

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
            f.write("\n")

    def extract(self, filepath: str) -> Optional[dict]:
        """Extract AKF metadata from a JSON file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return None

        if isinstance(data, dict) and "_akf" in data:
            return data["_akf"]  # type: ignore[no-any-return]
        return None

    def is_enriched(self, filepath: str) -> bool:
        """Return True if the JSON file contains an ``_akf`` key."""
        return self.extract(filepath) is not None


# ---------------------------------------------------------------------------
# Wrap helper
# ---------------------------------------------------------------------------


def wrap(
    data: dict,
    claims: List[dict],
    classification: Optional[str] = None,
    agent_id: Optional[str] = None,
    overall_trust: Optional[float] = None,
) -> dict:
    """Take a dict and claims list, return enriched dict with ``_akf`` key.

    Claims can include a ``loc`` field with a JSONPath-style location
    (e.g. ``$.revenue``, ``$.data[0].name``).

    Parameters
    ----------
    data : dict
        The original data dict.
    claims : list of dict
        Each claim dict should have at minimum ``c`` (content) and ``t`` (trust).
        An optional ``loc`` field specifies the JSONPath location in the data.
    classification : str, optional
        Data classification label.
    agent_id : str, optional
        Identifier for the agent that created the data.
    overall_trust : float, optional
        Overall trust score.  If not given, it is computed as the mean of
        claim trust scores.

    Returns
    -------
    dict
        A copy of *data* with an ``_akf`` key containing the metadata.
    """
    from datetime import datetime, timezone

    result = dict(data)  # shallow copy

    if overall_trust is None and claims:
        trust_values = [c.get("t", 0.0) for c in claims]
        overall_trust = sum(trust_values) / len(trust_values)

    akf_meta: Dict[str, Any] = {
        "akf": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claims": claims,
    }
    if overall_trust is not None:
        akf_meta["overall_trust"] = overall_trust
    if classification:
        akf_meta["classification"] = classification
    if agent_id:
        akf_meta["agent_id"] = agent_id

    result["_akf"] = akf_meta
    return result


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_handler = JSONHandler()
embed = _handler.embed
extract = _handler.extract
is_enriched = _handler.is_enriched
scan = _handler.scan
auto_enrich = _handler.auto_enrich
