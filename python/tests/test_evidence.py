"""Tests for Evidence model, Claim evidence/kind fields, trust grounding, and AKF envelope new fields."""

import json

import akf
from akf import AKF, AKFBuilder, Claim, Evidence, TrustResult, effective_trust, create, validate


class TestEvidenceModel:
    """Tests for the Evidence model."""

    def test_basic_evidence(self):
        ev = Evidence(type="test_pass", detail="42/42 tests passed")
        assert ev.type == "test_pass"
        assert ev.detail == "42/42 tests passed"
        assert ev.timestamp is None
        assert ev.tool is None

    def test_evidence_with_all_fields(self):
        ev = Evidence(type="type_check", detail="mypy: 0 errors", timestamp="2025-01-01T00:00:00Z", tool="mypy")
        assert ev.type == "type_check"
        assert ev.tool == "mypy"
        assert ev.timestamp == "2025-01-01T00:00:00Z"

    def test_evidence_extra_fields(self):
        ev = Evidence(type="test_pass", detail="ok", custom_field="hello")
        d = ev.to_dict()
        assert d["custom_field"] == "hello"

    def test_evidence_to_dict(self):
        ev = Evidence(type="lint_clean", detail="0 issues")
        d = ev.to_dict()
        assert d["type"] == "lint_clean"
        assert d["detail"] == "0 issues"
        assert "timestamp" not in d  # None excluded

    def test_evidence_to_dict_compact(self):
        ev = Evidence(type="ci_pass", detail="green", timestamp="2025-01-01T00:00:00Z")
        d = ev.to_dict(compact=True)
        assert d["type"] == "ci_pass"
        assert "at" in d


class TestClaimWithEvidence:
    """Tests for Claim with kind and evidence fields."""

    def test_claim_with_kind(self):
        c = Claim(content="Fixed bug", confidence=0.9, kind="code_change")
        assert c.kind == "code_change"

    def test_claim_kind_default_none(self):
        c = Claim(content="Test", confidence=0.5)
        assert c.kind is None

    def test_claim_with_evidence(self):
        ev = Evidence(type="test_pass", detail="all tests pass")
        c = Claim(content="Fixed bug", confidence=0.9, evidence=[ev])
        assert len(c.evidence) == 1
        assert c.evidence[0].type == "test_pass"

    def test_claim_evidence_default_none(self):
        c = Claim(content="Test", confidence=0.5)
        assert c.evidence is None

    def test_claim_to_dict_with_evidence(self):
        ev = Evidence(type="test_pass", detail="ok")
        c = Claim(content="Test", confidence=0.8, kind="code_change", evidence=[ev])
        d = c.to_dict()
        assert d["kind"] == "code_change"
        assert len(d["evidence"]) == 1
        assert d["evidence"][0]["type"] == "test_pass"

    def test_claim_to_dict_compact_with_evidence(self):
        ev = Evidence(type="test_pass", detail="ok")
        c = Claim(content="Test", confidence=0.8, evidence=[ev])
        d = c.to_dict(compact=True)
        assert "c" in d
        assert len(d["evidence"]) == 1


class TestTrustGrounding:
    """Tests for trust computation with evidence grounding."""

    def test_ungrounded_claim(self):
        c = Claim(content="Test", confidence=0.9)
        result = effective_trust(c)
        assert result.grounded is False
        assert result.evidence_count == 0

    def test_grounded_claim(self):
        ev = Evidence(type="test_pass", detail="all pass")
        c = Claim(content="Test", confidence=0.9, evidence=[ev])
        result = effective_trust(c)
        assert result.grounded is True
        assert result.evidence_count == 1

    def test_multiple_evidence(self):
        evs = [
            Evidence(type="test_pass", detail="42/42"),
            Evidence(type="type_check", detail="mypy: 0 errors"),
            Evidence(type="lint_clean", detail="ruff: 0 issues"),
        ]
        c = Claim(content="Test", confidence=0.9, evidence=evs)
        result = effective_trust(c)
        assert result.evidence_count == 3
        assert result.grounded is True

    def test_grounding_adds_bonus(self):
        """Evidence grounding adds a trust bonus in v1.1."""
        c1 = Claim(content="Test", confidence=0.9, authority_tier=1)
        c2 = Claim(content="Test", confidence=0.9, authority_tier=1,
                   evidence=[Evidence(type="test_pass", detail="ok")])
        r1 = effective_trust(c1)
        r2 = effective_trust(c2)
        assert r2.score > r1.score
        assert r2.breakdown["grounding_bonus"] == 0.05


class TestAKFEnvelopeNewFields:
    """Tests for model, tools, session fields on AKF."""

    def test_model_field(self):
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)], model="claude-sonnet-4-20250514")
        assert unit.model == "claude-sonnet-4-20250514"

    def test_tools_field(self):
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)], tools=["bash", "edit"])
        assert unit.tools == ["bash", "edit"]

    def test_session_field(self):
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)], session="sess-123")
        assert unit.session == "sess-123"

    def test_new_fields_default_none(self):
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        assert unit.model is None
        assert unit.tools is None
        assert unit.session is None


class TestRoundTrip:
    """Tests for serialization round-trip with new fields."""

    def test_evidence_round_trip(self):
        ev = Evidence(type="test_pass", detail="42/42 passed")
        c = Claim(content="Fixed bug", confidence=0.9, kind="code_change", evidence=[ev])
        unit = AKF(version="1.0", claims=[c], model="gpt-4", tools=["bash"], session="s1")

        json_str = unit.to_json(compact=False)
        data = json.loads(json_str)

        loaded = AKF(**data)
        assert loaded.claims[0].kind == "code_change"
        assert len(loaded.claims[0].evidence) == 1
        assert loaded.claims[0].evidence[0].type == "test_pass"
        assert loaded.model == "gpt-4"
        assert loaded.tools == ["bash"]
        assert loaded.session == "s1"

    def test_create_with_evidence(self):
        unit = create("Test claim", confidence=0.8, kind="code_change",
                      evidence=[{"type": "test_pass", "detail": "ok"}])
        assert unit.claims[0].kind == "code_change"
        assert len(unit.claims[0].evidence) == 1

    def test_create_with_evidence_strings(self):
        unit = create("Test claim", confidence=0.8,
                      evidence=["42/42 tests passed", "mypy: 0 errors"])
        assert len(unit.claims[0].evidence) == 2
        assert unit.claims[0].evidence[0].type == "test_pass"
        assert unit.claims[0].evidence[1].type == "type_check"


class TestInspectNewFields:
    """Tests for inspect() showing kind and evidence."""

    def test_inspect_shows_kind(self):
        c = Claim(content="Fixed bug", confidence=0.9, kind="code_change")
        unit = AKF(version="1.0", claims=[c])
        output = unit.inspect()
        assert "(code_change)" in output

    def test_inspect_shows_evidence_count(self):
        ev = Evidence(type="test_pass", detail="ok")
        c = Claim(content="Fixed bug", confidence=0.9, evidence=[ev])
        unit = AKF(version="1.0", claims=[c])
        output = unit.inspect()
        assert "[1ev]" in output

    def test_inspect_no_kind_no_evidence(self):
        c = Claim(content="Plain claim", confidence=0.5)
        unit = AKF(version="1.0", claims=[c])
        output = unit.inspect()
        assert "(code_change)" not in output
        assert "ev]" not in output
