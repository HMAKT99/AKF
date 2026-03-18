"""End-to-end integration tests for expanded agent platform support.

Tests the full pipeline for all supported agent platforms:
  config file exists → stamp with agent → read → inspect → trust → validate

Covers: Claude Code, Cursor, Windsurf, GitHub Copilot, OpenAI Codex, Manus.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from akf import AKF, stamp, validate
from akf.cli import main
from akf.core import load
from akf.shell_hook import (
    AI_CLI_TOOLS,
    generate_bash_hook,
    generate_shell_hook,
    generate_zsh_hook,
)
from akf.trust import compute_all

PYTHON = sys.executable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def tmp_md(tmp_path):
    """Create a temporary markdown file for stamping."""
    p = tmp_path / "test_output.md"
    p.write_text("# Agent Output\n\nGenerated content here.\n")
    return str(p)


@pytest.fixture
def tmp_akf(tmp_path):
    """Create a temporary .akf file via the builder for inspect/trust/validate."""
    from akf.builder import AKFBuilder
    unit = (
        AKFBuilder()
        .by("test@agent.dev")
        .label("internal")
        .claim("Test claim", 0.85, source="test", authority_tier=3)
        .build()
    )
    p = tmp_path / "test.akf"
    p.write_text(unit.to_json() + "\n")
    return str(p)


@pytest.fixture
def tmp_json(tmp_path):
    """Create a temporary JSON file for stamping."""
    p = tmp_path / "data.json"
    p.write_text(json.dumps({"result": "analysis complete"}, indent=2) + "\n")
    return str(p)


# ---------------------------------------------------------------------------
# Phase 1: Agent config files exist and are well-formed
# ---------------------------------------------------------------------------

class TestAgentConfigFiles:
    """Verify all agent config files exist with correct content."""

    def test_claude_md_exists(self):
        path = PROJECT_ROOT / "CLAUDE.md"
        assert path.exists(), "CLAUDE.md missing"
        text = path.read_text()
        assert "--agent claude-code" in text
        assert "akf stamp" in text

    def test_cursorrules_exists(self):
        path = PROJECT_ROOT / ".cursorrules"
        assert path.exists(), ".cursorrules missing"
        text = path.read_text()
        assert "--agent cursor" in text
        assert "akf stamp" in text

    def test_windsurfrules_exists(self):
        path = PROJECT_ROOT / ".windsurfrules"
        assert path.exists(), ".windsurfrules missing"
        text = path.read_text()
        assert "--agent windsurf" in text
        assert "akf stamp" in text
        assert "akf read" in text

    def test_copilot_instructions_exists(self):
        path = PROJECT_ROOT / ".github" / "copilot-instructions.md"
        assert path.exists(), ".github/copilot-instructions.md missing"
        text = path.read_text()
        assert "--agent copilot" in text
        assert "akf stamp" in text
        assert "Classification" in text

    def test_agents_md_exists(self):
        path = PROJECT_ROOT / "AGENTS.md"
        assert path.exists(), "AGENTS.md missing"
        text = path.read_text()
        assert "--agent codex" in text
        assert "akf stamp" in text

    def test_all_config_files_have_classification_rules(self):
        """Every config file should instruct the agent about classification."""
        configs = [
            PROJECT_ROOT / "CLAUDE.md",
            PROJECT_ROOT / ".cursorrules",
            PROJECT_ROOT / ".windsurfrules",
            PROJECT_ROOT / ".github" / "copilot-instructions.md",
            PROJECT_ROOT / "AGENTS.md",
        ]
        for path in configs:
            text = path.read_text()
            assert "confidential" in text.lower(), f"{path.name} missing classification rules"
            assert "public" in text.lower(), f"{path.name} missing classification rules"

    def test_all_config_files_have_key_commands(self):
        """Every config file should list key AKF commands."""
        configs = [
            PROJECT_ROOT / "CLAUDE.md",
            PROJECT_ROOT / ".cursorrules",
            PROJECT_ROOT / ".windsurfrules",
            PROJECT_ROOT / ".github" / "copilot-instructions.md",
            PROJECT_ROOT / "AGENTS.md",
        ]
        for path in configs:
            text = path.read_text()
            assert "akf stamp" in text, f"{path.name} missing stamp command"
            assert "akf read" in text, f"{path.name} missing read command"


# ---------------------------------------------------------------------------
# Phase 2: Shell hook includes all agents
# ---------------------------------------------------------------------------

class TestShellHookAgentCoverage:
    """Verify all new agent names appear in shell hook."""

    def test_manus_in_ai_cli_tools(self):
        assert "manus" in AI_CLI_TOOLS

    def test_copilot_in_ai_cli_tools(self):
        assert "copilot" in AI_CLI_TOOLS

    def test_all_expected_tools_present(self):
        expected = ["claude", "chatgpt", "aider", "ollama", "copilot", "manus"]
        for tool in expected:
            assert tool in AI_CLI_TOOLS, f"{tool} missing from AI_CLI_TOOLS"

    def test_zsh_hook_contains_manus(self):
        code = generate_zsh_hook()
        assert "manus" in code

    def test_bash_hook_contains_manus(self):
        code = generate_bash_hook()
        assert "manus" in code

    def test_zsh_hook_contains_copilot(self):
        code = generate_zsh_hook()
        assert "copilot" in code

    def test_bash_hook_contains_copilot(self):
        code = generate_bash_hook()
        assert "copilot" in code


# ---------------------------------------------------------------------------
# Phase 3: stamp() API works with all agent names
# ---------------------------------------------------------------------------

NEW_AGENTS = ["copilot", "windsurf", "codex", "manus"]


class TestStampAPIAllAgents:
    """Test stamp() Python API with every new agent identity."""

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_stamp_basic(self, agent):
        unit = stamp(f"Output from {agent}", agent=agent)
        assert isinstance(unit, AKF)
        assert unit.agent == agent
        assert len(unit.claims) == 1
        assert unit.claims[0].content == f"Output from {agent}"

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_stamp_with_evidence(self, agent):
        unit = stamp(
            f"Code generated by {agent}",
            agent=agent,
            kind="code_change",
            evidence=["42/42 tests passed", "mypy: 0 errors"],
        )
        assert unit.agent == agent
        assert len(unit.claims[0].evidence) == 2
        assert unit.claims[0].evidence[0].type == "test_pass"
        assert unit.claims[0].evidence[1].type == "type_check"

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_stamp_validates(self, agent):
        unit = stamp(f"Valid output from {agent}", agent=agent)
        result = validate(unit)
        assert result.valid, f"stamp from {agent} did not validate: {result.errors}"

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_stamp_serialization_roundtrip(self, agent):
        unit = stamp(
            f"Claim by {agent}",
            agent=agent,
            confidence=0.85,
            source="test-source",
        )
        json_str = unit.to_json(compact=False)
        data = json.loads(json_str)
        assert data["agent"] == agent
        assert data["claims"][0]["confidence"] == 0.85
        assert data["claims"][0]["source"] == "test-source"

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_stamp_trust_computation(self, agent):
        unit = stamp(f"Claim by {agent}", agent=agent, confidence=0.9)
        results = compute_all(unit)
        assert len(results) == 1
        assert 0 <= results[0].score <= 1
        assert results[0].decision in ("ACCEPT", "LOW", "REJECT")


# ---------------------------------------------------------------------------
# Phase 4: CLI stamp command works end-to-end with new agents
# ---------------------------------------------------------------------------

class TestCLIStampAllAgents:
    """Test CLI `akf stamp` command with each agent identity."""

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_cli_stamp_markdown(self, runner, tmp_md, agent):
        result = runner.invoke(main, [
            "stamp", tmp_md,
            "--agent", agent,
            "--evidence", "tests pass",
        ])
        assert result.exit_code == 0, f"stamp failed for {agent}: {result.output}"
        assert "Stamped" in result.output

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_cli_stamp_json(self, runner, tmp_json, agent):
        result = runner.invoke(main, [
            "stamp", tmp_json,
            "--agent", agent,
            "--evidence", "generated from spec",
        ])
        assert result.exit_code == 0, f"stamp failed for {agent}: {result.output}"
        assert "Stamped" in result.output

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_cli_stamp_with_label(self, runner, tmp_md, agent):
        result = runner.invoke(main, [
            "stamp", tmp_md,
            "--agent", agent,
            "--label", "confidential",
            "--evidence", "docs reviewed",
        ])
        assert result.exit_code == 0, f"stamp with label failed for {agent}: {result.output}"
        assert "Stamped" in result.output


# ---------------------------------------------------------------------------
# Phase 5: Full pipeline — stamp → read → inspect → trust
# ---------------------------------------------------------------------------

class TestFullPipelineAllAgents:
    """End-to-end: stamp a file, then read/inspect/trust it via CLI."""

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_stamp_md_then_read(self, runner, tmp_md, agent):
        """Stamp markdown, then read back metadata via universal extract."""
        r = runner.invoke(main, ["stamp", tmp_md, "--agent", agent, "--evidence", "tests pass"])
        assert r.exit_code == 0

        r = runner.invoke(main, ["read", tmp_md])
        assert r.exit_code == 0
        assert "AKF" in r.output or "akf" in r.output.lower() or "claim" in r.output.lower()

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_create_akf_then_inspect(self, runner, agent, tmp_path):
        """Create an .akf file with agent, then inspect it."""
        path = str(tmp_path / f"{agent}.akf")
        r = runner.invoke(main, [
            "create", path,
            "--claim", f"Output from {agent}",
            "--trust", "0.85",
            "--by", f"{agent}@agent.dev",
        ])
        assert r.exit_code == 0

        r = runner.invoke(main, ["inspect", path])
        assert r.exit_code == 0
        assert f"Output from {agent}" in r.output

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_create_akf_then_trust(self, runner, agent, tmp_path):
        """Create an .akf file with agent, then compute trust."""
        path = str(tmp_path / f"{agent}.akf")
        r = runner.invoke(main, [
            "create", path,
            "--claim", f"Claim by {agent}",
            "--trust", "0.88",
        ])
        assert r.exit_code == 0

        r = runner.invoke(main, ["trust", path])
        assert r.exit_code == 0
        assert "ACCEPT" in r.output or "LOW" in r.output or "REJECT" in r.output

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_create_akf_then_validate(self, runner, agent, tmp_path):
        """Create an .akf file with agent, then validate it."""
        path = str(tmp_path / f"{agent}.akf")
        r = runner.invoke(main, [
            "create", path,
            "--claim", f"Valid claim from {agent}",
            "--trust", "0.9",
        ])
        assert r.exit_code == 0

        r = runner.invoke(main, ["validate", path])
        assert r.exit_code == 0
        assert "Valid" in r.output

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_stamp_md_then_scan(self, runner, tmp_md, agent):
        """Stamp markdown, then scan it."""
        r = runner.invoke(main, ["stamp", tmp_md, "--agent", agent, "--evidence", "tests pass"])
        assert r.exit_code == 0

        r = runner.invoke(main, ["scan", tmp_md])
        assert r.exit_code == 0

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_create_akf_then_audit(self, runner, agent, tmp_path):
        """Create an .akf file with agent, then audit it."""
        path = str(tmp_path / f"{agent}.akf")
        r = runner.invoke(main, [
            "create", path,
            "--claim", f"Auditable claim from {agent}",
            "--trust", "0.85",
        ])
        assert r.exit_code == 0

        r = runner.invoke(main, ["audit", path])
        assert r.exit_code == 0
        assert "Audit" in r.output


# ---------------------------------------------------------------------------
# Phase 6: Cross-agent provenance chain
# ---------------------------------------------------------------------------

class TestCrossAgentProvenance:
    """Test that multiple agents can stamp the same file sequentially."""

    def test_multi_agent_stamp_chain(self, runner, tmp_md):
        """Simulate a file passing through multiple agents via stamp + read."""
        agents_in_chain = ["codex", "copilot", "windsurf", "manus"]

        for agent in agents_in_chain:
            r = runner.invoke(main, [
                "stamp", tmp_md,
                "--agent", agent,
                "--evidence", f"processed by {agent}",
            ])
            assert r.exit_code == 0, f"stamp failed for {agent}: {r.output}"

        # Final read should succeed (uses universal extract for markdown)
        r = runner.invoke(main, ["read", tmp_md])
        assert r.exit_code == 0

    def test_multi_agent_api_chain(self):
        """Build a provenance chain using the Python API."""
        from akf.builder import AKFBuilder
        from akf.provenance import add_hop

        unit = (
            AKFBuilder()
            .by("codex")
            .label("internal")
            .claim("Initial analysis", 0.85, source="dataset", authority_tier=3)
            .agent("codex")
            .build()
        )

        unit = add_hop(unit, by="copilot", action="enriched")
        unit = add_hop(unit, by="windsurf", action="reviewed")
        unit = add_hop(unit, by="manus", action="validated")

        assert len(unit.prov) >= 4  # created + 3 hops
        result = validate(unit)
        assert result.valid

        results = compute_all(unit)
        assert len(results) >= 1
        assert all(0 <= r.score <= 1 for r in results)


# ---------------------------------------------------------------------------
# Phase 7: AKF file round-trip via subprocess (true end-to-end)
# ---------------------------------------------------------------------------

class TestSubprocessEndToEnd:
    """Run the CLI via subprocess to test the full installed path."""

    def _akf(self, *args):
        cmd = [PYTHON, "-m", "akf"] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_subprocess_stamp_md_and_read(self, agent, tmp_path):
        """Stamp markdown via subprocess, then read back metadata."""
        md = tmp_path / "output.md"
        md.write_text(f"# Generated by {agent}\n\nContent here.\n")
        path = str(md)

        # Stamp
        rc, out, err = self._akf("stamp", path, "--agent", agent, "--evidence", "tests pass")
        assert rc == 0, f"stamp failed: {err}"
        assert "Stamped" in out

        # Read (uses universal extract — works for any format)
        rc, out, err = self._akf("read", path)
        assert rc == 0, f"read failed: {err}"

    @pytest.mark.parametrize("agent", NEW_AGENTS)
    def test_subprocess_create_akf_and_trust(self, agent, tmp_path):
        """Create .akf via subprocess, then validate and compute trust."""
        akf_path = str(tmp_path / f"{agent}.akf")

        # Create
        rc, out, err = self._akf(
            "create", akf_path,
            "--claim", f"Output from {agent}",
            "--trust", "0.85",
        )
        assert rc == 0, f"create failed: {err}"

        # Validate
        rc, out, err = self._akf("validate", akf_path)
        assert rc == 0, f"validate failed: {err}"
        assert "Valid" in out

        # Trust
        rc, out, err = self._akf("trust", akf_path)
        assert rc == 0, f"trust failed: {err}"
        assert any(d in out for d in ("ACCEPT", "LOW", "REJECT"))

    def test_subprocess_stamp_json_and_read(self, tmp_path):
        """Stamp a JSON file via subprocess, then read metadata."""
        jf = tmp_path / "data.json"
        jf.write_text(json.dumps({"key": "value"}) + "\n")
        path = str(jf)

        rc, out, err = self._akf("stamp", path, "--agent", "codex", "--evidence", "generated from spec")
        assert rc == 0, f"stamp failed: {err}"

        rc, out, err = self._akf("read", path)
        assert rc == 0, f"read failed: {err}"


# ---------------------------------------------------------------------------
# Phase 8: README and docs mention all platforms
# ---------------------------------------------------------------------------

class TestDocsCompleteness:
    """Verify docs reference all supported agent platforms."""

    def test_readme_mentions_all_agents(self):
        text = (PROJECT_ROOT / "README.md").read_text()
        for agent in ["Claude Code", "Cursor", "Windsurf", "GitHub Copilot", "OpenAI Codex", "Manus"]:
            assert agent in text, f"README.md missing mention of {agent}"

    def test_readme_mentions_all_config_files(self):
        text = (PROJECT_ROOT / "README.md").read_text()
        for cfg in ["CLAUDE.md", ".cursorrules", ".windsurfrules", "copilot-instructions.md", "AGENTS.md"]:
            assert cfg in text, f"README.md missing mention of {cfg}"

    def test_getting_started_mentions_all_config_files(self):
        text = (PROJECT_ROOT / "docs" / "getting-started-guide.md").read_text()
        for cfg in ["CLAUDE.md", ".cursorrules", ".windsurfrules", "AGENTS.md", "copilot-instructions.md"]:
            assert cfg in text, f"getting-started-guide.md missing mention of {cfg}"

    def test_launch_materials_mentions_all_platforms(self):
        text = (PROJECT_ROOT / "docs" / "launch-materials.md").read_text()
        for platform in ["Windsurf", "OpenAI Codex", "Manus", "M365 Copilot"]:
            assert platform in text, f"launch-materials.md missing mention of {platform}"
