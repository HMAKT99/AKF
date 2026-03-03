"""Tests for AKF PDF format handler."""

import base64
import json
import os
import tempfile
from typing import Dict
from unittest import mock

import pytest

from akf.formats.pdf import PDFHandler, embed, extract, is_enriched, scan


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def create_minimal_pdf(path: str) -> None:
    """Create a minimal valid PDF for testing."""
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n"
        b"0 4\n"
        b"0000000000 65535 f \n"
        b"0000000010 00000 n \n"
        b"0000000059 00000 n \n"
        b"0000000112 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n"
        b"190\n"
        b"%%EOF"
    )
    with open(path, "wb") as f:
        f.write(pdf_content)


SAMPLE_METADATA = {
    "akf": "1.0",
    "classification": "internal",
    "overall_trust": 0.85,
    "ai_contribution": 0.3,
    "claims": [
        {"c": "Revenue $4.2B", "t": 0.95, "ai": False, "ver": True},
        {"c": "Generated summary", "t": 0.7, "ai": True, "ver": False},
    ],
    "provenance": [
        {"actor": "analyst@corp.com", "action": "reviewed", "at": "2026-01-01T00:00:00Z"}
    ],
}


# ------------------------------------------------------------------
# Handler unit tests
# ------------------------------------------------------------------

class TestPDFHandlerAttributes:
    def test_format_name(self) -> None:
        h = PDFHandler()
        assert h.FORMAT_NAME == "PDF"

    def test_extensions(self) -> None:
        h = PDFHandler()
        assert ".pdf" in h.EXTENSIONS

    def test_mode(self) -> None:
        h = PDFHandler()
        assert h.MODE == "embedded"

    def test_mechanism(self) -> None:
        h = PDFHandler()
        assert h.MECHANISM == "XMP Metadata"

    def test_dependencies(self) -> None:
        h = PDFHandler()
        assert "pypdf" in h.DEPENDENCIES


# ------------------------------------------------------------------
# Sidecar fallback (works regardless of pypdf availability)
# ------------------------------------------------------------------

class TestPDFSidecarFallback:
    """Verify sidecar fallback when pypdf is not installed."""

    def test_embed_creates_sidecar_when_pypdf_missing(self) -> None:
        import akf.formats.pdf as pdf_mod

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")
            create_minimal_pdf(pdf_path)

            # Temporarily force _HAS_PYPDF to False
            old_val = pdf_mod._HAS_PYPDF
            try:
                pdf_mod._HAS_PYPDF = False

                handler = PDFHandler()
                handler.embed(pdf_path, SAMPLE_METADATA)

                sidecar = pdf_path + ".akf.json"
                assert os.path.isfile(sidecar), "Sidecar file should be created"

                with open(sidecar, "r", encoding="utf-8") as f:
                    data = json.load(f)
                assert data.get("akf") == "1.0"
                assert data.get("classification") == "internal"
            finally:
                pdf_mod._HAS_PYPDF = old_val

    def test_extract_reads_sidecar_when_pypdf_missing(self) -> None:
        import akf.formats.pdf as pdf_mod

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")
            create_minimal_pdf(pdf_path)

            old_val = pdf_mod._HAS_PYPDF
            try:
                pdf_mod._HAS_PYPDF = False

                handler = PDFHandler()
                handler.embed(pdf_path, SAMPLE_METADATA)

                result = handler.extract(pdf_path)
                assert result is not None
                assert result.get("classification") == "internal"
            finally:
                pdf_mod._HAS_PYPDF = old_val

    def test_is_enriched_false_for_plain_pdf(self) -> None:
        import akf.formats.pdf as pdf_mod

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "plain.pdf")
            create_minimal_pdf(pdf_path)

            old_val = pdf_mod._HAS_PYPDF
            try:
                pdf_mod._HAS_PYPDF = False

                handler = PDFHandler()
                assert handler.is_enriched(pdf_path) is False
            finally:
                pdf_mod._HAS_PYPDF = old_val


# ------------------------------------------------------------------
# Native pypdf round-trip (skipped if pypdf not installed)
# ------------------------------------------------------------------

def _has_pypdf() -> bool:
    try:
        import pypdf  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _has_pypdf(), reason="pypdf not installed")
