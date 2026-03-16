"""Smart context detection for AKF auto-stamping.

Infers rich metadata from a file's environment — git history, download
source, project rules, LLM tracking — so the watcher can stamp files
with meaningful data instead of static defaults.

Performance: designed for batch operation.  Per-directory results (git
repo check, project rules) are cached with 5-minute TTL so that
stamping 100 files in the same directory costs roughly the same as
stamping 1.
"""

from __future__ import annotations

import fnmatch
import json
import os
import platform
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------

@dataclass
class FileContext:
    """Inferred context for a file being stamped."""
    source: Optional[str] = None
    author: Optional[str] = None
    classification: Optional[str] = None
    authority_tier: Optional[int] = None
    ai_generated: Optional[bool] = None
    model: Optional[str] = None
    confidence: float = 0.7


# ---------------------------------------------------------------------------
# Platform check (done once at import time)
# ---------------------------------------------------------------------------

_IS_DARWIN = platform.system() == "Darwin"


# ---------------------------------------------------------------------------
# Shared cache infrastructure (per-directory, 5-min TTL)
# ---------------------------------------------------------------------------

_CACHE_TTL = 300  # 5 minutes

_git_repo_cache: Dict[str, Tuple[bool, float]] = {}
_rules_cache: Dict[str, Tuple[List[dict], float]] = {}
_download_source_cache: Dict[str, Tuple[Optional[str], float]] = {}


def _cache_get(cache, key):
    """Return cached value if present and not expired, else None."""
    entry = cache.get(key)
    if entry and (time.monotonic() - entry[1]) < _CACHE_TTL:
        return entry[0]
    return _SENTINEL


# Sentinel to distinguish "cached None" from "not cached"
_SENTINEL = object()


# ---------------------------------------------------------------------------
# Feature 0: Git repo check (cached per directory)
# ---------------------------------------------------------------------------

def _is_in_git_repo(filepath: Path) -> bool:
    """Check if filepath is inside a git repository (cached per directory)."""
    directory = str(filepath.parent)

    cached = _cache_get(_git_repo_cache, directory)
    if cached is not _SENTINEL:
        return cached

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=5,
        )
        is_git = result.returncode == 0 and result.stdout.strip() == "true"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        is_git = False

    _git_repo_cache[directory] = (is_git, time.monotonic())
    return is_git


# ---------------------------------------------------------------------------
# Feature 1: Git Author Detection
# ---------------------------------------------------------------------------

def _detect_git_author(filepath: Path) -> Optional[str]:
    """Detect the last git commit author for a file.

    Returns "Name <email>" or None if file is untracked / not in git.
    Skips the subprocess if the directory is known to not be a git repo.
    """
    if not _is_in_git_repo(filepath):
        return None
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%aN <%aE>", "--", str(filepath)],
            cwd=str(filepath.parent),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


# ---------------------------------------------------------------------------
# Feature 2: Download URL Tracking (macOS only)
# ---------------------------------------------------------------------------

def _detect_download_source(filepath: Path) -> Optional[str]:
    """Detect original download URL from macOS extended attributes.

    Results are cached per file path (download source is immutable).
    Returns None immediately on non-macOS platforms.
    """
    if not _IS_DARWIN:
        return None

    path_str = str(filepath)
    cached = _cache_get(_download_source_cache, path_str)
    if cached is not _SENTINEL:
        return cached

    url = None
    try:
        import plistlib

        result = subprocess.run(
            ["xattr", "-px", "com.apple.metadata:kMDItemWhereFroms", path_str],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            hex_str = result.stdout.replace(" ", "").replace("\n", "")
            raw = bytes.fromhex(hex_str)
            urls = plistlib.loads(raw)
            if isinstance(urls, list) and urls:
                url = urls[0]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError,
            ValueError, Exception):
        pass

    _download_source_cache[path_str] = (url, time.monotonic())
    return url


# ---------------------------------------------------------------------------
# Feature 3: Project-Based Classification Rules (cached per directory)
# ---------------------------------------------------------------------------

