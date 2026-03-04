"""Tests for AKF field name aliasing — compact and descriptive names."""

import json
import pytest
from akf.models import AKF, Claim, Fidelity, ProvHop
from akf.core import create, loads


class TestCompactInputStillWorks:
    """Compact names must still work on input (backward compat)."""

    def test_claim_compact(self):
        c = Claim(c="test", t=0.5, src="origin", tier=2, ver=True, ver_by="x", ai=True, decay=30, exp="2026-01-01", contra="c1")
        assert c.content == "test"
        assert c.confidence == 0.5
        assert c.source == "origin"
        assert c.authority_tier == 2
        assert c.verified is True
        assert c.verified_by == "x"
        assert c.ai_generated is True
        assert c.decay_half_life == 30
        assert c.expires == "2026-01-01"
        assert c.contradicts == "c1"

    def test_fidelity_compact(self):
        f = Fidelity(h="head", s="sum", f="full")
        assert f.headline == "head"
        assert f.summary == "sum"
        assert f.full == "full"

    def test_provhop_compact(self):
        hop = ProvHop(hop=0, by="user", **{"do": "created"}, at="2025-01-01T00:00:00Z", h="sha256:abc", pen=-0.03, adds=["c1"], drops=["c2"])
        assert hop.actor == "user"
        assert hop.action == "created"
        assert hop.timestamp == "2025-01-01T00:00:00Z"
        assert hop.hash == "sha256:abc"
        assert hop.penalty == -0.03
        assert hop.claims_added == ["c1"]
        assert hop.claims_removed == ["c2"]

    def test_akf_compact(self):
        unit = AKF(v="1.0", claims=[Claim(c="test", t=0.5)], by="author", at="2025-01-01T00:00:00Z", label="internal", inherit=True, ext=False, hash="sha256:abc")
        assert unit.version == "1.0"
        assert unit.author == "author"
        assert unit.created == "2025-01-01T00:00:00Z"
        assert unit.classification == "internal"
        assert unit.inherit_classification is True
        assert unit.allow_external is False
        assert unit.integrity_hash == "sha256:abc"


class TestDescriptiveInputWorks:
    """Descriptive names must work on input."""

    def test_claim_descriptive(self):
        c = Claim(content="test", confidence=0.5, source="origin", authority_tier=2, verified=True)
        assert c.content == "test"
        assert c.confidence == 0.5
        assert c.source == "origin"
        assert c.authority_tier == 2

    def test_akf_descriptive(self):
        unit = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], author="a", classification="internal")
        assert unit.version == "1.0"
        assert unit.author == "a"
        assert unit.classification == "internal"


class TestCompactSerialization:
    """to_dict(compact=True) must produce compact names."""

    def test_claim_compact_output(self):
        c = Claim(content="test", confidence=0.5, source="origin", authority_tier=2)
        d = c.to_dict(compact=True)
        assert "c" in d
        assert "t" in d
        assert "src" in d
        assert "tier" in d
        assert "content" not in d
        assert "confidence" not in d

    def test_provhop_compact_output(self):
        hop = ProvHop(hop=0, actor="user", action="created", timestamp="2025-01-01T00:00:00Z")
        d = hop.to_dict(compact=True)
        assert "by" in d
        assert "do" in d
        assert "at" in d
        assert "actor" not in d

    def test_akf_compact_output(self):
        unit = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="internal", author="a")
        d = unit.to_dict(compact=True)
        assert "v" in d
        assert "label" in d
        assert "by" in d
        assert d["claims"][0].get("c") == "t"
        assert d["claims"][0].get("t") == 0.5


class TestDescriptiveSerialization:
    """to_dict(compact=False) must produce descriptive names."""

    def test_claim_descriptive_output(self):
        c = Claim(content="test", confidence=0.5, source="origin")
        d = c.to_dict(compact=False)
        assert "content" in d
        assert "confidence" in d
        assert "source" in d

    def test_akf_descriptive_output(self):
        unit = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="internal")
        d = unit.to_dict(compact=False)
        assert "version" in d
        assert "classification" in d
        assert d["claims"][0].get("content") == "t"


class TestRoundTrip:
    """Compact JSON -> parse -> descriptive JSON -> parse -> same object."""

    def test_compact_round_trip(self):
        unit = create("Revenue $4.2B", confidence=0.98, source="SEC", authority_tier=1)
        compact_json = unit.to_json(compact=True)
        reloaded = loads(compact_json)
        assert reloaded.claims[0].content == "Revenue $4.2B"
        assert reloaded.claims[0].confidence == 0.98
        assert reloaded.claims[0].source == "SEC"
        assert reloaded.claims[0].authority_tier == 1

    def test_descriptive_round_trip(self):
        unit = create("Revenue $4.2B", confidence=0.98, source="SEC", authority_tier=1)
        desc_json = unit.to_json(compact=False)
        reloaded = loads(desc_json)
        assert reloaded.claims[0].content == "Revenue $4.2B"
        assert reloaded.claims[0].confidence == 0.98

    def test_compact_to_descriptive_to_compact(self):
        unit = create("test", confidence=0.7, source="origin")
        compact1 = unit.to_dict(compact=True)
        reloaded = AKF(**compact1)
        compact2 = reloaded.to_dict(compact=True)
        # Claims should match
        assert compact1["claims"][0]["c"] == compact2["claims"][0]["c"]
        assert compact1["claims"][0]["t"] == compact2["claims"][0]["t"]


class TestLoadsAcceptsBothFormats:
    """loads() should accept both compact and descriptive JSON."""

    def test_loads_compact(self):
        j = '{"v":"1.0","claims":[{"c":"test","t":0.5,"src":"origin"}]}'
        unit = loads(j)
        assert unit.claims[0].content == "test"
        assert unit.claims[0].source == "origin"

    def test_loads_descriptive(self):
        j = '{"version":"1.0","claims":[{"content":"test","confidence":0.5,"source":"origin"}]}'
        unit = loads(j)
        assert unit.claims[0].content == "test"
        assert unit.claims[0].source == "origin"

    def test_loads_mixed(self):
        """Mixed compact and descriptive should also work."""
        j = '{"v":"1.0","claims":[{"content":"test","t":0.5}]}'
        unit = loads(j)
        assert unit.claims[0].content == "test"
        assert unit.claims[0].confidence == 0.5
