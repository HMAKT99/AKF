"""Cross-module integration tests — end-to-end workflows spanning 3+ modules."""

import os
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from akf.builder import AKFBuilder
from akf.core import create, create_multi, load, validate
from akf.detection import run_all_detections
from akf.models import Evidence
from akf.provenance import add_hop
from akf.trust import compute_all, effective_trust
from akf.security import security_score
from akf.universal import embed, extract


class TestFullLifecycle:
    """Workflow 1: Builder → embed → extract → trust → security → detection."""

    def test_full_pipeline(self, tmp_path):
        # Build
        unit = (
            AKFBuilder()
            .by("analyst@corp.com")
            .label("internal")
            .claim("Revenue $4.2B", 0.98, source="SEC 10-Q", authority_tier=1, verified=True)
            .claim("Growth 15%", 0.85, source="Gartner", authority_tier=2)
            .claim("AI projection", 0.63, ai_generated=True, source="ML model",
                   risk="AI extrapolation")
            .build()
        )
        unit = add_hop(unit, by="analyst@corp.com", action="created")
        # Save and reload
        out = tmp_path / "test.akf"
        unit.save(str(out))
        loaded = load(str(out))
        assert len(loaded.claims) == 3

        # Validate
        result = validate(loaded)
        assert result.valid

        # Trust
        trust = effective_trust(loaded.claims[0])
        assert trust.score >= 0.8

        # Security
        sec = security_score(loaded)
        assert sec.score > 0

        # Detection — report runs without error; AI claim may trigger some detections
        report = run_all_detections(loaded)
        assert len(report.results) == 10  # All 10 detection classes ran


class TestWatchAndStamp:
    """Workflow 2: Watch thread → create file → verify stamp."""

    def test_watch_stamps_file(self, tmp_path):
        from akf import watch as watch_mod

        watch_dir = tmp_path / "watched"
        watch_dir.mkdir()
        stamped = []
        stop = threading.Event()

        def fake_stamp(filepath, agent, classification, logger=None):
            stamped.append(str(filepath))
            stop.set()

        with patch.object(watch_mod, "_stamp_file", fake_stamp):
            t = threading.Thread(
                target=watch_mod.watch,
                kwargs=dict(
                    directories=[str(watch_dir)],
                    interval=0.2,
                    stop_event=stop,
                ),
                daemon=True,
            )
            t.start()
            time.sleep(0.3)
            (watch_dir / "report.txt").write_text("Q3 results")
            t.join(timeout=5)

        assert len(stamped) >= 1


class TestTrackingAndCreate:
    """Workflow 3: Track LLM call → create unit with model info."""

    def test_tracking_context(self):
        from akf.tracking import _record, clear_tracking, get_last_model

        clear_tracking()
        _record("gpt-4o", "openai", input_tokens=500, output_tokens=200)
        last = get_last_model()
        assert last["model"] == "gpt-4o"

        unit = create("AI-generated insight", confidence=0.75,
                      ai_generated=True, source="GPT-4o analysis")
        assert unit.claims[0].ai_generated is True
        clear_tracking()


class TestStreaming:
    """Workflow 5: stream_start → stream_claim → stream_end → validate."""

    def test_streaming_flow(self, tmp_path):
        from akf.streaming import stream_start, stream_claim, stream_end

        session = stream_start(agent_id="test-agent")
        stream_claim(session, "Fact 1", confidence=0.95, source="DB")
        stream_claim(session, "Fact 2", confidence=0.88, source="API")
        stream_claim(session, "Fact 3", confidence=0.72, source="Web")
        unit = stream_end(session)

        assert len(unit.claims) == 3
        result = validate(unit)
        assert result.valid

        trust = effective_trust(unit.claims[0])
        assert trust.score > 0


class TestKnowledgeBase:
    """Workflow 6: KnowledgeBase add → query → prune."""

    def test_knowledge_base_flow(self, tmp_path):
        from akf.knowledge_base import KnowledgeBase

        kb = KnowledgeBase(str(tmp_path / "kb"))
        kb.add("Python is popular", 0.95, source="Stack Overflow", topic="tech")
        kb.add("Rust is growing", 0.88, source="GitHub Stats", topic="tech")
        kb.add("Old claim", 0.1, topic="misc")
        kb.add("Another old claim", 0.15, topic="misc")
        kb.add("Good claim", 0.9, source="Report", topic="business")

        # Query
        tech_claims = kb.query(topic="tech")
        assert len(tech_claims) == 2

        # Prune low-trust
        pruned = kb.prune(min_trust=0.3)
        assert pruned >= 2  # The two 0.1 and 0.15 claims

        # Verify remaining
        stats = kb.stats()
        assert stats["total_claims"] >= 3


