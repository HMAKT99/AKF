"""Tests for AKF models."""

import json
import pytest
from akf.models import AKF, Claim, Fidelity, ProvHop, _strip_none


class TestClaim:
    def test_minimal_claim(self):
        c = Claim(c="test", t=0.5)
        assert c.c == "test"
        assert c.t == 0.5
        assert c.id is not None  # auto-generated

    def test_full_claim(self):
        c = Claim(
            c="Revenue $4.2B",
            t=0.98,
            id="c1",
            src="SEC 10-Q",
            uri="https://sec.gov/filing",
            tier=1,
            ver=True,
            ver_by="sarah@test.com",
            ai=False,
            decay=90,
            exp="2026-01-01T00:00:00Z",
            tags=["revenue", "Q3"],
        )
        assert c.tier == 1
        assert c.ver is True
        assert len(c.tags) == 2

    def test_trust_out_of_range(self):
        with pytest.raises(Exception):
            Claim(c="bad", t=1.5)
        with pytest.raises(Exception):
            Claim(c="bad", t=-0.1)

    def test_tier_out_of_range(self):
        with pytest.raises(Exception):
            Claim(c="bad", t=0.5, tier=0)
        with pytest.raises(Exception):
            Claim(c="bad", t=0.5, tier=6)

    def test_auto_id(self):
        c = Claim(c="test", t=0.5)
        assert c.id is not None
        assert len(c.id) == 8

    def test_unknown_field_preserved(self):
        c = Claim(c="test", t=0.5, custom_field="hello")
        d = c.model_dump()
        assert d["custom_field"] == "hello"

    def test_fidelity(self):
        f = Fidelity(h="headline", s="summary text", f="full detail...")
        c = Claim(c="test", t=0.5, fidelity=f)
        assert c.fidelity.h == "headline"


class TestProvHop:
    def test_basic_hop(self):
        hop = ProvHop(hop=0, by="user@test.com", **{"do": "created"}, at="2025-01-01T00:00:00Z")
        assert hop.hop == 0
        assert hop.by == "user@test.com"

    def test_hop_with_penalty(self):
        hop = ProvHop(
            hop=1,
            by="agent",
            **{"do": "consumed"},
            at="2025-01-01T00:00:00Z",
            pen=-0.03,
        )
        assert hop.pen == -0.03

    def test_hop_dump_uses_alias(self):
        hop = ProvHop(hop=0, by="user@test.com", **{"do": "created"}, at="2025-01-01T00:00:00Z")
        d = hop.model_dump()
        assert "do" in d


class TestAKF:
    def test_minimal(self):
        unit = AKF(v="1.0", claims=[Claim(c="test", t=0.5)])
        assert unit.v == "1.0"
        assert len(unit.claims) == 1
        assert unit.id is not None  # auto-generated

    def test_full(self):
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
        assert unit.label == "confidential"
        assert unit.inherit is True

    def test_empty_claims_rejected(self):
        with pytest.raises(Exception):
            AKF(v="1.0", claims=[])

    def test_unknown_field_preserved(self):
        unit = AKF(v="1.0", claims=[Claim(c="test", t=0.5)], future_field="from-2050")
        d = unit.to_dict()
        assert d["future_field"] == "from-2050"

    def test_auto_id_and_timestamp(self):
        unit = AKF(v="1.0", claims=[Claim(c="test", t=0.5)])
        assert unit.id.startswith("akf-")
        assert unit.at is not None

    def test_to_json_no_nulls(self):
        unit = AKF(v="1.0", claims=[Claim(c="test", t=0.5)])
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
            v="1.0",
            by="sarah@test.com",
            label="confidential",
            claims=[
                Claim(c="Revenue $4.2B", t=0.98, src="SEC", tier=1, ver=True),
                Claim(c="Low confidence", t=0.3, tier=5, ai=True),
            ],
        )
        output = unit.inspect()
        assert "Revenue" in output
        assert "sarah@test.com" in output
        assert "confidential" in output


class TestStripNone:
    def test_removes_none(self):
        assert _strip_none({"a": 1, "b": None}) == {"a": 1}

    def test_nested(self):
        assert _strip_none({"a": {"b": None, "c": 1}}) == {"a": {"c": 1}}

    def test_list(self):
        assert _strip_none([{"a": None, "b": 1}]) == [{"b": 1}]
