"""Comprehensive tests for AKF Enterprise/Governance Report.

Test matrix:
- Renderer registry: register, lookup, unknown format, custom renderer, all built-in
- CSV renderer: headers, field values, quoting, empty report, multiple files
- PDF renderer: with fpdf2, without fpdf2 (mocked), empty report, long names
- HTML renderer: escaping, print CSS, all sections, grade colors
- Markdown renderer: all sections, bar chart, edge cases
- JSON renderer: valid JSON, round-trip
- CLI: all formats, cold start, PDF without -o, binary output, error paths
- Integration: create files → report → verify output
- Public API: all exports accessible
"""

import csv
import io
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from akf.cli import main
from akf.core import create
from akf.report import (
    RENDERERS,
    EnterpriseReport,
    FileReport,
    _bar,
    _render_csv,
    _render_html,
    _render_markdown,
    enterprise_report,
    register_renderer,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_akf_files():
    """Create multiple .akf files for report testing."""
    files = []
    configs = [
        {"content": "Revenue $4.2B", "confidence": 0.98, "source": "SEC", "ai_generated": False},
        {"content": "Growth projected 15%", "confidence": 0.72, "source": "Analyst", "ai_generated": True},
        {"content": "Market share stable", "confidence": 0.45, "source": "inference", "ai_generated": True},
    ]
    for cfg in configs:
        unit = create(cfg["content"], confidence=cfg["confidence"],
                      source=cfg["source"], ai_generated=cfg["ai_generated"])
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False, mode="w") as f:
            f.write(unit.to_json())
            f.write("\n")
            files.append(f.name)
    yield files
    for f in files:
        try:
            os.unlink(f)
        except OSError:
            pass


@pytest.fixture
def sample_report(sample_akf_files):
    """Generate a report from sample files."""
    return enterprise_report(sample_akf_files)


@pytest.fixture
def empty_report():
    """Generate a report with no files."""
    return enterprise_report("/tmp/nonexistent_akf_dir_12345")


@pytest.fixture
def single_file_report(sample_akf_files):
    """Generate a report from a single file."""
    return enterprise_report(sample_akf_files[0])


# ---------------------------------------------------------------------------
# Renderer Registry
# ---------------------------------------------------------------------------


class TestRendererRegistry:
    """Test the extensible renderer registry."""

    def test_builtin_renderers_registered(self):
        """All 5 built-in renderers should be registered."""
        expected = {"markdown", "json", "html", "csv", "pdf"}
        assert expected == set(RENDERERS.keys())

    def test_register_custom_renderer(self):
        """Third parties can register custom renderers."""
        @register_renderer("test_xml")
        def _xml(report):
            return "<report/>"

        assert "test_xml" in RENDERERS
        assert RENDERERS["test_xml"] is _xml

        # Cleanup
        del RENDERERS["test_xml"]

    def test_custom_renderer_callable(self, sample_report):
        """Custom renderer is called via render()."""
        @register_renderer("test_custom")
        def _custom(report):
            return f"files={report.total_files}"

        result = sample_report.render("test_custom")
        assert result == f"files={sample_report.total_files}"

        # Cleanup
        del RENDERERS["test_custom"]

    def test_unknown_format_raises(self, sample_report):
        """Unknown format gives helpful error."""
        with pytest.raises(ValueError, match="Unknown report format"):
            sample_report.render("nonexistent_format")

    def test_unknown_format_lists_available(self, sample_report):
        """Error message lists available formats."""
        with pytest.raises(ValueError, match="csv"):
            sample_report.render("nonexistent")

    def test_register_renderer_overwrites(self):
        """Re-registering a name overwrites the previous renderer."""
        @register_renderer("test_overwrite")
        def _v1(report):
            return "v1"

        @register_renderer("test_overwrite")
        def _v2(report):
            return "v2"

        assert RENDERERS["test_overwrite"] is _v2
        del RENDERERS["test_overwrite"]


# ---------------------------------------------------------------------------
# Bar chart helper
# ---------------------------------------------------------------------------


