"""Tests for the DOCX format handler.

Creates minimal valid DOCX files (ZIP archives with required OOXML parts)
to test embed/extract operations without needing python-docx.
"""

import json
import os
import tempfile
import zipfile

import pytest

from akf.formats.docx import DOCXHandler, embed, extract, is_enriched, scan
from akf.formats._ooxml import AKF_JSON_PATH, AKF_XML_PATH
from akf.formats.base import ScanReport


def create_minimal_docx(path):
    """Create a minimal valid DOCX (ZIP with required XML parts)."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        # [Content_Types].xml
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType='
            '"application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument'
            '.wordprocessingml.document.main+xml"/>'
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
            '/officeDocument" Target="word/document.xml"/>'
            "</Relationships>",
        )
        # word/document.xml
        z.writestr(
            "word/document.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w='
            '"http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            "<w:body><w:p><w:r><w:t>Hello World</w:t></w:r></w:p></w:body>"
            "</w:document>",
        )


@pytest.fixture
def docx_file(tmp_path):
    """Create a temporary minimal DOCX file."""
    path = str(tmp_path / "test.docx")
    create_minimal_docx(path)
    return path


@pytest.fixture
def sample_metadata():
    """Sample AKF metadata for testing."""
    return {
        "akf": "1.0",
        "classification": "public",
        "overall_trust": 0.85,
        "ai_contribution": 0.5,
        "claims": [
            {
                "location": "paragraph:0",
                "c": "Revenue was $4.2 billion in Q3",
                "t": 0.95,
                "src": "analyst-gpt",
                "ai": True,
                "tier": 2,
            },
            {
                "c": "Growth rate exceeded expectations",
                "t": 0.78,
                "src": "human-reviewer",
                "ai": False,
                "tier": 1,
                "ver": True,
            },
        ],
        "provenance": [
            {
                "actor": "analyst-gpt",
                "action": "generated",
                "at": "2025-01-15T10:00:00Z",
                "hash": "sha256:abc123",
            }
        ],
        "integrity_hash": "sha256:abc123",
    }


class TestDOCXHandler:
    """Tests for DOCXHandler class attributes and interface."""

    def test_format_name(self):
        handler = DOCXHandler()
        assert handler.FORMAT_NAME == "DOCX"

    def test_extensions(self):
        handler = DOCXHandler()
        assert handler.EXTENSIONS == [".docx"]

    def test_mode(self):
        handler = DOCXHandler()
        assert handler.MODE == "embedded"

    def test_mechanism(self):
        handler = DOCXHandler()
        assert handler.MECHANISM == "OOXML Custom XML Part"

    def test_no_required_dependencies(self):
        handler = DOCXHandler()
        assert handler.DEPENDENCIES == []


class TestEmbedExtract:
    """Tests for embed/extract round-trip operations."""

    def test_embed_and_extract_round_trip(self, docx_file, sample_metadata):
        """Embed metadata then extract it — should get identical data back."""
        embed(docx_file, sample_metadata)
        result = extract(docx_file)

        assert result is not None
        assert result["akf"] == "1.0"
        assert result["classification"] == "public"
        assert result["overall_trust"] == 0.85
        assert len(result["claims"]) == 2
        assert result["claims"][0]["c"] == "Revenue was $4.2 billion in Q3"
        assert result["claims"][0]["t"] == 0.95
        assert result["claims"][1]["ver"] is True

    def test_extract_from_non_enriched(self, docx_file):
        """Extracting from a DOCX without AKF metadata should return None."""
        result = extract(docx_file)
        assert result is None

    def test_embed_preserves_original_entries(self, docx_file, sample_metadata):
        """Embedding should preserve all original ZIP entries."""
        # Record original entries
        with zipfile.ZipFile(docx_file, "r") as z:
            original_entries = set(z.namelist())

        embed(docx_file, sample_metadata)

        # Check that all original entries are still present
        with zipfile.ZipFile(docx_file, "r") as z:
            new_entries = set(z.namelist())

        assert original_entries.issubset(new_entries)
        # Plus the two new AKF entries
        assert AKF_JSON_PATH in new_entries
        assert AKF_XML_PATH in new_entries

    def test_embed_preserves_original_content(self, docx_file, sample_metadata):
        """Embedding should preserve the content of original ZIP entries."""
        # Read original content
        with zipfile.ZipFile(docx_file, "r") as z:
            original_doc = z.read("word/document.xml")

        embed(docx_file, sample_metadata)

        # Read content after embedding
        with zipfile.ZipFile(docx_file, "r") as z:
            new_doc = z.read("word/document.xml")

        assert original_doc == new_doc

    def test_re_embed_replaces_metadata(self, docx_file, sample_metadata):
        """Re-embedding should replace existing AKF metadata."""
        embed(docx_file, sample_metadata)

        updated_meta = {
            "akf": "1.0",
            "classification": "internal",
            "overall_trust": 0.5,
            "claims": [{"c": "Updated claim", "t": 0.6}],
        }
        embed(docx_file, updated_meta)

        result = extract(docx_file)
        assert result is not None
        assert result["classification"] == "internal"
        assert result["overall_trust"] == 0.5
        assert len(result["claims"]) == 1
        assert result["claims"][0]["c"] == "Updated claim"

    def test_re_embed_no_duplicate_entries(self, docx_file, sample_metadata):
        """Re-embedding should not create duplicate AKF entries in the ZIP."""
        embed(docx_file, sample_metadata)
        embed(docx_file, sample_metadata)

        with zipfile.ZipFile(docx_file, "r") as z:
            names = z.namelist()
            assert names.count(AKF_JSON_PATH) == 1
            assert names.count(AKF_XML_PATH) == 1

    def test_embed_unicode_content(self, docx_file):
        """Embedding metadata with unicode content should work correctly."""
        meta = {
            "akf": "1.0",
            "claims": [
                {"c": "Umsatz betrug 4,2 Mrd. Euro", "t": 0.9},
                {"c": "Revenue in Japanese: \u58f2\u4e0a\u9ad8", "t": 0.8},
            ],
        }
        embed(docx_file, meta)
        result = extract(docx_file)
        assert result is not None
        assert result["claims"][0]["c"] == "Umsatz betrug 4,2 Mrd. Euro"
        assert "\u58f2\u4e0a\u9ad8" in result["claims"][1]["c"]


class TestIsEnriched:
    """Tests for is_enriched()."""

    def test_not_enriched_initially(self, docx_file):
        assert is_enriched(docx_file) is False

    def test_enriched_after_embed(self, docx_file, sample_metadata):
        embed(docx_file, sample_metadata)
        assert is_enriched(docx_file) is True


class TestScan:
    """Tests for scan()."""

    def test_scan_non_enriched(self, docx_file):
        """Scanning a non-enriched file should return a basic ScanReport."""
        report = scan(docx_file)
        assert isinstance(report, ScanReport)
        assert report.enriched is False
        assert report.format == "DOCX"
        assert report.mode == "embedded"

    def test_scan_enriched(self, docx_file, sample_metadata):
        """Scanning an enriched file should return a detailed ScanReport."""
        embed(docx_file, sample_metadata)
        report = scan(docx_file)

        assert report.enriched is True
        assert report.format == "DOCX"
        assert report.classification == "public"
        assert report.overall_trust == 0.85
        assert report.claim_count == 2
        assert report.ai_claim_count == 1
        assert report.verified_claim_count == 1
        assert report.provenance_depth == 1

    def test_scan_with_risk_claims(self, docx_file):
        """Scan should identify risk-flagged claims."""
        meta = {
            "akf": "1.0",
            "claims": [
                {"c": "Unverified financial projection", "t": 0.3, "risk": "speculation"},
                {"c": "Solid historical data", "t": 0.95},
            ],
        }
        embed(docx_file, meta)
        report = scan(docx_file)

        assert report.claim_count == 2
        assert len(report.risk_claims) == 1
        assert "Unverified financial projection" in report.risk_claims[0]


class TestXMLWrapper:
    """Tests for the XML wrapper stored alongside the JSON."""

    def test_xml_wrapper_exists(self, docx_file, sample_metadata):
        """After embedding, the XML wrapper should exist in the ZIP."""
        embed(docx_file, sample_metadata)
        with zipfile.ZipFile(docx_file, "r") as z:
            assert AKF_XML_PATH in z.namelist()
            xml_content = z.read(AKF_XML_PATH).decode("utf-8")
            assert "akf:metadata" in xml_content
            assert "https://akf.dev/v1" in xml_content
            assert "CDATA" in xml_content

    def test_xml_wrapper_contains_json(self, docx_file, sample_metadata):
        """The XML wrapper should contain the same JSON as the direct file."""
        embed(docx_file, sample_metadata)
        with zipfile.ZipFile(docx_file, "r") as z:
            json_data = json.loads(z.read(AKF_JSON_PATH))
            xml_content = z.read(AKF_XML_PATH).decode("utf-8")
            # The JSON should appear inside the CDATA section
            assert json.dumps(json_data["akf"]) is not None


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_embed_empty_metadata(self, docx_file):
        """Embedding empty metadata dict should work."""
        embed(docx_file, {})
        result = extract(docx_file)
        assert result == {}

    def test_embed_minimal_metadata(self, docx_file):
        """Embedding minimal valid AKF metadata should work."""
        meta = {"akf": "1.0", "claims": []}
        embed(docx_file, meta)
        result = extract(docx_file)
        assert result["akf"] == "1.0"
        assert result["claims"] == []

    def test_extract_from_nonexistent_file(self):
        """Extracting from a non-existent file should return None."""
        result = extract("/nonexistent/path/file.docx")
        assert result is None

    def test_is_enriched_nonexistent_file(self):
        """is_enriched on a non-existent file should return False."""
        assert is_enriched("/nonexistent/path/file.docx") is False

    def test_embed_large_metadata(self, docx_file):
        """Embedding large metadata should work correctly."""
        claims = []
        for i in range(100):
            claims.append(
                {
                    "c": "Claim number {} with some detailed text content".format(i),
                    "t": 0.5 + (i % 50) / 100.0,
                    "ai": True,
                    "tier": (i % 5) + 1,
                }
            )
        meta = {"akf": "1.0", "claims": claims}
        embed(docx_file, meta)
        result = extract(docx_file)
        assert result is not None
        assert len(result["claims"]) == 100

    def test_file_remains_valid_zip_after_embed(self, docx_file, sample_metadata):
        """After embedding, the file should still be a valid ZIP archive."""
        embed(docx_file, sample_metadata)
        # This should not raise
        with zipfile.ZipFile(docx_file, "r") as z:
            bad = z.testzip()
            assert bad is None  # None means no bad files

    def test_claims_with_location_fields(self, docx_file):
        """Claims with location fields should round-trip correctly."""
        meta = {
            "akf": "1.0",
            "claims": [
                {
                    "location": "paragraph:0",
                    "c": "First paragraph claim",
                    "t": 0.9,
                    "src": "gpt-4",
                    "ai": True,
                },
                {
                    "location": "paragraph:5",
                    "c": "Later paragraph claim",
                    "t": 0.75,
                    "src": "human",
                    "ai": False,
                    "ver": True,
                    "ver_by": "editor@example.com",
                },
            ],
        }
        embed(docx_file, meta)
        result = extract(docx_file)
        assert result["claims"][0]["location"] == "paragraph:0"
        assert result["claims"][1]["location"] == "paragraph:5"
        assert result["claims"][1]["ver_by"] == "editor@example.com"


class TestAutoEnrich:
    """Tests for auto_enrich (basic mode, without python-docx)."""

    def test_auto_enrich_basic(self, docx_file):
        """auto_enrich should at minimum embed basic metadata."""
        handler = DOCXHandler()
        handler.auto_enrich(docx_file, agent_id="test-agent")

        result = extract(docx_file)
        assert result is not None
        assert result["akf"] == "1.0"
        assert result["ai_contribution"] == 1.0
        assert "provenance" in result
        assert result["provenance"][0]["actor"] == "test-agent"
        assert "integrity_hash" in result

    def test_auto_enrich_with_classification(self, docx_file):
        """auto_enrich should include classification when provided."""
        handler = DOCXHandler()
        handler.auto_enrich(
            docx_file,
            agent_id="test-agent",
            classification="confidential",
        )
        result = extract(docx_file)
        assert result["classification"] == "confidential"

    def test_auto_enrich_with_custom_tier(self, docx_file):
        """auto_enrich should respect the default_tier parameter."""
        handler = DOCXHandler()
        handler.auto_enrich(docx_file, agent_id="test-agent", default_tier=4)

        result = extract(docx_file)
        assert result is not None
        assert result["overall_trust"] == 0.7
