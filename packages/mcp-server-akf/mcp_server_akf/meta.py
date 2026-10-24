"""Verification state for MCP tool results, carried in ``_meta``.

A tool result derived from a file can say whether that file was verified,
by what evidence, and whether it changed since — so the next agent can skip
re-verifying it. The state rides under the vendor-prefixed ``_meta`` key
``dev.akf/trust`` (reverse-DNS for akf.dev; not an MCP-reserved prefix).

Any MCP server can use it::

    from mcp_server_akf.meta import TRUST_META_KEY, trust_meta

    meta = trust_meta(path)
    return CallToolResult(content=[...], _meta={TRUST_META_KEY: meta} if meta else None)
"""

from __future__ import annotations

import os

TRUST_META_KEY = "dev.akf/trust"


def trust_meta(path: str, threshold: float = 0.6) -> dict | None:
    """Return the file's AKF verification state, or None if there is no file."""
    if not isinstance(path, str) or not os.path.isfile(path):
        return None

    from akf.check import check_file

    result = check_file(path, threshold=threshold)
    meta = {"v": "1", "status": result.status}
    for key in ("trust", "evidence", "agent", "age_days", "reason"):
        value = getattr(result, key)
        if value not in (None, []):
            meta[key] = value
    return meta
