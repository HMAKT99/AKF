"""AKF file watcher -- auto-stamp files in watched directories."""

from __future__ import annotations

import json
import time
from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".docx", ".xlsx", ".pptx", ".pdf", ".html", ".htm",
    ".json", ".md", ".markdown", ".png", ".jpg", ".jpeg",
    ".py", ".js", ".ts", ".eml", ".csv", ".txt",
}

DEFAULT_DIRS = ["~/Downloads", "~/Desktop", "~/Documents"]
CONFIG_FILE = Path.home() / ".akf" / "watch.json"


def load_watch_config() -> dict:
    """Load watch config from ~/.akf/watch.json."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def watch(directories=None, *, agent=None, classification="internal",
          interval=5.0, stop_event=None, logger=None):
    """Watch directories and auto-stamp new/modified files.

    Polls for file changes and stamps any new or modified files that
    don't already have AKF metadata.

    Args:
        directories: List of directory paths to watch. If None, loads from
            config or uses ~/Downloads, ~/Desktop, ~/Documents.
        agent: Agent ID for stamped metadata.
        classification: Classification label for stamped files.
        interval: Poll interval in seconds.
        stop_event: threading.Event for clean shutdown (daemon mode).
        logger: Logger instance for daemon mode.
    """
    if directories is None:
        config = load_watch_config()
        directories = config.get("directories", DEFAULT_DIRS)

    # Expand ~ and filter to existing directories
    resolved = []
    for d in directories:
        p = Path(d).expanduser().resolve()
        if p.is_dir():
            resolved.append(p)
        elif logger:
            logger.warning("Skipping non-existent directory: %s", d)
    directories = resolved

    if not directories:
        if logger:
            logger.error("No valid directories to watch")
        return

    if logger:
        logger.info("Watching %d directories: %s",
                     len(directories), [str(d) for d in directories])

    known: dict[str, float] = {}

    # Seed with current file mtimes
    for d in directories:
        try:
            for f in d.rglob("*"):
                if _should_watch(f):
                    try:
                        known[str(f)] = f.stat().st_mtime
                    except OSError:
                        pass
        except OSError:
            if logger:
                logger.warning("Error scanning directory: %s", d)

    cycles_since_prune = 0

    while True:
        if stop_event is not None:
            stop_event.wait(timeout=interval)
            if stop_event.is_set():
                break
        else:
            time.sleep(interval)

        seen: set[str] = set()

        for d in directories:
            try:
                for f in d.rglob("*"):
                    if not _should_watch(f):
                        continue
                    path_str = str(f)
                    try:
                        mtime = f.stat().st_mtime
                    except OSError:
                        continue
                    seen.add(path_str)
                    if path_str not in known or known[path_str] < mtime:
                        known[path_str] = mtime
                        _stamp_file(f, agent, classification, logger)
            except OSError:
                if logger:
                    logger.warning("Error scanning directory: %s", d)

        # Prune deleted files every 60 cycles (~5 min at default interval)
        # to bound memory growth without per-cycle overhead.
        cycles_since_prune += 1
        if cycles_since_prune >= 60:
            stale = known.keys() - seen
            for k in stale:
                del known[k]
            if stale and logger:
                logger.debug("Pruned %d stale entries from watch cache", len(stale))
            cycles_since_prune = 0


def _should_watch(f: Path) -> bool:
    """Check if a file should be watched."""
    if not f.is_file():
        return False
    if f.name.startswith("."):
        return False
    if f.suffix == ".akf":
        return False
    return f.suffix.lower() in SUPPORTED_EXTENSIONS


def _stamp_file(filepath: Path, agent, classification, logger=None):
    """Stamp a single file, skipping if it already has AKF metadata.

    If auto-tracking is active (via ``akf install``), the last tracked
    model/provider is automatically included in the stamp.
    """
    try:
        from .universal import extract
        from .stamp import stamp_file
        from .tracking import get_last_model

        existing = extract(str(filepath))
        if existing:  # Already has metadata, skip
            return

        # Pull model info from auto-tracking context if available
        kwargs = {}
        last = get_last_model()
        if last:
            kwargs["model"] = last.get("model")

        stamp_file(
            str(filepath),
            agent=agent,
            classification=classification,
            **kwargs,
        )
        if logger:
            logger.info("Stamped: %s", filepath)
    except Exception:
        if logger:
            logger.exception("Failed to stamp: %s", filepath)
