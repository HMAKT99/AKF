"""Tests for AKF universal format-agnostic API."""

import json
import os
import tempfile

import pytest

from akf import universal
from akf.formats.base import AKFFormatHandler, ScanReport


class TestSupportedFormats:
    def test_returns_dict(self):
        formats = universal.supported_formats()
        assert isinstance(formats, dict)

    def test_includes_sidecar(self):
        formats = universal.supported_formats()
        assert "sidecar" in formats
        assert formats["sidecar"]["mode"] == "sidecar"
        assert formats["sidecar"]["extensions"] == ["*"]


class TestEmbedExtract:
    def test_json_round_trip(self, tmp_path):
        filepath = str(tmp_path / "data.json")
        original_data = {"key": "value", "count": 42}
        with open(filepath, "w") as f:
            json.dump(original_data, f)

        metadata = {
            "akf": "1.0",
            "classification": "internal",
            "overall_trust": 0.9,
            "claims": [{"c": "JSON data is valid", "t": 0.95}],
        }

        universal.embed(filepath, metadata=metadata)
        result = universal.extract(filepath)

        assert result is not None
        assert result["classification"] == "internal"
        assert len(result["claims"]) == 1
        assert result["claims"][0]["c"] == "JSON data is valid"

    def test_embed_with_claims_and_classification(self, tmp_path):
        filepath = str(tmp_path / "data.json")
        with open(filepath, "w") as f:
            json.dump({"data": "test"}, f)

        claims = [
            {"c": "Claim one", "t": 0.8},
            {"c": "Claim two", "t": 0.7},
        ]

        universal.embed(filepath, claims=claims, classification="confidential")
        result = universal.extract(filepath)

        assert result is not None
        assert result.get("classification") == "confidential"
        assert len(result.get("claims", [])) == 2

    def test_extract_non_enriched_returns_none(self, tmp_path):
        filepath = str(tmp_path / "plain.json")
        with open(filepath, "w") as f:
            json.dump({"just": "data"}, f)

        result = universal.extract(filepath)
        assert result is None


class TestScan:
    def test_scan_enriched_file(self, tmp_path):
        filepath = str(tmp_path / "data.json")
        with open(filepath, "w") as f:
            json.dump({"data": True}, f)

        metadata = {
            "classification": "internal",
            "overall_trust": 0.85,
            "ai_contribution": 0.5,
            "claims": [
                {"c": "Claim A", "t": 0.9, "ai": True},
                {"c": "Claim B", "t": 0.8, "ver": True},
            ],
        }
        universal.embed(filepath, metadata=metadata)

        report = universal.scan(filepath)
        assert isinstance(report, ScanReport)
        assert report.enriched is True
        assert report.claim_count == 2

    def test_scan_non_enriched_file(self, tmp_path):
        filepath = str(tmp_path / "bare.json")
        with open(filepath, "w") as f:
            json.dump({"no": "metadata"}, f)

        report = universal.scan(filepath)
        assert report.enriched is False


class TestIsEnriched:
    def test_enriched_file(self, tmp_path):
        filepath = str(tmp_path / "enriched.json")
        with open(filepath, "w") as f:
            json.dump({"data": 1}, f)

        universal.embed(filepath, metadata={"claims": [{"c": "test", "t": 0.5}]})
        assert universal.is_enriched(filepath) is True

    def test_non_enriched_file(self, tmp_path):
        filepath = str(tmp_path / "plain.json")
        with open(filepath, "w") as f:
            json.dump({"data": 1}, f)

        assert universal.is_enriched(filepath) is False


class TestSidecarFallback:
    def test_unknown_extension_uses_sidecar(self, tmp_path):
        filepath = str(tmp_path / "data.xyz")
        with open(filepath, "w") as f:
            f.write("unknown format content")

        metadata = {
            "classification": "public",
            "claims": [{"c": "Sidecar claim", "t": 0.7}],
        }
        universal.embed(filepath, metadata=metadata)

        # Should have created a sidecar
        sc_path = filepath + ".akf.json"
        assert os.path.isfile(sc_path)

        result = universal.extract(filepath)
        assert result is not None
        assert result["claims"][0]["c"] == "Sidecar claim"

    def test_sidecar_fallback_scan(self, tmp_path):
        filepath = str(tmp_path / "binary.dat")
        with open(filepath, "wb") as f:
            f.write(b"\x00\x01\x02\x03")

        metadata = {
            "claims": [{"c": "Binary claim", "t": 0.6}],
        }
        universal.embed(filepath, metadata=metadata)

        report = universal.scan(filepath)
        assert report.enriched is True


