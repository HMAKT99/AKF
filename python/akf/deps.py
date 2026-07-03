"""First-degree local dependency resolution for dependency-aware staleness.

A stamp on ``auth.py`` is a claim about ``auth.py`` *as it behaved with the
modules it imports*. If a local helper it imports changes, the stamp is no
longer trustworthy even though ``auth.py``'s own bytes never moved (issue
#124). At stamp time we record the content hashes of the file's first-degree
local imports; ``akf check`` flips STALE when any of them no longer match.

Scope is deliberately conservative: Python files only, first-degree imports
only, and only modules that resolve to files near the stamped file (same
directory or package-relative). Stdlib and site-packages imports are ignored
— they're versioned by the environment, not the repo.
"""

from __future__ import annotations

import ast
import hashlib
import os
from typing import Dict, Optional


def _hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()[:16]


def _module_to_path(base_dir: str, module: str, level: int = 0) -> Optional[str]:
    """Resolve a module name to a local file path, or None if not local.

    ``level`` is the relative-import depth (``from .. import x`` -> 2).
    """
    root = base_dir
    for _ in range(max(0, level - 1)):
        root = os.path.dirname(root)

    parts = module.split(".") if module else []
    candidates = []
    if parts:
        candidates.append(os.path.join(root, *parts) + ".py")
        candidates.append(os.path.join(root, *parts, "__init__.py"))
    elif level:
        candidates.append(os.path.join(root, "__init__.py"))

    for cand in candidates:
        if os.path.isfile(cand):
            return cand
    return None


def resolve_local_deps(filepath: str) -> Dict[str, str]:
    """Map each first-degree local import of a Python file to its content hash.

    Keys are paths relative to the stamped file's directory (stable across
    checkouts); values are ``sha256:<16 hex>`` content hashes. Returns an
    empty dict for non-Python files or files that don't parse.
    """
    if not filepath.endswith(".py"):
        return {}

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            tree = ast.parse(f.read())
    except (OSError, SyntaxError):
        return {}

    base_dir = os.path.dirname(os.path.abspath(filepath))
    deps: Dict[str, str] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets = [(alias.name, 0) for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            targets = [(node.module or "", node.level)]
        else:
            continue

        for module, level in targets:
            path = _module_to_path(base_dir, module, level)
            if path is None:
                continue
            rel = os.path.relpath(path, base_dir)
            if rel not in deps:
                try:
                    deps[rel] = _hash_file(path)
                except OSError:
                    continue

    return deps


def changed_deps(filepath: str, recorded: Dict[str, str]) -> list:
    """Return the recorded dependencies whose content no longer matches."""
    base_dir = os.path.dirname(os.path.abspath(filepath))
    changed = []
    for rel, expected in recorded.items():
        dep_path = os.path.join(base_dir, rel)
        try:
            if _hash_file(dep_path) != expected:
                changed.append(rel)
        except OSError:
            changed.append(rel)  # dependency deleted or unreadable
    return changed
