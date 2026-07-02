"""Zero-effort project setup for AKF.

`akf init` wires AKF into everything it can detect in a project, so
stamping happens by default instead of by discipline:

- ``.akf/config.json``       — project defaults (classification, agent)
- git post-commit hook       — stamps every commit via ``akf hook post-commit``
- ``.claude/settings.json``  — Claude Code PostToolUse hook that stamps
                               every file the agent writes or edits
- agent rules files          — AKF protocol stanza in CLAUDE.md, AGENTS.md,
                               .cursorrules, .windsurfrules,
                               .github/copilot-instructions.md

All setup is idempotent: stanzas live between marker comments and are
replaced in place; hooks are skipped when already installed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

STANZA_BEGIN = "<!-- akf:protocol:begin -->"
STANZA_END = "<!-- akf:protocol:end -->"

PROTOCOL_STANZA = f"""{STANZA_BEGIN}
## AKF trust protocol

Before building on an existing file, check it:

    akf check <file>

OK = fresh stamp with verified evidence — build on it, skip re-verification.
STALE / LOW / UNSTAMPED = verify before trusting.

After creating or modifying a file, stamp what you verified:

    akf stamp <file> --agent <your-id> --evidence "<what you verified, e.g. 42/42 tests passed>"

Only claim evidence you actually observed.
{STANZA_END}"""

# Rules files that get the protocol stanza, in priority order. The first
# group are updated when present; AGENTS.md is created if nothing exists.
RULES_FILES = [
    "CLAUDE.md",
    "AGENTS.md",
    ".cursorrules",
    ".windsurfrules",
    ".github/copilot-instructions.md",
]

GIT_HOOK_LINE = "akf hook post-commit"
# Provenance must never make noise or block a commit, even with a broken install.
GIT_HOOK_INVOCATION = f"{GIT_HOOK_LINE} >/dev/null 2>&1 || true"
CLAUDE_HOOK_COMMAND = "akf hook claude"

MCP_SNIPPET = json.dumps(
    {"mcpServers": {"akf": {"command": "python", "args": ["-m", "mcp_server_akf"]}}},
    indent=2,
)


def setup_config(root: Path, agent: Optional[str], classification: str) -> List[str]:
    """Write .akf/config.json, preserving existing keys."""
    akf_dir = root / ".akf"
    akf_dir.mkdir(exist_ok=True)
    config_path = akf_dir / "config.json"

    config = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
        except (json.JSONDecodeError, OSError):
            config = {}

    config.setdefault("version", "1.0")
    config["classification"] = classification
    config.setdefault("auto_embed", True)
    if agent:
        config["agent"] = agent

    config_path.write_text(json.dumps(config, indent=2) + "\n")
    return [f"config    {config_path.relative_to(root)}"]


def setup_git_hooks(root: Path) -> List[str]:
    """Install a post-commit hook that stamps every commit."""
    git_dir = root / ".git"
    if not git_dir.exists():
        return ["git       skipped (not a git repository)"]

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    hook = hooks_dir / "post-commit"

    if hook.exists():
        existing = hook.read_text()
        if GIT_HOOK_LINE in existing:
            return ["git       post-commit hook already installed"]
        # Append to an existing hook rather than clobbering it.
        hook.write_text(existing.rstrip("\n") + f"\n{GIT_HOOK_INVOCATION}\n")
    else:
        hook.write_text(f"#!/bin/sh\n{GIT_HOOK_INVOCATION}\n")
    hook.chmod(0o755)
    return [f"git       post-commit hook -> {GIT_HOOK_LINE}"]


def setup_claude(root: Path) -> List[str]:
    """Add a PostToolUse hook to .claude/settings.json that auto-stamps
    files written or edited by Claude Code."""
    claude_dir = root / ".claude"
    settings_path = claude_dir / "settings.json"

    settings = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
        except (json.JSONDecodeError, OSError):
            return [f"claude    skipped ({settings_path.relative_to(root)} is not valid JSON)"]

    hooks = settings.setdefault("hooks", {})
    post_tool_use = hooks.setdefault("PostToolUse", [])

    for entry in post_tool_use:
        for h in entry.get("hooks", []):
            if CLAUDE_HOOK_COMMAND in h.get("command", ""):
                return ["claude    PostToolUse hook already installed"]

    post_tool_use.append({
        "matcher": "Write|Edit",
        "hooks": [{"type": "command", "command": CLAUDE_HOOK_COMMAND}],
    })

    claude_dir.mkdir(exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    return [f"claude    PostToolUse auto-stamp hook -> {settings_path.relative_to(root)}"]


def _apply_stanza(path: Path) -> str:
    """Insert or refresh the protocol stanza in a rules file."""
    text = path.read_text() if path.exists() else ""

    if STANZA_BEGIN in text and STANZA_END in text:
        before = text.split(STANZA_BEGIN)[0]
        after = text.split(STANZA_END, 1)[1]
        updated = before + PROTOCOL_STANZA + after
        if updated == text:
            return "unchanged"
        path.write_text(updated)
        return "refreshed"

    prefix = text.rstrip("\n") + "\n\n" if text.strip() else ""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(prefix + PROTOCOL_STANZA + "\n")
    return "created" if not text else "added"


def setup_rules(root: Path) -> List[str]:
    """Add the AKF protocol stanza to agent rules files.

    Updates every rules file that already exists; if none exist, creates
    AGENTS.md (the cross-tool convention).
    """
    messages = []
    existing = [f for f in RULES_FILES if (root / f).exists()]
    targets = existing if existing else ["AGENTS.md"]

    for name in targets:
        action = _apply_stanza(root / name)
        messages.append(f"rules     {name} ({action})")
    return messages
