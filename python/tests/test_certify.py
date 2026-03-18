"""Tests for akf.certify — certification engine and CLI."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from akf.certify import (
    CertifyReport,
    CertifyResult,
    certify_directory,
    certify_file,
    parse_evidence_json,
    parse_junit_xml,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_akf_file(tmp: Path, name: str = "test.akf", trust: float = 0.9) -> Path:
    """Create a valid .akf file with provenance and evidence for realistic trust."""
    data = {
        "v": "1.1",
        "claims": [
            {
                "c": "Revenue is $4.2B",
                "t": trust,
                "src": "report",
                "evidence": [{"type": "test_pass", "detail": "verified"}],
            },
        ],
        "label": "internal",
        "provenance": [
            {"agent": "claude-code", "action": "create", "at": "2025-01-01T00:00:00Z"},
        ],
    }
    fpath = tmp / name
    fpath.write_text(json.dumps(data))
    return fpath


def _make_junit_xml(tmp: Path, name: str = "results.xml", failures: int = 0) -> Path:
    """Create a minimal JUnit XML file."""
    tests = 5
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="unit" tests="{tests}" failures="{failures}" errors="0">
  <testcase classname="test.A" name="test_one"/>
  <testcase classname="test.A" name="test_two"/>
</testsuite>"""
    fpath = tmp / name
    fpath.write_text(xml)
    return fpath


# ---------------------------------------------------------------------------
# TestParseJunitXml
# ---------------------------------------------------------------------------


class TestParseJunitXml:
    def test_all_pass(self, tmp_path):
        xml_file = _make_junit_xml(tmp_path, failures=0)
        results = parse_junit_xml(xml_file)
        assert len(results) == 1
        assert results[0].type == "test_pass"
        assert "5 tests passed" in results[0].detail

    def test_with_failures(self, tmp_path):
        xml_file = _make_junit_xml(tmp_path, failures=2)
        results = parse_junit_xml(xml_file)
        assert len(results) == 1
        assert results[0].type == "test_fail"
        assert "2 failures" in results[0].detail

    def test_testsuites_wrapper(self, tmp_path):
        xml = """<?xml version="1.0"?>
<testsuites>
  <testsuite name="suite1" tests="3" failures="0" errors="0"/>
  <testsuite name="suite2" tests="2" failures="1" errors="0"/>
</testsuites>"""
        fpath = tmp_path / "wrapped.xml"
        fpath.write_text(xml)
        results = parse_junit_xml(fpath)
        assert len(results) == 2
        assert results[0].type == "test_pass"
        assert results[1].type == "test_fail"

    def test_unknown_root(self, tmp_path):
        fpath = tmp_path / "bad.xml"
        fpath.write_text("<root/>")
        assert parse_junit_xml(fpath) == []


# ---------------------------------------------------------------------------
# TestParseEvidenceJson
# ---------------------------------------------------------------------------


class TestParseEvidenceJson:
    def test_list_format(self, tmp_path):
        data = [
            {"type": "test_pass", "detail": "unit tests pass"},
            {"type": "human_review", "detail": "reviewed by Alice"},
        ]
        fpath = tmp_path / "evidence.json"
        fpath.write_text(json.dumps(data))
        results = parse_evidence_json(fpath)
        assert len(results) == 2
        assert results[0].type == "test_pass"
        assert results[1].type == "human_review"

    def test_deepeval_format(self, tmp_path):
        data = {
            "test_results": [
                {"name": "faithfulness", "score": 0.95, "success": True},
                {"name": "relevancy", "score": 0.3, "success": False},
            ]
        }
        fpath = tmp_path / "deepeval.json"
        fpath.write_text(json.dumps(data))
        results = parse_evidence_json(fpath)
        assert len(results) == 2
        assert results[0].type == "test_pass"
        assert results[1].type == "test_fail"

    def test_generic_score(self, tmp_path):
        data = {"score": 0.85, "passed": True}
        fpath = tmp_path / "score.json"
        fpath.write_text(json.dumps(data))
        results = parse_evidence_json(fpath)
        assert len(results) == 1
        assert results[0].type == "test_pass"

    def test_generic_fail(self, tmp_path):
        data = {"score": 0.2, "passed": False}
        fpath = tmp_path / "fail.json"
        fpath.write_text(json.dumps(data))
        results = parse_evidence_json(fpath)
        assert len(results) == 1
        assert results[0].type == "test_fail"


