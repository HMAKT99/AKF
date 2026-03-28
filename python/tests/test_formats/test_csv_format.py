"""Tests for the CSV format handler."""

import json

import pytest

from akf.formats.csv_format import CSVHandler


@pytest.fixture
def handler() -> CSVHandler:
    return CSVHandler()


@pytest.fixture
def tmp_csv(tmp_path):
    """Helper that returns a factory for temp CSV files."""

    def _make(content: str = "", name: str = "test.csv") -> str:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return str(p)

    return _make


SAMPLE_CSV = "name,age,city\nAlice,30,NYC\nBob,25,LA\n"


# --------------------------------------------------------------------------
# Class attributes
# --------------------------------------------------------------------------


class TestCSVHandlerAttributes:
    def test_format_name(self, handler: CSVHandler) -> None:
        assert handler.FORMAT_NAME == "CSV"

    def test_extensions(self, handler: CSVHandler) -> None:
        assert ".csv" in handler.EXTENSIONS

    def test_mode(self, handler: CSVHandler) -> None:
        assert handler.MODE == "embedded"

    def test_no_dependencies(self, handler: CSVHandler) -> None:
        assert handler.DEPENDENCIES == []


# --------------------------------------------------------------------------
# embed / extract round-trip
# --------------------------------------------------------------------------


class TestEmbedExtract:
    def test_round_trip(self, handler: CSVHandler, tmp_csv) -> None:
        filepath = tmp_csv(SAMPLE_CSV)
        metadata = {"akf": "1.0", "overall_trust": 0.85, "claims": []}

        handler.embed(filepath, metadata)
        result = handler.extract(filepath)

        assert result is not None
        assert result["akf"] == "1.0"
        assert result["overall_trust"] == 0.85

    def test_preserves_csv_data(self, handler: CSVHandler, tmp_csv) -> None:
        filepath = tmp_csv(SAMPLE_CSV)
        metadata = {"akf": "1.0", "claims": []}

        handler.embed(filepath, metadata)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # CSV data should still be intact after the comment line
        assert "name,age,city" in content
        assert "Alice,30,NYC" in content
        assert "Bob,25,LA" in content

    def test_csv_parseable_after_embed(self, handler: CSVHandler, tmp_csv) -> None:
        """CSV should still be parseable by stdlib csv (skipping comment lines)."""
        import csv

        filepath = tmp_csv(SAMPLE_CSV)
        handler.embed(filepath, {"akf": "1.0", "claims": []})

        with open(filepath, "r", encoding="utf-8") as f:
            # Skip comment lines starting with #
            lines = [line for line in f if not line.startswith("#")]

        reader = csv.reader(lines)
        rows = list(reader)
        assert rows[0] == ["name", "age", "city"]
        assert rows[1] == ["Alice", "30", "NYC"]

    def test_re_embed_replaces(self, handler: CSVHandler, tmp_csv) -> None:
        filepath = tmp_csv(SAMPLE_CSV)

        handler.embed(filepath, {"akf": "1.0", "overall_trust": 0.5, "claims": []})
        handler.embed(filepath, {"akf": "1.0", "overall_trust": 0.95, "claims": []})

        result = handler.extract(filepath)
        assert result is not None
        assert result["overall_trust"] == 0.95

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        assert content.count("# _akf:") == 1


# --------------------------------------------------------------------------
# extract returns None for non-enriched
# --------------------------------------------------------------------------


class TestExtractNone:
    def test_no_akf_comment(self, handler: CSVHandler, tmp_csv) -> None:
        filepath = tmp_csv(SAMPLE_CSV)
        result = handler.extract(filepath)
        assert result is None

    def test_empty_file(self, handler: CSVHandler, tmp_csv) -> None:
        filepath = tmp_csv("")
        result = handler.extract(filepath)
        assert result is None


# --------------------------------------------------------------------------
# is_enriched
# --------------------------------------------------------------------------


class TestIsEnriched:
    def test_enriched(self, handler: CSVHandler, tmp_csv) -> None:
        filepath = tmp_csv(SAMPLE_CSV)
        handler.embed(filepath, {"akf": "1.0", "claims": []})
        assert handler.is_enriched(filepath) is True

    def test_not_enriched(self, handler: CSVHandler, tmp_csv) -> None:
        filepath = tmp_csv(SAMPLE_CSV)
        assert handler.is_enriched(filepath) is False


# --------------------------------------------------------------------------
# Module-level convenience
# --------------------------------------------------------------------------


class TestModuleConvenience:
    def test_module_embed_extract(self, tmp_csv) -> None:
        from akf.formats.csv_format import embed as csv_embed
        from akf.formats.csv_format import extract as csv_extract

        filepath = tmp_csv(SAMPLE_CSV)
        csv_embed(filepath, {"akf": "1.0", "claims": []})
        result = csv_extract(filepath)
        assert result is not None
        assert result["akf"] == "1.0"
