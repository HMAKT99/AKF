"""AKF auto-tracking -- activated by `akf install`.

Drops a .pth file into site-packages so every Python process auto-patches
LLM SDKs (OpenAI, Anthropic, Mistral, Google) at import time.
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

_installed = False
_lock = threading.Lock()


def activate():
    """Called from .pth file on interpreter startup. Must be fast and safe."""
    global _installed
    if _installed:
        return
    with _lock:
        if _installed:
            return
        _installed = True
        try:
            _hook_imports()
        except Exception:
            pass  # Never break the interpreter


def _hook_imports():
    """Install an import hook that patches LLM SDKs when they're imported."""
    sys.meta_path.insert(0, _AKFImportHook())


class _AKFImportHook:
    """Patches LLM SDK clients automatically when the SDK is first imported."""

    _SDK_MODULES = {"openai", "anthropic", "mistralai", "google.generativeai"}
    _patched: set = set()

    def find_module(self, name, path=None):
        if name in self._SDK_MODULES and name not in self._patched:
            return self
        return None

    def load_module(self, name):
        self._patched.add(name)
        __import__(name)
        module = sys.modules[name]
        try:
            _patch_sdk(name, module)
        except Exception:
            pass  # Never break user code
        return module


def _patch_sdk(name, module):
    """Monkey-patch SDK client classes to auto-record with AKF tracking."""
    from akf.tracking import _record

    if name == "openai":
        _patch_openai(module, _record)
    elif name == "anthropic":
        _patch_anthropic(module, _record)
    elif name == "mistralai":
        _patch_mistral(module, _record)
    elif name == "google.generativeai":
        _patch_google(module, _record)


def _patch_openai(module, record):
    """Patch OpenAI client.chat.completions.create()."""
    try:
        Completions = module.resources.chat.completions.Completions
    except AttributeError:
        return

    original_create = Completions.create

    def patched_create(self, *args, **kwargs):
        response = original_create(self, *args, **kwargs)
        try:
            model = getattr(response, "model", None) or kwargs.get("model", "unknown")
            usage = getattr(response, "usage", None)
            record(
                model=model,
                provider="openai",
                input_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
                output_tokens=getattr(usage, "completion_tokens", None) if usage else None,
            )
        except Exception:
            pass
        return response

    Completions.create = patched_create


def _patch_anthropic(module, record):
    """Patch Anthropic client.messages.create()."""
    try:
        Messages = module.resources.messages.Messages
    except AttributeError:
        return

    original_create = Messages.create

    def patched_create(self, *args, **kwargs):
        response = original_create(self, *args, **kwargs)
        try:
            model = getattr(response, "model", None) or kwargs.get("model", "unknown")
            usage = getattr(response, "usage", None)
            record(
                model=model,
                provider="anthropic",
                input_tokens=getattr(usage, "input_tokens", None) if usage else None,
                output_tokens=getattr(usage, "output_tokens", None) if usage else None,
            )
        except Exception:
            pass
        return response

    Messages.create = patched_create


def _patch_mistral(module, record):
    """Patch Mistral client.chat() or client.chat.complete()."""
    try:
        Client = module.MistralClient
    except AttributeError:
        return

    if hasattr(Client, "chat"):
        original_chat = Client.chat

        def patched_chat(self, *args, **kwargs):
            response = original_chat(self, *args, **kwargs)
            try:
                model = getattr(response, "model", None) or kwargs.get("model", "unknown")
                usage = getattr(response, "usage", None)
                record(
                    model=model,
                    provider="mistral",
                    input_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
                    output_tokens=getattr(usage, "completion_tokens", None) if usage else None,
                )
            except Exception:
                pass
            return response

        Client.chat = patched_chat


def _patch_google(module, record):
    """Patch Google GenerativeAI GenerativeModel.generate_content()."""
    try:
        GenModel = module.GenerativeModel
    except AttributeError:
        return

    original_generate = GenModel.generate_content

    def patched_generate(self, *args, **kwargs):
        response = original_generate(self, *args, **kwargs)
        try:
            model = getattr(self, "model_name", None) or "unknown"
            usage = getattr(response, "usage_metadata", None)
            record(
                model=model,
                provider="google",
                input_tokens=getattr(usage, "prompt_token_count", None) if usage else None,
                output_tokens=getattr(usage, "candidates_token_count", None) if usage else None,
            )
        except Exception:
            pass
        return response

    GenModel.generate_content = patched_generate