def load_project_rules(filepath: Path) -> List[dict]:
    """Walk up from *filepath* looking for ``.akf/config.json`` with rules.

    Results are cached per parent directory (5-min TTL).
    Also loads rules from ``~/.akf/watch.json`` as fallback.
    """
    directory = str(filepath.parent.resolve())

    cached = _cache_get(_rules_cache, directory)
    if cached is not _SENTINEL:
        return cached

    rules: List[dict] = []

    # Walk up directories looking for .akf/config.json
    current = Path(directory)
    root = Path(current.anchor)
    while current != root:
        config_path = current / ".akf" / "config.json"
        if config_path.is_file():
            try:
                with open(config_path) as f:
                    data = json.load(f)
                project_rules = data.get("rules", [])
                if isinstance(project_rules, list):
                    rules.extend(project_rules)
                break  # Use closest .akf/config.json only
            except (json.JSONDecodeError, OSError):
                pass
        current = current.parent

    # Fallback: global rules from ~/.akf/watch.json
    global_config = Path.home() / ".akf" / "watch.json"
    if global_config.is_file():
        try:
            with open(global_config) as f:
                data = json.load(f)
            global_rules = data.get("rules", [])
            if isinstance(global_rules, list):
                rules.extend(global_rules)
        except (json.JSONDecodeError, OSError):
            pass

    _rules_cache[directory] = (rules, time.monotonic())
    return rules


def _match_rules(filepath: Path, rules: List[dict]) -> Tuple[Optional[str], Optional[int]]:
    """Match filepath against classification rules (first match wins).

    Each rule: ``{"pattern": "*/finance/*", "classification": "confidential", "tier": 2}``
    """
    path_str = str(filepath)
    for rule in rules:
        pattern = rule.get("pattern", "")
        if fnmatch.fnmatch(path_str, pattern):
            return rule.get("classification"), rule.get("tier")
    return None, None


# ---------------------------------------------------------------------------
# Feature 4: AI-Generated Content Detection
# ---------------------------------------------------------------------------

_AI_DETECTION_WINDOW = 60  # seconds

def _detect_ai_generated(
    filepath: Path,
    tracking_last: Optional[dict],
) -> Tuple[Optional[bool], Optional[str]]:
    """Detect if a file was likely AI-generated based on tracking timestamps.

    If the last tracked LLM call happened within 60 seconds of the file's
    mtime, the file is considered AI-generated.

    Returns (ai_generated, model_name).
    """
    if not tracking_last:
        return None, None

    timestamp_str = tracking_last.get("timestamp")
    if not timestamp_str:
        return None, None

    try:
        from datetime import datetime, timezone
        tracking_time = datetime.fromisoformat(timestamp_str)
        if tracking_time.tzinfo is None:
            tracking_time = tracking_time.replace(tzinfo=timezone.utc)

        file_mtime = os.path.getmtime(str(filepath))
        file_time = datetime.fromtimestamp(file_mtime, tz=timezone.utc)

        delta = abs((file_time - tracking_time).total_seconds())
        if delta <= _AI_DETECTION_WINDOW:
            return True, tracking_last.get("model")
    except (OSError, ValueError, TypeError):
        pass

    return None, None


# ---------------------------------------------------------------------------
# Feature 5: Smart Confidence Scoring
# ---------------------------------------------------------------------------

KNOWN_DOMAINS = frozenset({
    "github.com",
    "arxiv.org",
    "drive.google.com",
    "docs.google.com",
    "dropbox.com",
    "sharepoint.com",
    "notion.so",
    "confluence.atlassian.net",
    "stackoverflow.com",
    "huggingface.co",
    "kaggle.com",
    "pypi.org",
    "npmjs.com",
    "registry.npmjs.org",
})


def _is_known_domain(url: str) -> bool:
    """Check if a URL belongs to a known/trusted domain."""
    try:
        # Simple domain extraction without urllib for speed
        # Strip protocol
        stripped = url.split("://", 1)[-1]
        # Get domain (before first /)
        domain = stripped.split("/", 1)[0].lower()
        # Remove port
        domain = domain.split(":")[0]
        # Check domain and parent domains
        parts = domain.split(".")
        for i in range(len(parts) - 1):
            candidate = ".".join(parts[i:])
            if candidate in KNOWN_DOMAINS:
                return True
    except (ValueError, IndexError):
        pass
    return False