class TestRegisterFormat:
    def test_custom_handler(self, tmp_path):

        class CSVHandler(AKFFormatHandler):
            FORMAT_NAME = "csv"
            EXTENSIONS = ["csv"]
            MODE = "sidecar"
            MECHANISM = "sidecar for CSV"

            def embed(self, filepath, metadata):
                from akf import sidecar
                sidecar.create(filepath, metadata)

            def extract(self, filepath):
                from akf import sidecar
                return sidecar.read(filepath)

            def is_enriched(self, filepath):
                from akf import sidecar
                return sidecar.read(filepath) is not None

        handler = CSVHandler()
        universal.register_format("csv", handler)

        filepath = str(tmp_path / "data.csv")
        with open(filepath, "w") as f:
            f.write("a,b,c\n1,2,3\n")

        universal.embed(filepath, metadata={"claims": [{"c": "CSV data", "t": 0.8}]})
        result = universal.extract(filepath)
        assert result is not None
        assert result["claims"][0]["c"] == "CSV data"


class TestInfo:
    def test_info_enriched(self, tmp_path):
        filepath = str(tmp_path / "info_test.json")
        with open(filepath, "w") as f:
            json.dump({"data": True}, f)

        metadata = {
            "classification": "internal",
            "overall_trust": 0.85,
            "ai_contribution": 0.4,
            "claims": [{"c": "Info claim", "t": 0.9}],
        }
        universal.embed(filepath, metadata=metadata)

        output = universal.info(filepath)
        assert "info_test.json" in output
        assert "enriched" in output
        assert "internal" in output or "Classification" in output
        assert "Claims: 1" in output

    def test_info_non_enriched(self, tmp_path):
        filepath = str(tmp_path / "plain.json")
        with open(filepath, "w") as f:
            json.dump({"x": 1}, f)

        output = universal.info(filepath)
        assert "not enriched" in output


class TestToAkf:
    def test_to_akf_conversion(self, tmp_path):
        # Create an enriched JSON file
        source = str(tmp_path / "source.json")
        with open(source, "w") as f:
            json.dump({"data": True}, f)

        metadata = {
            "classification": "internal",
            "overall_trust": 0.9,
            "claims": [
                {"c": "Conversion claim", "t": 0.85, "src": "test"},
            ],
            "provenance": [
                {"actor": "agent-1", "action": "created", "at": "2025-01-01T00:00:00Z"}
            ],
        }
        universal.embed(source, metadata=metadata)

        # Convert to .akf
        output = str(tmp_path / "output.akf")
        universal.to_akf(source, output)

        assert os.path.isfile(output)

        # Verify the .akf file
        from akf.core import load
        unit = load(output)
        assert unit.version == "1.0"
        assert len(unit.claims) >= 1

    def test_to_akf_no_metadata_raises(self, tmp_path):
        source = str(tmp_path / "plain.json")
        with open(source, "w") as f:
            json.dump({"data": 1}, f)

        output = str(tmp_path / "out.akf")
        with pytest.raises(ValueError, match="No AKF metadata"):
            universal.to_akf(source, output)