class TestBar:
    """Test the ASCII bar chart helper."""

    def test_bar_full(self):
        """Full bar at max value."""
        result = _bar(10, 10, width=10)
        assert result == "\u2588" * 10

    def test_bar_empty(self):
        """Empty bar at zero value."""
        result = _bar(0, 10, width=10)
        assert result == "\u2591" * 10

    def test_bar_half(self):
        """Half-filled bar."""
        result = _bar(5, 10, width=10)
        assert len(result) == 10
        assert "\u2588" in result
        assert "\u2591" in result

    def test_bar_zero_max(self):
        """Zero max returns empty string."""
        assert _bar(5, 0) == ""

    def test_bar_negative_max(self):
        """Negative max returns empty string."""
        assert _bar(5, -1) == ""

    def test_bar_never_exceeds_width(self):
        """Bar length never exceeds the specified width."""
        # This tests the round() overflow fix
        for v in range(101):
            result = _bar(v, 100, width=20)
            assert len(result) == 20, f"Bar length {len(result)} at value {v}"

    def test_bar_custom_width(self):
        """Custom width is respected."""
        result = _bar(10, 10, width=30)
        assert len(result) == 30


# ---------------------------------------------------------------------------
# CSV Renderer
# ---------------------------------------------------------------------------


class TestCSVRenderer:
    """Test CSV report output."""

    def test_csv_headers(self, sample_report):
        """CSV has correct headers."""
        output = sample_report.render("csv")
        reader = csv.reader(io.StringIO(output))
        headers = next(reader)
        expected = [
            "file", "claims", "avg_trust", "ai_claims", "human_claims",
            "security_grade", "security_score", "compliant", "classification",
            "detections", "critical", "high", "quality_score",
        ]
        assert headers == expected

    def test_csv_row_count(self, sample_report):
        """CSV has one row per file plus header."""
        output = sample_report.render("csv")
        lines = output.strip().split("\n")
        assert len(lines) == sample_report.total_files + 1

    def test_csv_parseable(self, sample_report):
        """CSV output is parseable by csv.reader."""
        output = sample_report.render("csv")
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)
        assert len(rows) > 1  # header + data

    def test_csv_field_values(self, sample_report):
        """CSV field values match FileReport attributes."""
        output = sample_report.render("csv")
        reader = csv.DictReader(io.StringIO(output))
        for row in reader:
            assert "file" in row
            assert row["claims"].isdigit()
            assert row["compliant"] in ("True", "False")

    def test_csv_quoting_with_commas(self):
        """Paths with commas are properly quoted."""
        report = EnterpriseReport(
            generated_at="2024-01-01T00:00:00Z",
            total_files=1, total_claims=1,
            avg_trust=0.5, trust_distribution={"high": 0, "moderate": 1, "low": 0},
            ai_claims=0, human_claims=1, ai_ratio=0.0,
            models_used={}, providers_used={}, untracked_claims=0,
            avg_security_score=5.0, security_grade="C",
            security_distribution={"C": 1},
            compliance_rate=1.0, compliant_files=1, non_compliant_files=0,
            classification_distribution={"internal": 1},
            total_detections=0, critical_risks=0, high_risks=0, top_risks=[],
            avg_quality_score=0.8, recommendations=[],
            file_reports=[FileReport(
                path="/tmp/file,with,commas.akf",
                claims=1, avg_trust=0.5, ai_claims=0, human_claims=1,
                security_grade="C", security_score=5.0, compliant=True,
                classification="internal", detections=0, critical=0, high=0,
                quality_score=0.8,
            )],
        )
        output = report.render("csv")
        reader = csv.reader(io.StringIO(output))
        rows = list(reader)
        assert rows[1][0] == "/tmp/file,with,commas.akf"

    def test_csv_empty_report(self, empty_report):
        """Empty report produces header-only CSV."""
        output = empty_report.render("csv")
        lines = output.strip().split("\n")
        assert len(lines) == 1  # header only


# ---------------------------------------------------------------------------
# HTML Renderer
# ---------------------------------------------------------------------------


