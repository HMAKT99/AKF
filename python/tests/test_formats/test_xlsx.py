"""Tests for the XLSX format handler.

Creates minimal valid XLSX files (ZIP archives with required OOXML parts)
to test embed/extract operations without needing openpyxl.
"""

import json
import os
import tempfile
import zipfile

import pytest

from akf.formats.xlsx import XLSXHandler, embed, extract, is_enriched, scan
from akf.formats._ooxml import AKF_JSON_PATH, AKF_XML_PATH
from akf.formats.base import ScanReport


def create_minimal_xlsx(path):
    """Create a minimal valid XLSX (ZIP with required XML parts)."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        # [Content_Types].xml
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType='
            '"application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument'
            '.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument'
            '.spreadsheetml.worksheet+xml"/>'
            "</Types>",
        )
        # _rels/.rels
        z.writestr(
            "_rels/.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns='
            '"http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type='
            '"http://schemas.openxmlformats.org/officeDocument/2006/relationships'
            '/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>",
        )
        # xl/workbook.xml
        z.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
            ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            "<sheets>"
            '<sheet name="Sheet1" sheetId="1" r:id="rId1"/>'
            "</sheets>"
            "</workbook>",
        )
        # xl/_rels/workbook.xml.rels
        z.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns='
            '"http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type='
            '"http://schemas.openxmlformats.org/officeDocument/2006/relationships'
            '/worksheet" Target="worksheets/sheet1.xml"/>'
            "</Relationships>",
        )
        # xl/worksheets/sheet1.xml
        z.writestr(
            "xl/worksheets/sheet1.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            "<sheetData>"
            '<row r="1"><c r="A1" t="inlineStr"><is><t>Hello</t></is></c></row>'
            "</sheetData>"
            "</worksheet>",
        )


@pytest.fixture
def xlsx_file(tmp_path):
    """Create a temporary minimal XLSX file."""
    path = str(tmp_path / "test.xlsx")
    create_minimal_xlsx(path)
    return path


@pytest.fixture
def sample_metadata():
    """Sample AKF metadata for testing."""
    return {
        "akf": "1.0",
        "classification": "internal",
        "overall_trust": 0.9,
        "ai_contribution": 0.3,
        "claims": [
            {
                "location": "sheet:Sheet1,row:1",
                "c": "Q3 Revenue: $4,200,000",
                "t": 0.98,
                "src": "erp-system",
                "ai": False,
                "tier": 1,
                "ver": True,
            },
            {
                "location": "sheet:Sheet1,row:2",
                "c": "Projected Q4: $4,500,000",
                "t": 0.65,
                "src": "forecast-model",
                "ai": True,
                "tier": 3,
            },
        ],
        "provenance": [
            {
                "actor": "data-pipeline",
                "action": "generated",
                "at": "2025-01-15T10:00:00Z",
            }
        ],
    }


class TestXLSXHandler:
    """Tests for XLSXHandler class attributes."""

    def test_format_name(self):
        handler = XLSXHandler()
        assert handler.FORMAT_NAME == "XLSX"

    def test_extensions(self):
        handler = XLSXHandler()
        assert handler.EXTENSIONS == [".xlsx"]

    def test_mode(self):
        handler = XLSXHandler()
        assert handler.MODE == "embedded"

    def test_mechanism(self):
        handler = XLSXHandler()
        assert handler.MECHANISM == "OOXML Custom XML Part"

    def test_no_required_dependencies(self):
        handler = XLSXHandler()
        assert handler.DEPENDENCIES == []


class TestEmbedExtract:
    """Tests for embed/extract round-trip operations."""

    def test_embed_and_extract_round_trip(self, xlsx_file, sample_metadata):
        """Embed metadata then extract it — should get identical data back."""
        embed(xlsx_file, sample_metadata)
        result = extract(xlsx_file)

        assert result is not None
        assert result["akf"] == "1.0"
        assert result["classification"] == "internal"
        assert result["overall_trust"] == 0.9
        assert len(result["claims"]) == 2
        assert result["claims"][0]["c"] == "Q3 Revenue: $4,200,000"
        assert result["claims"][0]["ver"] is True
        assert result["claims"][1]["location"] == "sheet:Sheet1,row:2"

    def test_extract_from_non_enriched(self, xlsx_file):
        """Extracting from an XLSX without AKF metadata should return None."""
        result = extract(xlsx_file)
        assert result is None

    def test_embed_preserves_original_entries(self, xlsx_file, sample_metadata):
        """Embedding should preserve all original ZIP entries."""
        with zipfile.ZipFile(xlsx_file, "r") as z:
            original_entries = set(z.namelist())

        embed(xlsx_file, sample_metadata)

        with zipfile.ZipFile(xlsx_file, "r") as z:
            new_entries = set(z.namelist())

        assert original_entries.issubset(new_entries)
        assert AKF_JSON_PATH in new_entries
        assert AKF_XML_PATH in new_entries

    def test_embed_preserves_worksheet_content(self, xlsx_file, sample_metadata):
        """Embedding should preserve the worksheet XML content."""
        with zipfile.ZipFile(xlsx_file, "r") as z:
            original_sheet = z.read("xl/worksheets/sheet1.xml")

        embed(xlsx_file, sample_metadata)

        with zipfile.ZipFile(xlsx_file, "r") as z:
            new_sheet = z.read("xl/worksheets/sheet1.xml")

        assert original_sheet == new_sheet

    def test_re_embed_replaces_metadata(self, xlsx_file, sample_metadata):
        """Re-embedding should replace existing AKF metadata."""
        embed(xlsx_file, sample_metadata)

        updated_meta = {
            "akf": "1.0",
            "classification": "public",
            "overall_trust": 0.99,
            "claims": [{"c": "Updated data", "t": 0.99}],
        }
        embed(xlsx_file, updated_meta)

        result = extract(xlsx_file)
        assert result is not None
        assert result["classification"] == "public"
        assert result["overall_trust"] == 0.99
        assert len(result["claims"]) == 1

    def test_re_embed_no_duplicate_entries(self, xlsx_file, sample_metadata):
        """Re-embedding should not create duplicate AKF entries."""
        embed(xlsx_file, sample_metadata)
        embed(xlsx_file, sample_metadata)

        with zipfile.ZipFile(xlsx_file, "r") as z:
            names = z.namelist()
            assert names.count(AKF_JSON_PATH) == 1
            assert names.count(AKF_XML_PATH) == 1


class TestIsEnriched:
    """Tests for is_enriched()."""

    def test_not_enriched_initially(self, xlsx_file):
        assert is_enriched(xlsx_file) is False

    def test_enriched_after_embed(self, xlsx_file, sample_metadata):
        embed(xlsx_file, sample_metadata)
        assert is_enriched(xlsx_file) is True


class TestScan:
    """Tests for scan()."""

    def test_scan_non_enriched(self, xlsx_file):
        """Scanning a non-enriched file returns a basic ScanReport."""
        report = scan(xlsx_file)
        assert isinstance(report, ScanReport)
        assert report.enriched is False
        assert report.format == "XLSX"
        assert report.mode == "embedded"

    def test_scan_enriched(self, xlsx_file, sample_metadata):
        """Scanning an enriched file returns a detailed ScanReport."""
        embed(xlsx_file, sample_metadata)
        report = scan(xlsx_file)

        assert report.enriched is True
        assert report.format == "XLSX"
        assert report.classification == "internal"
        assert report.overall_trust == 0.9
        assert report.claim_count == 2
        assert report.ai_claim_count == 1
        assert report.verified_claim_count == 1
        assert report.provenance_depth == 1


class TestEdgeCases:
    """Tests for edge cases."""

    def test_embed_empty_metadata(self, xlsx_file):
        embed(xlsx_file, {})
        result = extract(xlsx_file)
        assert result == {}

    def test_extract_from_nonexistent_file(self):
        result = extract("/nonexistent/path/file.xlsx")
        assert result is None

    def test_is_enriched_nonexistent_file(self):
        assert is_enriched("/nonexistent/path/file.xlsx") is False

    def test_file_remains_valid_zip_after_embed(self, xlsx_file, sample_metadata):
        embed(xlsx_file, sample_metadata)
        with zipfile.ZipFile(xlsx_file, "r") as z:
            bad = z.testzip()
            assert bad is None

    def test_spreadsheet_location_claims(self, xlsx_file):
        """Claims with spreadsheet-specific location fields should round-trip."""
        meta = {
            "akf": "1.0",
            "claims": [
                {
                    "location": "sheet:Sheet1,row:1",
                    "c": "Header row data",
                    "t": 0.95,
                },
                {
                    "location": "sheet:Sheet1,row:10",
                    "c": "Total: $42,000",
                    "t": 0.99,
                    "ver": True,
                },
                {
                    "location": "sheet:Projections,row:3",
                    "c": "Forecast value",
                    "t": 0.6,
                    "ai": True,
                    "risk": "projection",
                },
            ],
        }
        embed(xlsx_file, meta)
        result = extract(xlsx_file)
        assert len(result["claims"]) == 3
        assert result["claims"][2]["risk"] == "projection"


class TestAutoEnrich:
    """Tests for auto_enrich (basic mode, without openpyxl)."""

    def test_auto_enrich_basic(self, xlsx_file):
        handler = XLSXHandler()
        handler.auto_enrich(xlsx_file, agent_id="data-agent")

        result = extract(xlsx_file)
        assert result is not None
        assert result["akf"] == "1.0"
        assert result["ai_contribution"] == 1.0
        assert "provenance" in result
        assert result["provenance"][0]["actor"] == "data-agent"

    def test_auto_enrich_with_classification(self, xlsx_file):
        handler = XLSXHandler()
        handler.auto_enrich(
            xlsx_file,
            agent_id="data-agent",
            classification="restricted",
        )
        result = extract(xlsx_file)
        assert result["classification"] == "restricted"