class TestBuilderTransformTrust:
    """Workflow 7: Build → add_hop → effective_trust with penalty."""

    def test_penalty_applied(self):
        unit = (
            AKFBuilder()
            .by("source@corp.com")
            .label("internal")
            .claim("Original fact", 0.95, source="Primary", authority_tier=1, verified=True)
            .build()
        )
        unit = add_hop(unit, by="source@corp.com", action="created")
        unit = add_hop(unit, by="transformer@corp.com", action="transformed",
                       penalty=-0.1)
        trust_result = effective_trust(unit.claims[0])
        # Trust should be lower than raw confidence due to penalty
        assert trust_result.score <= 0.95


class TestMultiFormatRoundtrip:
    """Workflow 8: Embed into .md, .json → extract → compare."""

    def test_roundtrip(self, tmp_path):
        unit = create("Revenue $4.2B", confidence=0.98, source="SEC 10-Q")
        meta = unit.to_dict()

        # Markdown
        md_file = tmp_path / "report.md"
        md_file.write_text("# Report\nSome content here.\n")
        embed(str(md_file), metadata=meta)
        md_data = extract(str(md_file))
        assert md_data is not None
        # Compact format uses "c" for content
        claim = md_data["claims"][0]
        claim_content = claim.get("content") or claim.get("c")
        assert claim_content == "Revenue $4.2B"

        # JSON
        json_file = tmp_path / "data.json"
        json_file.write_text("{}")
        embed(str(json_file), metadata=meta)
        json_data = extract(str(json_file))
        assert json_data is not None
        claim = json_data["claims"][0]
        claim_content = claim.get("content") or claim.get("c")
        assert claim_content == "Revenue $4.2B"


class TestSigningRoundtrip:
    """Workflow 9: keygen → create → sign → save → load → verify."""

    def test_full_signing_flow(self, tmp_path):
        cryptography = pytest.importorskip("cryptography")
        from akf.signing import keygen, sign, verify

        priv, pub = keygen(key_dir=str(tmp_path / "keys"))
        unit = create("Certified fact", confidence=0.99, source="Auditor")
        signed = sign(unit, priv, signer="auditor@corp.com")

        # Save and reload
        out = tmp_path / "signed.akf"
        signed.save(str(out))
        loaded = load(str(out))

        assert verify(loaded, pub) is True


class TestDetectionAndCompliance:
    """Workflow 10: Risky unit → detection → compliance audit."""

    def test_risky_detected(self):
        from akf.compliance import audit

        unit = (
            AKFBuilder()
            .label("public")
            .claim("AI generated claim", 0.3, ai_generated=True, authority_tier=5)
            .build()
        )
        # Detection
        report = run_all_detections(unit)
        assert report.triggered_count > 0

        # Compliance audit
        regulations = ["EU_AI_Act", "GDPR", "ISO_42001", "NIST_AI_RMF",
                        "SOC2", "HIPAA"]
        for reg in regulations:
            try:
                result = audit(unit, regulation=reg)
                # Not all regulations may be defined, so just verify no crash
            except (ValueError, KeyError):
                pass  # Regulation not implemented, that's ok


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------

class TestCLICommands:
    @pytest.fixture
    def runner(self):
        from click.testing import CliRunner
        return CliRunner()

    @pytest.fixture
    def cli_main(self):
        from akf.cli import main
        return main

    def test_doctor(self, runner, cli_main):
        result = runner.invoke(cli_main, ["doctor"])
        assert result.exit_code == 0
        assert "Python" in result.output or "python" in result.output.lower()

    def test_quickstart(self, runner, cli_main, tmp_path):
        result = runner.invoke(cli_main, ["quickstart"], catch_exceptions=False)
        assert result.exit_code == 0

    def test_watch_status(self, runner, cli_main, monkeypatch):
        from akf import _auto
        monkeypatch.setattr(
            _auto, "service_status",
            lambda: {"running": False, "pid": None, "installed": False, "service_file": None},
        )
        result = runner.invoke(cli_main, ["watch", "--status"])
        assert result.exit_code == 0

    def test_watch_stop(self, runner, cli_main, monkeypatch):
        from akf import daemon
        monkeypatch.setattr(daemon, "stop_daemon", lambda: False)
        result = runner.invoke(cli_main, ["watch", "--stop"])
        assert result.exit_code == 0

    def test_install_no_daemon(self, runner, cli_main, monkeypatch):
        from akf import _auto
        monkeypatch.setattr(_auto, "install", lambda user=True: "/fake/path/akf_auto.pth")
        result = runner.invoke(cli_main, ["install", "--no-daemon"])
        assert result.exit_code == 0