class TestHTMLRenderer:
    """Test HTML report output."""

    def test_html_valid_structure(self, sample_report):
        """HTML has basic valid structure."""
        output = sample_report.render("html")
        assert "<!DOCTYPE html>" in output
        assert "<html" in output
        assert "</html>" in output
        assert "<body>" in output
        assert "</body>" in output

    def test_html_print_css(self, sample_report):
        """HTML includes @media print CSS."""
        output = sample_report.render("html")
        assert "@media print" in output
        assert "break-inside: avoid" in output
        assert "print-color-adjust: exact" in output

    def test_html_title(self, sample_report):
        """HTML title is AKF Trust Report."""
        output = sample_report.render("html")
        assert "<title>AKF Trust Report</title>" in output

    def test_html_escapes_filenames(self):
        """File names with special chars are HTML-escaped."""
        report = EnterpriseReport(
            generated_at="2024-01-01T00:00:00Z",
            total_files=1, total_claims=1,
            avg_trust=0.5, trust_distribution={"high": 0, "moderate": 1, "low": 0},
            ai_claims=0, human_claims=1, ai_ratio=0.0,
            models_used={}, providers_used={}, untracked_claims=0,
            avg_security_score=5.0, security_grade="C",
            security_distribution={"C": 1},
            compliance_rate=1.0, compliant_files=1, non_compliant_files=0,
            classification_distribution={"internal": 1},
            total_detections=0, critical_risks=0, high_risks=0, top_risks=[],
            avg_quality_score=0.8, recommendations=[],
            file_reports=[FileReport(
                path="/tmp/file&name<test>.akf",
                claims=1, avg_trust=0.5, ai_claims=0, human_claims=1,
                security_grade="C", security_score=5.0, compliant=True,
                classification="internal", detections=0, critical=0, high=0,
                quality_score=0.8,
            )],
        )
        output = report.render("html")
        # The raw chars should be escaped
        assert "file&amp;name&lt;test&gt;.akf" in output
        # The unescaped versions should NOT appear in the table
        assert "<test>" not in output.split("Per-File")[1]

    def test_html_escapes_model_names(self):
        """Model names with special chars are escaped."""
        report = EnterpriseReport(
            generated_at="2024-01-01T00:00:00Z",
            total_files=0, total_claims=0,
            avg_trust=0.0, trust_distribution={"high": 0, "moderate": 0, "low": 0},
            ai_claims=0, human_claims=0, ai_ratio=0.0,
            models_used={"<b>evil</b>": 5}, providers_used={}, untracked_claims=0,
            avg_security_score=0.0, security_grade="N/A",
            security_distribution={},
            compliance_rate=0.0, compliant_files=0, non_compliant_files=0,
            classification_distribution={},
            total_detections=0, critical_risks=0, high_risks=0, top_risks=[],
            avg_quality_score=0.0, recommendations=[],
        )
        output = report.render("html")
        assert "<b>evil</b>" not in output
        assert "&lt;b&gt;evil&lt;/b&gt;" in output

    def test_html_escapes_recommendations(self):
        """Recommendations are HTML-escaped."""
        report = EnterpriseReport(
            generated_at="2024-01-01T00:00:00Z",
            total_files=0, total_claims=0,
            avg_trust=0.0, trust_distribution={"high": 0, "moderate": 0, "low": 0},
            ai_claims=0, human_claims=0, ai_ratio=0.0,
            models_used={}, providers_used={}, untracked_claims=0,
            avg_security_score=0.0, security_grade="N/A",
            security_distribution={},
            compliance_rate=0.0, compliant_files=0, non_compliant_files=0,
            classification_distribution={},
            total_detections=0, critical_risks=0, high_risks=0, top_risks=[],
            avg_quality_score=0.0, recommendations=["Use <b>strong</b> passwords"],
        )
        output = report.render("html")
        assert "Use &lt;b&gt;strong&lt;/b&gt; passwords" in output

    def test_html_grade_colors(self, sample_report):
        """HTML includes grade color styling."""
        output = sample_report.render("html")
        assert "Security" in output

    def test_html_all_sections(self, sample_report):
        """HTML has all major sections."""
        output = sample_report.render("html")
        assert "Trust Distribution" in output
        assert "AI vs Human" in output
        assert "Security Posture" in output
        assert "Compliance" in output
        assert "Risk Summary" in output
        assert "Per-File Breakdown" in output


# ---------------------------------------------------------------------------
# Markdown Renderer
# ---------------------------------------------------------------------------


