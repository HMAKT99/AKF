"""Tests for AKF audio format handler."""

import os

import pytest

from akf.formats.audio import AudioHandler, embed, extract, is_enriched, scan, scan_directory, auto_enrich


@pytest.fixture
def handler():
    return AudioHandler()


@pytest.fixture
def mp3_file(tmp_path):
    """Create a dummy .mp3 file."""
    fp = tmp_path / "track.mp3"
    fp.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 100)
    return str(fp)


@pytest.fixture
def sample_metadata():
    return {
        "classification": "internal",
        "overall_trust": 0.8,
        "ai_contribution": 0.6,
        "claims": [
            {"c": "AI-generated audio", "t": 0.7, "src": "test-agent"},
        ],
    }


class TestAudioHandler:
    def test_format_attributes(self, handler):
        assert handler.FORMAT_NAME == "Audio"
        assert handler.MODE == "sidecar"
        assert ".mp3" in handler.EXTENSIONS
        assert ".wav" in handler.EXTENSIONS
        assert ".flac" in handler.EXTENSIONS
        assert ".ogg" in handler.EXTENSIONS
        assert handler.DEPENDENCIES == []

    def test_embed_and_extract_round_trip(self, handler, mp3_file, sample_metadata):
        handler.embed(mp3_file, sample_metadata)
        result = handler.extract(mp3_file)
        assert result is not None
        assert result["classification"] == "internal"
        assert result["overall_trust"] == 0.8
        assert result["claims"][0]["c"] == "AI-generated audio"

    def test_is_enriched_false_before_embed(self, handler, mp3_file):
        assert handler.is_enriched(mp3_file) is False

    def test_is_enriched_true_after_embed(self, handler, mp3_file, sample_metadata):
        handler.embed(mp3_file, sample_metadata)
        assert handler.is_enriched(mp3_file) is True

    def test_sidecar_file_created(self, mp3_file, sample_metadata):
        embed(mp3_file, sample_metadata)
        sidecar_path = mp3_file + ".akf.json"
        assert os.path.isfile(sidecar_path)

    def test_scan_returns_scan_report(self, handler, mp3_file, sample_metadata):
        handler.embed(mp3_file, sample_metadata)
        report = handler.scan(mp3_file)
        assert report.enriched is True
        assert report.format == "Audio"
        assert report.classification == "internal"

    def test_scan_unenriched(self, handler, mp3_file):
        report = handler.scan(mp3_file)
        assert report.enriched is False

    def test_scan_directory_finds_audio(self, tmp_path, handler, sample_metadata):
        # Create a few audio files
        for name in ("a.mp3", "b.wav", "c.txt"):
            fp = tmp_path / name
            fp.write_bytes(b"\x00" * 50)

        # Enrich one
        handler.embed(str(tmp_path / "a.mp3"), sample_metadata)

        results = handler.scan_directory(str(tmp_path))
        assert len(results) == 2  # a.mp3 and b.wav (not c.txt)
        enriched_files = [r for r in results if r["enriched"]]
        assert len(enriched_files) == 1
        assert enriched_files[0]["file"].endswith("a.mp3")

    def test_scan_directory_nonexistent(self, handler):
        results = handler.scan_directory("/nonexistent/path")
        assert results == []

    def test_auto_enrich(self, handler, mp3_file):
        handler.auto_enrich(mp3_file, "test-agent")
        assert handler.is_enriched(mp3_file) is True
        meta = handler.extract(mp3_file)
        assert meta is not None
        assert "integrity_hash" in meta


class TestModuleFunctions:
    """Test module-level convenience functions."""

    def test_embed_extract(self, mp3_file, sample_metadata):
        embed(mp3_file, sample_metadata)
        result = extract(mp3_file)
        assert result is not None
        assert result["classification"] == "internal"

    def test_is_enriched(self, mp3_file, sample_metadata):
        assert is_enriched(mp3_file) is False
        embed(mp3_file, sample_metadata)
        assert is_enriched(mp3_file) is True

    def test_scan(self, mp3_file, sample_metadata):
        embed(mp3_file, sample_metadata)
        report = scan(mp3_file)
        assert report.enriched is True

    def test_scan_directory(self, tmp_path):
        fp = tmp_path / "test.mp3"
        fp.write_bytes(b"\x00" * 50)
        results = scan_directory(str(tmp_path))
        assert len(results) == 1
        assert results[0]["enriched"] is False

    def test_auto_enrich(self, mp3_file):
        auto_enrich(mp3_file, "test-agent")
        assert is_enriched(mp3_file) is True


class TestUniversalIntegration:
    """Test that audio files work through the universal API."""

    def test_universal_embed_extract(self, mp3_file, sample_metadata):
        from akf import universal

        universal.embed(mp3_file, metadata=sample_metadata)
        result = universal.extract(mp3_file)
        assert result is not None
        assert result["classification"] == "internal"

    def test_universal_is_enriched(self, mp3_file, sample_metadata):
        from akf import universal

        assert universal.is_enriched(mp3_file) is False
        universal.embed(mp3_file, metadata=sample_metadata)
        assert universal.is_enriched(mp3_file) is True

    def test_universal_scan(self, mp3_file, sample_metadata):
        from akf import universal

        universal.embed(mp3_file, metadata=sample_metadata)
        report = universal.scan(mp3_file)
        assert report.enriched is True

    def test_all_extensions_registered(self):
        from akf.universal import _FORMAT_REGISTRY

        for ext in ("mp3", "wav", "flac", "ogg"):
            assert ext in _FORMAT_REGISTRY, f".{ext} not registered"