# ---------------------------------------------------------------------------
# Install / uninstall helpers (write/remove .pth file)
# ---------------------------------------------------------------------------

_PTH_FILENAME = "akf_auto.pth"
_PTH_CONTENT = "import akf._auto; akf._auto.activate()\n"


def _get_site_packages(user: bool = True) -> str:
    """Return the target site-packages directory."""
    import site

    if user:
        return site.getusersitepackages()
    else:
        paths = site.getsitepackages()
        return paths[0] if paths else site.getusersitepackages()


def install(user: bool = True) -> str:
    """Write the .pth file to site-packages. Returns the path written."""
    from pathlib import Path

    sp = _get_site_packages(user)
    sp_dir = Path(sp)
    sp_dir.mkdir(parents=True, exist_ok=True)
    pth_path = sp_dir / _PTH_FILENAME
    pth_path.write_text(_PTH_CONTENT)
    return str(pth_path)


def uninstall() -> str | None:
    """Remove the .pth file from site-packages. Returns path removed, or None."""
    import site
    from pathlib import Path

    # Check both user and system site-packages
    candidates = []
    try:
        candidates.append(site.getusersitepackages())
    except Exception:
        pass
    try:
        candidates.extend(site.getsitepackages())
    except Exception:
        pass

    for sp in candidates:
        pth_path = Path(sp) / _PTH_FILENAME
        if pth_path.exists():
            pth_path.unlink()
            return str(pth_path)
    return None


# ---------------------------------------------------------------------------
# Service management (install/uninstall background daemon)
# ---------------------------------------------------------------------------

_AKF_DIR = Path(sys.prefix).parent / ".akf"  # resolved lazily below
_LAUNCHD_LABEL = "com.akf.watcher"
_SYSTEMD_UNIT = "akf-watcher.service"


def _akf_dir() -> Path:
    return Path.home() / ".akf"


def _write_default_config(dirs: list[str] | None = None):
    """Write ~/.akf/watch.json if it doesn't exist."""
    import json
    cfg_path = _akf_dir() / "watch.json"
    if cfg_path.exists():
        return str(cfg_path)
    _akf_dir().mkdir(parents=True, exist_ok=True)
    config = {
        "directories": dirs or ["~/Downloads", "~/Desktop", "~/Documents"],
        "interval": 5.0,
        "classification": "internal",
        "agent": None,
    }
    cfg_path.write_text(json.dumps(config, indent=2) + "\n")
    return str(cfg_path)


def install_service(dirs: list[str] | None = None) -> str:
    """Install the AKF watcher as a system login service.

    Returns a description of what was installed.
    """
    _write_default_config(dirs)
    plat = sys.platform
    if plat == "darwin":
        return _install_launchd()
    elif plat == "win32":
        return _install_windows_startup()
    else:
        return _install_linux()


def uninstall_service() -> str | None:
    """Remove the AKF watcher service. Returns description or None."""
    from .daemon import stop_daemon
    stop_daemon()

    plat = sys.platform
    if plat == "darwin":
        return _uninstall_launchd()
    elif plat == "win32":
        return _uninstall_windows_startup()
    else:
        return _uninstall_linux()


def service_status() -> dict:
    """Return daemon/service status info."""
    from .daemon import is_running
    pid = is_running()
    info = {"running": pid is not None, "pid": pid, "installed": False, "service_file": None}

    plat = sys.platform
    if plat == "darwin":
        plist = Path.home() / "Library" / "LaunchAgents" / f"{_LAUNCHD_LABEL}.plist"
        if plist.exists():
            info["installed"] = True
            info["service_file"] = str(plist)
    elif plat == "win32":
        vbs = _akf_dir() / "akf-watcher.vbs"
        startup = _windows_startup_dir() / "akf-watcher.vbs"
        if startup.exists() or vbs.exists():
            info["installed"] = True
            info["service_file"] = str(startup)
    else:
        unit = Path.home() / ".config" / "systemd" / "user" / _SYSTEMD_UNIT
        desktop = (Path.home() / ".config" / "autostart" / "akf-watcher.desktop")
        if unit.exists():
            info["installed"] = True
            info["service_file"] = str(unit)
        elif desktop.exists():
            info["installed"] = True
            info["service_file"] = str(desktop)

    return info


# --- macOS (launchd) ---