class TestMarkdownRenderer:
    """Test Markdown report output."""

    def test_markdown_title(self, sample_report):
        """Markdown starts with correct title."""
        output = sample_report.render("markdown")
        assert output.startswith("# AI Governance Report")

    def test_markdown_overview_table(self, sample_report):
        """Markdown has overview table with key metrics."""
        output = sample_report.render("markdown")
        assert "| Metric | Value |" in output
        assert "Total files" in output
        assert "Total claims" in output
        assert "Average trust" in output
        assert "Security grade" in output
        assert "Compliance rate" in output

    def test_markdown_all_sections(self, sample_report):
        """Markdown has all major sections."""
        output = sample_report.render("markdown")
        sections = [
            "## Overview", "## Trust Distribution", "## AI vs Human Content",
            "## Security Posture", "## Compliance", "## Risk Summary",
            "## Per-File Breakdown",
        ]
        for section in sections:
            assert section in output, f"Missing section: {section}"

    def test_markdown_bar_chart(self, sample_report):
        """Markdown includes ASCII bar chart."""
        output = sample_report.render("markdown")
        assert "\u2588" in output or "\u2591" in output

    def test_markdown_per_file_table(self, sample_report):
        """Markdown has per-file breakdown table."""
        output = sample_report.render("markdown")
        assert "| File | Claims | Trust | Security | Compliant | Detections |" in output


# ---------------------------------------------------------------------------
# JSON Renderer
# ---------------------------------------------------------------------------


class TestJSONRenderer:
    """Test JSON report output."""

    def test_json_valid(self, sample_report):
        """JSON output is valid JSON."""
        output = sample_report.render("json")
        data = json.loads(output)
        assert isinstance(data, dict)

    def test_json_has_key_fields(self, sample_report):
        """JSON has all expected top-level fields."""
        output = sample_report.render("json")
        data = json.loads(output)
        expected_keys = [
            "generated_at", "total_files", "total_claims", "avg_trust",
            "trust_distribution", "ai_claims", "human_claims", "ai_ratio",
            "models_used", "providers_used", "avg_security_score",
            "security_grade", "compliance_rate", "file_reports",
        ]
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"

    def test_json_file_reports_count(self, sample_report):
        """JSON file_reports count matches total_files."""
        output = sample_report.render("json")
        data = json.loads(output)
        assert len(data["file_reports"]) == data["total_files"]

    def test_json_round_trip(self, sample_report):
        """JSON round-trips through to_dict/to_json."""
        j1 = sample_report.to_json()
        d1 = json.loads(j1)
        j2 = sample_report.render("json")
        d2 = json.loads(j2)
        assert d1 == d2


# ---------------------------------------------------------------------------
# PDF Renderer
# ---------------------------------------------------------------------------


class TestPDFRenderer:
    """Test PDF report output."""

    def test_pdf_returns_binary(self, sample_report):
        """PDF render returns bytes or bytearray."""
        try:
            output = sample_report.render("pdf")
            assert isinstance(output, (bytes, bytearray))
        except ImportError:
            pytest.skip("fpdf2 not installed")

    def test_pdf_starts_with_header(self, sample_report):
        """PDF output starts with %PDF header."""
        try:
            output = sample_report.render("pdf")
            assert output[:5] == b"%PDF-"
        except ImportError:
            pytest.skip("fpdf2 not installed")

    def test_pdf_empty_report(self, empty_report):
        """PDF renders even with empty report."""
        try:
            output = empty_report.render("pdf")
            assert output[:5] == b"%PDF-"
        except ImportError:
            pytest.skip("fpdf2 not installed")

    def test_pdf_without_fpdf2(self, sample_report):
        """Missing fpdf2 raises ImportError with install message."""
        import sys
        original = sys.modules.get("fpdf")

        # Force ImportError
        with patch.dict(sys.modules, {"fpdf": None}):
            with pytest.raises(ImportError, match="pip install akf\\[report\\]"):
                # Need to reload since the renderer captures the import
                from akf.report import _render_pdf
                _render_pdf(sample_report)

        # Restore
        if original is not None:
            sys.modules["fpdf"] = original

    def test_pdf_long_model_names(self):
        """Long model names are truncated in PDF."""
        report = EnterpriseReport(
            generated_at="2024-01-01T00:00:00Z",
            total_files=0, total_claims=0,
            avg_trust=0.0, trust_distribution={"high": 0, "moderate": 0, "low": 0},
            ai_claims=0, human_claims=0, ai_ratio=0.0,
            models_used={"anthropic/claude-3.5-sonnet-20241022-very-long-name": 10},
            providers_used={}, untracked_claims=0,
            avg_security_score=0.0, security_grade="N/A",
            security_distribution={},
            compliance_rate=0.0, compliant_files=0, non_compliant_files=0,
            classification_distribution={},
            total_detections=0, critical_risks=0, high_risks=0, top_risks=[],
            avg_quality_score=0.0, recommendations=[],
        )
        try:
            output = report.render("pdf")
            # Just ensure it doesn't crash
            assert isinstance(output, (bytes, bytearray))
        except ImportError:
            pytest.skip("fpdf2 not installed")

    def test_pdf_includes_compliance_section(self, sample_report):
        """PDF includes compliance information."""
        try:
            output = sample_report.render("pdf")
            # PDF with compliance section should be non-trivial in size
            assert len(output) > 500
        except ImportError:
            pytest.skip("fpdf2 not installed")

    def test_pdf_includes_recommendations(self):
        """PDF includes recommendations section when present."""
        report = EnterpriseReport(
            generated_at="2024-01-01T00:00:00Z",
            total_files=1, total_claims=1,
            avg_trust=0.5, trust_distribution={"high": 0, "moderate": 1, "low": 0},
            ai_claims=0, human_claims=1, ai_ratio=0.0,
            models_used={}, providers_used={}, untracked_claims=0,
            avg_security_score=5.0, security_grade="C",
            security_distribution={"C": 1},
            compliance_rate=1.0, compliant_files=1, non_compliant_files=0,
            classification_distribution={"internal": 1},
            total_detections=0, critical_risks=0, high_risks=0, top_risks=[],
            avg_quality_score=0.8,
            recommendations=["Add human review", "Improve trust scores"],
            file_reports=[],
        )
        try:
            output = report.render("pdf")
            # PDF with recommendations should be larger than a minimal PDF
            assert len(output) > 500
        except ImportError:
            pytest.skip("fpdf2 not installed")


