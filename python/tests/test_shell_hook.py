"""Tests for shell hook generation."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from akf.shell_hook import (
    AI_CLI_TOOLS,
    WATCHED_EXTENSIONS,
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
