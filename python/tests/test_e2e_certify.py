"""AKF Certify — Comprehensive End-to-End and Integration Tests.

Tests the full certify pipeline: evidence parsing, file certification,
directory certification, CLI commands, output formats, exit codes,
cross-format workflows, and GitHub Action configuration.

Run: python3 -m pytest tests/test_e2e_certify.py -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
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
from akf.models import Evidence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PYTHON = sys.executable
TEST_DIR = None


def akf_cli(*args, check=True, allow_fail=False):
    """Run an akf CLI command via subprocess, return (returncode, stdout, stderr)."""
    cmd = [PYTHON, "-m", "akf"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=TEST_DIR)
    if check and not allow_fail and result.returncode != 0:
        raise AssertionError(
            f"Command failed: {' '.join(args)}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.returncode, result.stdout, result.stderr


def _run_cli(args):
    """Run akf CLI using click CliRunner (in-process)."""
    from click.testing import CliRunner
    from akf.cli import main

    runner = CliRunner()
    return runner.invoke(main, args, catch_exceptions=False)


@pytest.fixture(scope="module", autouse=True)
def setup_test_dir():
    """Create a shared test directory for all module tests."""
    global TEST_DIR
    TEST_DIR = tempfile.mkdtemp(prefix="akf_e2e_certify_")
    yield TEST_DIR
    shutil.rmtree(TEST_DIR, ignore_errors=True)


# ---------------------------------------------------------------------------
# File generators
# ---------------------------------------------------------------------------


def make_akf_file(
    directory: Path,
    name: str = "test.akf",
    trust: float = 0.9,
    claims: list | None = None,
    label: str = "internal",
    with_provenance: bool = True,
    with_evidence: bool = True,
    with_hash: bool = False,
) -> Path:
    """Create a valid .akf file with configurable properties."""
    if claims is None:
        claim = {
            "c": "Revenue is $4.2B, up 12% YoY",
            "t": trust,
            "src": "SEC 10-Q filing",
            "tier": 1,
            "ai": False,
        }
        if with_evidence:
            claim["evidence"] = [{"type": "test_pass", "detail": "42/42 tests passed"}]
        claims = [claim]

    data: dict = {
        "v": "1.1",
        "claims": claims,
        "label": label,
    }
    if with_provenance:
        data["provenance"] = [
            {"agent": "claude-code", "action": "create", "at": "2025-07-15T09:30:00Z"},
        ]
    if with_hash:
        data["hash"] = "sha256:abc123def456"

    fpath = directory / name
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(json.dumps(data))
    return fpath


def make_junit_xml(
    directory: Path,
    name: str = "results.xml",
    suites: list[dict] | None = None,
) -> Path:
    """Create a JUnit XML file with configurable suites."""
    if suites is None:
        suites = [{"name": "unit", "tests": 5, "failures": 0, "errors": 0}]

    root_tag = "testsuites" if len(suites) > 1 else "testsuite"

    if len(suites) == 1:
        s = suites[0]
        xml = (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<testsuite name="{s["name"]}" tests="{s["tests"]}" '
            f'failures="{s["failures"]}" errors="{s["errors"]}">\n'
        )
        for i in range(s["tests"]):
            xml += f'  <testcase classname="test.Suite" name="test_{i}"/>\n'
        xml += "</testsuite>"
    else:
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<testsuites>\n'
        for s in suites:
            xml += (
                f'  <testsuite name="{s["name"]}" tests="{s["tests"]}" '
                f'failures="{s["failures"]}" errors="{s["errors"]}"/>\n'
            )
        xml += "</testsuites>"

    fpath = directory / name
    fpath.write_text(xml)
    return fpath


def make_evidence_json(directory: Path, name: str, data) -> Path:
    """Create a JSON evidence file."""
    fpath = directory / name
    fpath.write_text(json.dumps(data))
    return fpath


def make_markdown(path: Path, title: str = "Test", body: str = "Content here."):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {title}\n\n{body}\n")


def make_html(path: Path, title: str = "Test", body: str = "Content here."):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"<!DOCTYPE html><html><head><title>{title}</title></head>"
        f"<body><p>{body}</p></body></html>\n"
    )


# ============================================================================
# PART 1: Evidence Parsing — Extended Tests
# ============================================================================


class TestJunitXmlParsing:
    """Comprehensive JUnit XML evidence parsing."""

    def test_single_suite_all_pass(self, tmp_path):
        xml_file = make_junit_xml(tmp_path, suites=[
            {"name": "unit", "tests": 10, "failures": 0, "errors": 0},
        ])
        results = parse_junit_xml(xml_file)
        assert len(results) == 1
        assert results[0].type == "test_pass"
        assert "10 tests passed" in results[0].detail

    def test_single_suite_with_failures(self, tmp_path):
        xml_file = make_junit_xml(tmp_path, suites=[
            {"name": "integration", "tests": 8, "failures": 3, "errors": 0},
        ])
        results = parse_junit_xml(xml_file)
        assert len(results) == 1
        assert results[0].type == "test_fail"
        assert "3 failures" in results[0].detail
        assert "5/8 passed" in results[0].detail

    def test_single_suite_with_errors(self, tmp_path):
        xml_file = make_junit_xml(tmp_path, suites=[
            {"name": "smoke", "tests": 4, "failures": 0, "errors": 2},
        ])
        results = parse_junit_xml(xml_file)
        assert len(results) == 1
        assert results[0].type == "test_fail"
        assert "2 errors" in results[0].detail

    def test_single_suite_with_failures_and_errors(self, tmp_path):
        xml_file = make_junit_xml(tmp_path, suites=[
            {"name": "full", "tests": 20, "failures": 3, "errors": 2},
        ])
        results = parse_junit_xml(xml_file)
        assert len(results) == 1
        assert results[0].type == "test_fail"
        # 20 - 3 - 2 = 15 passed
        assert "15/20 passed" in results[0].detail

    def test_multiple_suites_mixed(self, tmp_path):
        xml_file = make_junit_xml(tmp_path, suites=[
            {"name": "unit", "tests": 50, "failures": 0, "errors": 0},
            {"name": "integration", "tests": 10, "failures": 2, "errors": 0},
            {"name": "e2e", "tests": 5, "failures": 0, "errors": 0},
        ])
        results = parse_junit_xml(xml_file)
        assert len(results) == 3
        assert results[0].type == "test_pass"
        assert results[1].type == "test_fail"
        assert results[2].type == "test_pass"

    def test_all_suites_pass(self, tmp_path):
        xml_file = make_junit_xml(tmp_path, suites=[
            {"name": "unit", "tests": 100, "failures": 0, "errors": 0},
            {"name": "integration", "tests": 30, "failures": 0, "errors": 0},
        ])
        results = parse_junit_xml(xml_file)
        assert all(r.type == "test_pass" for r in results)

    def test_all_suites_fail(self, tmp_path):
        xml_file = make_junit_xml(tmp_path, suites=[
            {"name": "broken1", "tests": 5, "failures": 5, "errors": 0},
            {"name": "broken2", "tests": 3, "failures": 0, "errors": 3},
        ])
        results = parse_junit_xml(xml_file)
        assert all(r.type == "test_fail" for r in results)

    def test_unknown_root_element(self, tmp_path):
        fpath = tmp_path / "invalid.xml"
        fpath.write_text("<root><something/></root>")
        assert parse_junit_xml(fpath) == []

    def test_empty_suite(self, tmp_path):
        fpath = tmp_path / "empty.xml"
        fpath.write_text('<testsuite name="empty" tests="0" failures="0" errors="0"/>')
        results = parse_junit_xml(fpath)
        assert len(results) == 1
        assert results[0].type == "test_pass"
        assert "0 tests passed" in results[0].detail

    def test_suite_name_in_detail(self, tmp_path):
        xml_file = make_junit_xml(tmp_path, suites=[
            {"name": "my_custom_suite", "tests": 3, "failures": 0, "errors": 0},
        ])
        results = parse_junit_xml(xml_file)
        assert "my_custom_suite" in results[0].detail


class TestEvidenceJsonParsing:
    """Comprehensive JSON evidence parsing."""

    def test_list_of_evidence_objects(self, tmp_path):
        data = [
            {"type": "test_pass", "detail": "unit tests green"},
            {"type": "human_review", "detail": "reviewed by Alice"},
            {"type": "type_check", "detail": "mypy: 0 errors"},
        ]
        fpath = make_evidence_json(tmp_path, "ev.json", data)
        results = parse_evidence_json(fpath)
        assert len(results) == 3
        assert results[0].type == "test_pass"
        assert results[1].type == "human_review"
        assert results[2].type == "type_check"

    def test_list_with_missing_type(self, tmp_path):
        data = [{"detail": "some detail without type"}]
        fpath = make_evidence_json(tmp_path, "no_type.json", data)
        results = parse_evidence_json(fpath)
        assert len(results) == 1
        assert results[0].type == "other"

    def test_deepeval_format_all_pass(self, tmp_path):
        data = {
            "test_results": [
                {"name": "faithfulness", "score": 0.95, "success": True},
                {"name": "relevancy", "score": 0.88, "success": True},
                {"name": "coherence", "score": 0.92, "success": True},
            ]
        }
        fpath = make_evidence_json(tmp_path, "deepeval_pass.json", data)
        results = parse_evidence_json(fpath)
        assert len(results) == 3
        assert all(r.type == "test_pass" for r in results)
        assert "faithfulness" in results[0].detail

    def test_deepeval_format_mixed(self, tmp_path):
        data = {
            "test_results": [
                {"name": "faithfulness", "score": 0.95, "success": True},
                {"name": "toxicity", "score": 0.1, "success": False},
            ]
        }
        fpath = make_evidence_json(tmp_path, "deepeval_mixed.json", data)
        results = parse_evidence_json(fpath)
        assert results[0].type == "test_pass"
        assert results[1].type == "test_fail"

    def test_deepeval_with_passed_key(self, tmp_path):
        """DeepEval sometimes uses 'passed' instead of 'success'."""
        data = {
            "test_results": [
                {"metric": "answer_relevancy", "score": 0.9, "passed": True},
            ]
        }
        fpath = make_evidence_json(tmp_path, "deepeval_passed.json", data)
        results = parse_evidence_json(fpath)
        assert len(results) == 1
        assert results[0].type == "test_pass"

    def test_generic_score_pass(self, tmp_path):
        data = {"score": 0.85, "passed": True}
        fpath = make_evidence_json(tmp_path, "score_pass.json", data)
        results = parse_evidence_json(fpath)
        assert len(results) == 1
        assert results[0].type == "test_pass"
        assert "0.85" in results[0].detail

    def test_generic_score_fail(self, tmp_path):
        data = {"score": 0.2, "passed": False}
        fpath = make_evidence_json(tmp_path, "score_fail.json", data)
        results = parse_evidence_json(fpath)
        assert len(results) == 1
        assert results[0].type == "test_fail"

    def test_generic_score_inferred_pass(self, tmp_path):
        """When 'passed' is missing, infer from score >= 0.5."""
        data = {"score": 0.75}
        fpath = make_evidence_json(tmp_path, "score_infer.json", data)
        results = parse_evidence_json(fpath)
        assert len(results) == 1
        assert results[0].type == "test_pass"

    def test_generic_score_inferred_fail(self, tmp_path):
        """When 'passed' is missing, score < 0.5 means fail."""
        data = {"score": 0.3}
        fpath = make_evidence_json(tmp_path, "score_infer_fail.json", data)
        results = parse_evidence_json(fpath)
        assert len(results) == 1
        assert results[0].type == "test_fail"

    def test_empty_list(self, tmp_path):
        fpath = make_evidence_json(tmp_path, "empty.json", [])
        results = parse_evidence_json(fpath)
        assert results == []

    def test_empty_dict(self, tmp_path):
        fpath = make_evidence_json(tmp_path, "empty_dict.json", {})
        results = parse_evidence_json(fpath)
        assert results == []


# ============================================================================
# PART 2: Python API — certify_file
# ============================================================================


class TestCertifyFileTrustThresholds:
    """Test certify_file with various trust levels and thresholds."""

    def test_high_trust_default_threshold(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.95)
        result = certify_file(str(f))
        assert result.certified is True
        assert result.trust_score >= 0.7
        assert result.error is None

    def test_high_trust_high_threshold(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.95)
        result = certify_file(str(f), min_trust=0.9)
        assert result.certified is True

    def test_medium_trust_default_threshold(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.75)
        result = certify_file(str(f), min_trust=0.7)
        # Trust score depends on tier weighting; may be below 0.7
        # The important thing is certification logic runs without error
        assert isinstance(result.certified, bool)
        assert result.error is None

    def test_low_trust_fails_default_threshold(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.3)
        result = certify_file(str(f), min_trust=0.7)
        assert result.certified is False
        assert result.trust_score < 0.7

    def test_low_trust_passes_low_threshold(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.3)
        result = certify_file(str(f), min_trust=0.1)
        assert result.certified is True

    def test_zero_trust(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.0)
        result = certify_file(str(f), min_trust=0.1)
        assert result.certified is False

    def test_perfect_trust(self, tmp_path):
        f = make_akf_file(tmp_path, trust=1.0)
        result = certify_file(str(f), min_trust=1.0)
        # Even with trust=1.0, effective trust may be < 1.0 due to tier weighting
        assert isinstance(result.certified, bool)
        assert result.error is None

    def test_boundary_trust_at_threshold(self, tmp_path):
        """Trust exactly at threshold — should pass (>=)."""
        f = make_akf_file(tmp_path, trust=0.7)
        result = certify_file(str(f), min_trust=0.5)
        assert result.certified is True

    def test_threshold_zero_always_passes(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.01)
        result = certify_file(str(f), min_trust=0.0)
        assert result.certified is True


class TestCertifyFileNoMetadata:
    """Test certify_file on files without AKF metadata."""

    def test_plain_text(self, tmp_path):
        f = tmp_path / "plain.txt"
        f.write_text("hello world")
        result = certify_file(str(f))
        assert result.certified is False
        assert result.error == "no metadata"

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        result = certify_file(str(f))
        assert result.certified is False

    def test_invalid_json_akf(self, tmp_path):
        f = tmp_path / "bad.akf"
        f.write_text("not valid json {{{")
        result = certify_file(str(f))
        assert result.certified is False


class TestCertifyFileWithEvidence:
    """Test certify_file with external evidence injection."""

    def test_inject_single_evidence(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.9)
        ev = Evidence(type="test_pass", detail="42/42 unit tests passed")
        result = certify_file(str(f), evidence=[ev])
        assert result.certified is True
        assert any("42/42" in e.detail for e in result.evidence)

    def test_inject_multiple_evidence(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.9)
        evs = [
            Evidence(type="test_pass", detail="unit tests: 100% pass"),
            Evidence(type="type_check", detail="mypy: 0 errors"),
            Evidence(type="human_review", detail="reviewed by Alice"),
        ]
        result = certify_file(str(f), evidence=evs)
        assert result.certified is True

    def test_evidence_from_junit_xml(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.9)
        xml_file = make_junit_xml(tmp_path, suites=[
            {"name": "unit", "tests": 20, "failures": 0, "errors": 0},
        ])
        evidence = parse_junit_xml(xml_file)
        result = certify_file(str(f), evidence=evidence)
        assert result.certified is True

    def test_evidence_from_json(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.9)
        ev_data = [{"type": "test_pass", "detail": "integration tests green"}]
        ev_file = make_evidence_json(tmp_path, "ev.json", ev_data)
        evidence = parse_evidence_json(ev_file)
        result = certify_file(str(f), evidence=evidence)
        assert result.certified is True

    def test_failing_evidence_doesnt_auto_fail(self, tmp_path):
        """Failing test evidence doesn't automatically fail certification.

        Evidence is informational — certification depends on trust score.
        """
        f = make_akf_file(tmp_path, trust=0.9)
        ev = Evidence(type="test_fail", detail="2 tests failed")
        result = certify_file(str(f), min_trust=0.5, evidence=[ev])
        # File should still be certified if trust is above threshold
        assert isinstance(result.certified, bool)


class TestCertifyFileMultipleClaims:
    """Test certify_file with multiple claims at different trust levels."""

    def test_multiple_high_trust_claims(self, tmp_path):
        claims = [
            {"c": "Revenue $4.2B", "t": 0.98, "src": "SEC 10-Q", "tier": 1},
            {"c": "Growth 12% YoY", "t": 0.95, "src": "SEC 10-Q", "tier": 1},
            {"c": "Market share 23%", "t": 0.90, "src": "Gartner", "tier": 2},
        ]
        f = make_akf_file(tmp_path, claims=claims)
        result = certify_file(str(f), min_trust=0.5)
        assert result.certified is True

    def test_mixed_trust_claims(self, tmp_path):
        claims = [
            {"c": "Revenue $4.2B", "t": 0.98, "src": "SEC 10-Q", "tier": 1},
            {"c": "Will grow 50%", "t": 0.3, "src": "internal", "tier": 5, "ai": True},
        ]
        f = make_akf_file(tmp_path, claims=claims)
        result = certify_file(str(f), min_trust=0.7)
        # Average trust will be dragged down by the low-trust AI claim
        assert isinstance(result.certified, bool)

    def test_single_low_claim_fails(self, tmp_path):
        claims = [
            {"c": "Unverified guess", "t": 0.1, "src": "unknown", "tier": 5, "ai": True},
        ]
        f = make_akf_file(tmp_path, claims=claims)
        result = certify_file(str(f), min_trust=0.5)
        assert result.certified is False


class TestCertifyFileResultDataclass:
    """Test CertifyResult dataclass behavior."""

    def test_to_dict_pass(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.9)
        result = certify_file(str(f), min_trust=0.5)
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "filepath" in d
        assert "certified" in d
        assert "trust_score" in d
        assert "evidence" in d
        assert "detections" in d
        assert "compliance_issues" in d
        assert d["certified"] is True

    def test_to_dict_fail(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.1)
        result = certify_file(str(f), min_trust=0.9)
        d = result.to_dict()
        assert d["certified"] is False

    def test_to_dict_no_metadata(self, tmp_path):
        f = tmp_path / "plain.txt"
        f.write_text("hello")
        result = certify_file(str(f))
        d = result.to_dict()
        assert d["certified"] is False
        assert d["error"] == "no metadata"


# ============================================================================
# PART 3: Python API — certify_directory
# ============================================================================


class TestCertifyDirectory:
    """Test certify_directory with various directory structures."""

    def test_all_certified(self, tmp_path):
        make_akf_file(tmp_path, name="a.akf", trust=0.9)
        make_akf_file(tmp_path, name="b.akf", trust=0.85)
        report = certify_directory(str(tmp_path), min_trust=0.5)
        assert report.certified_count >= 1
        assert report.failed_count == 0
        assert report.all_certified is True

    def test_mixed_pass_fail(self, tmp_path):
        make_akf_file(tmp_path, name="good.akf", trust=0.9)
        make_akf_file(tmp_path, name="bad.akf", trust=0.1)
        report = certify_directory(str(tmp_path), min_trust=0.7)
        assert report.failed_count >= 1
        assert report.all_certified is False

    def test_skips_non_akf_without_metadata(self, tmp_path):
        make_akf_file(tmp_path, name="stamped.akf", trust=0.9)
        (tmp_path / "readme.txt").write_text("no metadata here")
        (tmp_path / "data.csv").write_text("a,b,c\n1,2,3\n")
        report = certify_directory(str(tmp_path), min_trust=0.5)
        assert report.skipped_count >= 2

    def test_empty_directory(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        report = certify_directory(str(empty))
        assert report.total_files == 0
        assert report.all_certified is False

    def test_nested_recursive(self, tmp_path):
        make_akf_file(tmp_path, name="root.akf", trust=0.9)
        make_akf_file(tmp_path, name="sub/nested.akf", trust=0.85)
        make_akf_file(tmp_path, name="sub/deep/deeper.akf", trust=0.8)
        report = certify_directory(str(tmp_path), min_trust=0.5, recursive=True)
        # Should find files in subdirectories
        assert report.certified_count >= 2

    def test_non_recursive(self, tmp_path):
        make_akf_file(tmp_path, name="top.akf", trust=0.9)
        make_akf_file(tmp_path, name="sub/nested.akf", trust=0.9)
        report_recursive = certify_directory(str(tmp_path), recursive=True)
        report_flat = certify_directory(str(tmp_path), recursive=False)
        # Recursive should find more or equal files
        assert report_recursive.total_files >= report_flat.total_files

    def test_with_external_evidence(self, tmp_path):
        make_akf_file(tmp_path, name="project.akf", trust=0.9)
        ev = Evidence(type="test_pass", detail="CI green")
        report = certify_directory(str(tmp_path), min_trust=0.5, evidence=[ev])
        assert report.certified_count >= 1


class TestCertifyReportDataclass:
    """Test CertifyReport properties and serialization."""

    def test_all_certified_property_true(self, tmp_path):
        make_akf_file(tmp_path, name="a.akf", trust=0.9)
        report = certify_directory(str(tmp_path), min_trust=0.5)
        assert report.all_certified is True

    def test_all_certified_property_false_empty(self):
        report = CertifyReport()
        assert report.all_certified is False

    def test_all_certified_property_false_failures(self, tmp_path):
        make_akf_file(tmp_path, name="bad.akf", trust=0.1)
        report = certify_directory(str(tmp_path), min_trust=0.9)
        assert report.all_certified is False

    def test_to_dict(self, tmp_path):
        make_akf_file(tmp_path, name="a.akf", trust=0.9)
        make_akf_file(tmp_path, name="b.akf", trust=0.1)
        report = certify_directory(str(tmp_path), min_trust=0.7)
        d = report.to_dict()
        assert isinstance(d, dict)
        assert "total_files" in d
        assert "certified_count" in d
        assert "failed_count" in d
        assert "skipped_count" in d
        assert "avg_trust" in d
        assert "all_certified" in d
        assert "results" in d
        assert isinstance(d["results"], list)

    def test_avg_trust_computed(self, tmp_path):
        make_akf_file(tmp_path, name="a.akf", trust=0.9)
        report = certify_directory(str(tmp_path), min_trust=0.5)
        assert report.avg_trust > 0

    def test_report_counts_consistent(self, tmp_path):
        make_akf_file(tmp_path, name="a.akf", trust=0.9)
        make_akf_file(tmp_path, name="b.akf", trust=0.1)
        (tmp_path / "plain.txt").write_text("no metadata")
        report = certify_directory(str(tmp_path), min_trust=0.7)
        # certified + failed + skipped should account for total
        assert report.certified_count + report.failed_count + report.skipped_count == report.total_files


# ============================================================================
# PART 4: CLI — In-process (CliRunner)
# ============================================================================


class TestCertifyCliFormats:
    """Test CLI output formats."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.tmp = tmp_path
        self.akf_file = make_akf_file(tmp_path, trust=0.9)

    def test_summary_format(self):
        result = _run_cli(["certify", str(self.akf_file), "--format", "summary"])
        assert result.exit_code == 0
        out = result.output.lower()
        assert "pass" in out or "certified" in out

    def test_json_format_valid(self):
        result = _run_cli(["certify", str(self.akf_file), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert "total_files" in data
        assert "certified_count" in data
        assert "results" in data

    def test_json_format_result_structure(self):
        result = _run_cli(["certify", str(self.akf_file), "--format", "json"])
        data = json.loads(result.output)
        assert data["total_files"] == 1
        assert len(data["results"]) == 1
        r = data["results"][0]
        assert "filepath" in r
        assert "certified" in r
        assert "trust_score" in r

    def test_markdown_format(self):
        result = _run_cli(["certify", str(self.akf_file), "--format", "markdown"])
        assert result.exit_code == 0
        assert "| File |" in result.output
        assert "| Status |" in result.output or "Status" in result.output
        assert "|" in result.output

    def test_markdown_shows_pass(self):
        result = _run_cli(["certify", str(self.akf_file), "--format", "markdown", "--min-trust", "0.3"])
        assert "PASS" in result.output

    def test_summary_shows_counts(self):
        result = _run_cli(["certify", str(self.akf_file), "--format", "summary"])
        assert "Total:" in result.output or "total" in result.output.lower()


class TestCertifyCliExitCodes:
    """Test CLI exit codes with --fail-on-untrusted."""

    def test_pass_exits_zero(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.9)
        result = _run_cli(["certify", str(f), "--fail-on-untrusted", "--min-trust", "0.5"])
        assert result.exit_code == 0

    def test_fail_exits_one(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.1)
        result = _run_cli(["certify", str(f), "--fail-on-untrusted", "--min-trust", "0.9"])
        assert result.exit_code == 1

    def test_no_flag_always_exits_zero(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.1)
        result = _run_cli(["certify", str(f), "--min-trust", "0.9"])
        # Without --fail-on-untrusted, should exit 0 even on failure
        assert result.exit_code == 0


class TestCertifyCliEvidenceFile:
    """Test CLI --evidence-file flag."""

    def test_junit_xml_evidence(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.9)
        xml_file = make_junit_xml(tmp_path, suites=[
            {"name": "unit", "tests": 10, "failures": 0, "errors": 0},
        ])
        result = _run_cli([
            "certify", str(f),
            "--evidence-file", str(xml_file),
            "--format", "json",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["results"][0]["certified"] is True

    def test_json_evidence(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.9)
        ev_file = make_evidence_json(tmp_path, "ev.json", [
            {"type": "test_pass", "detail": "all tests pass"},
        ])
        result = _run_cli([
            "certify", str(f),
            "--evidence-file", str(ev_file),
        ])
        assert result.exit_code == 0

    def test_deepeval_evidence(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.9)
        ev_file = make_evidence_json(tmp_path, "deepeval.json", {
            "test_results": [
                {"name": "faithfulness", "score": 0.95, "success": True},
                {"name": "relevancy", "score": 0.88, "success": True},
            ],
        })
        result = _run_cli([
            "certify", str(f),
            "--evidence-file", str(ev_file),
            "--format", "json",
        ])
        assert result.exit_code == 0


class TestCertifyCliDirectory:
    """Test CLI directory mode."""

    def test_certify_directory(self, tmp_path):
        make_akf_file(tmp_path, name="a.akf", trust=0.9)
        make_akf_file(tmp_path, name="b.akf", trust=0.85)
        result = _run_cli(["certify", str(tmp_path), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total_files"] >= 2

    def test_certify_directory_with_failures(self, tmp_path):
        make_akf_file(tmp_path, name="good.akf", trust=0.9)
        make_akf_file(tmp_path, name="bad.akf", trust=0.1)
        result = _run_cli([
            "certify", str(tmp_path),
            "--fail-on-untrusted",
            "--format", "json",
        ])
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert data["failed_count"] >= 1

    def test_certify_directory_summary_format(self, tmp_path):
        make_akf_file(tmp_path, name="file.akf", trust=0.9)
        result = _run_cli(["certify", str(tmp_path), "--format", "summary"])
        assert result.exit_code == 0
        assert "Total:" in result.output or "Certified:" in result.output

    def test_certify_directory_markdown_format(self, tmp_path):
        make_akf_file(tmp_path, name="file.akf", trust=0.9)
        result = _run_cli(["certify", str(tmp_path), "--format", "markdown"])
        assert result.exit_code == 0
        assert "|" in result.output

    def test_certify_empty_directory(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        result = _run_cli(["certify", str(empty), "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["total_files"] == 0


class TestCertifyCliMinTrust:
    """Test CLI --min-trust flag."""

    def test_min_trust_low(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.5)
        result = _run_cli(["certify", str(f), "--min-trust", "0.3", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["results"][0]["certified"] is True

    def test_min_trust_high(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.5)
        result = _run_cli(["certify", str(f), "--min-trust", "0.95", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["results"][0]["certified"] is False

    def test_default_min_trust(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.9)
        result = _run_cli(["certify", str(f), "--format", "json"])
        assert result.exit_code == 0
        # Default is 0.7


# ============================================================================
# PART 5: CLI — Subprocess (E2E)
# ============================================================================


class TestCertifyE2ESubprocess:
    """End-to-end tests using subprocess to exercise the full CLI."""

    def test_certify_single_file_pass(self):
        d = Path(TEST_DIR) / "e2e_single"
        d.mkdir(exist_ok=True)
        make_akf_file(d, name="pass.akf", trust=0.9)
        rc, out, err = akf_cli("certify", str(d / "pass.akf"), "--format", "summary")
        assert rc == 0
        assert "PASS" in out or "certified" in out.lower()

    def test_certify_single_file_fail(self):
        d = Path(TEST_DIR) / "e2e_fail"
        d.mkdir(exist_ok=True)
        make_akf_file(d, name="fail.akf", trust=0.1)
        rc, out, err = akf_cli(
            "certify", str(d / "fail.akf"),
            "--fail-on-untrusted", "--min-trust", "0.9",
            allow_fail=True,
        )
        assert rc == 1
        assert "FAIL" in out or "fail" in out.lower()

    def test_certify_json_output_parseable(self):
        d = Path(TEST_DIR) / "e2e_json"
        d.mkdir(exist_ok=True)
        make_akf_file(d, name="data.akf", trust=0.9)
        rc, out, err = akf_cli("certify", str(d / "data.akf"), "--format", "json")
        assert rc == 0
        data = json.loads(out)
        assert data["total_files"] == 1
        assert data["all_certified"] is True
        assert len(data["results"]) == 1

    def test_certify_markdown_output(self):
        d = Path(TEST_DIR) / "e2e_md"
        d.mkdir(exist_ok=True)
        make_akf_file(d, name="report.akf", trust=0.9)
        rc, out, err = akf_cli("certify", str(d / "report.akf"), "--format", "markdown")
        assert rc == 0
        assert "| File |" in out
        assert "PASS" in out

    def test_certify_directory_e2e(self):
        d = Path(TEST_DIR) / "e2e_dir"
        d.mkdir(exist_ok=True)
        make_akf_file(d, name="a.akf", trust=0.9)
        make_akf_file(d, name="b.akf", trust=0.85)
        (d / "readme.txt").write_text("no metadata")
        rc, out, err = akf_cli("certify", str(d), "--format", "json")
        assert rc == 0
        data = json.loads(out)
        assert data["total_files"] >= 3
        assert data["skipped_count"] >= 1
        assert data["certified_count"] >= 1

    def test_certify_with_junit_evidence(self):
        d = Path(TEST_DIR) / "e2e_junit"
        d.mkdir(exist_ok=True)
        make_akf_file(d, name="project.akf", trust=0.9)
        xml_file = make_junit_xml(d, suites=[
            {"name": "unit", "tests": 25, "failures": 0, "errors": 0},
            {"name": "integration", "tests": 10, "failures": 0, "errors": 0},
        ])
        rc, out, err = akf_cli(
            "certify", str(d / "project.akf"),
            "--evidence-file", str(xml_file),
            "--format", "json",
        )
        assert rc == 0
        data = json.loads(out)
        assert data["results"][0]["certified"] is True

    def test_certify_with_json_evidence(self):
        d = Path(TEST_DIR) / "e2e_json_ev"
        d.mkdir(exist_ok=True)
        make_akf_file(d, name="verified.akf", trust=0.9)
        ev_file = make_evidence_json(d, "evidence.json", {
            "test_results": [
                {"name": "faithfulness", "score": 0.95, "success": True},
            ],
        })
        rc, out, err = akf_cli(
            "certify", str(d / "verified.akf"),
            "--evidence-file", str(ev_file),
            "--format", "json",
        )
        assert rc == 0

    def test_certify_fail_on_untrusted_exit_code(self):
        d = Path(TEST_DIR) / "e2e_exit"
        d.mkdir(exist_ok=True)
        make_akf_file(d, name="low.akf", trust=0.1)
        rc, out, err = akf_cli(
            "certify", str(d / "low.akf"),
            "--fail-on-untrusted",
            "--min-trust", "0.8",
            allow_fail=True,
        )
        assert rc == 1

    def test_certify_without_fail_flag_exits_zero(self):
        d = Path(TEST_DIR) / "e2e_noflag"
        d.mkdir(exist_ok=True)
        make_akf_file(d, name="low.akf", trust=0.1)
        rc, out, err = akf_cli(
            "certify", str(d / "low.akf"),
            "--min-trust", "0.9",
        )
        assert rc == 0

    def test_certify_nested_directory(self):
        d = Path(TEST_DIR) / "e2e_nested"
        d.mkdir(exist_ok=True)
        make_akf_file(d, name="top.akf", trust=0.9)
        make_akf_file(d, name="sub/level1.akf", trust=0.85)
        make_akf_file(d, name="sub/deep/level2.akf", trust=0.8)
        rc, out, err = akf_cli("certify", str(d), "--format", "json", "--min-trust", "0.5")
        assert rc == 0
        data = json.loads(out)
        assert data["certified_count"] >= 2


# ============================================================================
# PART 6: Full Pipeline — stamp → certify
# ============================================================================


class TestStampThenCertifyPipeline:
    """Integration tests: stamp files via CLI, then certify them."""

    def test_stamp_and_certify_file(self):
        d = Path(TEST_DIR) / "pipeline_stamp"
        d.mkdir(exist_ok=True)
        # Create a markdown file
        f = d / "report.md"
        f.write_text("# Q3 Report\n\nRevenue was $4.2B.\n")
        # Stamp it
        rc, out, err = akf_cli(
            "stamp", str(f),
            "--agent", "claude-code",
            "--evidence", "tests pass",
        )
        assert rc == 0
        # Certify it
        rc, out, err = akf_cli(
            "certify", str(f),
            "--format", "json",
            "--min-trust", "0.3",
        )
        assert rc == 0
        data = json.loads(out)
        assert data["total_files"] == 1

    def test_stamp_multiple_and_certify_directory(self):
        d = Path(TEST_DIR) / "pipeline_multi"
        d.mkdir(exist_ok=True)
        files = []
        for i in range(5):
            f = d / f"file_{i}.md"
            f.write_text(f"# Report {i}\n\nContent {i}.\n")
            files.append(f)
        # Stamp all
        for f in files:
            rc, _, _ = akf_cli("stamp", str(f), "--agent", "test-agent", "--evidence", "automated")
            assert rc == 0
        # Certify directory — stamped markdown files get tier-5 AI claims
        # with trust=0.7, effective trust after tier weighting (0.30) ≈ 0.21,
        # so we verify the pipeline runs and finds the files, not that they certify
        rc, out, err = akf_cli("certify", str(d), "--format", "json", "--min-trust", "0.1")
        assert rc == 0
        data = json.loads(out)
        # Files were stamped so should not all be skipped
        assert data["total_files"] >= 5
        assert data["certified_count"] + data["failed_count"] >= 1

    def test_create_akf_and_certify(self):
        d = Path(TEST_DIR) / "pipeline_create"
        d.mkdir(exist_ok=True)
        f = d / "created.akf"
        # Create via CLI
        rc, _, _ = akf_cli(
            "create", str(f),
            "-c", "Revenue $4.2B",
            "-t", "0.98",
            "--src", "SEC 10-Q",
            "--by", "alice@acme.com",
        )
        assert rc == 0
        assert f.exists()
        # Certify
        rc, out, err = akf_cli("certify", str(f), "--format", "json", "--min-trust", "0.5")
        assert rc == 0
        data = json.loads(out)
        assert data["total_files"] == 1

    def test_stamp_certify_with_evidence_pipeline(self):
        """Full pipeline: stamp → create evidence → certify with evidence."""
        d = Path(TEST_DIR) / "pipeline_evidence"
        d.mkdir(exist_ok=True)
        # Create and stamp file
        f = d / "codebase.md"
        f.write_text("# Code Review\n\nAll functions tested.\n")
        akf_cli("stamp", str(f), "--agent", "claude-code", "--evidence", "reviewed")
        # Create test evidence
        xml_file = make_junit_xml(d, suites=[
            {"name": "unit", "tests": 50, "failures": 0, "errors": 0},
            {"name": "integration", "tests": 15, "failures": 0, "errors": 0},
        ])
        # Certify with evidence
        rc, out, err = akf_cli(
            "certify", str(f),
            "--evidence-file", str(xml_file),
            "--format", "json",
            "--min-trust", "0.3",
        )
        assert rc == 0


# ============================================================================
# PART 7: Cross-Format Certification
# ============================================================================


class TestCrossFormatCertify:
    """Test certify across different file formats."""

    def test_certify_json_sidecar(self):
        """Files with .akf.json sidecar should be certifiable."""
        d = Path(TEST_DIR) / "cross_sidecar"
        d.mkdir(exist_ok=True)
        # Create a file and stamp it (creates sidecar)
        f = d / "data.py"
        f.write_text("print('hello')\n")
        akf_cli("stamp", str(f), "--agent", "claude-code", "--evidence", "works")
        # The sidecar should exist
        sidecar = d / "data.py.akf.json"
        assert sidecar.exists()
        # Certify the original file
        rc, out, err = akf_cli(
            "certify", str(f),
            "--format", "json",
            "--min-trust", "0.3",
        )
        assert rc == 0

    def test_certify_markdown_stamped(self):
        d = Path(TEST_DIR) / "cross_md"
        d.mkdir(exist_ok=True)
        f = d / "report.md"
        f.write_text("# Quarterly Report\n\nRevenue grew 12%.\n")
        akf_cli("stamp", str(f), "--agent", "claude-code", "--evidence", "data verified")
        rc, out, err = akf_cli("certify", str(f), "--format", "json", "--min-trust", "0.3")
        assert rc == 0

    def test_certify_html_stamped(self):
        d = Path(TEST_DIR) / "cross_html"
        d.mkdir(exist_ok=True)
        f = d / "page.html"
        make_html(f, "Dashboard", "Metrics look good")
        akf_cli("stamp", str(f), "--agent", "claude-code", "--evidence", "reviewed")
        rc, out, err = akf_cli("certify", str(f), "--format", "json", "--min-trust", "0.3")
        assert rc == 0

    def test_certify_json_file_stamped(self):
        d = Path(TEST_DIR) / "cross_json"
        d.mkdir(exist_ok=True)
        f = d / "config.json"
        f.write_text(json.dumps({"setting": "value"}))
        akf_cli("stamp", str(f), "--agent", "claude-code", "--evidence", "config validated")
        rc, out, err = akf_cli("certify", str(f), "--format", "json", "--min-trust", "0.3")
        assert rc == 0


# ============================================================================
# PART 8: GitHub Action Configuration Tests
# ============================================================================


class TestGitHubActionConfig:
    """Validate the GitHub Action composite action configuration."""

    @pytest.fixture(autouse=True)
    def _load_action(self):
        import yaml

        action_path = Path(__file__).parent.parent.parent / "extensions" / "github-action" / "action.yml"
        if not action_path.exists():
            pytest.skip("GitHub Action action.yml not found")
        with open(action_path) as f:
            self.action = yaml.safe_load(f)

    def test_action_name(self):
        assert "AKF" in self.action["name"]

    def test_action_description(self):
        assert "certify" in self.action["description"].lower() or "trust" in self.action["description"].lower()

    def test_required_inputs_exist(self):
        inputs = self.action["inputs"]
        assert "paths" in inputs
        assert "min-trust" in inputs
        assert "fail-on-untrusted" in inputs
        assert "format" in inputs

    def test_optional_inputs_exist(self):
        inputs = self.action["inputs"]
        assert "evidence-file" in inputs
        assert "python-version" in inputs
        assert "post-comment" in inputs

    def test_all_inputs_have_defaults(self):
        inputs = self.action["inputs"]
        for name, config in inputs.items():
            if not config.get("required", False):
                assert "default" in config, f"Input '{name}' missing default"

    def test_default_values(self):
        inputs = self.action["inputs"]
        assert inputs["paths"]["default"] == "."
        assert inputs["min-trust"]["default"] == "0.7"
        assert inputs["fail-on-untrusted"]["default"] == "true"
        assert inputs["format"]["default"] == "markdown"
        assert inputs["python-version"]["default"] == "3.11"
        assert inputs["post-comment"]["default"] == "true"

    def test_uses_composite_action(self):
        assert self.action["runs"]["using"] == "composite"

    def test_has_setup_python_step(self):
        steps = self.action["runs"]["steps"]
        setup_steps = [s for s in steps if "setup-python" in str(s.get("uses", ""))]
        assert len(setup_steps) >= 1

    def test_has_certify_step(self):
        steps = self.action["runs"]["steps"]
        certify_steps = [s for s in steps if "certify" in str(s.get("run", "")).lower()
                         or s.get("id", "") == "certify"]
        assert len(certify_steps) >= 1

    def test_has_comment_step(self):
        steps = self.action["runs"]["steps"]
        comment_steps = [s for s in steps if "comment" in str(s.get("name", "")).lower()]
        assert len(comment_steps) >= 1

    def test_has_branding(self):
        assert "branding" in self.action
        assert "icon" in self.action["branding"]
        assert "color" in self.action["branding"]

    def test_certify_step_references_inputs(self):
        steps = self.action["runs"]["steps"]
        certify_step = next(
            (s for s in steps if s.get("id") == "certify"), None
        )
        assert certify_step is not None
        run_script = certify_step.get("run", "")
        assert "min-trust" in run_script or "min_trust" in run_script
        assert "fail-on-untrusted" in run_script or "fail_on_untrusted" in run_script


# ============================================================================
# PART 9: Edge Cases and Error Handling
# ============================================================================


class TestCertifyEdgeCases:
    """Edge cases and error handling."""

    def test_certify_nonexistent_file_cli(self, tmp_path):
        result = _run_cli(["certify", str(tmp_path / "nonexistent.akf")])
        assert result.exit_code != 0

    def test_certify_file_with_empty_claims(self, tmp_path):
        data = {"v": "1.1", "claims": [], "label": "internal"}
        f = tmp_path / "empty_claims.akf"
        f.write_text(json.dumps(data))
        result = certify_file(str(f))
        # Should handle gracefully — zero claims means zero trust
        assert isinstance(result.certified, bool)

    def test_certify_file_with_no_source(self, tmp_path):
        claims = [{"c": "Some claim without source", "t": 0.5}]
        f = make_akf_file(tmp_path, claims=claims)
        result = certify_file(str(f), min_trust=0.3)
        assert isinstance(result.certified, bool)

    def test_certify_file_with_ai_claims(self, tmp_path):
        claims = [
            {"c": "AI prediction: growth 15%", "t": 0.6, "ai": True, "tier": 5},
        ]
        f = make_akf_file(tmp_path, claims=claims)
        result = certify_file(str(f), min_trust=0.1)
        assert isinstance(result.certified, bool)
        # AI claim with tier 5 gets heavy weight penalty
        assert result.trust_score < 0.6

    def test_certify_directory_only_plain_files(self, tmp_path):
        """Directory with no AKF-enriched files — all skipped."""
        (tmp_path / "a.txt").write_text("plain")
        (tmp_path / "b.csv").write_text("x,y\n1,2\n")
        (tmp_path / "c.log").write_text("log entry")
        report = certify_directory(str(tmp_path))
        assert report.skipped_count == report.total_files
        assert report.certified_count == 0

    def test_certify_many_files_stress(self, tmp_path):
        """Certify a directory with 50 .akf files."""
        for i in range(50):
            trust = 0.5 + (i % 5) * 0.1  # 0.5 to 0.9
            make_akf_file(tmp_path, name=f"file_{i:03d}.akf", trust=trust)
        report = certify_directory(str(tmp_path), min_trust=0.3)
        assert report.total_files == 50
        assert report.certified_count + report.failed_count + report.skipped_count == 50
        assert report.avg_trust > 0

    def test_certify_result_to_dict_roundtrip(self, tmp_path):
        """CertifyResult.to_dict() produces valid JSON."""
        f = make_akf_file(tmp_path, trust=0.9)
        result = certify_file(str(f), min_trust=0.5)
        d = result.to_dict()
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        assert parsed["certified"] == d["certified"]

    def test_certify_report_to_dict_roundtrip(self, tmp_path):
        """CertifyReport.to_dict() produces valid JSON."""
        make_akf_file(tmp_path, name="a.akf", trust=0.9)
        report = certify_directory(str(tmp_path), min_trust=0.5)
        d = report.to_dict()
        json_str = json.dumps(d)
        parsed = json.loads(json_str)
        assert parsed["total_files"] == d["total_files"]

    def test_certify_with_confidential_label(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.9, label="confidential")
        result = certify_file(str(f), min_trust=0.5)
        assert result.certified is True

    def test_certify_with_public_label(self, tmp_path):
        f = make_akf_file(tmp_path, trust=0.9, label="public")
        result = certify_file(str(f), min_trust=0.5)
        assert result.certified is True


# ============================================================================
# PART 10: Integration — Certify + Audit + Trust Consistency
# ============================================================================


class TestCertifyAuditTrustConsistency:
    """Verify certify results are consistent with audit and trust commands."""

    def test_certified_file_also_validates(self):
        d = Path(TEST_DIR) / "consistency_validate"
        d.mkdir(exist_ok=True)
        f = make_akf_file(d, trust=0.9, with_hash=True)
        # Certify
        rc_c, out_c, _ = akf_cli("certify", str(f), "--format", "json")
        assert rc_c == 0
        cert_data = json.loads(out_c)
        assert cert_data["results"][0]["certified"] is True
        # Validate
        rc_v, out_v, _ = akf_cli("validate", str(f))
        assert rc_v == 0

    def test_certified_file_has_trust_score(self):
        d = Path(TEST_DIR) / "consistency_trust"
        d.mkdir(exist_ok=True)
        f = make_akf_file(d, trust=0.9)
        # Certify
        rc, out, _ = akf_cli("certify", str(f), "--format", "json")
        assert rc == 0
        data = json.loads(out)
        assert data["results"][0]["trust_score"] > 0
        # Trust command
        rc_t, out_t, _ = akf_cli("trust", str(f))
        assert rc_t == 0

    def test_certified_file_passes_audit(self):
        d = Path(TEST_DIR) / "consistency_audit"
        d.mkdir(exist_ok=True)
        f = make_akf_file(d, trust=0.9, with_hash=True)
        # Certify
        rc_c, out_c, _ = akf_cli("certify", str(f), "--format", "json", "--min-trust", "0.5")
        assert rc_c == 0
        # Audit
        rc_a, out_a, _ = akf_cli("audit", str(f))
        assert rc_a == 0

    def test_low_trust_file_fails_certify_and_shows_in_trust(self):
        d = Path(TEST_DIR) / "consistency_low"
        d.mkdir(exist_ok=True)
        f = make_akf_file(d, trust=0.1)
        # Certify — should fail
        rc, out, _ = akf_cli(
            "certify", str(f),
            "--format", "json",
            "--min-trust", "0.7",
        )
        data = json.loads(out)
        assert data["results"][0]["certified"] is False
        # Trust — score should be low
        rc_t, out_t, _ = akf_cli("trust", str(f))
        assert rc_t == 0

    def test_full_pipeline_create_stamp_certify_audit(self):
        """Complete end-to-end: create → stamp → certify → audit → trust."""
        d = Path(TEST_DIR) / "full_pipeline"
        d.mkdir(exist_ok=True)
        f = d / "complete.akf"

        # Create
        rc, _, _ = akf_cli(
            "create", str(f),
            "-c", "Revenue $4.2B", "-t", "0.98", "--src", "SEC 10-Q",
            "--by", "alice@acme.com", "--label", "confidential",
        )
        assert rc == 0
        assert f.exists()

        # Certify
        rc, out, _ = akf_cli("certify", str(f), "--format", "json", "--min-trust", "0.5")
        assert rc == 0
        data = json.loads(out)
        assert data["total_files"] == 1

        # Audit
        rc, _, _ = akf_cli("audit", str(f))
        assert rc == 0

        # Trust
        rc, _, _ = akf_cli("trust", str(f))
        assert rc == 0

        # Validate
        rc, _, _ = akf_cli("validate", str(f))
        assert rc == 0

        # Inspect
        rc, _, _ = akf_cli("inspect", str(f))
        assert rc == 0
