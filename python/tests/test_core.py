"""Tests for AKF core API."""

import json
import os
import tempfile
import pytest
from akf.core import create, create_multi, load, loads, validate
from akf.models import AKF, Claim


class TestCreate:
    def test_single_claim(self):
        unit = create("Revenue $4.2B", confidence=0.98)
        assert unit.version == "1.0"
        assert len(unit.claims) == 1
        assert unit.claims[0].content == "Revenue $4.2B"
        assert unit.claims[0].confidence == 0.98

    def test_single_claim_compact_t(self):
        """Backward compat: t= still works."""
        unit = create("Revenue $4.2B", t=0.98)
        assert unit.claims[0].confidence == 0.98

    def test_single_claim_with_kwargs(self):
        unit = create("Revenue $4.2B", confidence=0.98, source="SEC 10-Q", authority_tier=1, verified=True)
        assert unit.claims[0].source == "SEC 10-Q"
        assert unit.claims[0].authority_tier == 1
        assert unit.claims[0].verified is True

    def test_single_claim_with_compact_kwargs(self):
        """Compact kwargs still work via AliasChoices."""
        unit = create("Revenue $4.2B", t=0.98, src="SEC 10-Q", tier=1, ver=True)
        assert unit.claims[0].source == "SEC 10-Q"
        assert unit.claims[0].authority_tier == 1
        assert unit.claims[0].verified is True

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
        assert unit.author == "user@test.com"
        assert unit.classification == "internal"

    def test_multi_claim_descriptive(self):
        unit = create_multi(
            [
                {"content": "Claim 1", "confidence": 0.9},
                {"content": "Claim 2", "confidence": 0.8, "source": "source"},
            ],
            author="user@test.com",
            classification="internal",
        )
        assert len(unit.claims) == 2
        assert unit.author == "user@test.com"
        assert unit.classification == "internal"

    def test_create_requires_score(self):
        with pytest.raises(ValueError, match="Trust score required"):
            create("test")


class TestLoadSave:
    def test_round_trip(self):
        unit = create("Test claim", confidence=0.85, source="test")
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False) as f:
            path = f.name
        try:
            unit.save(path)
            loaded = load(path)
            assert loaded.claims[0].content == unit.claims[0].content
            assert loaded.claims[0].confidence == unit.claims[0].confidence
            assert loaded.claims[0].source == unit.claims[0].source
            assert loaded.id == unit.id
        finally:
            os.unlink(path)

    def test_loads_from_string(self):
        json_str = '{"v":"1.0","claims":[{"c":"test","t":0.5}]}'
        unit = loads(json_str)
        assert unit.version == "1.0"
        assert unit.claims[0].content == "test"

    def test_json_excludes_none(self):
        unit = create("test", confidence=0.5)
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
        unit = create("test", confidence=0.5)
        result = validate(unit)
        assert result.valid
        # create() applies secure defaults (classification="internal", source="unspecified")
        # so level is at least 2 (practical)
        assert result.level == 2

    def test_valid_practical(self):
        unit = create("test", confidence=0.5, source="source")
        result = validate(unit)
        assert result.valid
        assert result.level == 2

    def test_valid_file(self):
        unit = create("test", confidence=0.5, source="source")
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False) as f:
            path = f.name
        try:
            unit.save(path)
            result = validate(path)
            assert result.valid
        finally:
            os.unlink(path)

    def test_invalid_label(self):
        unit = AKF(version="1.0", claims=[Claim(content="test", confidence=0.5)], classification="top-secret")
        result = validate(unit)
        assert not result.valid
        assert any("RULE 5" in e for e in result.errors)

    def test_invalid_hash_prefix(self):
        unit = AKF(version="1.0", claims=[Claim(content="test", confidence=0.5)], integrity_hash="md5:abc123")
        result = validate(unit)
        assert not result.valid
        assert any("RULE 10" in e for e in result.errors)

    def test_invalid_provenance_sequence(self):
        from akf.models import ProvHop
        unit = AKF(
            version="1.0",
            claims=[Claim(content="test", confidence=0.5)],
            prov=[
                ProvHop(hop=0, actor="a", action="created", timestamp="2025-01-01T00:00:00Z"),
                ProvHop(hop=5, actor="b", action="enriched", timestamp="2025-01-01T00:00:00Z"),
            ],
        )
        result = validate(unit)
        assert not result.valid
        assert any("RULE 7" in e for e in result.errors)

    def test_warning_ai_tier5_no_risk(self):
        unit = create("AI claim", confidence=0.6, ai_generated=True, authority_tier=5)
        result = validate(unit)
        assert result.valid
        assert len(result.warnings) > 0
        assert any("RULE 9" in w for w in result.warnings)

    def test_positive_penalty_invalid(self):
        from akf.models import ProvHop
        unit = AKF(
            version="1.0",
            claims=[Claim(content="test", confidence=0.5)],
            prov=[
                ProvHop(hop=0, actor="a", action="created", timestamp="2025-01-01T00:00:00Z", penalty=0.5),
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
