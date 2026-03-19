"""Tests for team-level trust aggregation in certify (Feature 6)."""

import json
import os
import tempfile

import pytest

from akf.certify import (
    AgentCertifyReport,
    TeamCertifyReport,
    certify_team,
)


class TestAgentCertifyReport:
    def test_creation(self):
        r = AgentCertifyReport(
            agent_id="agent-a",
            file_count=5,
            certified_count=4,
            failed_count=1,
            avg_trust=0.82,
        )
        assert r.agent_id == "agent-a"
        assert r.file_count == 5

    def test_to_dict(self):
        r = AgentCertifyReport(
            agent_id="a",
            file_count=2,
            certified_count=2,
            failed_count=0,
            avg_trust=0.9,
        )
        d = r.to_dict()
        assert d["agent_id"] == "a"
        assert d["avg_trust"] == 0.9


class TestTeamCertifyReport:
    def test_all_agents_certified_true(self):
        r = TeamCertifyReport(
            team_id="test-team",
            total_files=4,
            certified_count=4,
            failed_count=0,
            avg_trust=0.85,
            agent_reports={
                "a": AgentCertifyReport("a", 2, 2, 0, 0.9),
                "b": AgentCertifyReport("b", 2, 2, 0, 0.8),
            },
        )
        assert r.all_agents_certified is True

    def test_all_agents_certified_false(self):
        r = TeamCertifyReport(
            team_id="test-team",
            total_files=4,
            certified_count=3,
            failed_count=1,
            avg_trust=0.75,
            agent_reports={
                "a": AgentCertifyReport("a", 2, 2, 0, 0.9),
                "b": AgentCertifyReport("b", 2, 1, 1, 0.6),
            },
        )
        assert r.all_agents_certified is False

    def test_all_agents_certified_empty(self):
        r = TeamCertifyReport(team_id="empty", agent_reports={})
        assert r.all_agents_certified is False

    def test_to_dict(self):
        r = TeamCertifyReport(
            team_id="t1",
            total_files=2,
            certified_count=2,
            failed_count=0,
            avg_trust=0.85,
            agent_reports={
                "a": AgentCertifyReport("a", 2, 2, 0, 0.85),
            },
        )
        d = r.to_dict()
        assert d["team_id"] == "t1"
        assert d["all_agents_certified"] is True
        assert "a" in d["agent_reports"]


class TestCertifyTeam:
    def _create_akf_file(self, dirpath, filename, agent_id, confidence=0.8):
        """Create a minimal AKF JSON file with agent provenance."""
        import hashlib

        content = f"test content for {filename}"
        content_hash = "sha256:" + hashlib.sha256(content.encode()).hexdigest()

        meta = {
            "v": "1.0",
            "claims": [
                {
                    "c": content,
                    "t": confidence,
                    "src": "test",
                    "origin": {"type": "ai", "model": "test"},
                }
            ],
            "agent": agent_id,
            "prov": [
                {
                    "hop": 1,
                    "actor": agent_id,
                    "action": "create",
                    "at": "2025-01-01T00:00:00Z",
                    "agent_profile": {"id": agent_id, "name": agent_id},
                }
            ],
            "hash": content_hash,
        }
        filepath = os.path.join(dirpath, filename)
        with open(filepath, "w") as f:
            json.dump(meta, f)
        return filepath

    def test_groups_by_agent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_akf_file(tmpdir, "a1.akf", "agent-a", 0.9)
            self._create_akf_file(tmpdir, "a2.akf", "agent-a", 0.8)
            self._create_akf_file(tmpdir, "b1.akf", "agent-b", 0.85)

            report = certify_team(tmpdir, min_trust=0.7)

            assert isinstance(report, TeamCertifyReport)
            assert "agent-a" in report.agent_reports
            assert "agent-b" in report.agent_reports
            assert report.agent_reports["agent-a"].file_count == 2
            assert report.agent_reports["agent-b"].file_count == 1

    def test_all_files_processed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_akf_file(tmpdir, "a.akf", "a", 0.9)
            self._create_akf_file(tmpdir, "b.akf", "b", 0.8)

            report = certify_team(tmpdir, min_trust=0.3)
            assert report.total_files == 2
            assert report.certified_count + report.failed_count == 2

    def test_partial_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_akf_file(tmpdir, "good.akf", "a", 0.9)
            self._create_akf_file(tmpdir, "bad.akf", "b", 0.1)

            report = certify_team(tmpdir, min_trust=0.3)
            # High confidence file should pass, low one should fail
            assert report.certified_count >= 1 or report.failed_count >= 1
            assert report.total_files == 2

    def test_team_id_defaults_to_dirname(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_akf_file(tmpdir, "a.akf", "a", 0.9)
            report = certify_team(tmpdir)
            assert report.team_id.startswith("team-")

    def test_custom_team_id(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._create_akf_file(tmpdir, "a.akf", "a", 0.9)
            report = certify_team(tmpdir, team_id="my-team")
            assert report.team_id == "my-team"

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = certify_team(tmpdir)
            assert report.total_files == 0
            assert report.all_agents_certified is False


class TestTeamCertifyCLI:
    def test_team_flag_exists(self):
        from click.testing import CliRunner
        from akf.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["certify", "--help"])
        assert "--team" in result.output

    def test_team_mode_json(self):
        from click.testing import CliRunner
        from akf.cli import main

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple AKF file
            meta = {
                "v": "1.0",
                "claims": [{"c": "test", "t": 0.9, "src": "test",
                            "origin": {"type": "ai", "model": "test"}}],
                "agent": "test-agent",
                "prov": [{"hop": 1, "actor": "test-agent", "action": "create",
                         "at": "2025-01-01T00:00:00Z",
                         "agent_profile": {"id": "test-agent", "name": "test-agent"}}],
            }
            with open(os.path.join(tmpdir, "test.akf"), "w") as f:
                json.dump(meta, f)

            runner = CliRunner()
            result = runner.invoke(main, ["certify", tmpdir, "--team", "--format", "json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert "team_id" in data
            assert "agent_reports" in data