def _compute_confidence(
    base: float,
    *,
    has_source: bool = False,
    in_git_with_commits: bool = False,
    is_verified_download: bool = False,
    ai_generated_no_source: bool = False,
    evidence_count: int = 0,
) -> float:
    """Compute smart confidence score with adjustments.

    Adjustments:
        +0.10  has source URL
        +0.05  in git with commit history
        +0.10  source is a known/trusted domain
        -0.10  AI-generated without source attribution
        +0.05  per evidence signal (capped at +0.15)
    """
    score = base

    if has_source:
        score += 0.10
    if in_git_with_commits:
        score += 0.05
    if is_verified_download:
        score += 0.10
    if ai_generated_no_source:
        score -= 0.10

    evidence_boost = min(evidence_count * 0.05, 0.15)
    score += evidence_boost

    # Clamp to [0.1, 1.0]
    return max(0.1, min(1.0, round(score, 2)))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def infer_context(
    filepath: os.PathLike,
    *,
    base_classification: str = "internal",
    base_confidence: float = 0.7,
    tracking_last: Optional[dict] = None,
    project_rules: Optional[List[dict]] = None,
) -> FileContext:
    """Infer rich context for a file from its environment.

    Each detector is fault-tolerant — failures return None and are
    silently ignored so stamping always succeeds.

    Args:
        filepath: Path to the file being stamped.
        base_classification: Default classification if rules don't match.
        base_confidence: Starting confidence score before adjustments.
        tracking_last: Output of ``get_last_model()`` (or None).
        project_rules: Pre-loaded rules list (or None to auto-discover).
    """
    filepath = Path(filepath)
    ctx = FileContext()

    # --- Git author ---
    try:
        ctx.author = _detect_git_author(filepath)
    except Exception:
        pass

    # --- Download source ---
    try:
        ctx.source = _detect_download_source(filepath)
    except Exception:
        pass

    # --- Project rules (cached per directory) ---
    try:
        if project_rules is None:
            project_rules = load_project_rules(filepath)
        classification, tier = _match_rules(filepath, project_rules)
        ctx.classification = classification or base_classification
        ctx.authority_tier = tier
    except Exception:
        ctx.classification = base_classification

    # --- AI-generated detection (layered) ---
    # Layer 1: Tracking timestamp (most reliable — gives us model name)
    try:
        ai_gen, model = _detect_ai_generated(filepath, tracking_last)
        ctx.ai_generated = ai_gen
        if model:
            ctx.model = model
    except Exception:
        pass

    # Layer 2: Content heuristics + macOS creator app (fallback)
    # Only runs when tracking didn't give a definitive answer.
    if ctx.ai_generated is None:
        try:
            from .ai_detect import detect_ai_content

            detection = detect_ai_content(filepath)
            if detection.likely_ai:
                ctx.ai_generated = True
                if detection.creator_app and not ctx.source:
                    ctx.source = f"app:{detection.creator_app}"
        except Exception:
            pass

    # --- Smart confidence ---
    try:
        evidence_count = 0
        if ctx.author:
            evidence_count += 1
        if ctx.source:
            evidence_count += 1
        if ctx.classification and ctx.classification != base_classification:
            evidence_count += 1

        in_git = _is_in_git_repo(filepath) and ctx.author is not None

        ctx.confidence = _compute_confidence(
            base_confidence,
            has_source=ctx.source is not None,
            in_git_with_commits=in_git,
            is_verified_download=(
                ctx.source is not None and _is_known_domain(ctx.source)
            ),
            ai_generated_no_source=(
                ctx.ai_generated is True and ctx.source is None
            ),
            evidence_count=evidence_count,
        )
    except Exception:
        ctx.confidence = base_confidence

    return ctx
