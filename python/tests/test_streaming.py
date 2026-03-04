"""Tests for v1.1 streaming .akfl support."""

import json
import os
import tempfile

import pytest
from akf.streaming import (
    StreamSession, stream_start, stream_claim, stream_end,
    collect_stream, iter_stream,
)
from akf.models import AKF


class TestStreamLifecycle:
    def test_stream_start_creates_session(self):
        session = stream_start(agent_id="test-agent")
        assert session.session_id
        assert session.agent == "test-agent"
        assert session.started_at
        assert session.claims == []

    def test_stream_claim_adds_to_session(self):
        session = stream_start()
        claim = stream_claim(session, "Test claim", 0.8)
        assert claim.content == "Test claim"
        assert claim.confidence == 0.8
        assert len(session.claims) == 1

    def test_stream_end_produces_akf(self):
        session = stream_start(agent_id="agent-1")
        stream_claim(session, "Claim 1", 0.9)
        stream_claim(session, "Claim 2", 0.7)
        unit = stream_end(session)
        assert isinstance(unit, AKF)
        assert len(unit.claims) == 2
        assert unit.agent == "agent-1"
        assert unit.integrity_hash.startswith("sha256:")

    def test_stream_claim_with_kwargs(self):
        session = stream_start()
        claim = stream_claim(session, "AI claim", 0.6,
                            ai_generated=True, source="model-output")
        assert claim.ai_generated is True
        assert claim.source == "model-output"


class TestStreamToFile:
    def test_stream_writes_to_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".akfl", delete=False) as f:
            path = f.name

        try:
            session = stream_start(agent_id="writer", output_path=path)
            stream_claim(session, "Line 1", 0.9)
            stream_claim(session, "Line 2", 0.8)
            unit = stream_end(session)

            # Read back the file
            with open(path) as f:
                lines = [json.loads(l) for l in f if l.strip()]

            assert len(lines) == 4  # start + 2 claims + end
            assert lines[0]["type"] == "start"
            assert lines[1]["type"] == "claim"
            assert lines[2]["type"] == "claim"
            assert lines[3]["type"] == "end"
            assert lines[3]["count"] == 2
        finally:
            os.unlink(path)

    def test_stream_end_saves_akf(self):
        with tempfile.NamedTemporaryFile(suffix=".akfl", delete=False) as f:
            akfl_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False) as f:
            akf_path = f.name

        try:
            session = stream_start(output_path=akfl_path)
            stream_claim(session, "Saved claim", 0.85)
            unit = stream_end(session, output_path=akf_path)

            # Verify .akf was saved
            assert os.path.exists(akf_path)
            with open(akf_path) as f:
                data = json.load(f)
            assert len(data["claims"]) == 1
        finally:
            os.unlink(akfl_path)
            os.unlink(akf_path)


class TestCollectStream:
    def _write_akfl(self, path, claims_data):
        with open(path, "w") as f:
            f.write(json.dumps({"type": "start", "session": "s1", "agent": "a1"}) + "\n")
            for c, t in claims_data:
                f.write(json.dumps({"type": "claim", "c": c, "t": t}) + "\n")
            f.write(json.dumps({"type": "end", "count": len(claims_data)}) + "\n")

    def test_collect_basic(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".akfl", delete=False) as f:
            path = f.name

        try:
            self._write_akfl(path, [("Claim A", 0.9), ("Claim B", 0.7)])
            unit = collect_stream(path)
            assert isinstance(unit, AKF)
            assert len(unit.claims) == 2
            assert unit.claims[0].content == "Claim A"
            assert unit.session == "s1"
        finally:
            os.unlink(path)

    def test_collect_missing_file(self):
        with pytest.raises(FileNotFoundError):
            collect_stream("/nonexistent/file.akfl")

    def test_collect_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".akfl", delete=False) as f:
            f.write(json.dumps({"type": "start", "session": "s1"}) + "\n")
            f.write(json.dumps({"type": "end", "count": 0}) + "\n")
            path = f.name

        try:
            with pytest.raises(ValueError, match="No claims found"):
                collect_stream(path)
        finally:
            os.unlink(path)

    def test_collect_malformed_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".akfl", delete=False) as f:
            f.write("not json\n")
            path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                collect_stream(path)
        finally:
            os.unlink(path)


class TestIterStream:
    def test_iter_basic(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".akfl", delete=False) as f:
            f.write(json.dumps({"type": "start"}) + "\n")
            f.write(json.dumps({"type": "claim", "c": "X", "t": 0.5}) + "\n")
            f.write(json.dumps({"type": "end"}) + "\n")
            path = f.name

        try:
            items = list(iter_stream(path))
            assert len(items) == 3
            assert items[0]["type"] == "start"
            assert items[1]["type"] == "claim"
            assert items[2]["type"] == "end"
        finally:
            os.unlink(path)

    def test_iter_skips_empty_lines(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".akfl", delete=False) as f:
            f.write(json.dumps({"type": "start"}) + "\n")
            f.write("\n")
            f.write(json.dumps({"type": "end"}) + "\n")
            path = f.name

        try:
            items = list(iter_stream(path))
            assert len(items) == 2
        finally:
            os.unlink(path)