def _install_launchd() -> str:
    import subprocess
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_dir.mkdir(parents=True, exist_ok=True)
    plist_path = plist_dir / f"{_LAUNCHD_LABEL}.plist"

    python = sys.executable
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{_LAUNCHD_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python}</string>
        <string>-m</string>
        <string>akf.daemon</string>
        <string>--foreground</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>{_akf_dir() / "watch-stdout.log"}</string>
    <key>StandardErrorPath</key>
    <string>{_akf_dir() / "watch-stderr.log"}</string>
</dict>
</plist>
"""
    plist_path.write_text(plist_content)
    subprocess.run(["launchctl", "load", str(plist_path)],
                   capture_output=True)
    return f"launchd service: {plist_path}"


def _uninstall_launchd() -> str | None:
    import subprocess
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"{_LAUNCHD_LABEL}.plist"
    if not plist_path.exists():
        return None
    subprocess.run(["launchctl", "unload", str(plist_path)],
                   capture_output=True)
    plist_path.unlink(missing_ok=True)
    return f"Removed {plist_path}"


# --- Linux (systemd user unit, fallback to XDG autostart) ---

def _install_linux() -> str:
    import shutil
    python = sys.executable

    # Try systemd first
    if shutil.which("systemctl"):
        return _install_systemd(python)
    return _install_xdg_autostart(python)


def _install_systemd(python: str) -> str:
    import subprocess
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    unit_dir.mkdir(parents=True, exist_ok=True)
    unit_path = unit_dir / _SYSTEMD_UNIT

    unit_content = f"""[Unit]
Description=AKF File Watcher
After=default.target

[Service]
ExecStart={python} -m akf.daemon --foreground
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
"""
    unit_path.write_text(unit_content)
    subprocess.run(["systemctl", "--user", "daemon-reload"],
                   capture_output=True)
    subprocess.run(["systemctl", "--user", "enable", _SYSTEMD_UNIT],
                   capture_output=True)
    subprocess.run(["systemctl", "--user", "start", _SYSTEMD_UNIT],
                   capture_output=True)
    return f"systemd user service: {unit_path}"


def _install_xdg_autostart(python: str) -> str:
    autostart_dir = Path.home() / ".config" / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)
    desktop_path = autostart_dir / "akf-watcher.desktop"

    desktop_content = f"""[Desktop Entry]
Type=Application
Name=AKF File Watcher
Exec={python} -m akf.daemon --foreground
Hidden=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
"""
    desktop_path.write_text(desktop_content)
    return f"XDG autostart: {desktop_path}"


def _uninstall_linux() -> str | None:
    import shutil, subprocess

    # Try systemd first
    unit_path = Path.home() / ".config" / "systemd" / "user" / _SYSTEMD_UNIT
    if unit_path.exists():
        if shutil.which("systemctl"):
            subprocess.run(["systemctl", "--user", "stop", _SYSTEMD_UNIT],
                           capture_output=True)
            subprocess.run(["systemctl", "--user", "disable", _SYSTEMD_UNIT],
                           capture_output=True)
        unit_path.unlink(missing_ok=True)
        return f"Removed {unit_path}"

    # XDG autostart fallback
    desktop_path = Path.home() / ".config" / "autostart" / "akf-watcher.desktop"
    if desktop_path.exists():
        desktop_path.unlink(missing_ok=True)
        return f"Removed {desktop_path}"

    return None


# --- Windows (VBS startup script) ---

def _windows_startup_dir() -> Path:
    appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _install_windows_startup() -> str:
    import shutil
    python = sys.executable
    vbs_path = _akf_dir() / "akf-watcher.vbs"
    _akf_dir().mkdir(parents=True, exist_ok=True)

    # VBS uses doubled quotes for escaping inside strings
    vbs_content = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        f'WshShell.Run """"{python}"""" -m akf.daemon --foreground", 0, False\n'
    )
    vbs_path.write_text(vbs_content)

    startup_dir = _windows_startup_dir()
    startup_dir.mkdir(parents=True, exist_ok=True)
    startup_path = startup_dir / "akf-watcher.vbs"
    shutil.copy2(str(vbs_path), str(startup_path))
    return f"Windows startup: {startup_path}"


def _uninstall_windows_startup() -> str | None:
    startup_path = _windows_startup_dir() / "akf-watcher.vbs"
    vbs_path = _akf_dir() / "akf-watcher.vbs"

    removed = []
    for p in [startup_path, vbs_path]:
        if p.exists():
            p.unlink(missing_ok=True)
            removed.append(str(p))

    return f"Removed {', '.join(removed)}" if removed else None
