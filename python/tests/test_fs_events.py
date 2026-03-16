"""Tests for OS-native file system monitoring."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from akf.fs_events import (
    AI_APPS,
    HAS_KQUEUE,
    PollingWatcher,
    create_watcher,
    detect_creator_app,
    is_from_ai_app,
)


# ---------------------------------------------------------------------------
# Creator app detection
# ---------------------------------------------------------------------------

class TestCreatorAppDetection:
    def test_non_darwin_returns_none(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("data")
        with patch("akf.fs_events.platform") as mock_platform:
            mock_platform.system.return_value = "Linux"
            assert detect_creator_app(f) is None

    def test_darwin_ai_app(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("data")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '"Claude"\n2024-01-01'

        with patch("akf.fs_events.platform") as mock_platform, \
             patch("akf.fs_events.subprocess.run", return_value=mock_result):
            mock_platform.system.return_value = "Darwin"
            result = detect_creator_app(f)
            assert result is not None
            assert "claude" in result

    def test_is_from_ai_app_convenience(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("data")
        with patch("akf.fs_events.platform") as mock_platform:
            mock_platform.system.return_value = "Linux"
            assert is_from_ai_app(f) is False

    def test_known_ai_apps(self):
        assert "claude" in AI_APPS
        assert "chatgpt" in AI_APPS
        assert "cursor" in AI_APPS


# ---------------------------------------------------------------------------
# Polling watcher
# ---------------------------------------------------------------------------

class TestPollingWatcher:
    def test_detects_new_file(self, tmp_path):
        """PollingWatcher detects new files and calls callback."""
        stamped = []
        stop = threading.Event()

        # Create a watched file extension
        sub = tmp_path / "watched"
        sub.mkdir()

        def callback(filepath):
            stamped.append(str(filepath))
            stop.set()

        watcher = PollingWatcher(
            [sub], callback,
            interval=0.2, stop_event=stop,
        )

        t = threading.Thread(target=watcher.run, daemon=True)
        t.start()
        time.sleep(0.3)

        # Create a new file
        (sub / "test.txt").write_text("hello")
        t.join(timeout=5)

        assert len(stamped) >= 1
        assert "test.txt" in stamped[0]

    def test_stops_on_event(self, tmp_path):
        sub = tmp_path / "watched"
        sub.mkdir()
        stop = threading.Event()

        watcher = PollingWatcher(
            [sub], lambda f: None,
            interval=0.2, stop_event=stop,
        )

        t = threading.Thread(target=watcher.run, daemon=True)
        t.start()
        time.sleep(0.3)
        stop.set()
        t.join(timeout=2)
        assert not t.is_alive()

    def test_ignores_unsupported_extensions(self, tmp_path):
        sub = tmp_path / "watched"
        sub.mkdir()
        stamped = []
        stop = threading.Event()

        def callback(filepath):
            stamped.append(str(filepath))

        watcher = PollingWatcher(
            [sub], callback,
            interval=0.2, stop_event=stop,
        )

        t = threading.Thread(target=watcher.run, daemon=True)
        t.start()
        time.sleep(0.3)

        # Create unsupported file
        (sub / "binary.exe").write_bytes(b"\x00\x01\x02")
        time.sleep(0.5)
        stop.set()
        t.join(timeout=2)

        assert len(stamped) == 0


# ---------------------------------------------------------------------------
# Kqueue watcher (conditional on platform)
# ---------------------------------------------------------------------------

class TestKqueueWatcher:
    @pytest.mark.skipif(not HAS_KQUEUE, reason="kqueue not available")
    def test_detects_new_file(self, tmp_path):
        from akf.fs_events import KqueueWatcher

        stamped = []
        stop = threading.Event()
        sub = tmp_path / "watched"
        sub.mkdir()

        def callback(filepath):
            stamped.append(str(filepath))
            stop.set()

        watcher = KqueueWatcher(
            [sub], callback,
            stop_event=stop,
        )

        t = threading.Thread(target=watcher.run, daemon=True)
        t.start()
        time.sleep(0.5)

        (sub / "test.md").write_text("# Hello")
        t.join(timeout=5)

        assert len(stamped) >= 1
        assert "test.md" in stamped[0]

    @pytest.mark.skipif(not HAS_KQUEUE, reason="kqueue not available")
    def test_stops_cleanly(self, tmp_path):
        from akf.fs_events import KqueueWatcher

        sub = tmp_path / "watched"
        sub.mkdir()
        stop = threading.Event()

        watcher = KqueueWatcher(
            [sub], lambda f: None,
            stop_event=stop,
        )

        t = threading.Thread(target=watcher.run, daemon=True)
        t.start()
        time.sleep(0.5)
        stop.set()
        t.join(timeout=3)
        assert not t.is_alive()


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class TestCreateWatcher:
    def test_returns_watcher(self, tmp_path):
        sub = tmp_path / "watched"
        sub.mkdir()
        watcher = create_watcher([sub], lambda f: None)
        # Should return either KqueueWatcher or PollingWatcher
        assert hasattr(watcher, "run")

    @pytest.mark.skipif(not HAS_KQUEUE, reason="kqueue not available")
    def test_prefers_kqueue_on_macos(self, tmp_path):
        from akf.fs_events import KqueueWatcher

        sub = tmp_path / "watched"
        sub.mkdir()
        watcher = create_watcher([sub], lambda f: None)
        assert isinstance(watcher, KqueueWatcher)
