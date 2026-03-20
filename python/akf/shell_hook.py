"""Shell hook generator for auto-stamping AI CLI tool output.

Usage::

    # Add to ~/.zshrc or ~/.bashrc:
    eval "$(akf shell-hook)"

    # Now any files created/modified by AI CLI tools get auto-stamped:
    claude "Write a Python script" > script.py   # → auto-stamped
    chatgpt "Summarize this doc" > summary.md    # → auto-stamped
    aider --message "Add tests"                  # → modified files stamped

The hook works by:
1. Before each command: if the command invokes a known AI tool,
   snapshot file mtimes in watched directories
2. After the command: find new/modified files and stamp them
3. Before upload commands (gws, box, m365, dbxcli, rclone): stamp
   the file *before* the upload so trust metadata travels with it
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

# AI CLI tools we recognize
AI_CLI_TOOLS = [
    "claude",
    "chatgpt",
    "sgpt",
    "aider",
    "ollama",
    "llm",
    "gh copilot",
    "copilot",
    "fabric",
    "mods",
    "tgpt",
    "manus",
]

# Content platform CLIs that upload files — stamp *before* upload
UPLOAD_CLI_TOOLS = {
    "gws":          {"cmds": ["upload", "cp"],          "desc": "Google Workspace CLI"},
    "box":          {"cmds": ["files:upload"],           "desc": "Box CLI"},
    "m365":         {"cmds": ["spo file add"],           "desc": "Microsoft 365 CLI"},
    "dbxcli":       {"cmds": ["put"],                    "desc": "Dropbox CLI"},
    "obsidian-cli": {"cmds": ["import", "add"],          "desc": "Obsidian CLI"},
    "rclone":       {"cmds": ["copy", "sync", "move"],   "desc": "Rclone (multi-cloud)"},
}

# File extensions to stamp (mirrors watch.py SUPPORTED_EXTENSIONS)
WATCHED_EXTENSIONS = (
    "docx", "xlsx", "pptx", "pdf", "html", "htm",
    "json", "md", "markdown", "png", "jpg", "jpeg",
    "py", "js", "ts", "eml", "csv", "txt",
)


def _tool_pattern() -> str:
    """Build a shell regex pattern matching AI CLI tool invocations."""
    # Escape for shell regex; handle multi-word tools
    escaped = []
    for tool in AI_CLI_TOOLS:
        escaped.append(tool.replace(" ", "[[:space:]]"))
    return "|".join(escaped)


def _upload_tool_pattern() -> str:
    """Build a shell regex pattern matching upload CLI invocations.

    Returns patterns like: ``gws[[:space:]]+(upload|cp)|box[[:space:]]+files:upload|...``
    """
    parts = []
    for tool, info in UPLOAD_CLI_TOOLS.items():
        cmds = "|".join(
            cmd.replace(" ", "[[:space:]]+") for cmd in info["cmds"]
        )
        parts.append(f"{tool}[[:space:]]+({cmds})")
    return "|".join(parts)


def _upload_extensions_check() -> str:
    """Build a shell case pattern for watched file extensions."""
    return "|".join(f"*.{ext}" for ext in WATCHED_EXTENSIONS)


def generate_zsh_hook(include_uploads: bool = True) -> str:
    """Generate zsh shell hook code."""
    tool_pattern = _tool_pattern()
    upload_pattern = _upload_tool_pattern() if include_uploads else ""
    ext_case = _upload_extensions_check()

    upload_block = ""
    if include_uploads:
        upload_block = textwrap.dedent(f'''\

            # ── Pre-upload stamping ──────────────────────────────
            _akf_extract_upload_path() {{
                # Find the first arg that is an existing file with a watched extension
                for arg in "$@"; do
                    [[ "$arg" == -* ]] && continue
                    [[ -f "$arg" ]] || continue
                    case "$arg" in
                        {ext_case}) echo "$arg"; return 0 ;;
                    esac
                done
                return 1
            }}

            _akf_pre_upload() {{
                local cmd="$1"
                # Check if command is a content platform upload
                if [[ "$cmd" =~ ^[[:space:]]*(sudo[[:space:]]+)?({upload_pattern}) ]]; then
                    local file
                    # Split cmd into words and find the file arg
                    local -a words=($(echo "$cmd"))
                    file=$(_akf_extract_upload_path "${{words[@]}}") || return 0

                    local log_dir="$HOME/.akf"
                    local log_file="$log_dir/upload.log"
                    mkdir -p "$log_dir"

                    local tool="${{words[1]}}"
                    local ts
                    ts=$(date -u +"%Y-%m-%dT%H:%M:%S")

                    # Stamp the file before upload
                    if akf stamp "$file" --agent shell-hook --evidence "pre-upload stamp" 2>/dev/null; then
                        echo "\\033[0;36m[akf]\\033[0m Pre-upload stamped: $file"
                        echo "$ts $tool upload $file stamped" >> "$log_file"
                    else
                        echo "\\033[0;33m[akf]\\033[0m Pre-upload stamp skipped: $file (already stamped or error)"
                        echo "$ts $tool upload $file already-stamped" >> "$log_file"
                    fi
                fi
            }}
            # ── End pre-upload stamping ──────────────────────────
        ''')

    find_ext_pattern = " -o ".join(
        f'-name "*.{e}"' for e in WATCHED_EXTENSIONS
    )

    preexec_upload_call = ""
    if include_uploads:
        preexec_upload_call = (
            '\n\n            # Check for content platform upload commands (pre-stamp)'
            '\n            _akf_pre_upload "$cmd"'
        )

    return textwrap.dedent(f'''\
        # ── AKF Shell Hook (zsh) ──────────────────────────────────
        # Auto-stamps files created/modified by AI CLI tools.
        # Generated by: akf shell-hook

        _akf_marker_file="/tmp/.akf_shell_marker_$$"

        _akf_watched_dirs() {{
            local dirs=()
            if command -v akf >/dev/null 2>&1; then
                # Try to read dirs from watch config
                local cfg="$HOME/.akf/watch.json"
                if [[ -f "$cfg" ]]; then
                    dirs=($(python3 -c "
import json, os
try:
    cfg = json.load(open('$cfg'))
    for d in cfg.get('directories', []):
        print(os.path.expanduser(d))
except: pass
" 2>/dev/null))
                fi
            fi
            # Fallback to defaults
            if [[ ${{#dirs[@]}} -eq 0 ]]; then
                dirs=("$HOME/Downloads" "$HOME/Desktop" "$HOME/Documents")
            fi
            # Filter to existing directories
            local existing=()
            for d in "${{dirs[@]}}"; do
                [[ -d "$d" ]] && existing+=("$d")
            done
            echo "${{existing[@]}}"
        }}
{upload_block}
        _akf_preexec() {{
            local cmd="$1"
            # Check if command invokes a known AI CLI tool
            if [[ "$cmd" =~ ^[[:space:]]*(sudo[[:space:]]+)?({tool_pattern}) ]]; then
                export _AKF_AI_CMD="$cmd"
                touch "$_akf_marker_file"
            fi{preexec_upload_call}
        }}

        _akf_precmd() {{
            # Only run if an AI command was tracked
            [[ -z "$_AKF_AI_CMD" ]] && return
            [[ ! -f "$_akf_marker_file" ]] && return

            local cmd="$_AKF_AI_CMD"
            unset _AKF_AI_CMD

            # Find files newer than our marker in watched directories
            local dirs
            dirs=($(_akf_watched_dirs))

            for dir in "${{dirs[@]}}"; do
                [[ -d "$dir" ]] || continue
                find "$dir" -maxdepth 3 -newer "$_akf_marker_file" \\
                    -type f \\( {find_ext_pattern} \\) \\
                    ! -name ".*" ! -name "*.akf" 2>/dev/null | while IFS= read -r f; do
                    akf stamp "$f" --ai 2>/dev/null && \\
                        echo "\\033[0;36m[akf]\\033[0m Stamped: $f"
                done
            done

            # Also stamp files in current directory that changed
            find . -maxdepth 1 -newer "$_akf_marker_file" \\
                -type f \\( {find_ext_pattern} \\) \\
                ! -name ".*" ! -name "*.akf" 2>/dev/null | while IFS= read -r f; do
                akf stamp "$f" --ai 2>/dev/null && \\
                    echo "\\033[0;36m[akf]\\033[0m Stamped: $f"
            done

            rm -f "$_akf_marker_file"
        }}

        # Register hooks
        autoload -Uz add-zsh-hook 2>/dev/null
        if (( $+functions[add-zsh-hook] )); then
            add-zsh-hook preexec _akf_preexec
            add-zsh-hook precmd _akf_precmd
        fi

        # Cleanup on shell exit
        _akf_cleanup() {{
            rm -f "$_akf_marker_file"
        }}
        add-zsh-hook zshexit _akf_cleanup 2>/dev/null
        # ── End AKF Shell Hook ────────────────────────────────────
    ''')


def generate_bash_hook(include_uploads: bool = True) -> str:
    """Generate bash shell hook code."""
    tool_pattern = _tool_pattern()
    upload_pattern = _upload_tool_pattern() if include_uploads else ""
    ext_case = _upload_extensions_check()

    upload_block = ""
    if include_uploads:
        upload_block = textwrap.dedent(f'''\

            # ── Pre-upload stamping ──────────────────────────────
            _akf_extract_upload_path() {{
                for arg in "$@"; do
                    [[ "$arg" == -* ]] && continue
                    [[ -f "$arg" ]] || continue
                    case "$arg" in
                        {ext_case}) echo "$arg"; return 0 ;;
                    esac
                done
                return 1
            }}

            _akf_pre_upload() {{
                local cmd="$1"
                if [[ "$cmd" =~ ^[[:space:]]*(sudo[[:space:]]+)?({upload_pattern}) ]]; then
                    local file
                    read -ra words <<< "$cmd"
                    file=$(_akf_extract_upload_path "${{words[@]}}") || return 0

                    local log_dir="$HOME/.akf"
                    local log_file="$log_dir/upload.log"
                    mkdir -p "$log_dir"

                    local tool="${{words[0]}}"
                    local ts
                    ts=$(date -u +"%Y-%m-%dT%H:%M:%S")

                    if akf stamp "$file" --agent shell-hook --evidence "pre-upload stamp" 2>/dev/null; then
                        echo -e "\\033[0;36m[akf]\\033[0m Pre-upload stamped: $file"
                        echo "$ts $tool upload $file stamped" >> "$log_file"
                    else
                        echo -e "\\033[0;33m[akf]\\033[0m Pre-upload stamp skipped: $file (already stamped or error)"
                        echo "$ts $tool upload $file already-stamped" >> "$log_file"
                    fi
                fi
            }}
            # ── End pre-upload stamping ──────────────────────────
        ''')

    find_ext_pattern = " -o ".join(
        f'-name "*.{e}"' for e in WATCHED_EXTENSIONS
    )

    preexec_upload_call = ""
    if include_uploads:
        preexec_upload_call = (
            '\n\n            # Check for content platform upload commands (pre-stamp)'
            '\n            _akf_pre_upload "$cmd"'
        )

    return textwrap.dedent(f'''\
        # ── AKF Shell Hook (bash) ─────────────────────────────────
        # Auto-stamps files created/modified by AI CLI tools.
        # Generated by: akf shell-hook

        _akf_marker_file="/tmp/.akf_shell_marker_$$"

        _akf_watched_dirs() {{
            local cfg="$HOME/.akf/watch.json"
            if [[ -f "$cfg" ]] && command -v python3 >/dev/null 2>&1; then
                python3 -c "
import json, os
try:
    cfg = json.load(open('$cfg'))
    for d in cfg.get('directories', []):
        p = os.path.expanduser(d)
        if os.path.isdir(p): print(p)
except: pass
" 2>/dev/null
            else
                for d in "$HOME/Downloads" "$HOME/Desktop" "$HOME/Documents"; do
                    [[ -d "$d" ]] && echo "$d"
                done
            fi
        }}
{upload_block}
        _akf_preexec_handler() {{
            local cmd="$1"
            if [[ "$cmd" =~ ^[[:space:]]*(sudo[[:space:]]+)?({tool_pattern}) ]]; then
                export _AKF_AI_CMD="$cmd"
                touch "$_akf_marker_file"
            fi{preexec_upload_call}
        }}

        _akf_precmd_handler() {{
            [[ -z "$_AKF_AI_CMD" ]] && return
            [[ ! -f "$_akf_marker_file" ]] && return

            unset _AKF_AI_CMD

            while IFS= read -r dir; do
                [[ -d "$dir" ]] || continue
                find "$dir" -maxdepth 3 -newer "$_akf_marker_file" \\
                    -type f \\( {find_ext_pattern} \\) \\
                    ! -name ".*" ! -name "*.akf" 2>/dev/null | while IFS= read -r f; do
                    akf stamp "$f" --ai 2>/dev/null && \\
                        echo -e "\\033[0;36m[akf]\\033[0m Stamped: $f"
                done
            done < <(_akf_watched_dirs)

            # Current directory
            find . -maxdepth 1 -newer "$_akf_marker_file" \\
                -type f \\( {find_ext_pattern} \\) \\
                ! -name ".*" ! -name "*.akf" 2>/dev/null | while IFS= read -r f; do
                akf stamp "$f" --ai 2>/dev/null && \\
                    echo -e "\\033[0;36m[akf]\\033[0m Stamped: $f"
            done

            rm -f "$_akf_marker_file"
        }}

        # Use bash-preexec if available, otherwise use DEBUG trap
        if [[ -n "${{bash_preexec_imported:-}}" ]] || \\
           declare -F __bp_preexec_invoke_exec >/dev/null 2>&1; then
            preexec_functions+=(_akf_preexec_handler)
            precmd_functions+=(_akf_precmd_handler)
        else
            trap '_akf_preexec_handler "$BASH_COMMAND"' DEBUG
            PROMPT_COMMAND="_akf_precmd_handler;${{PROMPT_COMMAND:-}}"
        fi

        # Cleanup
        trap 'rm -f "$_akf_marker_file"' EXIT
        # ── End AKF Shell Hook ────────────────────────────────────
    ''')


def generate_shell_hook(
    shell: str = "auto",
    include_uploads: bool = True,
) -> str:
    """Generate shell hook code for the detected or specified shell.

    Args:
        shell: "zsh", "bash", or "auto" (detect from $SHELL).
        include_uploads: Include content platform upload hooks.

    Returns:
        Shell code string to be eval'd.
    """
    if shell == "auto":
        user_shell = os.environ.get("SHELL", "")
        if "zsh" in user_shell:
            shell = "zsh"
        else:
            shell = "bash"

    if shell == "zsh":
        return generate_zsh_hook(include_uploads=include_uploads)
    return generate_bash_hook(include_uploads=include_uploads)