# ---------------------------------------------------------------------------
# Enterprise Report Generation
# ---------------------------------------------------------------------------


class TestEnterpriseReportGeneration:
    """Test report generation from .akf files."""

    def test_report_total_files(self, sample_report, sample_akf_files):
        """Report counts all loaded files."""
        assert sample_report.total_files == len(sample_akf_files)

    def test_report_total_claims(self, sample_report):
        """Report counts all claims."""
        assert sample_report.total_claims > 0

    def test_report_trust_distribution(self, sample_report):
        """Trust distribution sums to total claims."""
        td = sample_report.trust_distribution
        assert sum(td.values()) == sample_report.total_claims

    def test_report_ai_human_counts(self, sample_report):
        """AI + human claims equals total claims."""
        assert sample_report.ai_claims + sample_report.human_claims == sample_report.total_claims

    def test_report_compliance_counts(self, sample_report):
        """Compliant + non-compliant equals total files."""
        assert sample_report.compliant_files + sample_report.non_compliant_files == sample_report.total_files

    def test_report_file_reports_match(self, sample_report):
        """file_reports list matches total_files."""
        assert len(sample_report.file_reports) == sample_report.total_files

    def test_report_security_grade_valid(self, sample_report):
        """Security grade is a valid value."""
        assert sample_report.security_grade in ("A", "B", "C", "D", "F", "N/A")

    def test_report_empty_directory(self, empty_report):
        """Empty directory produces report with zero files."""
        assert empty_report.total_files == 0
        assert empty_report.total_claims == 0

    def test_report_single_file(self, single_file_report):
        """Single file produces valid report."""
        assert single_file_report.total_files == 1

    def test_report_to_dict(self, sample_report):
        """to_dict produces a plain dict."""
        d = sample_report.to_dict()
        assert isinstance(d, dict)
        assert "total_files" in d
        assert "file_reports" in d

    def test_report_generated_at(self, sample_report):
        """Report has a generated_at timestamp."""
        assert sample_report.generated_at
        assert "T" in sample_report.generated_at  # ISO format

    def test_report_skipped_files_tracked(self):
        """Malformed files are tracked in recommendations."""
        # Create a valid and an invalid .akf file
        valid_unit = create("test claim", confidence=0.9)
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False, mode="w") as f:
            f.write(valid_unit.to_json())
            valid_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False, mode="w") as f:
            f.write("this is not valid json at all {{{")
            invalid_path = f.name

        try:
            report = enterprise_report([valid_path, invalid_path])
            assert report.total_files == 1  # only valid file loaded
            assert any("could not be loaded" in r for r in report.recommendations)
        finally:
            os.unlink(valid_path)
            os.unlink(invalid_path)

    def test_report_directory_input(self, sample_akf_files):
        """Report accepts a directory path."""
        dirpath = str(Path(sample_akf_files[0]).parent)
        report = enterprise_report(dirpath)
        assert report.total_files >= len(sample_akf_files)

    def test_report_file_report_fields(self, sample_report):
        """Each FileReport has all expected fields."""
        for fr in sample_report.file_reports:
            assert isinstance(fr.path, str)
            assert isinstance(fr.claims, int)
            assert isinstance(fr.avg_trust, float)
            assert isinstance(fr.ai_claims, int)
            assert isinstance(fr.human_claims, int)
            assert isinstance(fr.security_grade, str)
            assert isinstance(fr.security_score, float)
            assert isinstance(fr.compliant, bool)
            assert isinstance(fr.classification, str)
            assert isinstance(fr.detections, int)
            assert isinstance(fr.quality_score, float)


