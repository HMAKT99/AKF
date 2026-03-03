"""Tests for the PPTX format handler.

Creates minimal valid PPTX files (ZIP archives with required OOXML parts)
to test embed/extract operations without needing python-pptx.
"""

import json
import os
import tempfile
import zipfile

import pytest

from akf.formats.pptx import PPTXHandler, embed, extract, is_enriched, scan
from akf.formats._ooxml import AKF_JSON_PATH, AKF_XML_PATH
from akf.formats.base import ScanReport


def create_minimal_pptx(path):
    """Create a minimal valid PPTX (ZIP with required XML parts)."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        # [Content_Types].xml
        z.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType='
            '"application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/ppt/presentation.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument'
            '.presentationml.presentation.main+xml"/>'
            '<Override PartName="/ppt/slides/slide1.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument'
            '.presentationml.slide+xml"/>'
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
            '/officeDocument" Target="ppt/presentation.xml"/>'
            "</Relationships>",
        )
        # ppt/presentation.xml
        z.writestr(
            "ppt/presentation.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
            ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            "<p:sldIdLst>"
            '<p:sldId id="256" r:id="rId2"/>'
            "</p:sldIdLst>"
            "</p:presentation>",
        )
        # ppt/_rels/presentation.xml.rels
        z.writestr(
            "ppt/_rels/presentation.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns='
            '"http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId2" Type='
            '"http://schemas.openxmlformats.org/officeDocument/2006/relationships'
            '/slide" Target="slides/slide1.xml"/>'
            "</Relationships>",
        )
        # ppt/slides/slide1.xml
        z.writestr(
            "ppt/slides/slide1.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"'
            ' xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            "<p:cSld><p:spTree>"
            '<p:sp><p:txBody><a:p><a:r><a:t>Slide Title</a:t></a:r></a:p></p:txBody></p:sp>'
            "</p:spTree></p:cSld>"
            "</p:sld>",
        )


@pytest.fixture
def pptx_file(tmp_path):
    """Create a temporary minimal PPTX file."""
    path = str(tmp_path / "test.pptx")
    create_minimal_pptx(path)
    return path


@pytest.fixture
def sample_metadata():
    """Sample AKF metadata for testing."""
    return {
        "akf": "1.0",
        "classification": "internal",
        "overall_trust": 0.8,
        "ai_contribution": 0.75,
        "claims": [
            {
                "location": "slide:1",
                "c": "Q3 2025 Financial Results",
                "t": 0.95,
                "src": "analyst-gpt",
                "ai": True,
                "tier": 2,
            },
            {
                "location": "slide:2",
                "c": "Revenue grew 15% YoY to $4.2B",
                "t": 0.88,
                "src": "erp-extract",
                "ai": False,
                "tier": 1,
                "ver": True,
            },
            {
                "location": "slide:3",
                "c": "Market outlook remains positive",
                "t": 0.6,
                "src": "analyst-gpt",
                "ai": True,
                "tier": 3,
            },
        ],
        "provenance": [
            {
                "actor": "presentation-builder",
                "action": "generated",
                "at": "2025-01-15T10:00:00Z",
            }
        ],
    }


class TestPPTXHandler:
    """Tests for PPTXHandler class attributes."""

    def test_format_name(self):
        handler = PPTXHandler()
        assert handler.FORMAT_NAME == "PPTX"

    def test_extensions(self):
        handler = PPTXHandler()
        assert handler.EXTENSIONS == [".pptx"]

    def test_mode(self):
        handler = PPTXHandler()
        assert handler.MODE == "embedded"

    def test_mechanism(self):
        handler = PPTXHandler()
        assert handler.MECHANISM == "OOXML Custom XML Part"

    def test_no_required_dependencies(self):
        handler = PPTXHandler()
        assert handler.DEPENDENCIES == []


class TestEmbedExtract:
    """Tests for embed/extract round-trip operations."""

    def test_embed_and_extract_round_trip(self, pptx_file, sample_metadata):
        """Embed metadata then extract it — should get identical data back."""
        embed(pptx_file, sample_metadata)
        result = extract(pptx_file)

        assert result is not None
        assert result["akf"] == "1.0"
        assert result["classification"] == "internal"
        assert result["overall_trust"] == 0.8
        assert len(result["claims"]) == 3
        assert result["claims"][0]["location"] == "slide:1"
        assert result["claims"][1]["ver"] is True

    def test_extract_from_non_enriched(self, pptx_file):
        """Extracting from a PPTX without AKF metadata should return None."""
        result = extract(pptx_file)
        assert result is None

    def test_embed_preserves_original_entries(self, pptx_file, sample_metadata):
        """Embedding should preserve all original ZIP entries."""
        with zipfile.ZipFile(pptx_file, "r") as z:
            original_entries = set(z.namelist())

        embed(pptx_file, sample_metadata)

        with zipfile.ZipFile(pptx_file, "r") as z:
            new_entries = set(z.namelist())

        assert original_entries.issubset(new_entries)
        assert AKF_JSON_PATH in new_entries
        assert AKF_XML_PATH in new_entries

    def test_embed_preserves_slide_content(self, pptx_file, sample_metadata):
        """Embedding should preserve the slide XML content."""
        with zipfile.ZipFile(pptx_file, "r") as z:
            original_slide = z.read("ppt/slides/slide1.xml")

        embed(pptx_file, sample_metadata)

        with zipfile.ZipFile(pptx_file, "r") as z:
            new_slide = z.read("ppt/slides/slide1.xml")

        assert original_slide == new_slide

    def test_re_embed_replaces_metadata(self, pptx_file, sample_metadata):
        """Re-embedding should replace existing AKF metadata."""
        embed(pptx_file, sample_metadata)

        updated_meta = {
            "akf": "1.0",
            "classification": "public",
            "overall_trust": 0.95,
            "claims": [
                {"location": "slide:1", "c": "Updated slide content", "t": 0.9}
            ],
        }
        embed(pptx_file, updated_meta)

        result = extract(pptx_file)
        assert result is not None
        assert result["classification"] == "public"
        assert len(result["claims"]) == 1

    def test_re_embed_no_duplicate_entries(self, pptx_file, sample_metadata):
        """Re-embedding should not create duplicate AKF entries."""
        embed(pptx_file, sample_metadata)
        embed(pptx_file, sample_metadata)

        with zipfile.ZipFile(pptx_file, "r") as z:
            names = z.namelist()
            assert names.count(AKF_JSON_PATH) == 1
            assert names.count(AKF_XML_PATH) == 1


class TestIsEnriched:
    """Tests for is_enriched()."""

    def test_not_enriched_initially(self, pptx_file):
        assert is_enriched(pptx_file) is False

    def test_enriched_after_embed(self, pptx_file, sample_metadata):
        embed(pptx_file, sample_metadata)
        assert is_enriched(pptx_file) is True


class TestScan:
    """Tests for scan()."""

    def test_scan_non_enriched(self, pptx_file):
        """Scanning a non-enriched file returns a basic ScanReport."""
        report = scan(pptx_file)
        assert isinstance(report, ScanReport)
        assert report.enriched is False
        assert report.format == "PPTX"
        assert report.mode == "embedded"

    def test_scan_enriched(self, pptx_file, sample_metadata):
        """Scanning an enriched file returns a detailed ScanReport."""
        embed(pptx_file, sample_metadata)
        report = scan(pptx_file)

        assert report.enriched is True
        assert report.format == "PPTX"
        assert report.classification == "internal"
        assert report.overall_trust == 0.8
        assert report.claim_count == 3
        assert report.ai_claim_count == 2
        assert report.verified_claim_count == 1
        assert report.provenance_depth == 1

    def test_scan_with_risk_claims(self, pptx_file):
        """Scan should identify risk-flagged claims."""
        meta = {
            "akf": "1.0",
            "claims": [
                {
                    "location": "slide:1",
                    "c": "Optimistic market forecast",
                    "t": 0.4,
                    "ai": True,
                    "risk": "speculation",
                },
                {
                    "location": "slide:2",
                    "c": "Verified revenue data",
                    "t": 0.98,
                    "ver": True,
                },
            ],
        }
        embed(pptx_file, meta)
        report = scan(pptx_file)

        assert report.claim_count == 2
        assert len(report.risk_claims) == 1
        assert "Optimistic market forecast" in report.risk_claims[0]


class TestEdgeCases:
    """Tests for edge cases."""

    def test_embed_empty_metadata(self, pptx_file):
        embed(pptx_file, {})
        result = extract(pptx_file)
        assert result == {}

    def test_extract_from_nonexistent_file(self):
        result = extract("/nonexistent/path/file.pptx")
        assert result is None

    def test_is_enriched_nonexistent_file(self):
        assert is_enriched("/nonexistent/path/file.pptx") is False

    def test_file_remains_valid_zip_after_embed(self, pptx_file, sample_metadata):
        embed(pptx_file, sample_metadata)
        with zipfile.ZipFile(pptx_file, "r") as z:
            bad = z.testzip()
            assert bad is None

    def test_slide_location_claims(self, pptx_file):
        """Claims with slide-specific location fields should round-trip."""
        meta = {
            "akf": "1.0",
            "claims": [
                {
                    "location": "slide:1",
                    "c": "Title slide content",
                    "t": 0.95,
                },
                {
                    "location": "slide:5",
                    "c": "Conclusion and next steps",
                    "t": 0.8,
                    "ai": True,
                },
            ],
        }
        embed(pptx_file, meta)
        result = extract(pptx_file)
        assert len(result["claims"]) == 2
        assert result["claims"][0]["location"] == "slide:1"
        assert result["claims"][1]["location"] == "slide:5"

    def test_embed_large_presentation_metadata(self, pptx_file):
        """Embedding metadata for a large presentation should work."""
        claims = []
        for i in range(50):
            claims.append(
                {
                    "location": "slide:{}".format(i + 1),
                    "c": "Content for slide {}".format(i + 1),
                    "t": 0.5 + (i % 50) / 100.0,
                    "ai": i % 2 == 0,
                    "tier": (i % 5) + 1,
                }
            )
        meta = {"akf": "1.0", "claims": claims}
        embed(pptx_file, meta)
        result = extract(pptx_file)
        assert result is not None
        assert len(result["claims"]) == 50


class TestAutoEnrich:
    """Tests for auto_enrich (basic mode, without python-pptx)."""

    def test_auto_enrich_basic(self, pptx_file):
        handler = PPTXHandler()
        handler.auto_enrich(pptx_file, agent_id="slide-agent")

        result = extract(pptx_file)
        assert result is not None
        assert result["akf"] == "1.0"
        assert result["ai_contribution"] == 1.0
        assert "provenance" in result
        assert result["provenance"][0]["actor"] == "slide-agent"

    def test_auto_enrich_with_classification(self, pptx_file):
        handler = PPTXHandler()
        handler.auto_enrich(
            pptx_file,
            agent_id="slide-agent",
            classification="confidential",
        )
        result = extract(pptx_file)
        assert result["classification"] == "confidential"
