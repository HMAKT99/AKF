"""Tests for zero-effort akf init and hook entry points."""

import json
import subprocess

import pytest
from click.testing import CliRunner

from akf.cli import main
from akf import init_setup


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def project(tmp_path):
    """A bare project directory with a git repo."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


class TestInitDefault:
    def test_sets_up_everything(self, runner, project):
        result = runner.invoke(main, ["init", "--path", str(project)])
        assert result.exit_code == 0
        assert (project / ".akf" / "config.json").exists()
        assert (project / ".git" / "hooks" / "post-commit").exists()
        assert (project / ".claude" / "settings.json").exists()
        assert (project / "AGENTS.md").exists()
        assert "mcp_server_akf" in result.output

    def test_idempotent(self, runner, project):
        runner.invoke(main, ["init", "--path", str(project)])
        first = {
            "settings": (project / ".claude" / "settings.json").read_text(),
            "agents": (project / "AGENTS.md").read_text(),
            "hook": (project / ".git" / "hooks" / "post-commit").read_text(),
        }
        result = runner.invoke(main, ["init", "--path", str(project)])
        assert result.exit_code == 0
        assert (project / ".claude" / "settings.json").read_text() == first["settings"]
        assert (project / "AGENTS.md").read_text() == first["agents"]
        assert (project / ".git" / "hooks" / "post-commit").read_text() == first["hook"]

    def test_only_scoping(self, runner, project):
        result = runner.invoke(main, ["init", "--path", str(project), "--only", "git"])
        assert result.exit_code == 0
        assert (project / ".git" / "hooks" / "post-commit").exists()
        assert not (project / ".claude").exists()
        assert not (project / "AGENTS.md").exists()

    def test_no_git_repo_skips_hooks(self, runner, tmp_path):
        result = runner.invoke(main, ["init", "--path", str(tmp_path)])
        assert result.exit_code == 0
        assert "skipped (not a git repository)" in result.output


class TestGitHook:
    def test_hook_calls_akf_hook_post_commit(self, runner, project):
        runner.invoke(main, ["init", "--path", str(project), "--only", "git"])
        hook = (project / ".git" / "hooks" / "post-commit").read_text()
        assert "akf hook post-commit" in hook

    def test_appends_to_existing_hook(self, runner, project):
        hooks_dir = project / ".git" / "hooks"
        hooks_dir.mkdir(exist_ok=True)
        existing = hooks_dir / "post-commit"
        existing.write_text("#!/bin/sh\necho existing\n")
        runner.invoke(main, ["init", "--path", str(project), "--only", "git"])
        content = existing.read_text()
        assert "echo existing" in content
        assert "akf hook post-commit" in content


class TestClaudeHookSetup:
    def test_settings_shape(self, runner, project):
        runner.invoke(main, ["init", "--path", str(project), "--only", "claude"])
        settings = json.loads((project / ".claude" / "settings.json").read_text())
        entries = settings["hooks"]["PostToolUse"]
        assert entries[0]["matcher"] == "Write|Edit"
        assert entries[0]["hooks"][0]["command"] == "akf hook claude"

    def test_merges_into_existing_settings(self, runner, project):
        claude_dir = project / ".claude"
        claude_dir.mkdir()
        (claude_dir / "settings.json").write_text(json.dumps({"model": "opus"}))
        runner.invoke(main, ["init", "--path", str(project), "--only", "claude"])
        settings = json.loads((claude_dir / "settings.json").read_text())
        assert settings["model"] == "opus"
        assert "PostToolUse" in settings["hooks"]


class TestRulesStanza:
    def test_updates_existing_rules_files(self, runner, project):
        (project / "CLAUDE.md").write_text("# My project\n")
        (project / ".cursorrules").write_text("be terse\n")
        runner.invoke(main, ["init", "--path", str(project), "--only", "rules"])
        claude_md = (project / "CLAUDE.md").read_text()
        assert "# My project" in claude_md
        assert init_setup.STANZA_BEGIN in claude_md
        assert "akf check <file>" in claude_md
        assert init_setup.STANZA_BEGIN in (project / ".cursorrules").read_text()
        # AGENTS.md is only created when no rules files exist.
        assert not (project / "AGENTS.md").exists()

    def test_stanza_refresh_replaces_in_place(self, runner, project):
        (project / "CLAUDE.md").write_text(
            f"# Top\n\n{init_setup.STANZA_BEGIN}\nold stanza\n{init_setup.STANZA_END}\n\n# Bottom\n"
        )
        runner.invoke(main, ["init", "--path", str(project), "--only", "rules"])
        content = (project / "CLAUDE.md").read_text()
        assert "old stanza" not in content
        assert "akf check <file>" in content
        assert content.startswith("# Top")
        assert "# Bottom" in content
        assert content.count(init_setup.STANZA_BEGIN) == 1


class TestClaudeHookEntry:
    def test_stamps_file_from_payload(self, runner, tmp_path):
        target = tmp_path / "out.md"
        target.write_text("# Out\n")
        payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(target)}})
        result = runner.invoke(main, ["hook", "claude"], input=payload)
        assert result.exit_code == 0
        from akf.check import check_file
        assert check_file(str(target)).status != "UNSTAMPED"

    def test_never_fails_on_garbage(self, runner):
        result = runner.invoke(main, ["hook", "claude"], input="not json")
        assert result.exit_code == 0

    def test_skips_missing_file(self, runner):
        payload = json.dumps({"tool_input": {"file_path": "/nonexistent/x.md"}})
        result = runner.invoke(main, ["hook", "claude"], input=payload)
        assert result.exit_code == 0
