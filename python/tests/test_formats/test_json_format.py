"""Tests for the JSON format handler."""

import json
from typing import Optional

import pytest

from akf.formats.json_format import JSONHandler, wrap


@pytest.fixture
def handler() -> JSONHandler:
    return JSONHandler()


@pytest.fixture
def tmp_json(tmp_path):
    """Helper that returns a factory for temp JSON files."""

    def _make(data, name: str = "test.json", indent: int = 2) -> str:
        p = tmp_path / name
        p.write_text(json.dumps(data, indent=indent), encoding="utf-8")
        return str(p)

    return _make


# --------------------------------------------------------------------------
# Class attributes
# --------------------------------------------------------------------------


class TestJSONHandlerAttributes:
    def test_format_name(self, handler: JSONHandler) -> None:
        assert handler.FORMAT_NAME == "JSON"

    def test_extensions(self, handler: JSONHandler) -> None:
        assert ".json" in handler.EXTENSIONS

    def test_mode(self, handler: JSONHandler) -> None:
        assert handler.MODE == "embedded"

    def test_mechanism(self, handler: JSONHandler) -> None:
        assert handler.MECHANISM == "_akf key"

    def test_no_dependencies(self, handler: JSONHandler) -> None:
        assert handler.DEPENDENCIES == []


# --------------------------------------------------------------------------
# embed / extract round-trip
# --------------------------------------------------------------------------


class TestEmbedExtract:
    def test_round_trip(self, handler: JSONHandler, tmp_json) -> None:
        filepath = tmp_json({"name": "test", "value": 42})
        metadata = {"akf": "1.0", "overall_trust": 0.85, "claims": []}

        handler.embed(filepath, metadata)
        result = handler.extract(filepath)

        assert result is not None
        assert result["akf"] == "1.0"
        assert result["overall_trust"] == 0.85

    def test_preserves_existing_data(self, handler: JSONHandler, tmp_json) -> None:
        original = {"name": "test", "value": 42, "nested": {"a": 1}}
        filepath = tmp_json(original)
        metadata = {"akf": "1.0", "claims": []}

        handler.embed(filepath, metadata)

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["name"] == "test"
        assert data["value"] == 42
        assert data["nested"]["a"] == 1
        assert "_akf" in data

    def test_preserves_indentation_4(self, handler: JSONHandler, tmp_json) -> None:
        filepath = tmp_json({"name": "test"}, indent=4)
        handler.embed(filepath, {"akf": "1.0", "claims": []})

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Should use 4-space indent
        assert '    "name"' in content

    def test_preserves_indentation_2(self, handler: JSONHandler, tmp_json) -> None:
        filepath = tmp_json({"name": "test"}, indent=2)
        handler.embed(filepath, {"akf": "1.0", "claims": []})

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Should use 2-space indent
        assert '  "name"' in content

    def test_re_embed_replaces(self, handler: JSONHandler, tmp_json) -> None:
        filepath = tmp_json({"name": "test"})

        handler.embed(filepath, {"akf": "1.0", "overall_trust": 0.5, "claims": []})
        handler.embed(filepath, {"akf": "1.0", "overall_trust": 0.95, "claims": []})

        result = handler.extract(filepath)
        assert result is not None
        assert result["overall_trust"] == 0.95


# --------------------------------------------------------------------------
# extract returns None for non-enriched
# --------------------------------------------------------------------------


class TestExtractNone:
    def test_no_akf_key(self, handler: JSONHandler, tmp_json) -> None:
        filepath = tmp_json({"name": "test", "value": 42})
        result = handler.extract(filepath)
        assert result is None

    def test_empty_object(self, handler: JSONHandler, tmp_json) -> None:
        filepath = tmp_json({})
        result = handler.extract(filepath)
        assert result is None


# --------------------------------------------------------------------------
# is_enriched
# --------------------------------------------------------------------------


class TestIsEnriched:
    def test_enriched(self, handler: JSONHandler, tmp_json) -> None:
        filepath = tmp_json({"name": "test"})
        handler.embed(filepath, {"akf": "1.0", "claims": []})
        assert handler.is_enriched(filepath) is True

    def test_not_enriched(self, handler: JSONHandler, tmp_json) -> None:
        filepath = tmp_json({"name": "test"})
        assert handler.is_enriched(filepath) is False


# --------------------------------------------------------------------------
# wrap()
# --------------------------------------------------------------------------