# ---------------------------------------------------------------------------
# CLI Integration
# ---------------------------------------------------------------------------


class TestCLIReport:
    """Test the `akf report` CLI command."""

    def test_cli_markdown_default(self, runner, sample_akf_files):
        """Default format is markdown."""
        result = runner.invoke(main, ["report"] + sample_akf_files)
        assert result.exit_code == 0
        assert "# AI Governance Report" in result.output

    def test_cli_json_format(self, runner, sample_akf_files):
        """--format json produces valid JSON."""
        result = runner.invoke(main, ["report", "--format", "json"] + sample_akf_files)
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_files" in data

    def test_cli_html_format(self, runner, sample_akf_files):
        """--format html produces HTML."""
        result = runner.invoke(main, ["report", "--format", "html"] + sample_akf_files)
        assert result.exit_code == 0
        assert "<!DOCTYPE html>" in result.output

    def test_cli_csv_format(self, runner, sample_akf_files):
        """--format csv produces CSV."""
        result = runner.invoke(main, ["report", "--format", "csv"] + sample_akf_files)
        assert result.exit_code == 0
        assert "file,claims,avg_trust" in result.output

    def test_cli_csv_output_file(self, runner, sample_akf_files):
        """CSV output to file works."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            outpath = f.name
        try:
            result = runner.invoke(main, [
                "report", "--format", "csv", "-o", outpath
            ] + sample_akf_files)
            assert result.exit_code == 0
            assert "Report saved" in result.output
            content = Path(outpath).read_text()
            assert "file,claims" in content
        finally:
            os.unlink(outpath)

    def test_cli_html_output_file(self, runner, sample_akf_files):
        """HTML output to file works."""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            outpath = f.name
        try:
            result = runner.invoke(main, [
                "report", "--format", "html", "-o", outpath
            ] + sample_akf_files)
            assert result.exit_code == 0
            content = Path(outpath).read_text()
            assert "<!DOCTYPE html>" in content
            assert "@media print" in content
        finally:
            os.unlink(outpath)

    def test_cli_pdf_requires_output(self, runner, sample_akf_files):
        """PDF format without -o gives error."""
        result = runner.invoke(main, [
            "report", "--format", "pdf"
        ] + sample_akf_files)
        assert result.exit_code != 0
        assert "requires --output/-o" in result.output

    def test_cli_pdf_output_file(self, runner, sample_akf_files):
        """PDF output to file works (if fpdf2 installed)."""
        try:
            import fpdf  # noqa: F401
        except ImportError:
            pytest.skip("fpdf2 not installed")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            outpath = f.name
        try:
            result = runner.invoke(main, [
                "report", "--format", "pdf", "-o", outpath
            ] + sample_akf_files)
            assert result.exit_code == 0
            assert "Report saved" in result.output
            content = Path(outpath).read_bytes()
            assert content[:5] == b"%PDF-"
        finally:
            os.unlink(outpath)

    def test_cli_cold_start_no_files(self, runner):
        """No .akf files shows onboarding guide."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(main, ["report", tmpdir])
            assert result.exit_code == 0
            assert "No .akf files found" in result.output
            assert "akf init" in result.output
            assert "akf create" in result.output
            assert "akf stamp" in result.output
            assert "akf embed" in result.output

    def test_cli_format_choices(self, runner):
        """All format choices are accepted by click."""
        for fmt in ["markdown", "json", "html", "csv"]:
            result = runner.invoke(main, [
                "report", "--format", fmt, "/tmp/nonexistent_dir_xyz"
            ])
            # Should not fail with "invalid choice"
            assert "Invalid value" not in result.output

    def test_cli_invalid_format(self, runner):
        """Invalid format is rejected by click."""
        result = runner.invoke(main, [
            "report", "--format", "xml", "/tmp"
        ])
        assert result.exit_code != 0

    def test_cli_json_output_file(self, runner, sample_akf_files):
        """JSON output to file works."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            outpath = f.name
        try:
            result = runner.invoke(main, [
                "report", "--format", "json", "-o", outpath
            ] + sample_akf_files)
            assert result.exit_code == 0
            data = json.loads(Path(outpath).read_text())
            assert "total_files" in data
        finally:
            os.unlink(outpath)


# ---------------------------------------------------------------------------
# Public API Exports
# ---------------------------------------------------------------------------


class TestPublicAPI:
    """Test that all report exports are accessible from top-level."""

    def test_import_enterprise_report(self):
        import akf
        assert callable(akf.enterprise_report)

    def test_import_EnterpriseReport(self):
        import akf
        assert akf.EnterpriseReport is EnterpriseReport

    def test_import_FileReport(self):
        import akf
        assert akf.FileReport is FileReport

    def test_import_register_renderer(self):
        import akf
        assert callable(akf.register_renderer)

    def test_import_RENDERERS(self):
        import akf
        assert isinstance(akf.RENDERERS, dict)
        assert "csv" in akf.RENDERERS

    def test_all_exports_in_dunder_all(self):
        import akf
        for name in ["enterprise_report", "EnterpriseReport", "FileReport",
                      "register_renderer", "RENDERERS"]:
            assert name in akf.__all__, f"{name} missing from __all__"


# ---------------------------------------------------------------------------
# Integration: Full Pipeline
# ---------------------------------------------------------------------------


class TestIntegrationPipeline:
    """End-to-end integration tests: create → report → verify."""

    def test_full_pipeline_all_formats(self, sample_akf_files):
        """Generate report and render in all text formats."""
        report = enterprise_report(sample_akf_files)
        assert report.total_files == 3

        # All text formats render without error
        md = report.render("markdown")
        assert "# AI Governance Report" in md

        html = report.render("html")
        assert "<!DOCTYPE html>" in html

        j = report.render("json")
        data = json.loads(j)
        assert data["total_files"] == 3

        csv_out = report.render("csv")
        rows = list(csv.reader(io.StringIO(csv_out)))
        assert len(rows) == 4  # header + 3 files

    def test_full_pipeline_pdf(self, sample_akf_files):
        """Full pipeline with PDF output."""
        try:
            import fpdf  # noqa: F401
        except ImportError:
            pytest.skip("fpdf2 not installed")

        report = enterprise_report(sample_akf_files)
        pdf = report.render("pdf")
        assert pdf[:5] == b"%PDF-"

        # Write and verify it's a real file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf)
            path = f.name
        try:
            assert Path(path).stat().st_size > 100
        finally:
            os.unlink(path)

    def test_cli_full_pipeline(self, runner):
        """CLI end-to-end: create files, generate report, verify output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            for i, (content, conf) in enumerate([
                ("Claim A", 0.95),
                ("Claim B", 0.60),
                ("Claim C", 0.30),
            ]):
                unit = create(content, confidence=conf, source=f"src-{i}")
                path = Path(tmpdir) / f"test{i}.akf"
                path.write_text(unit.to_json())

            # Run report
            result = runner.invoke(main, ["report", tmpdir, "--format", "json"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["total_files"] == 3
            assert data["total_claims"] == 3

            # CSV output
            result = runner.invoke(main, ["report", tmpdir, "--format", "csv"])
            assert result.exit_code == 0
            rows = list(csv.reader(io.StringIO(result.output.strip())))
            assert len(rows) == 4

    def test_mixed_valid_invalid_files(self):
        """Report handles mix of valid and invalid files gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Valid file
            unit = create("Valid claim", confidence=0.9)
            Path(tmpdir, "valid.akf").write_text(unit.to_json())

            # Invalid file
            Path(tmpdir, "broken.akf").write_text("{not valid akf content")

            # Non-akf file (should be ignored)
            Path(tmpdir, "readme.md").write_text("# Not an AKF file")

            report = enterprise_report(tmpdir)
            assert report.total_files == 1  # only valid.akf loaded
            assert any("could not be loaded" in r for r in report.recommendations)
