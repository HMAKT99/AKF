"""Tests for AKF auto-tracking install/uninstall and service management."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from akf import _auto as auto_mod


@pytest.fixture
def fake_site_packages(tmp_path, monkeypatch):
    """Redirect site-packages to tmp_path."""
    sp = tmp_path / "site-packages"
    sp.mkdir()
    monkeypatch.setattr(auto_mod, "_get_site_packages", lambda user=True: str(sp))
    return sp


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Redirect Path.home() and _akf_dir() to tmp_path."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: home))
    monkeypatch.setattr(auto_mod, "_akf_dir", lambda: home / ".akf")
    return home


# ---------------------------------------------------------------------------
# PTH install / uninstall
# ---------------------------------------------------------------------------

class TestPthInstall:
    def test_install_creates_pth(self, fake_site_packages):
        auto_mod.install(user=True)
        pth = fake_site_packages / auto_mod._PTH_FILENAME
        assert pth.exists()

    def test_pth_content(self, fake_site_packages):
        auto_mod.install(user=True)
        pth = fake_site_packages / auto_mod._PTH_FILENAME
        assert "akf._auto" in pth.read_text()
        assert "activate()" in pth.read_text()

    def test_install_returns_path(self, fake_site_packages):
        result = auto_mod.install(user=True)
        assert auto_mod._PTH_FILENAME in result

    def test_uninstall_removes_pth(self, fake_site_packages, monkeypatch):
        # Install first
        auto_mod.install(user=True)
        pth = fake_site_packages / auto_mod._PTH_FILENAME
        assert pth.exists()

        # Monkeypatch site functions to point to our fake dir
        import site
        monkeypatch.setattr(site, "getusersitepackages", lambda: str(fake_site_packages))
        monkeypatch.setattr(site, "getsitepackages", lambda: [str(fake_site_packages)])

        result = auto_mod.uninstall()
        assert result is not None
        assert not pth.exists()

    def test_uninstall_no_file(self, monkeypatch, tmp_path):
        import site
        sp = tmp_path / "empty-sp"
        sp.mkdir()
        monkeypatch.setattr(site, "getusersitepackages", lambda: str(sp))
        monkeypatch.setattr(site, "getsitepackages", lambda: [str(sp)])
        result = auto_mod.uninstall()
        assert result is None

    def test_roundtrip(self, fake_site_packages, monkeypatch):
        import site
        monkeypatch.setattr(site, "getusersitepackages", lambda: str(fake_site_packages))
        monkeypatch.setattr(site, "getsitepackages", lambda: [str(fake_site_packages)])

        auto_mod.install(user=True)
        assert (fake_site_packages / auto_mod._PTH_FILENAME).exists()
        auto_mod.uninstall()
        assert not (fake_site_packages / auto_mod._PTH_FILENAME).exists()


# ---------------------------------------------------------------------------
# macOS service
# ---------------------------------------------------------------------------

class TestMacOSService:
    def test_install_plist(self, fake_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "darwin")
        monkeypatch.setattr("subprocess.run", MagicMock())

        result = auto_mod.install_service()
        plist = fake_home / "Library" / "LaunchAgents" / f"{auto_mod._LAUNCHD_LABEL}.plist"
        assert plist.exists()
        content = plist.read_text()
        assert auto_mod._LAUNCHD_LABEL in content
        assert "--foreground" in content
        assert "RunAtLoad" in content

    def test_uninstall(self, fake_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "darwin")
        monkeypatch.setattr("subprocess.run", MagicMock())
        monkeypatch.setattr("akf.daemon.stop_daemon", lambda: False)

        # Install first
        auto_mod.install_service()
        plist = fake_home / "Library" / "LaunchAgents" / f"{auto_mod._LAUNCHD_LABEL}.plist"
        assert plist.exists()

        result = auto_mod.uninstall_service()
        assert not plist.exists()


# ---------------------------------------------------------------------------
# Linux service
# ---------------------------------------------------------------------------

class TestLinuxService:
    def test_install_systemd(self, fake_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/systemctl" if x == "systemctl" else None)
        monkeypatch.setattr("subprocess.run", MagicMock())

        result = auto_mod.install_service()
        unit = fake_home / ".config" / "systemd" / "user" / auto_mod._SYSTEMD_UNIT
        assert unit.exists()
        content = unit.read_text()
        assert "akf.daemon" in content
        assert "--foreground" in content

    def test_install_xdg_fallback(self, fake_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setattr("shutil.which", lambda x: None)

        result = auto_mod.install_service()
        desktop = fake_home / ".config" / "autostart" / "akf-watcher.desktop"
        assert desktop.exists()
        content = desktop.read_text()
        assert "akf.daemon" in content

    def test_uninstall_systemd(self, fake_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setattr("shutil.which", lambda x: "/usr/bin/systemctl" if x == "systemctl" else None)
        monkeypatch.setattr("subprocess.run", MagicMock())
        monkeypatch.setattr("akf.daemon.stop_daemon", lambda: False)

        auto_mod.install_service()
        unit = fake_home / ".config" / "systemd" / "user" / auto_mod._SYSTEMD_UNIT
        assert unit.exists()

        auto_mod.uninstall_service()
        assert not unit.exists()


# ---------------------------------------------------------------------------
# Windows service
# ---------------------------------------------------------------------------

class TestWindowsService:
    def test_install_vbs(self, fake_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        startup = fake_home / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        monkeypatch.setattr(auto_mod, "_windows_startup_dir", lambda: startup)

        result = auto_mod.install_service()
        vbs = (fake_home / ".akf") / "akf-watcher.vbs"
        assert vbs.exists()
        content = vbs.read_text()
        assert "WScript.Shell" in content
        assert "akf.daemon" in content

    def test_uninstall_vbs(self, fake_home, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")
        startup = fake_home / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        monkeypatch.setattr(auto_mod, "_windows_startup_dir", lambda: startup)
        monkeypatch.setattr("akf.daemon.stop_daemon", lambda: False)

        auto_mod.install_service()
        auto_mod.uninstall_service()
        vbs = (fake_home / ".akf") / "akf-watcher.vbs"
        assert not vbs.exists()


# ---------------------------------------------------------------------------
# service_status
# ---------------------------------------------------------------------------

class TestServiceStatus:
    def test_not_running(self, fake_home, monkeypatch):
        monkeypatch.setattr("akf.daemon.is_running", lambda: None)
        monkeypatch.setattr(sys, "platform", "darwin")
        status = auto_mod.service_status()
        assert status["running"] is False
        assert status["installed"] is False

    def test_running_installed(self, fake_home, monkeypatch):
        monkeypatch.setattr("akf.daemon.is_running", lambda: 1234)
        monkeypatch.setattr(sys, "platform", "darwin")
        # Create plist
        plist_dir = fake_home / "Library" / "LaunchAgents"
        plist_dir.mkdir(parents=True)
        (plist_dir / f"{auto_mod._LAUNCHD_LABEL}.plist").write_text("<plist/>")

        status = auto_mod.service_status()
        assert status["running"] is True
        assert status["pid"] == 1234
        assert status["installed"] is True


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class TestWriteDefaultConfig:
    def test_write_default(self, fake_home):
        auto_mod._write_default_config()
        cfg = fake_home / ".akf" / "watch.json"
        assert cfg.exists()
        data = json.loads(cfg.read_text())
        assert "~/Downloads" in data["directories"]

    def test_custom_dirs(self, fake_home):
        auto_mod._write_default_config(dirs=["/my/dir"])
        cfg = fake_home / ".akf" / "watch.json"
        data = json.loads(cfg.read_text())
        assert data["directories"] == ["/my/dir"]

    def test_no_overwrite(self, fake_home):
        akf = fake_home / ".akf"
        akf.mkdir(parents=True)
        cfg = akf / "watch.json"
        cfg.write_text('{"custom": true}')
        auto_mod._write_default_config()
        # Should not have been overwritten
        data = json.loads(cfg.read_text())
        assert data == {"custom": True}
