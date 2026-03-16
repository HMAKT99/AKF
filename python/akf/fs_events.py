"""OS-native file system monitoring for AKF.

Uses kqueue (macOS/BSD) for event-driven directory watching with polling
fallback on other platforms.  Also provides creator-app detection via
macOS Spotlight metadata to identify files produced by AI applications.

This module replaces the polling loop in ``watch.py`` when the platform
supports kqueue, providing near-instant file-change detection instead
of periodic 5-second scans.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set

# kqueue is only available on macOS/BSD
try:
    from select import KQ_EV_ADD, KQ_EV_CLEAR, KQ_FILTER_VNODE, KQ_NOTE_WRITE
    from select import kevent, kqueue

    HAS_KQUEUE = True
except ImportError:
    HAS_KQUEUE = False

# ---------------------------------------------------------------------------
# Creator app detection (macOS Spotlight)
# ---------------------------------------------------------------------------

# AI applications whose output should be tagged as AI-generated
AI_APPS = frozenset({
    "claude",
    "chatgpt",
    "cursor",
    "windsurf",
    "codeium",
    "copilot",
    "google gemini",
    "aider",
    "continue",
    "pieces",
    "replit",
})


def detect_creator_app(filepath: os.PathLike) -> Optional[str]:
    """Query macOS Spotlight for the app that created *filepath*.

    Returns the lowered app name if it matches a known AI tool,
    ``None`` otherwise.  Always returns ``None`` on non-macOS.
    """
    if platform.system() != "Darwin":
        return None

    try:
        result = subprocess.run(
            ["mdls", "-name", "kMDItemCreator",
             "-name", "kMDItemContentCreationDate",
             "-raw", str(filepath)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None

        # mdls -raw with multiple keys outputs values on separate lines
        lines = result.stdout.strip().split("\n")
        creator = lines[0].strip().strip('"').lower() if lines else ""
        if creator == "(null)" or not creator:
            return None

        for app in AI_APPS:
            if app in creator:
                return creator
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def is_from_ai_app(filepath: os.PathLike) -> bool:
    """Quick check: was this file created by a known AI application?"""
    return detect_creator_app(filepath) is not None


# ---------------------------------------------------------------------------
# Event-driven watcher (kqueue)
# ---------------------------------------------------------------------------

class KqueueWatcher:
    """Event-driven directory watcher using kqueue (macOS/BSD).

    Instead of polling every N seconds, this registers for directory
    change events via the kernel.  When a directory changes, it scans
    for new/modified files — much more efficient than blind polling.
    """

    def __init__(
        self,
        directories: List[Path],
        callback: Callable[[Path], None],
        *,
        stop_event: Optional[threading.Event] = None,
        logger=None,
    ):
        self.directories = directories
        self.callback = callback
        self.stop_event = stop_event or threading.Event()
        self.logger = logger
        self._kq: Optional[kqueue] = None
        self._fds: Dict[int, Path] = {}  # fd → directory
        self._known: Dict[str, float] = {}  # filepath → mtime

    def _open_directories(self):
        """Open file descriptors for watched directories."""
        self._kq = kqueue()
        events = []
        for d in self.directories:
            try:
                fd = os.open(str(d), os.O_RDONLY)
                self._fds[fd] = d
                ev = kevent(
                    fd,
                    filter=KQ_FILTER_VNODE,
                    flags=KQ_EV_ADD | KQ_EV_CLEAR,
                    fflags=KQ_NOTE_WRITE,
                )
                events.append(ev)
            except OSError as e:
                if self.logger:
                    self.logger.warning("Cannot watch %s: %s", d, e)
        if events:
            self._kq.control(events, 0)

    def _close_directories(self):
        """Close all watched file descriptors."""
        for fd in self._fds:
            try:
                os.close(fd)
            except OSError:
                pass
        self._fds.clear()
        if self._kq:
            self._kq.close()
            self._kq = None

    def _seed_known(self):
        """Build initial mtime map so we only flag new/changed files."""
        from .watch import _should_watch

        for d in self.directories:
            try:
                for f in d.rglob("*"):
                    if _should_watch(f):
                        try:
                            self._known[str(f)] = f.stat().st_mtime
                        except OSError:
                            pass
            except OSError:
                pass

    def _scan_directory(self, directory: Path):
        """Scan a directory for new/modified files and invoke callback."""
        from .watch import _should_watch

        try:
            for f in directory.rglob("*"):
                if not _should_watch(f):
                    continue
                try:
                    mtime = f.stat().st_mtime
                except OSError:
                    continue
                path_str = str(f)
                if path_str not in self._known or self._known[path_str] < mtime:
                    self._known[path_str] = mtime
                    try:
                        self.callback(f)
                    except Exception:
                        if self.logger:
                            self.logger.exception("Callback failed: %s", f)
        except OSError:
            if self.logger:
                self.logger.warning("Error scanning: %s", directory)

    def run(self):
        """Main event loop — blocks until stop_event is set."""
        if not HAS_KQUEUE:
            raise RuntimeError("kqueue not available on this platform")

        self._open_directories()
        self._seed_known()

        if self.logger:
            self.logger.info(
                "KqueueWatcher started, watching %d directories",
                len(self._fds),
            )

        try:
            while not self.stop_event.is_set():
                try:
                    # Wait for events with 1-second timeout so we can
                    # check stop_event periodically
                    events = self._kq.control([], len(self._fds) + 1, 1.0)
                except OSError:
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.5)
                    continue

                for ev in events:
                    directory = self._fds.get(ev.ident)
                    if directory:
                        self._scan_directory(directory)
        finally:
            self._close_directories()
            if self.logger:
                self.logger.info("KqueueWatcher stopped")


# ---------------------------------------------------------------------------
# Polling fallback
# ---------------------------------------------------------------------------

class PollingWatcher:
    """Polling-based directory watcher (cross-platform fallback).

    This is essentially the same logic as ``watch.py`` but packaged as
    a class for consistent interface with ``KqueueWatcher``.
    """

    def __init__(
        self,
        directories: List[Path],
        callback: Callable[[Path], None],
        *,
        interval: float = 5.0,
        stop_event: Optional[threading.Event] = None,
        logger=None,
    ):
        self.directories = directories
        self.callback = callback
        self.interval = interval
        self.stop_event = stop_event or threading.Event()
        self.logger = logger
        self._known: Dict[str, float] = {}

    def _seed_known(self):
        from .watch import _should_watch

        for d in self.directories:
            try:
                for f in d.rglob("*"):
                    if _should_watch(f):
                        try:
                            self._known[str(f)] = f.stat().st_mtime
                        except OSError:
                            pass
            except OSError:
                pass

    def run(self):
        """Main polling loop — blocks until stop_event is set."""
        self._seed_known()

        if self.logger:
            self.logger.info(
                "PollingWatcher started (%0.1fs interval), watching %d dirs",
                self.interval, len(self.directories),
            )

        from .watch import _should_watch

        while not self.stop_event.is_set():
            self.stop_event.wait(timeout=self.interval)
            if self.stop_event.is_set():
                break

            for d in self.directories:
                try:
                    for f in d.rglob("*"):
                        if not _should_watch(f):
                            continue
                        try:
                            mtime = f.stat().st_mtime
                        except OSError:
                            continue
                        path_str = str(f)
                        if (path_str not in self._known
                                or self._known[path_str] < mtime):
                            self._known[path_str] = mtime
                            try:
                                self.callback(f)
                            except Exception:
                                if self.logger:
                                    self.logger.exception(
                                        "Callback failed: %s", f)
                except OSError:
                    if self.logger:
                        self.logger.warning("Error scanning: %s", d)

        if self.logger:
            self.logger.info("PollingWatcher stopped")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_watcher(
    directories: List[Path],
    callback: Callable[[Path], None],
    *,
    interval: float = 5.0,
    stop_event: Optional[threading.Event] = None,
    logger=None,
):
    """Create the best available watcher for this platform.

    Uses kqueue on macOS/BSD, falls back to polling elsewhere.
    """
    if HAS_KQUEUE:
        if logger:
            logger.info("Using kqueue event-driven watcher")
        return KqueueWatcher(
            directories, callback,
            stop_event=stop_event, logger=logger,
        )
    else:
        if logger:
            logger.info("Using polling watcher (kqueue not available)")
        return PollingWatcher(
            directories, callback,
            interval=interval, stop_event=stop_event, logger=logger,
        )
