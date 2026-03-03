"""Tests for AKF Image format handler."""

import json
import os
import struct
import tempfile
import zlib
from typing import List
from unittest import mock

import pytest

from akf.formats.image import ImageHandler, embed, extract, is_enriched, scan, scan_directory


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _has_pillow() -> bool:
    try:
        from PIL import Image  # noqa: F401
        return True
    except ImportError:
        return False


def create_test_png_pillow(path: str) -> bool:
    """Create a 1x1 red PNG via Pillow. Returns True on success."""
    try:
        from PIL import Image
        img = Image.new("RGB", (1, 1), color="red")
        img.save(path)
        return True
    except ImportError:
        return False


def create_test_png_raw(path: str) -> None:
    """Create a minimal 1x1 white PNG using raw bytes (no dependencies)."""
    # PNG signature
    sig = b"\x89PNG\r\n\x1a\n"

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        length = struct.pack(">I", len(data))
        return length + c + crc

    # IHDR: 1x1, 8-bit RGB
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = _chunk(b"IHDR", ihdr_data)

    # IDAT: single white pixel (filter byte 0, then R=255, G=255, B=255)
    raw_row = b"\x00\xff\xff\xff"
    compressed = zlib.compress(raw_row)
    idat = _chunk(b"IDAT", compressed)

    # IEND
    iend = _chunk(b"IEND", b"")

    with open(path, "wb") as f:
        f.write(sig + ihdr + idat + iend)


def create_test_png(path: str) -> None:
    """Create a test PNG, preferring Pillow but falling back to raw bytes."""
    if not create_test_png_pillow(path):
        create_test_png_raw(path)


def create_test_jpeg(path: str) -> None:
    """Create a minimal JPEG test file (or via Pillow if available)."""
    try:
        from PIL import Image
        img = Image.new("RGB", (1, 1), color="blue")
        img.save(path, format="JPEG")
    except ImportError:
        # Minimal JPEG stub -- just enough to be recognized as a file
        # SOI + APP0 (JFIF) + EOI
        with open(path, "wb") as f:
            f.write(
                b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01"
                b"\x00\x01\x00\x00\xff\xd9"
            )


SAMPLE_METADATA = {
    "akf": "1.0",
    "classification": "public",
    "overall_trust": 0.9,
    "ai_contribution": 0.5,
    "claims": [
        {"c": "Photo of storefront", "t": 0.99, "ai": False, "ver": True},
        {"c": "AI-enhanced colors", "t": 0.6, "ai": True, "ver": False},
    ],
    "provenance": [
        {"actor": "photographer", "action": "captured", "at": "2026-02-01T00:00:00Z"}
    ],
}


# ------------------------------------------------------------------
# Handler attributes
# ------------------------------------------------------------------

class TestImageHandlerAttributes:
    def test_format_name(self) -> None:
        h = ImageHandler()
        assert h.FORMAT_NAME == "Image"

    def test_extensions(self) -> None:
        h = ImageHandler()
        assert ".png" in h.EXTENSIONS
        assert ".jpg" in h.EXTENSIONS
        assert ".jpeg" in h.EXTENSIONS

    def test_dependencies(self) -> None:
        h = ImageHandler()
        assert "Pillow" in h.DEPENDENCIES


# ------------------------------------------------------------------
# PNG native round-trip (requires Pillow)
# ------------------------------------------------------------------

