"""Tests for AKF core API."""

import json
import os
import tempfile
import pytest
from akf.core import create, create_multi, load, loads, validate
from akf.models import AKF, Claim


class TestCreate:
    def test_single_claim(self):
        unit = create("Revenue $4.2B", t=0.98)
        assert unit.v == "1.0"
        assert len(unit.claims) == 1
        assert unit.claims[0].c == "Revenue $4.2B"
        assert unit.claims[0].t == 0.98

    def test_single_claim_with_kwargs(self):
        unit = create("Revenue $4.2B", t=0.98, src="SEC 10-Q", tier=1, ver=True)
        assert unit.claims[0].src == "SEC 10-Q"
        assert unit.claims[0].tier == 1
        assert unit.claims[0].ver is True

    def test_multi_claim(self):
        unit = create_multi(
            [
                {"c": "Claim 1", "t": 0.9},
                {"c": "Claim 2", "t": 0.8, "src": "source"},
            ],
            by="user@test.com",
            label="internal",
        )
        assert len(unit.claims) == 2
        assert unit.by == "user@test.com"
        assert unit.label == "internal"


class TestLoadSave:
    def test_round_trip(self):
        unit = create("Test claim", t=0.85, src="test")
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False) as f:
            path = f.name
        try:
            unit.save(path)
            loaded = load(path)
            assert loaded.claims[0].c == unit.claims[0].c
            assert loaded.claims[0].t == unit.claims[0].t
            assert loaded.claims[0].src == unit.claims[0].src
            assert loaded.id == unit.id
        finally:
            os.unlink(path)

    def test_loads_from_string(self):
        json_str = '{"v":"1.0","claims":[{"c":"test","t":0.5}]}'
        unit = loads(json_str)
        assert unit.v == "1.0"
        assert unit.claims[0].c == "test"

    def test_json_excludes_none(self):
        unit = create("test", t=0.5)
        j = unit.to_json()
        parsed = json.loads(j)
        for key, val in parsed.items():
            assert val is not None

    def test_unknown_fields_survive_round_trip(self):
        json_str = '{"v":"1.0","claims":[{"c":"test","t":0.5,"future":"2050"}],"new_field":"value"}'
        unit = loads(json_str)
        j = unit.to_json()
        parsed = json.loads(j)
        assert parsed["new_field"] == "value"
        assert parsed["claims"][0]["future"] == "2050"


class TestValidate:
    def test_valid_minimal(self):
        unit = create("test", t=0.5)
        result = validate(unit)
        assert result.valid
        assert result.level == 1

    def test_valid_practical(self):
        unit = create("test", t=0.5, src="source")
        result = validate(unit)
        assert result.valid
        assert result.level == 2

    def test_valid_file(self):
        unit = create("test", t=0.5, src="source")
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False) as f:
            path = f.name
        try:
            unit.save(path)
            result = validate(path)
            assert result.valid
        finally:
            os.unlink(path)

    def test_invalid_label(self):
        unit = AKF(v="1.0", claims=[Claim(c="test", t=0.5)], label="top-secret")
        result = validate(unit)
        assert not result.valid
        assert any("RULE 5" in e for e in result.errors)

    def test_invalid_hash_prefix(self):
        unit = AKF(v="1.0", claims=[Claim(c="test", t=0.5)], hash="md5:abc123")
        result = validate(unit)
        assert not result.valid
        assert any("RULE 10" in e for e in result.errors)

    def test_invalid_provenance_sequence(self):
        from akf.models import ProvHop
        unit = AKF(
            v="1.0",
            claims=[Claim(c="test", t=0.5)],
            prov=[
                ProvHop(hop=0, by="a", **{"do": "created"}, at="2025-01-01T00:00:00Z"),
                ProvHop(hop=5, by="b", **{"do": "enriched"}, at="2025-01-01T00:00:00Z"),
            ],
        )
        result = validate(unit)
        assert not result.valid
        assert any("RULE 7" in e for e in result.errors)

    def test_warning_ai_tier5_no_risk(self):
        unit = create("AI claim", t=0.6, ai=True, tier=5)
        result = validate(unit)
        assert result.valid
        assert len(result.warnings) > 0
        assert any("RULE 9" in w for w in result.warnings)

    def test_positive_penalty_invalid(self):
        from akf.models import ProvHop
        unit = AKF(
            v="1.0",
            claims=[Claim(c="test", t=0.5)],
            prov=[
                ProvHop(hop=0, by="a", **{"do": "created"}, at="2025-01-01T00:00:00Z", pen=0.5),
            ],
        )
        result = validate(unit)
        assert not result.valid
        assert any("RULE 8" in e for e in result.errors)

    def test_validate_example_files(self):
        import os
        examples_dir = os.path.join(os.path.dirname(__file__), "..", "..", "spec", "examples")
        if os.path.exists(examples_dir):
            for fname in os.listdir(examples_dir):
                if fname.endswith(".akf"):
                    path = os.path.join(examples_dir, fname)
                    result = validate(path)
                    assert result.valid, "Failed: {} - {}".format(fname, result.errors)