# ---------------------------------------------------------------------------
# TestCertifyFile
# ---------------------------------------------------------------------------


class TestCertifyFile:
    def test_stamped_file_passes(self, tmp_path):
        akf_file = _make_akf_file(tmp_path, trust=0.9)
        result = certify_file(str(akf_file), min_trust=0.5)
        assert result.certified is True
        assert result.trust_score >= 0.5
        assert result.error is None

    def test_no_metadata_fails(self, tmp_path):
        plain = tmp_path / "plain.txt"
        plain.write_text("hello world")
        result = certify_file(str(plain))
        assert result.certified is False
        assert result.error == "no metadata"

    def test_low_trust_fails(self, tmp_path):
        akf_file = _make_akf_file(tmp_path, trust=0.3)
        result = certify_file(str(akf_file), min_trust=0.7)
        assert result.certified is False
        assert result.trust_score < 0.7

    def test_with_external_evidence(self, tmp_path):
        from akf.models import Evidence

        akf_file = _make_akf_file(tmp_path, trust=0.9)
        ev = Evidence(type="test_pass", detail="all tests pass")
        result = certify_file(str(akf_file), min_trust=0.5, evidence=[ev])
        assert result.certified is True


# ---------------------------------------------------------------------------
# TestCertifyDirectory
# ---------------------------------------------------------------------------


class TestCertifyDirectory:
    def test_mixed_directory(self, tmp_path):
        _make_akf_file(tmp_path, name="good.akf", trust=0.9)
        (tmp_path / "plain.txt").write_text("no metadata")
        report = certify_directory(str(tmp_path), min_trust=0.5)
        assert report.total_files == 2
        assert report.skipped_count >= 1  # plain.txt skipped
        assert report.certified_count >= 1

    def test_empty_directory(self, tmp_path):
        report = certify_directory(str(tmp_path))
        assert report.total_files == 0
        assert report.all_certified is False  # no files = not certified


# ---------------------------------------------------------------------------
# TestCertifyCli
# ---------------------------------------------------------------------------


class TestCertifyCli:
    """Test the CLI ``akf certify`` command."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.tmp = tmp_path
        self.akf_file = _make_akf_file(tmp_path, trust=0.9)

    def _run(self, args):
        from click.testing import CliRunner
        from akf.cli import main

        runner = CliRunner()
        return runner.invoke(main, args, catch_exceptions=False)

    def test_summary_output(self):
        result = self._run(["certify", str(self.akf_file), "--format", "summary"])
        assert result.exit_code == 0
        assert "PASS" in result.output or "CERTIFIED" in result.output or "certified" in result.output.lower()

    def test_json_output(self):
        result = self._run(["certify", str(self.akf_file), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "certified" in data or "results" in data

    def test_markdown_output(self):
        result = self._run(["certify", str(self.akf_file), "--format", "markdown"])
        assert result.exit_code == 0
        assert "|" in result.output  # table

    def test_fail_on_untrusted_pass(self):
        result = self._run([
            "certify", str(self.akf_file),
            "--fail-on-untrusted", "--min-trust", "0.5",
        ])
        assert result.exit_code == 0

    def test_fail_on_untrusted_fails(self):
        low_file = _make_akf_file(self.tmp, name="low.akf", trust=0.3)
        result = self._run([
            "certify", str(low_file),
            "--fail-on-untrusted", "--min-trust", "0.7",
        ])
        assert result.exit_code == 1

    def test_evidence_file(self, tmp_path):
        ev_data = [{"type": "test_pass", "detail": "tests green"}]
        ev_file = tmp_path / "evidence.json"
        ev_file.write_text(json.dumps(ev_data))
        result = self._run([
            "certify", str(self.akf_file),
            "--evidence-file", str(ev_file),
        ])
        assert result.exit_code == 0

    def test_directory_mode(self):
        result = self._run(["certify", str(self.tmp), "--format", "summary"])
        assert result.exit_code == 0
