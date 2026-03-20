"""Tests for shell hook generation."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from akf.cli import main
from akf.shell_hook import (
    AI_CLI_TOOLS,
    UPLOAD_CLI_TOOLS,
    WATCHED_EXTENSIONS,
    _upload_tool_pattern,
    generate_bash_hook,
    generate_shell_hook,
    generate_zsh_hook,
)


class TestZshHook:
    def test_generates_valid_code(self):
        code = generate_zsh_hook()
        assert "AKF Shell Hook" in code
        assert "_akf_preexec" in code
        assert "_akf_precmd" in code
        assert "add-zsh-hook" in code

    def test_contains_ai_tools(self):
        code = generate_zsh_hook()
        assert "claude" in code
        assert "chatgpt" in code
        assert "aider" in code

    def test_contains_extensions(self):
        code = generate_zsh_hook()
        assert "*.py" in code
        assert "*.md" in code
        assert "*.txt" in code

    def test_contains_cleanup(self):
        code = generate_zsh_hook()
        assert "_akf_cleanup" in code
        assert "zshexit" in code

    def test_stamps_command(self):
        code = generate_zsh_hook()
        assert "akf stamp" in code


class TestBashHook:
    def test_generates_valid_code(self):
        code = generate_bash_hook()
        assert "AKF Shell Hook" in code
        assert "_akf_preexec_handler" in code
        assert "_akf_precmd_handler" in code

    def test_contains_ai_tools(self):
        code = generate_bash_hook()
        assert "claude" in code
        assert "chatgpt" in code

    def test_has_fallback_mechanism(self):
        code = generate_bash_hook()
        # Should support both bash-preexec and DEBUG trap fallback
        assert "DEBUG" in code
        assert "PROMPT_COMMAND" in code

    def test_cleanup_on_exit(self):
        code = generate_bash_hook()
        assert "trap" in code
        assert "EXIT" in code


class TestShellHookAutoDetect:
    def test_auto_detects_zsh(self):
        with patch.dict("os.environ", {"SHELL": "/bin/zsh"}):
            code = generate_shell_hook("auto")
            assert "add-zsh-hook" in code

    def test_auto_detects_bash(self):
        with patch.dict("os.environ", {"SHELL": "/bin/bash"}):
            code = generate_shell_hook("auto")
            assert "PROMPT_COMMAND" in code

    def test_explicit_zsh(self):
        code = generate_shell_hook("zsh")
        assert "add-zsh-hook" in code

    def test_explicit_bash(self):
        code = generate_shell_hook("bash")
        assert "PROMPT_COMMAND" in code

    def test_unknown_shell_defaults_to_bash(self):
        with patch.dict("os.environ", {"SHELL": "/bin/fish"}):
            code = generate_shell_hook("auto")
            assert "PROMPT_COMMAND" in code


class TestAIToolsList:
    def test_common_tools_present(self):
        assert "claude" in AI_CLI_TOOLS
        assert "chatgpt" in AI_CLI_TOOLS
        assert "aider" in AI_CLI_TOOLS
        assert "ollama" in AI_CLI_TOOLS

    def test_extensions_complete(self):
        assert "py" in WATCHED_EXTENSIONS
        assert "md" in WATCHED_EXTENSIONS
        assert "json" in WATCHED_EXTENSIONS
        assert "txt" in WATCHED_EXTENSIONS


# ── Upload Hook Tests ──────────────────────────────────────


class TestUploadCLITools:
    def test_all_tools_present(self):
        assert "gws" in UPLOAD_CLI_TOOLS
        assert "box" in UPLOAD_CLI_TOOLS
        assert "m365" in UPLOAD_CLI_TOOLS
        assert "dbxcli" in UPLOAD_CLI_TOOLS
        assert "obsidian-cli" in UPLOAD_CLI_TOOLS
        assert "rclone" in UPLOAD_CLI_TOOLS

    def test_tools_have_cmds_and_desc(self):
        for tool, info in UPLOAD_CLI_TOOLS.items():
            assert "cmds" in info, f"{tool} missing 'cmds'"
            assert "desc" in info, f"{tool} missing 'desc'"
            assert len(info["cmds"]) > 0, f"{tool} has empty cmds"

    def test_gws_commands(self):
        assert "upload" in UPLOAD_CLI_TOOLS["gws"]["cmds"]
        assert "cp" in UPLOAD_CLI_TOOLS["gws"]["cmds"]

    def test_rclone_commands(self):
        cmds = UPLOAD_CLI_TOOLS["rclone"]["cmds"]
        assert "copy" in cmds
        assert "sync" in cmds
        assert "move" in cmds


class TestUploadToolPattern:
    def test_pattern_contains_all_tools(self):
        pattern = _upload_tool_pattern()
        for tool in UPLOAD_CLI_TOOLS:
            assert tool in pattern

    def test_pattern_contains_subcommands(self):
        pattern = _upload_tool_pattern()
        assert "upload" in pattern
        assert "files:upload" in pattern
        assert "put" in pattern
        assert "copy" in pattern

    def test_pattern_uses_shell_regex_spacing(self):
        pattern = _upload_tool_pattern()
        # Multi-word subcommands like "spo file add" should use [[:space:]]+
        assert "[[:space:]]+" in pattern


class TestZshUploadHook:
    def test_includes_upload_hooks_by_default(self):
        code = generate_zsh_hook()
        assert "_akf_pre_upload" in code
        assert "_akf_extract_upload_path" in code
        assert "pre-upload stamp" in code

    def test_contains_upload_tools(self):
        code = generate_zsh_hook()
        assert "gws" in code
        assert "rclone" in code
        assert "dbxcli" in code

    def test_upload_logging(self):
        code = generate_zsh_hook()
        assert "upload.log" in code

    def test_no_upload_hooks_when_disabled(self):
        code = generate_zsh_hook(include_uploads=False)
        assert "_akf_pre_upload" not in code
        assert "_akf_extract_upload_path" not in code

    def test_ai_hooks_still_present_when_uploads_disabled(self):
        code = generate_zsh_hook(include_uploads=False)
        assert "claude" in code
        assert "_akf_preexec" in code
        assert "akf stamp" in code


class TestBashUploadHook:
    def test_includes_upload_hooks_by_default(self):
        code = generate_bash_hook()
        assert "_akf_pre_upload" in code
        assert "_akf_extract_upload_path" in code
        assert "pre-upload stamp" in code

    def test_contains_upload_tools(self):
        code = generate_bash_hook()
        assert "gws" in code
        assert "rclone" in code
        assert "box" in code

    def test_upload_logging(self):
        code = generate_bash_hook()
        assert "upload.log" in code

    def test_no_upload_hooks_when_disabled(self):
        code = generate_bash_hook(include_uploads=False)
        assert "_akf_pre_upload" not in code
        assert "_akf_extract_upload_path" not in code

    def test_ai_hooks_still_present_when_uploads_disabled(self):
        code = generate_bash_hook(include_uploads=False)
        assert "claude" in code
        assert "_akf_preexec_handler" in code


class TestGenerateShellHookIncludeUploads:
    def test_include_uploads_passed_to_zsh(self):
        code = generate_shell_hook("zsh", include_uploads=True)
        assert "_akf_pre_upload" in code

    def test_exclude_uploads_passed_to_zsh(self):
        code = generate_shell_hook("zsh", include_uploads=False)
        assert "_akf_pre_upload" not in code

    def test_include_uploads_passed_to_bash(self):
        code = generate_shell_hook("bash", include_uploads=True)
        assert "_akf_pre_upload" in code

    def test_exclude_uploads_passed_to_bash(self):
        code = generate_shell_hook("bash", include_uploads=False)
        assert "_akf_pre_upload" not in code


# ── CLI Tests ──────────────────────────────────────────────


class TestShellHookCLI:
    def test_shell_hook_with_upload_hooks(self):
        runner = CliRunner()
        result = runner.invoke(main, ["shell-hook"])
        assert result.exit_code == 0
        assert "_akf_pre_upload" in result.output

    def test_shell_hook_without_upload_hooks(self):
        runner = CliRunner()
        result = runner.invoke(main, ["shell-hook", "--no-upload-hooks"])
        assert result.exit_code == 0
        assert "_akf_pre_upload" not in result.output
        assert "_akf_preexec" in result.output  # AI hooks still present


class TestUploadsCLI:
    def test_no_log_shows_message(self, tmp_path):
        runner = CliRunner()
        with patch.object(Path, "home", return_value=tmp_path):
            result = runner.invoke(main, ["uploads"])
        assert result.exit_code == 0
        assert "No uploads tracked" in result.output

    def test_clear_nonexistent_log(self, tmp_path):
        runner = CliRunner()
        with patch.object(Path, "home", return_value=tmp_path):
            result = runner.invoke(main, ["uploads", "--clear"])
        assert result.exit_code == 0
        assert "No upload log" in result.output

    def test_clear_existing_log(self, tmp_path):
        log_dir = tmp_path / ".akf"
        log_dir.mkdir()
        log_file = log_dir / "upload.log"
        log_file.write_text("2026-03-20T14:30:00 gws upload report.docx stamped\n")

        runner = CliRunner()
        with patch.object(Path, "home", return_value=tmp_path):
            result = runner.invoke(main, ["uploads", "--clear"])
        assert result.exit_code == 0
        assert "cleared" in result.output
        assert not log_file.exists()

    def test_display_log(self, tmp_path):
        log_dir = tmp_path / ".akf"
        log_dir.mkdir()
        log_file = log_dir / "upload.log"
        log_file.write_text(
            "2026-03-20T14:30:00 gws upload report.docx stamped\n"
            "2026-03-20T14:31:00 box upload data.xlsx stamped\n"
        )

        runner = CliRunner()
        with patch.object(Path, "home", return_value=tmp_path):
            result = runner.invoke(main, ["uploads"])
        assert result.exit_code == 0
        assert "2 upload(s) tracked" in result.output
        assert "gws" in result.output
        assert "report.docx" in result.output
        assert "box" in result.output

    def test_json_output(self, tmp_path):
        log_dir = tmp_path / ".akf"
        log_dir.mkdir()
        log_file = log_dir / "upload.log"
        log_file.write_text(
            "2026-03-20T14:30:00 gws upload report.docx stamped\n"
        )

        runner = CliRunner()
        with patch.object(Path, "home", return_value=tmp_path):
            result = runner.invoke(main, ["uploads", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["tool"] == "gws"
        assert data[0]["file"] == "report.docx"
        assert data[0]["status"] == "stamped"
