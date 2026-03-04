"""Tests for AKF models."""

import json
import pytest
from akf.models import AKF, Claim, Fidelity, ProvHop, _strip_none


class TestClaim:
    def test_minimal_claim(self):
        c = Claim(content="test", confidence=0.5)
        assert c.content == "test"
        assert c.confidence == 0.5
        assert c.id is not None  # auto-generated

    def test_minimal_claim_compact(self):
        """Compact names still work on input."""
        c = Claim(c="test", t=0.5)
        assert c.content == "test"
        assert c.confidence == 0.5

    def test_full_claim(self):
        c = Claim(
            content="Revenue $4.2B",
            confidence=0.98,
            id="c1",
            source="SEC 10-Q",
            uri="https://sec.gov/filing",
            authority_tier=1,
            verified=True,
            verified_by="sarah@test.com",
            ai_generated=False,
            decay_half_life=90,
            expires="2026-01-01T00:00:00Z",
            tags=["revenue", "Q3"],
        )
        assert c.authority_tier == 1
        assert c.verified is True
        assert len(c.tags) == 2

    def test_full_claim_compact_input(self):
        """Compact names accepted on input, descriptive on access."""
        c = Claim(
            c="Revenue $4.2B",
            t=0.98,
            id="c1",
            src="SEC 10-Q",
            tier=1,
            ver=True,
            ver_by="sarah@test.com",
            ai=False,
            decay=90,
            exp="2026-01-01T00:00:00Z",
            tags=["revenue", "Q3"],
        )
        assert c.content == "Revenue $4.2B"
        assert c.confidence == 0.98
        assert c.source == "SEC 10-Q"
        assert c.authority_tier == 1
        assert c.verified is True
        assert c.verified_by == "sarah@test.com"
        assert c.ai_generated is False
        assert c.decay_half_life == 90
        assert c.expires == "2026-01-01T00:00:00Z"

    def test_trust_out_of_range(self):
        with pytest.raises(Exception):
            Claim(content="bad", confidence=1.5)
        with pytest.raises(Exception):
            Claim(content="bad", confidence=-0.1)

    def test_tier_out_of_range(self):
        with pytest.raises(Exception):
            Claim(content="bad", confidence=0.5, authority_tier=0)
        with pytest.raises(Exception):
            Claim(content="bad", confidence=0.5, authority_tier=6)

    def test_auto_id(self):
        c = Claim(content="test", confidence=0.5)
        assert c.id is not None
        assert len(c.id) == 8

    def test_unknown_field_preserved(self):
        c = Claim(content="test", confidence=0.5, custom_field="hello")
        d = c.model_dump()
        assert d["custom_field"] == "hello"

    def test_fidelity(self):
        f = Fidelity(headline="headline", summary="summary text", full="full detail...")
        c = Claim(content="test", confidence=0.5, fidelity=f)
        assert c.fidelity.headline == "headline"

    def test_fidelity_compact_input(self):
        f = Fidelity(h="headline", s="summary text", f="full detail...")
        assert f.headline == "headline"
        assert f.summary == "summary text"
        assert f.full == "full detail..."


class TestProvHop:
    def test_basic_hop(self):
        hop = ProvHop(hop=0, actor="user@test.com", action="created", timestamp="2025-01-01T00:00:00Z")
        assert hop.hop == 0
        assert hop.actor == "user@test.com"
        assert hop.action == "created"
        assert hop.timestamp == "2025-01-01T00:00:00Z"

    def test_basic_hop_compact_input(self):
        """Compact names accepted on input."""
        hop = ProvHop(hop=0, by="user@test.com", **{"do": "created"}, at="2025-01-01T00:00:00Z")
        assert hop.actor == "user@test.com"
        assert hop.action == "created"
        assert hop.timestamp == "2025-01-01T00:00:00Z"

    def test_hop_with_penalty(self):
        hop = ProvHop(
            hop=1,
            actor="agent",
            action="consumed",
            timestamp="2025-01-01T00:00:00Z",
            penalty=-0.03,
        )
        assert hop.penalty == -0.03

    def test_hop_compact_serialization(self):
        hop = ProvHop(hop=0, actor="user@test.com", action="created", timestamp="2025-01-01T00:00:00Z")
        d = hop.to_dict(compact=True)
        assert "do" in d
        assert "by" in d
        assert "at" in d

    def test_hop_descriptive_serialization(self):
        hop = ProvHop(hop=0, actor="user@test.com", action="created", timestamp="2025-01-01T00:00:00Z")
        d = hop.to_dict(compact=False)
        assert "action" in d
        assert "actor" in d
        assert "timestamp" in d


