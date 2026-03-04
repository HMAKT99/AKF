"""Tests for AKF builder."""

import json
import pytest
from akf.builder import AKFBuilder
from akf.core import validate


class TestAKFBuilder:
    def test_basic_build(self):
        unit = (
            AKFBuilder()
            .by("sarah@woodgrove.com")
            .claim("Revenue $4.2B", 0.98, source="SEC 10-Q", authority_tier=1)
            .build()
        )
        assert unit.version == "1.0"
        assert len(unit.claims) == 1
        assert unit.author == "sarah@woodgrove.com"
        assert unit.id.startswith("akf-")

    def test_multi_claim_build(self):
        unit = (
            AKFBuilder()
            .by("sarah@woodgrove.com")
            .label("confidential")
            .claim("Revenue $4.2B", 0.98, source="SEC 10-Q", authority_tier=1, verified=True)
            .claim("Cloud growth 15-18%", 0.85, source="Gartner", authority_tier=2)
            .claim("Pipeline strong", 0.72, source="my estimate", authority_tier=4)
            .build()
        )
        assert len(unit.claims) == 3
        assert unit.classification == "confidential"

    def test_auto_provenance(self):
        unit = (
            AKFBuilder()
            .by("sarah@woodgrove.com")
            .claim("test", 0.5)
            .build()
        )
        assert unit.prov is not None
        assert len(unit.prov) == 1
        assert unit.prov[0].hop == 0
        assert unit.prov[0].actor == "sarah@woodgrove.com"
        assert unit.prov[0].action == "created"

    def test_auto_integrity_hash(self):
        unit = (
            AKFBuilder()
            .by("user@test.com")
            .claim("test", 0.5)
            .build()
        )
        assert unit.integrity_hash is not None
        assert unit.integrity_hash.startswith("sha256:")

    def test_tags(self):
        unit = (
            AKFBuilder()
            .claim("test", 0.5)
            .tag("revenue", "Q3")
            .build()
        )
        assert unit.claims[0].tags == ["revenue", "Q3"]

    def test_tag_without_claim_raises(self):
        with pytest.raises(ValueError):
            AKFBuilder().tag("test")

    def test_no_claims_raises(self):
        with pytest.raises(ValueError):
            AKFBuilder().build()

    def test_built_unit_validates(self):
        unit = (
            AKFBuilder()
            .by("user@test.com")
            .label("internal")
            .claim("test claim", 0.8, source="source")
            .build()
        )
        result = validate(unit)
        assert result.valid

    def test_agent_builder(self):
        unit = (
            AKFBuilder()
            .agent("copilot-m365")
            .claim("AI insight", 0.7, ai_generated=True)
            .build()
        )
        assert unit.agent == "copilot-m365"

    def test_serialization_no_nulls(self):
        unit = (
            AKFBuilder()
            .by("user@test.com")
            .claim("test", 0.5)
            .build()
        )
        j = unit.to_json()
        parsed = json.loads(j)

        def check_no_nulls(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    assert v is not None, "Null found for key '{}'".format(k)
                    check_no_nulls(v)
            elif isinstance(obj, list):
                for item in obj:
                    check_no_nulls(item)
        check_no_nulls(parsed)