@pytest.mark.skipif(not _has_pillow(), reason="Pillow not installed")
class TestImagePNGNative:
    """Test PNG embedding via Pillow tEXt chunk."""

    def test_embed_extract_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = os.path.join(tmpdir, "test.png")
            create_test_png(png_path)

            handler = ImageHandler()
            handler.embed(png_path, SAMPLE_METADATA)

            result = handler.extract(png_path)
            assert result is not None
            assert result["akf"] == "1.0"
            assert result["classification"] == "public"
            assert len(result["claims"]) == 2

    def test_is_enriched_after_embed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = os.path.join(tmpdir, "test.png")
            create_test_png(png_path)

            handler = ImageHandler()
            assert handler.is_enriched(png_path) is False

            handler.embed(png_path, SAMPLE_METADATA)
            assert handler.is_enriched(png_path) is True

    def test_extract_unenriched_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = os.path.join(tmpdir, "plain.png")
            create_test_png(png_path)

            handler = ImageHandler()
            result = handler.extract(png_path)
            assert result is None

    def test_preserves_existing_text_chunks(self) -> None:
        from PIL import Image
        from PIL.PngImagePlugin import PngInfo

        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = os.path.join(tmpdir, "chunks.png")
            img = Image.new("RGB", (1, 1), color="green")
            info = PngInfo()
            info.add_text("author", "Test Author")
            img.save(png_path, pnginfo=info)

            handler = ImageHandler()
            handler.embed(png_path, SAMPLE_METADATA)

            # Re-open and verify both chunks exist
            img2 = Image.open(png_path)
            assert img2.text.get("author") == "Test Author"
            assert "akf" in img2.text

    def test_overwrite_existing_akf(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = os.path.join(tmpdir, "overwrite.png")
            create_test_png(png_path)

            handler = ImageHandler()
            handler.embed(png_path, SAMPLE_METADATA)

            updated = dict(SAMPLE_METADATA)
            updated["classification"] = "confidential"
            handler.embed(png_path, updated)

            result = handler.extract(png_path)
            assert result is not None
            assert result["classification"] == "confidential"


# ------------------------------------------------------------------
# Sidecar fallback
# ------------------------------------------------------------------

class TestImageSidecarFallback:
    """Test sidecar fallback for non-PNG or missing Pillow."""

    def test_jpeg_uses_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            jpeg_path = os.path.join(tmpdir, "test.jpg")
            create_test_jpeg(jpeg_path)

            handler = ImageHandler()
            handler.embed(jpeg_path, SAMPLE_METADATA)

            sidecar = jpeg_path + ".akf.json"
            assert os.path.isfile(sidecar), "JPEG should use sidecar"

            result = handler.extract(jpeg_path)
            assert result is not None
            assert result.get("classification") == "public"

    def test_png_sidecar_when_pillow_missing(self) -> None:
        import akf.formats.image as img_mod

        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = os.path.join(tmpdir, "test.png")
            create_test_png_raw(png_path)

            old_val = img_mod._HAS_PILLOW
            try:
                img_mod._HAS_PILLOW = False

                handler = ImageHandler()
                handler.embed(png_path, SAMPLE_METADATA)

                sidecar = png_path + ".akf.json"
                assert os.path.isfile(sidecar), "Should use sidecar without Pillow"

                result = handler.extract(png_path)
                assert result is not None
                assert result.get("classification") == "public"
            finally:
                img_mod._HAS_PILLOW = old_val

    def test_is_enriched_false_for_plain_jpeg(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            jpeg_path = os.path.join(tmpdir, "plain.jpg")
            create_test_jpeg(jpeg_path)

            handler = ImageHandler()
            assert handler.is_enriched(jpeg_path) is False


# ------------------------------------------------------------------
# Scan
# ------------------------------------------------------------------

class TestImageScan:
    def test_scan_unenriched(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            png_path = os.path.join(tmpdir, "scan.png")
            create_test_png(png_path)

            handler = ImageHandler()
            report = handler.scan(png_path)
            assert report.enriched is False
            assert report.format == "Image"

    def test_scan_enriched(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            jpeg_path = os.path.join(tmpdir, "scan.jpg")
            create_test_jpeg(jpeg_path)

            handler = ImageHandler()
            handler.embed(jpeg_path, SAMPLE_METADATA)

            report = handler.scan(jpeg_path)
            assert report.enriched is True
            assert report.claim_count == 2
            assert report.ai_claim_count == 1


# ------------------------------------------------------------------
# Directory scanning
# ------------------------------------------------------------------

class TestImageScanDirectory:
    def test_scan_directory_finds_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mixed files
            png_path = os.path.join(tmpdir, "photo.png")
            jpg_path = os.path.join(tmpdir, "photo.jpg")
            txt_path = os.path.join(tmpdir, "notes.txt")

            create_test_png(png_path)
            create_test_jpeg(jpg_path)
            with open(txt_path, "w") as f:
                f.write("not an image")

            handler = ImageHandler()
            handler.embed(jpg_path, SAMPLE_METADATA)

            results = handler.scan_directory(tmpdir)
            # Should find png and jpg, not txt
            assert len(results) == 2
            enriched = [r for r in results if r["enriched"]]
            assert len(enriched) == 1

    def test_scan_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            handler = ImageHandler()
            results = handler.scan_directory(tmpdir)
            assert results == []

    def test_scan_nonexistent_directory(self) -> None:
        handler = ImageHandler()
        results = handler.scan_directory("/nonexistent/path/xyz")
        assert results == []


# ------------------------------------------------------------------
# Auto-enrich
# ------------------------------------------------------------------

class TestImageAutoEnrich:
    def test_auto_enrich_jpeg(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            jpeg_path = os.path.join(tmpdir, "auto.jpg")
            create_test_jpeg(jpeg_path)

            handler = ImageHandler()
            handler.auto_enrich(jpeg_path, "dall-e-3", classification="public")

            result = handler.extract(jpeg_path)
            assert result is not None
            assert result["akf"] == "1.0"
            assert result["classification"] == "public"
            assert result["ai_contribution"] == 1.0


# ------------------------------------------------------------------
# Module-level convenience functions
# ------------------------------------------------------------------

class TestModuleFunctions:
    def test_module_embed_extract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            jpeg_path = os.path.join(tmpdir, "modtest.jpg")
            create_test_jpeg(jpeg_path)

            embed(jpeg_path, SAMPLE_METADATA)
            result = extract(jpeg_path)
            assert result is not None
            assert result.get("classification") == "public"
            assert is_enriched(jpeg_path) is True

    def test_module_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            jpeg_path = os.path.join(tmpdir, "modtest.jpg")
            create_test_jpeg(jpeg_path)

            report = scan(jpeg_path)
            assert report.enriched is False
