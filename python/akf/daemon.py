"""AKF background daemon — runs the file watcher as a system service.

Invoked as ``python -m akf.daemon`` by launchd/systemd/startup scripts.
Use ``akf watch --start`` / ``akf watch --stop`` to control.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

AKF_DIR = Path.home() / ".akf"
PID_FILE = AKF_DIR / "watch.pid"
LOG_FILE = AKF_DIR / "watch.log"
CONFIG_FILE = AKF_DIR / "watch.json"

DEFAULT_CONFIG = {
    "directories": ["~/Downloads", "~/Desktop", "~/Documents"],
    "interval": 5.0,
    "classification": "internal",
    "agent": None,
    "smart": True,
}


def load_config() -> dict:
    """Load watch config from ~/.akf/watch.json, falling back to defaults."""
    config = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                user = json.load(f)
            config.update(user)
        except (json.JSONDecodeError, OSError):
            pass
    return config


def is_running() -> int | None:
    """Check if a daemon is running. Returns PID if alive, None otherwise."""
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None
    # Check if process is alive
    try:
        os.kill(pid, 0)
        return pid
    except (OSError, ProcessLookupError):
        # Stale PID file
        _remove_pid()
        return None


def write_pid():
    """Write current PID to the PID file."""
    AKF_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))


def _remove_pid():
    """Remove the PID file if it exists."""
    try:
        PID_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def setup_logging() -> logging.Logger:
    """Set up rotating file logger for the daemon."""
    AKF_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("akf.daemon")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(
            str(LOG_FILE), maxBytes=2 * 1024 * 1024, backupCount=1
        )
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(handler)
    return logger


def daemonize():
    """Double-fork to detach from terminal (Unix only)."""
    if sys.platform == "win32":
        return

    # First fork
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    os.setsid()

    # Second fork
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # Redirect stdin/stdout/stderr to /dev/null
    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, 0)
    os.dup2(devnull, 1)
    os.dup2(devnull, 2)
    os.close(devnull)


def stop_daemon() -> bool:
    """Send SIGTERM to a running daemon. Returns True if stopped."""
    pid = is_running()
    if pid is None:
        return False
    try:
        if sys.platform == "win32":
            import subprocess
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           capture_output=True)
        else:
            os.kill(pid, signal.SIGTERM)
        # Wait briefly for it to exit
        for _ in range(20):
            try:
                os.kill(pid, 0)
                time.sleep(0.1)
            except (OSError, ProcessLookupError):
                break
        _remove_pid()
        return True
    except (OSError, ProcessLookupError):
        _remove_pid()
        return True


def run_daemon(foreground: bool = False):
    """Main daemon entry point — load config, start watcher loop."""
    existing = is_running()
    if existing:
        print(f"Daemon already running (PID {existing})", file=sys.stderr)
        sys.exit(1)

    if not foreground:
        daemonize()

    logger = setup_logging()
    logger.info("AKF watcher daemon starting (PID %d)", os.getpid())

    write_pid()
    stop_event = threading.Event()

    def _handle_signal(signum, frame):
        logger.info("Received signal %d, shutting down", signum)
        stop_event.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    config = load_config()
    logger.info("Config: %s", json.dumps(config))

    try:
        from .watch import watch
        watch(
            directories=config.get("directories"),
            agent=config.get("agent"),
            classification=config.get("classification", "internal"),
            interval=config.get("interval", 5.0),
            stop_event=stop_event,
            logger=logger,
            config=config,
            use_events=config.get("events", False),
        )
    except Exception:
        logger.exception("Daemon crashed")
    finally:
        logger.info("Daemon stopped")
        _remove_pid()


def main():
    parser = argparse.ArgumentParser(description="AKF watcher daemon")
    parser.add_argument(
        "--foreground", action="store_true",
        help="Run in foreground (for service managers)",
    )
    args = parser.parse_args()
    run_daemon(foreground=args.foreground)


if __name__ == "__main__":
    main()