class TestScanDirectory:
    def test_scan_directory(self, tmp_path):
        # Create some files
        f1 = str(tmp_path / "a.json")
        f2 = str(tmp_path / "b.json")
        f3 = str(tmp_path / "c.txt")

        with open(f1, "w") as f:
            json.dump({"a": 1}, f)
        with open(f2, "w") as f:
            json.dump({"b": 2}, f)
        with open(f3, "w") as f:
            f.write("plain text")

        # Enrich f1 and f3
        universal.embed(f1, metadata={"claims": [{"c": "A claim", "t": 0.8}]})
        universal.embed(f3, metadata={"claims": [{"c": "C claim", "t": 0.7}]})

        reports = universal.scan_directory(str(tmp_path), recursive=False)
        assert isinstance(reports, list)
        assert len(reports) >= 2  # At least the enriched files + non-enriched

        enriched_count = sum(1 for r in reports if r.enriched)
        assert enriched_count >= 2

    def test_scan_directory_recursive(self, tmp_path):
        # Create subdirectory with file
        subdir = tmp_path / "sub"
        subdir.mkdir()

        f1 = str(tmp_path / "top.json")
        f2 = str(subdir / "nested.json")

        with open(f1, "w") as f:
            json.dump({"data": 1}, f)
        with open(f2, "w") as f:
            json.dump({"data": 2}, f)

        universal.embed(f1, metadata={"claims": [{"c": "Top", "t": 0.8}]})
        universal.embed(f2, metadata={"claims": [{"c": "Nested", "t": 0.7}]})

        reports = universal.scan_directory(str(tmp_path), recursive=True)
        enriched = [r for r in reports if r.enriched]
        assert len(enriched) >= 2

    def test_scan_empty_directory(self, tmp_path):
        reports = universal.scan_directory(str(tmp_path))
        assert reports == []

    def test_scan_nonexistent_directory(self):
        reports = universal.scan_directory("/nonexistent/path")
        assert reports == []


class TestDerive:
    def test_derive_creates_provenance_link(self, tmp_path):
        # Create source
        source = str(tmp_path / "source.json")
        with open(source, "w") as f:
            json.dump({"data": "original"}, f)

        universal.embed(source, metadata={
            "classification": "internal",
            "overall_trust": 0.9,
            "claims": [{"c": "Source claim", "t": 0.85}],
        })

        # Create output file
        output = str(tmp_path / "derived.txt")
        with open(output, "w") as f:
            f.write("Derived content")

        # Derive
        universal.derive(
            source, output, "agent-2",
            action="summarized",
            claims=[{"c": "Derived claim", "t": 0.7}],
        )

        result = universal.extract(output)
        assert result is not None
        assert result.get("parent_file") == "source.json"
        assert result.get("parent_hash", "").startswith("sha256:")
        assert result.get("classification") == "internal"
        assert len(result.get("provenance", [])) >= 1


