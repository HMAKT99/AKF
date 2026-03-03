"""Tests for AKF sidecar module."""

import json
import os
import tempfile

import pytest

from akf import sidecar


class TestSidecarPath:
    def test_returns_akf_json_suffix(self):
        path = sidecar.sidecar_path("/tmp/report.pdf")
        assert path == "/tmp/report.pdf.akf.json"

    def test_works_with_relative_path(self):
        path = sidecar.sidecar_path("data/file.csv")
        assert path == "data/file.csv.akf.json"


class TestCreateAndRead:
    def test_round_trip(self, tmp_path):
        # Create a test file
        original = str(tmp_path / "test.txt")
        with open(original, "w") as f:
            f.write("Hello, world!")

        metadata = {
            "classification": "internal",
            "overall_trust": 0.85,
            "ai_contribution": 0.3,
            "claims": [
                {"c": "Test claim", "t": 0.9, "src": "unit-test"},
            ],
            "provenance": [
                {"actor": "test-agent", "action": "created", "at": "2025-01-01T00:00:00Z"}
            ],
        }

        # Create sidecar
        sc_path = sidecar.create(original, metadata)
        assert os.path.isfile(sc_path)
        assert sc_path == original + ".akf.json"

        # Read it back
        result = sidecar.read(original)
        assert result is not None
        assert result["akf"] == "1.0"
        assert result["mode"] == "sidecar"
        assert result["target_file"] == "test.txt"
        assert result["classification"] == "internal"
        assert result["overall_trust"] == 0.85
        assert result["ai_contribution"] == 0.3
        assert len(result["claims"]) == 1
        assert result["claims"][0]["c"] == "Test claim"
        assert "integrity_hash" in result
        assert result["integrity_hash"].startswith("sha256:")

    def test_read_nonexistent_returns_none(self, tmp_path):
        filepath = str(tmp_path / "nonexistent.txt")
        result = sidecar.read(filepath)
        assert result is None

    def test_envelope_fields_preserved(self, tmp_path):
        original = str(tmp_path / "data.csv")
        with open(original, "w") as f:
            f.write("a,b,c\n1,2,3\n")

        # User cannot override akf and mode
        metadata = {
            "akf": "2.0",  # should be overridden to 1.0
            "mode": "embedded",  # should be overridden to sidecar
            "custom_field": "custom_value",
        }
        sidecar.create(original, metadata)
        result = sidecar.read(original)
        assert result["akf"] == "1.0"
        assert result["mode"] == "sidecar"
        assert result["custom_field"] == "custom_value"


class TestVerifyIntegrity:
    def test_integrity_passes(self, tmp_path):
        original = str(tmp_path / "doc.txt")
        with open(original, "w") as f:
            f.write("Original content")

        sidecar.create(original, {"claims": []})

        # File unchanged
        result = sidecar.verify_integrity(original)
        assert result is True

    def test_integrity_fails_after_modification(self, tmp_path):
        original = str(tmp_path / "doc.txt")
        with open(original, "w") as f:
            f.write("Original content")

        sidecar.create(original, {"claims": []})

        # Modify the file
        with open(original, "w") as f:
            f.write("Modified content!")

        result = sidecar.verify_integrity(original)
        assert result is False

    def test_no_sidecar_returns_none(self, tmp_path):
        original = str(tmp_path / "bare.txt")
        with open(original, "w") as f:
            f.write("no metadata")

        result = sidecar.verify_integrity(original)
        assert result is None


class TestListEnriched:
    def test_finds_enriched_files(self, tmp_path):
        # Create some files
        f1 = str(tmp_path / "a.txt")
        f2 = str(tmp_path / "b.txt")
        f3 = str(tmp_path / "c.txt")
        for f in (f1, f2, f3):
            with open(f, "w") as fh:
                fh.write("content")

        # Enrich only f1 and f3
        sidecar.create(f1, {"claims": []})
        sidecar.create(f3, {"claims": []})

        enriched = sidecar.list_enriched(str(tmp_path))
        basenames = [os.path.basename(p) for p in enriched]
        assert "a.txt" in basenames
        assert "c.txt" in basenames
        assert "b.txt" not in basenames

    def test_empty_directory(self, tmp_path):
        enriched = sidecar.list_enriched(str(tmp_path))
        assert enriched == []

    def test_nonexistent_directory(self):
        enriched = sidecar.list_enriched("/nonexistent/directory/path")
        assert enriched == []


class TestRemove:
    def test_removes_sidecar(self, tmp_path):
        original = str(tmp_path / "file.txt")
        with open(original, "w") as f:
            f.write("content")

        sidecar.create(original, {"claims": []})
        assert sidecar.read(original) is not None

        result = sidecar.remove(original)
        assert result is True
        assert sidecar.read(original) is None

    def test_remove_nonexistent_returns_false(self, tmp_path):
        original = str(tmp_path / "bare.txt")
        with open(original, "w") as f:
            f.write("no sidecar")

        result = sidecar.remove(original)
        assert result is False


class TestSidecarDiscovery:
    def test_discovers_primary_sidecar(self, tmp_path):
        original = str(tmp_path / "file.txt")
        with open(original, "w") as f:
            f.write("content")

        sidecar.create(original, {"claims": []})
        result = sidecar.read(original)
        assert result is not None
        assert result["mode"] == "sidecar"

    def test_discovers_hidden_dir_sidecar(self, tmp_path):
        original = str(tmp_path / "file.txt")
        with open(original, "w") as f:
            f.write("content")

        # Create .akf/ directory with sidecar
        akf_dir = tmp_path / ".akf"
        akf_dir.mkdir()
        sc_data = {
            "akf": "1.0",
            "mode": "sidecar",
            "target_file": "file.txt",
            "claims": [{"c": "from hidden dir", "t": 0.5}],
            "integrity_hash": "sha256:abc",
        }
        sc_path = akf_dir / "file.txt.akf.json"
        with open(str(sc_path), "w") as f:
            json.dump(sc_data, f)

        result = sidecar.read(original)
        assert result is not None
        assert result["claims"][0]["c"] == "from hidden dir"


class TestBinaryFile:
    def test_binary_file_hashing(self, tmp_path):
        # Create a binary file
        original = str(tmp_path / "image.bin")
        with open(original, "wb") as f:
            f.write(bytes(range(256)))

        sidecar.create(original, {"claims": [{"c": "Binary test", "t": 0.8}]})

        result = sidecar.read(original)
        assert result is not None
        assert result["integrity_hash"].startswith("sha256:")

        # Verify integrity with binary file
        assert sidecar.verify_integrity(original) is True

        # Modify binary file
        with open(original, "wb") as f:
            f.write(bytes(range(255, -1, -1)))

        assert sidecar.verify_integrity(original) is False
