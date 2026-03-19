"""Tests for team-aware streaming (Feature 2)."""

import json
import os
import tempfile

import pytest

from akf.team_stream import (
    TeamStream,
    TeamStreamSession,
    TeamTrustResult,
    team_stream_claim,
    team_stream_end,
    team_stream_start,
    team_trust_aggregate,
)


class TestTeamStreamStart:
    def test_creates_session(self):
        session = team_stream_start(["agent-a", "agent-b"])
        assert isinstance(session, TeamStreamSession)
        assert len(session.agents) == 2
        assert "agent-a" in session.agents
        assert "agent-b" in session.agents
        assert session.team_id

    def test_session_has_unique_id(self):
        s1 = team_stream_start(["a"])
        s2 = team_stream_start(["a"])
        assert s1.team_id != s2.team_id

    def test_writes_header_to_file(self):
        with tempfile.NamedTemporaryFile(suffix=".akfl", delete=False) as f:
            path = f.name
        try:
            session = team_stream_start(["agent-a", "agent-b"], output_path=path)
            team_stream_end(session)
            with open(path) as f:
                lines = f.readlines()
            header = json.loads(lines[0])
            assert header["type"] == "team_start"
            assert header["team"] == session.team_id
            assert set(header["agents"]) == {"agent-a", "agent-b"}
        finally:
            os.unlink(path)


class TestTeamStreamClaim:
    def test_claim_attributed_to_agent(self):
        session = team_stream_start(["agent-a", "agent-b"])
        claim = team_stream_claim(session, "agent-a", "Test claim", 0.9)
        assert claim.content == "Test claim"
        assert claim.confidence == 0.9
        assert len(session.agents["agent-a"].claims) == 1
        assert len(session.agents["agent-b"].claims) == 0

    def test_multiple_agents_claims(self):
        session = team_stream_start(["a", "b"])
        team_stream_claim(session, "a", "Claim from A", 0.8)
        team_stream_claim(session, "b", "Claim from B", 0.7)
        team_stream_claim(session, "a", "Another from A", 0.9)
        assert len(session.agents["a"].claims) == 2
        assert len(session.agents["b"].claims) == 1

    def test_invalid_agent_raises(self):
        session = team_stream_start(["agent-a"])
        with pytest.raises(ValueError, match="not in team session"):
            team_stream_claim(session, "unknown-agent", "Claim", 0.5)

    def test_claim_written_to_file_with_agent(self):
        with tempfile.NamedTemporaryFile(suffix=".akfl", delete=False) as f:
            path = f.name
        try:
            session = team_stream_start(["a", "b"], output_path=path)
            team_stream_claim(session, "a", "Claim A", 0.8)
            team_stream_claim(session, "b", "Claim B", 0.7)
            team_stream_end(session)

            with open(path) as f:
                lines = [json.loads(line) for line in f.readlines()]

            claim_lines = [l for l in lines if l["type"] == "claim"]
            assert len(claim_lines) == 2
            assert claim_lines[0]["agent"] == "a"
            assert claim_lines[1]["agent"] == "b"
        finally:
            os.unlink(path)


class TestTeamStreamEnd:
    def test_collects_all_claims(self):
        session = team_stream_start(["a", "b"])
        team_stream_claim(session, "a", "A1", 0.8)
        team_stream_claim(session, "b", "B1", 0.7)
        team_stream_claim(session, "a", "A2", 0.9)
        unit = team_stream_end(session)
        assert len(unit.claims) == 3
        assert unit.integrity_hash.startswith("sha256:")

    def test_writes_footer(self):
        with tempfile.NamedTemporaryFile(suffix=".akfl", delete=False) as f:
            path = f.name
        try:
            session = team_stream_start(["a"], output_path=path)
            team_stream_claim(session, "a", "Claim", 0.8)
            team_stream_end(session)

            with open(path) as f:
                lines = [json.loads(line) for line in f.readlines()]

            footer = lines[-1]
            assert footer["type"] == "team_end"
            assert footer["count"] == 1
        finally:
            os.unlink(path)


class TestTeamTrustAggregate:
    def test_per_agent_scores(self):
        session = team_stream_start(["a", "b"])
        team_stream_claim(session, "a", "A1", 0.8)
        team_stream_claim(session, "a", "A2", 0.6)
        team_stream_claim(session, "b", "B1", 0.9)

        result = team_trust_aggregate(session)
        assert isinstance(result, TeamTrustResult)
        assert result.agent_scores["a"] == 0.7
        assert result.agent_scores["b"] == 0.9
        assert result.total_claims == 3
        assert result.claims_per_agent["a"] == 2
        assert result.claims_per_agent["b"] == 1

    def test_team_avg_trust(self):
        session = team_stream_start(["a", "b"])
        team_stream_claim(session, "a", "A1", 0.8)
        team_stream_claim(session, "b", "B1", 0.6)
        result = team_trust_aggregate(session)
        assert result.team_avg_trust == 0.7

    def test_empty_agent_scores_zero(self):
        session = team_stream_start(["a", "b"])
        team_stream_claim(session, "a", "A1", 0.8)
        result = team_trust_aggregate(session)
        assert result.agent_scores["b"] == 0.0
        assert result.claims_per_agent["b"] == 0


class TestTeamStreamContextManager:
    def test_basic_usage(self):
        with TeamStream(["a", "b"]) as ts:
            ts.write("a", "Claim A", confidence=0.9)
            ts.write("b", "Claim B", confidence=0.8)
        assert ts.unit is not None
        assert len(ts.unit.claims) == 2

    def test_default_confidence(self):
        with TeamStream(["a"], confidence=0.6) as ts:
            claim = ts.write("a", "Test")
        assert claim.confidence == 0.6

    def test_aggregate_during_stream(self):
        with TeamStream(["a", "b"]) as ts:
            ts.write("a", "A1", confidence=0.9)
            ts.write("b", "B1", confidence=0.7)
            result = ts.aggregate()
            assert result.total_claims == 2

    def test_file_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            outpath = os.path.join(tmpdir, "output.md")
            with TeamStream(["a"], output_path=outpath) as ts:
                ts.write("a", "Claim", confidence=0.8)

            akfl = outpath + ".team.akfl"
            assert os.path.exists(akfl)
            with open(akfl) as f:
                lines = [json.loads(l) for l in f.readlines()]
            assert lines[0]["type"] == "team_start"
            assert lines[-1]["type"] == "team_end"

    def test_not_started_raises(self):
        ts = TeamStream(["a"])
        with pytest.raises(RuntimeError, match="not started"):
            ts.write("a", "test")