class TestWrap:
    def test_basic_wrap(self) -> None:
        data = {"revenue": 1000000, "quarter": "Q3"}
        claims = [
            {"c": "Revenue was $1M.", "t": 0.98, "src": "SEC 10-Q", "loc": "$.revenue"},
            {"c": "Quarter is Q3.", "t": 0.95, "loc": "$.quarter"},
        ]

        result = wrap(data, claims)

        assert result["revenue"] == 1000000
        assert result["quarter"] == "Q3"
        assert "_akf" in result
        assert result["_akf"]["akf"] == "1.0"
        assert len(result["_akf"]["claims"]) == 2

    def test_overall_trust_computed(self) -> None:
        data = {"x": 1}
        claims = [
            {"c": "A", "t": 0.8},
            {"c": "B", "t": 0.6},
        ]

        result = wrap(data, claims)
        assert abs(result["_akf"]["overall_trust"] - 0.7) < 0.001

    def test_overall_trust_explicit(self) -> None:
        data = {"x": 1}
        claims = [{"c": "A", "t": 0.5}]

        result = wrap(data, claims, overall_trust=0.99)
        assert result["_akf"]["overall_trust"] == 0.99

    def test_classification(self) -> None:
        data = {"x": 1}
        claims = [{"c": "A", "t": 0.5}]

        result = wrap(data, claims, classification="confidential")
        assert result["_akf"]["classification"] == "confidential"

    def test_agent_id(self) -> None:
        data = {"x": 1}
        claims = [{"c": "A", "t": 0.5}]

        result = wrap(data, claims, agent_id="agent-v2")
        assert result["_akf"]["agent_id"] == "agent-v2"

    def test_does_not_mutate_original(self) -> None:
        data = {"x": 1, "y": 2}
        claims = [{"c": "A", "t": 0.5}]

        result = wrap(data, claims)
        assert "_akf" not in data  # original unmodified
        assert "_akf" in result

    def test_jsonpath_locations_preserved(self) -> None:
        data = {"data": [{"name": "Alice"}]}
        claims = [
            {"c": "Name is Alice.", "t": 0.99, "loc": "$.data[0].name"},
        ]

        result = wrap(data, claims)
        assert result["_akf"]["claims"][0]["loc"] == "$.data[0].name"


# --------------------------------------------------------------------------
# Error handling
# --------------------------------------------------------------------------


class TestErrors:
    def test_embed_non_object_raises(self, handler: JSONHandler, tmp_path) -> None:
        filepath = str(tmp_path / "array.json")
        with open(filepath, "w") as f:
            json.dump([1, 2, 3], f)

        with pytest.raises(TypeError, match="non-object"):
            handler.embed(filepath, {"akf": "1.0", "claims": []})


# --------------------------------------------------------------------------
# auto_enrich (inherited from base)
# --------------------------------------------------------------------------


class TestAutoEnrich:
    def test_auto_enrich_creates_metadata(self, handler: JSONHandler, tmp_json) -> None:
        filepath = tmp_json({"content": "AI generated data"})

        handler.auto_enrich(filepath, agent_id="test-agent-v1")

        result = handler.extract(filepath)
        assert result is not None
        assert result["akf"] == "1.0"
        assert result["ai_contribution"] == 1.0
        assert len(result["provenance"]) == 1
        assert result["provenance"][0]["actor"] == "test-agent-v1"


# --------------------------------------------------------------------------
# scan (inherited from base)
# --------------------------------------------------------------------------


class TestScan:
    def test_scan_enriched(self, handler: JSONHandler, tmp_json) -> None:
        filepath = tmp_json({"data": "test"})
        handler.embed(
            filepath,
            {
                "akf": "1.0",
                "overall_trust": 0.85,
                "claims": [{"c": "Data is test", "t": 0.9}],
            },
        )

        report = handler.scan(filepath)
        assert report.enriched is True
        assert report.claim_count == 1
        assert report.format == "JSON"

    def test_scan_non_enriched(self, handler: JSONHandler, tmp_json) -> None:
        filepath = tmp_json({"data": "plain"})
        report = handler.scan(filepath)
        assert report.enriched is False


# --------------------------------------------------------------------------
# Module-level convenience functions
# --------------------------------------------------------------------------


class TestModuleConvenience:
    def test_module_embed_extract(self, tmp_json) -> None:
        from akf.formats.json_format import embed as json_embed
        from akf.formats.json_format import extract as json_extract

        filepath = tmp_json({"key": "value"})
        json_embed(filepath, {"akf": "1.0", "claims": []})
        result = json_extract(filepath)
        assert result is not None
        assert result["akf"] == "1.0"
