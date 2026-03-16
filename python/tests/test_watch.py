"""Tests for AKF file watcher (polling loop, stamping, extension filter)."""

import json
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from akf import watch as watch_mod


@pytest.fixture
def watch_dir(tmp_path):
    """Create a temporary watch directory."""
    d = tmp_path / "watched"
    d.mkdir()
    return d


@pytest.fixture
def akf_config(tmp_path, monkeypatch):
    """Redirect watch config to tmp_path."""
    cfg_path = tmp_path / "watch.json"
    monkeypatch.setattr(watch_mod, "CONFIG_FILE", cfg_path)
    return cfg_path


class TestShouldWatch:
    @pytest.mark.parametrize("ext", [".docx", ".md", ".json", ".py", ".txt",
                                      ".html", ".csv", ".pdf", ".png", ".ts"])
    def test_supported(self, ext, tmp_path):
        f = tmp_path / f"file{ext}"
        f.write_text("data")
        assert watch_mod._should_watch(f) is True

    @pytest.mark.parametrize("ext", [".exe", ".zip", ".dll", ".so", ".o"])
    def test_unsupported(self, ext, tmp_path):
        f = tmp_path / f"file{ext}"
        f.write_text("data")
        assert watch_mod._should_watch(f) is False

    def test_hidden(self, tmp_path):
        f = tmp_path / ".hidden.md"
        f.write_text("data")
        assert watch_mod._should_watch(f) is False

    def test_akf_suffix(self, tmp_path):
        f = tmp_path / "data.akf"
        f.write_text("data")
        assert watch_mod._should_watch(f) is False

    def test_directory(self, tmp_path):
        d = tmp_path / "subdir"
        d.mkdir()
        assert watch_mod._should_watch(d) is False


class TestLoadWatchConfig:
    def test_missing(self, akf_config):
        result = watch_mod.load_watch_config()
        assert result == {}

    def test_exists(self, akf_config):
        cfg = {"directories": ["/tmp"], "interval": 3.0}
        akf_config.write_text(json.dumps(cfg))
        result = watch_mod.load_watch_config()
        assert result == cfg


class TestWatch:
    def test_detects_new_file(self, watch_dir):
        """Watch loop detects a new file and calls _stamp_file."""
        stamp_calls = []
        stop = threading.Event()

        def fake_stamp(filepath, agent, classification, logger=None, **kwargs):
            stamp_calls.append(str(filepath))
            stop.set()  # Stop after first stamp

        with patch.object(watch_mod, "_stamp_file", fake_stamp):
            t = threading.Thread(
                target=watch_mod.watch,
                kwargs=dict(
                    directories=[str(watch_dir)],
                    interval=0.2,
                    stop_event=stop,
                ),
                daemon=True,
            )
            t.start()
            # Give it time to seed known files
            time.sleep(0.3)
            # Create a new file
            (watch_dir / "test.txt").write_text("hello")
            t.join(timeout=5)

        assert len(stamp_calls) >= 1
        assert "test.txt" in stamp_calls[0]

    def test_nonexistent_dirs(self):
        """Non-existent directories → returns gracefully."""
        stop = threading.Event()
        stop.set()  # Exit immediately
        # Should not raise
        watch_mod.watch(
            directories=["/nonexistent/path/xyz"],
            interval=0.1,
            stop_event=stop,
        )

    def test_respects_stop_event(self, watch_dir):
        """Watch thread exits within 2s after stop_event is set."""
        stop = threading.Event()
        t = threading.Thread(
            target=watch_mod.watch,
            kwargs=dict(
                directories=[str(watch_dir)],
                interval=0.2,
                stop_event=stop,
            ),
            daemon=True,
        )
        t.start()
        time.sleep(0.3)
        stop.set()
        t.join(timeout=2)
        assert not t.is_alive()

    def test_multiple_dirs(self, tmp_path):
        """Files in multiple watched dirs get stamped."""
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()

        stamp_calls = []
        stop = threading.Event()

        def fake_stamp(filepath, agent, classification, logger=None, **kwargs):
            stamp_calls.append(str(filepath))
            if len(stamp_calls) >= 2:
                stop.set()

        with patch.object(watch_mod, "_stamp_file", fake_stamp):
            t = threading.Thread(
                target=watch_mod.watch,
                kwargs=dict(
                    directories=[str(dir_a), str(dir_b)],
                    interval=0.2,
                    stop_event=stop,
                ),
                daemon=True,
            )
            t.start()
            time.sleep(0.3)
            (dir_a / "file_a.txt").write_text("a")
            (dir_b / "file_b.md").write_text("b")
            t.join(timeout=5)

        assert len(stamp_calls) >= 2

    def test_default_dirs_from_config(self, akf_config, monkeypatch):
        """directories=None → loads from config."""
        akf_config.write_text(json.dumps({"directories": ["/nonexistent/abc"]}))
        stop = threading.Event()
        stop.set()
        # Should load config dirs, find none valid, and return
        watch_mod.watch(directories=None, interval=0.1, stop_event=stop)


class TestStampFile:
    def test_calls_stamp(self, tmp_path, monkeypatch):
        """_stamp_file calls stamp.stamp_file when file has no existing metadata."""
        import importlib
        stamp_mod = importlib.import_module("akf.stamp")

        f = tmp_path / "doc.txt"
        f.write_text("test content")

        stamp_calls = []

        import akf.universal
        import akf.tracking
        monkeypatch.setattr(akf.universal, "extract", lambda *a, **k: None)
        monkeypatch.setattr(stamp_mod, "stamp_file", lambda *a, **k: stamp_calls.append(k))
        monkeypatch.setattr(akf.tracking, "get_last_model", lambda: None)

        watch_mod._stamp_file(f, agent="test-agent", classification="internal")
        assert len(stamp_calls) == 1

    def test_skips_stamped_file(self, tmp_path, monkeypatch):
        """_stamp_file skips files that already have AKF metadata."""
        import importlib
        stamp_mod = importlib.import_module("akf.stamp")

        f = tmp_path / "doc.txt"
        f.write_text("test content")

        stamp_calls = []

        import akf.universal
        monkeypatch.setattr(akf.universal, "extract", lambda *a, **k: {"some": "metadata"})
        monkeypatch.setattr(stamp_mod, "stamp_file", lambda *a, **k: stamp_calls.append(k))

        watch_mod._stamp_file(f, agent="test-agent", classification="internal")
        assert len(stamp_calls) == 0
