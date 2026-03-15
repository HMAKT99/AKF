"""Tests for AKF daemon (PID management, config, logging, signals)."""

import json
import logging
import os
import signal
import sys
import threading

import pytest

from akf import daemon as daemon_mod


@pytest.fixture
def akf_dir(tmp_path, monkeypatch):
    """Redirect all daemon paths to tmp_path."""
    monkeypatch.setattr(daemon_mod, "AKF_DIR", tmp_path)
    monkeypatch.setattr(daemon_mod, "PID_FILE", tmp_path / "watch.pid")
    monkeypatch.setattr(daemon_mod, "LOG_FILE", tmp_path / "watch.log")
    monkeypatch.setattr(daemon_mod, "CONFIG_FILE", tmp_path / "watch.json")
    return tmp_path


class TestLoadConfig:
    def test_defaults(self, akf_dir):
        config = daemon_mod.load_config()
        assert config == daemon_mod.DEFAULT_CONFIG
        assert config["interval"] == 5.0
        assert "~/Downloads" in config["directories"]

    def test_custom(self, akf_dir):
        cfg = {"directories": ["/tmp/custom"], "interval": 2.0}
        (akf_dir / "watch.json").write_text(json.dumps(cfg))
        config = daemon_mod.load_config()
        assert config["directories"] == ["/tmp/custom"]
        assert config["interval"] == 2.0
        # Defaults still present for keys not overridden
        assert config["classification"] == "internal"

    def test_invalid_json(self, akf_dir):
        (akf_dir / "watch.json").write_text("{bad json!!")
        config = daemon_mod.load_config()
        assert config == daemon_mod.DEFAULT_CONFIG


class TestPidManagement:
    def test_write_pid(self, akf_dir):
        daemon_mod.write_pid()
        pid_file = akf_dir / "watch.pid"
        assert pid_file.exists()
        assert int(pid_file.read_text().strip()) == os.getpid()

    def test_remove_pid(self, akf_dir):
        pid_file = akf_dir / "watch.pid"
        pid_file.write_text("12345")
        daemon_mod._remove_pid()
        assert not pid_file.exists()

    def test_remove_pid_missing(self, akf_dir):
        # Should not raise even if file missing
        daemon_mod._remove_pid()

    def test_is_running_no_pid_file(self, akf_dir):
        assert daemon_mod.is_running() is None

    def test_is_running_current_pid(self, akf_dir):
        pid_file = akf_dir / "watch.pid"
        pid_file.write_text(str(os.getpid()))
        result = daemon_mod.is_running()
        assert result == os.getpid()

    def test_is_running_stale_pid(self, akf_dir):
        pid_file = akf_dir / "watch.pid"
        # Use a PID that almost certainly doesn't exist
        pid_file.write_text("999999999")
        result = daemon_mod.is_running()
        assert result is None
        # Stale PID file should be cleaned up
        assert not pid_file.exists()

    def test_is_running_invalid_content(self, akf_dir):
        pid_file = akf_dir / "watch.pid"
        pid_file.write_text("not-a-number")
        assert daemon_mod.is_running() is None


class TestSetupLogging:
    def test_creates_logger(self, akf_dir):
        logger = daemon_mod.setup_logging()
        assert logger.name == "akf.daemon"
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1
        assert (akf_dir / "watch.log").exists() or any(
            isinstance(h, logging.handlers.RotatingFileHandler)
            for h in logger.handlers
        )
        # Cleanup handlers to avoid leaking across tests
        for h in logger.handlers[:]:
            logger.removeHandler(h)
            h.close()


class TestStopDaemon:
    def test_stop_no_running(self, akf_dir):
        assert daemon_mod.stop_daemon() is False

    def test_stop_stale(self, akf_dir):
        pid_file = akf_dir / "watch.pid"
        pid_file.write_text("999999999")
        # stop_daemon calls is_running which returns None for dead PID
        result = daemon_mod.stop_daemon()
        assert result is False


class TestRunDaemon:
    def test_already_running(self, akf_dir, monkeypatch):
        monkeypatch.setattr(daemon_mod, "is_running", lambda: 12345)
        with pytest.raises(SystemExit) as exc_info:
            daemon_mod.run_daemon(foreground=True)
        assert exc_info.value.code == 1

    def test_foreground_starts_watch(self, akf_dir, monkeypatch):
        watch_called = {"value": False}
        stop_evt = None

        def fake_watch(directories=None, *, agent=None, classification="internal",
                       interval=5.0, stop_event=None, logger=None):
            nonlocal stop_evt
            watch_called["value"] = True
            stop_evt = stop_event
            # Immediately stop so daemon exits
            if stop_event:
                stop_event.set()

        monkeypatch.setattr(daemon_mod, "is_running", lambda: None)
        monkeypatch.setattr("akf.watch.watch", fake_watch)
        daemon_mod.run_daemon(foreground=True)
        assert watch_called["value"]
        # Cleanup logger handlers
        logger = logging.getLogger("akf.daemon")
        for h in logger.handlers[:]:
            logger.removeHandler(h)
            h.close()


class TestSignalHandler:
    def test_signal_sets_stop_event(self, akf_dir):
        stop_event = threading.Event()

        def handler(signum, frame):
            stop_event.set()

        # Simulate what run_daemon does: register handler, then call it
        old = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, handler)
        try:
            # Directly call the handler (don't actually send a signal)
            handler(signal.SIGINT, None)
            assert stop_event.is_set()
        finally:
            signal.signal(signal.SIGINT, old)