class TestConvertDirectory:
    """Tests for convert_directory batch conversion."""

    def _make_enriched_json(self, path, claim_text="claim"):
        with open(path, "w") as f:
            json.dump({"data": True}, f)
        universal.embed(path, metadata={"claims": [{"c": claim_text, "t": 0.8}]})

    def _make_plain_file(self, path, content="plain"):
        with open(path, "w") as f:
            f.write(content)

    def test_extract_mode(self, tmp_path):
        """extract mode only converts files WITH existing metadata."""
        self._make_enriched_json(str(tmp_path / "a.json"))
        self._make_plain_file(str(tmp_path / "b.txt"))

        out = tmp_path / "out"
        out.mkdir()
        result = universal.convert_directory(str(tmp_path), str(out), mode="extract")

        assert result.converted == 1
        assert result.skipped >= 1  # b.txt skipped
        assert os.path.isfile(str(out / "a.json.akf"))
        assert not os.path.isfile(str(out / "b.txt.akf"))

    def test_enrich_mode(self, tmp_path):
        """enrich mode only converts files WITHOUT existing metadata."""
        self._make_enriched_json(str(tmp_path / "a.json"))
        self._make_plain_file(str(tmp_path / "b.txt"))

        out = tmp_path / "out"
        out.mkdir()
        result = universal.convert_directory(str(tmp_path), str(out), mode="enrich")

        assert result.converted == 1
        assert result.skipped >= 1  # a.json skipped
        assert os.path.isfile(str(out / "b.txt.akf"))

    def test_both_mode(self, tmp_path):
        """both mode converts all files (extract if metadata, enrich otherwise)."""
        self._make_enriched_json(str(tmp_path / "a.json"))
        self._make_plain_file(str(tmp_path / "b.txt"))

        out = tmp_path / "out"
        out.mkdir()
        result = universal.convert_directory(str(tmp_path), str(out), mode="both")

        assert result.converted == 2
        assert os.path.isfile(str(out / "a.json.akf"))
        assert os.path.isfile(str(out / "b.txt.akf"))

    def test_skip_existing_no_overwrite(self, tmp_path):
        """Without --overwrite, existing .akf outputs are skipped."""
        self._make_plain_file(str(tmp_path / "a.txt"))

        out = tmp_path / "out"
        out.mkdir()
        # Pre-create the output file
        (out / "a.txt.akf").write_text("existing")

        result = universal.convert_directory(str(tmp_path), str(out), overwrite=False)

        assert result.skipped >= 1
        assert (out / "a.txt.akf").read_text() == "existing"

    def test_overwrite_existing(self, tmp_path):
        """With --overwrite, existing .akf outputs are replaced."""
        self._make_plain_file(str(tmp_path / "a.txt"))

        out = tmp_path / "out"
        out.mkdir()
        (out / "a.txt.akf").write_text("old")

        result = universal.convert_directory(str(tmp_path), str(out), overwrite=True)

        assert result.converted >= 1
        assert (out / "a.txt.akf").read_text() != "old"

    def test_recursive_structure_mirroring(self, tmp_path):
        """Recursive mode mirrors subdirectory structure in output."""
        sub = tmp_path / "sub"
        sub.mkdir()
        self._make_plain_file(str(tmp_path / "top.txt"))
        self._make_plain_file(str(sub / "nested.txt"))

        out = tmp_path / "out"
        out.mkdir()
        result = universal.convert_directory(str(tmp_path), str(out), recursive=True)

        assert result.converted == 2
        assert os.path.isfile(str(out / "top.txt.akf"))
        assert os.path.isfile(str(out / "sub" / "nested.txt.akf"))

    def test_non_recursive(self, tmp_path):
        """Non-recursive mode only processes top-level files."""
        sub = tmp_path / "sub"
        sub.mkdir()
        self._make_plain_file(str(tmp_path / "top.txt"))
        self._make_plain_file(str(sub / "nested.txt"))

        out = tmp_path / "out"
        out.mkdir()
        result = universal.convert_directory(str(tmp_path), str(out), recursive=False)

        assert result.converted == 1
        assert os.path.isfile(str(out / "top.txt.akf"))
        assert not os.path.isfile(str(out / "sub" / "nested.txt.akf"))

    def test_nonexistent_dir_error(self):
        """Nonexistent directory returns a failed result with error."""
        result = universal.convert_directory("/nonexistent/path", "/tmp/out")

        assert result.failed == 1
        assert not result  # __bool__ returns False
        assert any("not found" in e for e in result.errors)

    def test_extract_skips_plain_files(self, tmp_path):
        """extract mode skips files without AKF metadata."""
        self._make_plain_file(str(tmp_path / "plain.txt"))

        out = tmp_path / "out"
        out.mkdir()
        result = universal.convert_directory(str(tmp_path), str(out), mode="extract")

        assert result.converted == 0
        assert result.skipped == 1

    def test_agent_provenance_in_enrich(self, tmp_path):
        """enrich mode includes agent in provenance hop."""
        self._make_plain_file(str(tmp_path / "a.txt"))

        out = tmp_path / "out"
        out.mkdir()
        universal.convert_directory(str(tmp_path), str(out), mode="enrich", agent="test-agent")

        from akf.core import load
        unit = load(str(out / "a.txt.akf"))
        assert unit.prov is not None
        assert len(unit.prov) >= 1
        assert unit.prov[0].actor == "test-agent"

    def test_hidden_and_sidecar_skipped(self, tmp_path):
        """Hidden files and .akf.json sidecars are skipped."""
        self._make_plain_file(str(tmp_path / ".hidden"))
        self._make_plain_file(str(tmp_path / "data.akf.json"))
        self._make_plain_file(str(tmp_path / "existing.akf"))
        self._make_plain_file(str(tmp_path / "real.txt"))

        out = tmp_path / "out"
        out.mkdir()
        result = universal.convert_directory(str(tmp_path), str(out))

        assert result.converted == 1
        assert os.path.isfile(str(out / "real.txt.akf"))

    def test_convert_result_bool(self):
        """ConvertResult is truthy when no failures."""
        assert universal.ConvertResult(converted=3, skipped=1, failed=0)
        assert not universal.ConvertResult(converted=1, skipped=0, failed=1)