class TestAKF:
    def test_minimal(self):
        unit = AKF(version="1.0", claims=[Claim(content="test", confidence=0.5)])
        assert unit.version == "1.0"
        assert len(unit.claims) == 1
        assert unit.id is not None  # auto-generated

    def test_minimal_compact_input(self):
        unit = AKF(v="1.0", claims=[Claim(c="test", t=0.5)])
        assert unit.version == "1.0"
        assert unit.claims[0].content == "test"

    def test_full(self):
        unit = AKF(
            version="1.0",
            id="test-id",
            author="user@test.com",
            created="2025-01-01T00:00:00Z",
            classification="confidential",
            inherit_classification=True,
            allow_external=False,
            claims=[Claim(content="test", confidence=0.5, id="c1")],
            prov=[ProvHop(hop=0, actor="user@test.com", action="created", timestamp="2025-01-01T00:00:00Z")],
        )
        assert unit.classification == "confidential"
        assert unit.inherit_classification is True

    def test_full_compact_input(self):
        unit = AKF(
            v="1.0",
            id="test-id",
            by="user@test.com",
            at="2025-01-01T00:00:00Z",
            label="confidential",
            inherit=True,
            ext=False,
            claims=[Claim(c="test", t=0.5, id="c1")],
            prov=[ProvHop(hop=0, by="user@test.com", **{"do": "created"}, at="2025-01-01T00:00:00Z")],
        )
        assert unit.classification == "confidential"
        assert unit.inherit_classification is True
        assert unit.allow_external is False
        assert unit.author == "user@test.com"
        assert unit.version == "1.0"

    def test_empty_claims_rejected(self):
        with pytest.raises(Exception):
            AKF(version="1.0", claims=[])

    def test_unknown_field_preserved(self):
        unit = AKF(version="1.0", claims=[Claim(content="test", confidence=0.5)], future_field="from-2050")
        d = unit.to_dict()
        assert d["future_field"] == "from-2050"

    def test_auto_id_and_timestamp(self):
        unit = AKF(version="1.0", claims=[Claim(content="test", confidence=0.5)])
        assert unit.id.startswith("akf-")
        assert unit.created is not None

    def test_to_json_no_nulls(self):
        unit = AKF(version="1.0", claims=[Claim(content="test", confidence=0.5)])
        j = unit.to_json()
        parsed = json.loads(j)
        # No null values anywhere
        def check_no_nulls(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    assert v is not None, "Found null for key '{}'".format(k)
                    check_no_nulls(v)
            elif isinstance(obj, list):
                for item in obj:
                    check_no_nulls(item)
        check_no_nulls(parsed)

    def test_inspect(self):
        unit = AKF(
            version="1.0",
            author="sarah@test.com",
            classification="confidential",
            claims=[
                Claim(content="Revenue $4.2B", confidence=0.98, source="SEC", authority_tier=1, verified=True),
                Claim(content="Low confidence", confidence=0.3, authority_tier=5, ai_generated=True),
            ],
        )
        output = unit.inspect()
        assert "Revenue" in output
        assert "sarah@test.com" in output
        assert "confidential" in output

    def test_compact_serialization(self):
        unit = AKF(version="1.0", claims=[Claim(content="test", confidence=0.5)])
        d = unit.to_dict(compact=True)
        assert "v" in d
        assert "c" in d["claims"][0]
        assert "t" in d["claims"][0]

    def test_descriptive_serialization(self):
        unit = AKF(version="1.0", claims=[Claim(content="test", confidence=0.5)])
        d = unit.to_dict(compact=False)
        assert "version" in d
        assert "content" in d["claims"][0]
        assert "confidence" in d["claims"][0]


class TestStripNone:
    def test_removes_none(self):
        assert _strip_none({"a": 1, "b": None}) == {"a": 1}

    def test_nested(self):
        assert _strip_none({"a": {"b": None, "c": 1}}) == {"a": {"c": 1}}

    def test_list(self):
        assert _strip_none([{"a": None, "b": 1}]) == [{"b": 1}]