class TestPDFNative:
    """Test native embedding with pypdf."""

    def test_embed_extract_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "roundtrip.pdf")
            create_minimal_pdf(pdf_path)

            handler = PDFHandler()
            handler.embed(pdf_path, SAMPLE_METADATA)

            result = handler.extract(pdf_path)
            assert result is not None
            assert result["akf"] == "1.0"
            assert result["classification"] == "internal"
            assert result["overall_trust"] == 0.85
            assert len(result["claims"]) == 2

    def test_is_enriched_after_embed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "enriched.pdf")
            create_minimal_pdf(pdf_path)

            handler = PDFHandler()
            assert handler.is_enriched(pdf_path) is False

            handler.embed(pdf_path, SAMPLE_METADATA)
            assert handler.is_enriched(pdf_path) is True

    def test_extract_unenriched_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "plain.pdf")
            create_minimal_pdf(pdf_path)

            handler = PDFHandler()
            result = handler.extract(pdf_path)
            assert result is None

    def test_overwrite_existing_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "overwrite.pdf")
            create_minimal_pdf(pdf_path)

            handler = PDFHandler()
            handler.embed(pdf_path, SAMPLE_METADATA)

            updated = dict(SAMPLE_METADATA)
            updated["classification"] = "confidential"
            handler.embed(pdf_path, updated)

            result = handler.extract(pdf_path)
            assert result is not None
            assert result["classification"] == "confidential"


# ------------------------------------------------------------------
# Scan
# ------------------------------------------------------------------

class TestPDFScan:
    def test_scan_unenriched(self) -> None:
        import akf.formats.pdf as pdf_mod

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "scan.pdf")
            create_minimal_pdf(pdf_path)

            old_val = pdf_mod._HAS_PYPDF
            try:
                pdf_mod._HAS_PYPDF = False

                handler = PDFHandler()
                report = handler.scan(pdf_path)
                assert report.enriched is False
                assert report.format == "PDF"
            finally:
                pdf_mod._HAS_PYPDF = old_val

    def test_scan_enriched_via_sidecar(self) -> None:
        import akf.formats.pdf as pdf_mod

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "scan.pdf")
            create_minimal_pdf(pdf_path)

            old_val = pdf_mod._HAS_PYPDF
            try:
                pdf_mod._HAS_PYPDF = False

                handler = PDFHandler()
                handler.embed(pdf_path, SAMPLE_METADATA)
                report = handler.scan(pdf_path)
                assert report.enriched is True
                assert report.classification == "internal"
                assert report.claim_count == 2
                assert report.ai_claim_count == 1
                assert report.verified_claim_count == 1
            finally:
                pdf_mod._HAS_PYPDF = old_val


# ------------------------------------------------------------------
# Auto-enrich
# ------------------------------------------------------------------

class TestPDFAutoEnrich:
    def test_auto_enrich_creates_metadata(self) -> None:
        import akf.formats.pdf as pdf_mod

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "auto.pdf")
            create_minimal_pdf(pdf_path)

            old_val = pdf_mod._HAS_PYPDF
            try:
                pdf_mod._HAS_PYPDF = False

                handler = PDFHandler()
                handler.auto_enrich(pdf_path, "gpt-4", classification="internal")

                result = handler.extract(pdf_path)
                assert result is not None
                assert result["akf"] == "1.0"
                assert result["classification"] == "internal"
                assert result["ai_contribution"] == 1.0
            finally:
                pdf_mod._HAS_PYPDF = old_val


# ------------------------------------------------------------------
# Module-level convenience functions
# ------------------------------------------------------------------

class TestModuleFunctions:
    def test_module_embed_extract(self) -> None:
        import akf.formats.pdf as pdf_mod

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "modtest.pdf")
            create_minimal_pdf(pdf_path)

            old_val = pdf_mod._HAS_PYPDF
            try:
                pdf_mod._HAS_PYPDF = False

                embed(pdf_path, SAMPLE_METADATA)
                result = extract(pdf_path)
                assert result is not None
                assert result.get("classification") == "internal"

                assert is_enriched(pdf_path) is True
            finally:
                pdf_mod._HAS_PYPDF = old_val
