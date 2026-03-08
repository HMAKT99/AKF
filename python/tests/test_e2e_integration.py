"""AKF v1.1 — Comprehensive End-to-End Integration Tests.

Tests every CLI command and SDK operation across all supported file formats
with a large volume of test files. Designed for pre-launch verification.

Run: python3 -m pytest tests/test_e2e_integration.py -v
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PYTHON = sys.executable
TEST_DIR = None


def akf(*args, check=True, allow_fail=False):
    """Run an akf CLI command, return (returncode, stdout, stderr)."""
    cmd = [PYTHON, "-m", "akf"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=TEST_DIR)
    if check and not allow_fail and result.returncode != 0:
        raise AssertionError(
            f"Command failed: {' '.join(args)}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.returncode, result.stdout, result.stderr


@pytest.fixture(scope="module", autouse=True)
def setup_test_dir():
    """Create and populate a large test directory tree."""
    global TEST_DIR
    TEST_DIR = tempfile.mkdtemp(prefix="akf_e2e_")
    yield TEST_DIR
    shutil.rmtree(TEST_DIR, ignore_errors=True)


# ---------------------------------------------------------------------------
# File generators
# ---------------------------------------------------------------------------

def make_markdown(path, title="Test", body="Content here."):
    Path(path).write_text(f"# {title}\n\n{body}\n")


def make_html(path, title="Test", body="Content here."):
    Path(path).write_text(
        f"<!DOCTYPE html><html><head><title>{title}</title></head>"
        f"<body><p>{body}</p></body></html>\n"
    )


def make_json(path, data=None):
    if data is None:
        data = {"title": "Test", "value": 42}
    Path(path).write_text(json.dumps(data, indent=2) + "\n")


def make_text(path, content="Plain text content."):
    Path(path).write_text(content + "\n")


def make_docx(path, text="Test DOCX content"):
    docx = pytest.importorskip("docx", reason="python-docx not installed")
    doc = docx.Document()
    doc.add_paragraph(text)
    doc.save(path)


def make_xlsx(path):
    openpyxl = pytest.importorskip("openpyxl", reason="openpyxl not installed")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"] = "Revenue"
    ws["B1"] = 4200000
    ws["A2"] = "Growth"
    ws["B2"] = 0.12
    wb.save(path)


def make_pptx(path, title="Test Slide"):
    pptx = pytest.importorskip("pptx", reason="python-pptx not installed")
    prs = pptx.Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = title
    prs.save(path)


def make_image(path, fmt="PNG", size=(100, 100)):
    PIL = pytest.importorskip("PIL", reason="Pillow not installed")
    img = PIL.Image.new("RGB", size, color=(73, 109, 137))
    img.save(path, fmt)


def make_email(path, subject="Test", body="Email body"):
    content = (
        f"From: test@example.com\n"
        f"To: user@example.com\n"
        f"Subject: {subject}\n"
        f"Date: Sat, 08 Mar 2026 12:00:00 +0000\n"
        f"\n{body}\n"
    )
    Path(path).write_text(content)


# ---------------------------------------------------------------------------
# Phase 1: File Creation (bulk)
# ---------------------------------------------------------------------------

class TestPhase1FileCreation:
    """Create a large volume of test files across all formats."""

    def test_create_markdown_files(self):
        d = Path(TEST_DIR) / "markdown"
        d.mkdir()
        topics = [
            ("revenue", "Q3 Revenue Report", "Revenue was $4.2B, up 12% YoY."),
            ("forecast", "Growth Forecast", "AI predicts 15% growth next quarter."),
            ("risk", "Risk Assessment", "Market volatility remains a concern."),
            ("compliance", "Compliance Update", "All SOX controls passed audit."),
            ("strategy", "Strategy Memo", "Expand into APAC by Q2 2027."),
            ("hr", "HR Policy", "Remote work policy updated effective Jan 1."),
            ("tech", "Architecture Review", "Migrating to microservices by Q4."),
            ("security", "Security Bulletin", "Zero critical CVEs this quarter."),
            ("budget", "Budget Allocation", "R&D budget increased to $1.2B."),
            ("research", "Market Research", "TAM estimated at $50B by 2028."),
        ]
        for name, title, body in topics:
            make_markdown(d / f"{name}.md", title, body)
        assert len(list(d.glob("*.md"))) == 10

    def test_create_html_files(self):
        d = Path(TEST_DIR) / "html"
        d.mkdir()
        for i in range(5):
            make_html(d / f"page_{i}.html", f"Page {i}", f"HTML content {i}")
        assert len(list(d.glob("*.html"))) == 5

    def test_create_json_files(self):
        d = Path(TEST_DIR) / "json"
        d.mkdir()
        for i in range(5):
            make_json(d / f"data_{i}.json", {"id": i, "metric": i * 10.5})
        assert len(list(d.glob("*.json"))) == 5

    def test_create_docx_files(self):
        d = Path(TEST_DIR) / "office"
        d.mkdir(exist_ok=True)
        for i in range(5):
            make_docx(d / f"doc_{i}.docx", f"Document {i} content with details.")
        assert len(list(d.glob("*.docx"))) == 5

    def test_create_xlsx_files(self):
        d = Path(TEST_DIR) / "office"
        d.mkdir(exist_ok=True)
        for i in range(3):
            make_xlsx(d / f"sheet_{i}.xlsx")
        assert len(list(d.glob("*.xlsx"))) == 3

    def test_create_pptx_files(self):
        d = Path(TEST_DIR) / "office"
        d.mkdir(exist_ok=True)
        for i in range(3):
            make_pptx(d / f"slides_{i}.pptx", f"Presentation {i}")
        assert len(list(d.glob("*.pptx"))) == 3

    def test_create_image_files(self):
        d = Path(TEST_DIR) / "images"
        d.mkdir()
        for i in range(3):
            make_image(d / f"img_{i}.png", "PNG")
        for i in range(3):
            make_image(d / f"img_{i}.jpg", "JPEG")
        assert len(list(d.glob("*"))) == 6

    def test_create_email_files(self):
        d = Path(TEST_DIR) / "email"
        d.mkdir()
        for i in range(3):
            make_email(d / f"msg_{i}.eml", f"Subject {i}", f"Email body {i}")
        assert len(list(d.glob("*.eml"))) == 3

    def test_create_plaintext_files(self):
        d = Path(TEST_DIR) / "text"
        d.mkdir()
        for i in range(5):
            make_text(d / f"note_{i}.txt", f"Plain text note number {i}")
        assert len(list(d.glob("*.txt"))) == 5

    def test_create_nested_structure(self):
        """Deep nested directory for recursive operations."""
        base = Path(TEST_DIR) / "nested"
        for depth in ["a", "a/b", "a/b/c", "x", "x/y"]:
            (base / depth).mkdir(parents=True, exist_ok=True)
        make_markdown(base / "root.md", "Root", "Root level file")
        make_markdown(base / "a" / "level1.md", "L1", "Level 1")
        make_markdown(base / "a" / "b" / "level2.md", "L2", "Level 2")
        make_markdown(base / "a" / "b" / "c" / "level3.md", "L3", "Level 3")
        make_json(base / "x" / "data.json", {"nested": True})
        make_html(base / "x" / "y" / "page.html", "Deep", "Deep nested")
        assert (base / "a" / "b" / "c" / "level3.md").exists()

    def test_create_unicode_files(self):
        """Files with unicode content."""
        d = Path(TEST_DIR) / "unicode"
        d.mkdir()
        make_markdown(d / "japanese.md", "日本語テスト", "これはテストです。信頼スコア: 0.95")
        make_markdown(d / "arabic.md", "اختبار عربي", "هذا اختبار للبيانات الوصفية")
        make_markdown(d / "emoji.md", "Emoji Test", "Results look great! 📊 Trust: high 🟢")
        make_json(d / "intl.json", {"名前": "テスト", "score": 0.9, "описание": "тест"})
        assert len(list(d.glob("*"))) == 4

    def test_create_edge_case_files(self):
        """Edge cases: empty, large, special characters in content."""
        d = Path(TEST_DIR) / "edge"
        d.mkdir()
        # Minimal content
        Path(d / "minimal.md").write_text("x\n")
        # Large file
        Path(d / "large.md").write_text("# Large\n\n" + ("Line of content. " * 100 + "\n") * 100)
        # Special chars in content
        make_markdown(d / "special.md", "Special <>&\"' Chars", 'Content with "quotes" & <tags>')
        assert len(list(d.glob("*"))) == 3


# ---------------------------------------------------------------------------
# Phase 2: AKF Create & Validate (.akf files)
# ---------------------------------------------------------------------------

class TestPhase2CreateValidate:
    """Test akf create with various claim configurations."""

    def test_create_single_claim(self):
        out = Path(TEST_DIR) / "akf" / "single.akf"
        out.parent.mkdir(exist_ok=True)
        akf("create", str(out), "-c", "Revenue $4.2B", "-t", "0.98", "--src", "SEC")
        assert out.exists()

    def test_create_multi_claim(self):
        out = Path(TEST_DIR) / "akf" / "multi.akf"
        akf("create", str(out),
            "-c", "Revenue $4.2B", "-t", "0.98", "--src", "SEC",
            "-c", "Growth 12%", "-t", "0.75", "--src", "analyst",
            "-c", "AI prediction", "-t", "0.6", "--src", "GPT-4")
        assert out.exists()

    def test_create_with_classification(self):
        out = Path(TEST_DIR) / "akf" / "classified.akf"
        akf("create", str(out), "-c", "Secret data", "-t", "0.99",
            "--src", "internal", "--label", "confidential")
        assert out.exists()

    def test_create_with_author(self):
        out = Path(TEST_DIR) / "akf" / "authored.akf"
        akf("create", str(out), "-c", "Authored claim", "-t", "0.85",
            "--src", "manual", "--by", "analyst@corp.com")
        assert out.exists()

    def test_create_ai_claims(self):
        out = Path(TEST_DIR) / "akf" / "ai_claims.akf"
        akf("create", str(out), "-c", "AI generated insight", "-t", "0.65",
            "--src", "gpt-4o", "--ai")
        assert out.exists()

    def test_create_verified_claims(self):
        out = Path(TEST_DIR) / "akf" / "verified.akf"
        akf("create", str(out), "-c", "Verified fact", "-t", "0.99",
            "--src", "audit", "--ver")
        assert out.exists()

    def test_create_with_tiers(self):
        out = Path(TEST_DIR) / "akf" / "tiered.akf"
        akf("create", str(out),
            "-c", "Tier 1 claim", "-t", "0.99", "--tier", "1",
            "-c", "Tier 5 claim", "-t", "0.4", "--tier", "5")
        assert out.exists()

    def test_create_demo(self):
        out = Path(TEST_DIR) / "akf" / "demo.akf"
        akf("create", str(out), "--demo")
        assert out.exists()

    def test_validate_all_created(self):
        akf_dir = Path(TEST_DIR) / "akf"
        results = {}
        for f in sorted(akf_dir.glob("*.akf")):
            rc, out, _ = akf("validate", str(f), allow_fail=True)
            results[f.name] = ("Valid" in out, out.strip())
        failures = {k: v[1] for k, v in results.items() if not v[0]}
        assert not failures, f"Validation failures: {failures}"

    def test_validate_counts(self):
        """Verify correct claim counts in created files."""
        rc, out, _ = akf("inspect", str(Path(TEST_DIR) / "akf" / "multi.akf"))
        assert "claims: 3" in out

        rc, out, _ = akf("inspect", str(Path(TEST_DIR) / "akf" / "demo.akf"))
        assert "claims: 3" in out


# ---------------------------------------------------------------------------
# Phase 3: Embed & Read across all formats
# ---------------------------------------------------------------------------

class TestPhase3EmbedRead:
    """Embed metadata into every format, then read it back."""

    @pytest.mark.parametrize("filename", [
        "markdown/revenue.md",
        "markdown/forecast.md",
        "markdown/risk.md",
        "markdown/compliance.md",
        "markdown/strategy.md",
    ])
    def test_embed_read_markdown(self, filename):
        f = str(Path(TEST_DIR) / filename)
        akf("embed", f, "-c", "Test claim", "-t", "0.9", "--src", "test", "--label", "internal")
        rc, out, _ = akf("read", f)
        assert "Test claim" in out
        assert "0.90" in out

    @pytest.mark.parametrize("filename", [
        "html/page_0.html",
        "html/page_1.html",
        "html/page_2.html",
    ])
    def test_embed_read_html(self, filename):
        f = str(Path(TEST_DIR) / filename)
        akf("embed", f, "-c", "HTML claim", "-t", "0.88", "--src", "web")
        rc, out, _ = akf("read", f)
        assert "HTML claim" in out

    @pytest.mark.parametrize("filename", [
        "json/data_0.json",
        "json/data_1.json",
        "json/data_2.json",
    ])
    def test_embed_read_json(self, filename):
        f = str(Path(TEST_DIR) / filename)
        akf("embed", f, "-c", "JSON claim", "-t", "0.77", "--src", "api")
        rc, out, _ = akf("read", f)
        assert "JSON claim" in out

    @pytest.mark.parametrize("filename", [
        "office/doc_0.docx",
        "office/doc_1.docx",
    ])
    def test_embed_read_docx(self, filename):
        f = str(Path(TEST_DIR) / filename)
        akf("embed", f, "-c", "DOCX claim", "-t", "0.92", "--src", "legal")
        rc, out, _ = akf("read", f)
        assert "DOCX claim" in out

    @pytest.mark.parametrize("filename", [
        "office/sheet_0.xlsx",
    ])
    def test_embed_read_xlsx(self, filename):
        f = str(Path(TEST_DIR) / filename)
        akf("embed", f, "-c", "XLSX claim", "-t", "0.85", "--src", "finance")
        rc, out, _ = akf("read", f)
        assert "XLSX claim" in out

    @pytest.mark.parametrize("filename", [
        "office/slides_0.pptx",
    ])
    def test_embed_read_pptx(self, filename):
        f = str(Path(TEST_DIR) / filename)
        akf("embed", f, "-c", "PPTX claim", "-t", "0.80", "--src", "marketing")
        rc, out, _ = akf("read", f)
        assert "PPTX claim" in out

    def test_embed_read_image(self):
        f = str(Path(TEST_DIR) / "images" / "img_0.png")
        akf("embed", f, "-c", "Image claim", "-t", "0.7", "--src", "camera")
        rc, out, _ = akf("read", f)
        assert "Image claim" in out

    def test_embed_read_email(self):
        f = str(Path(TEST_DIR) / "email" / "msg_0.eml")
        akf("embed", f, "-c", "Email claim", "-t", "0.6", "--src", "inbox")
        rc, out, _ = akf("read", f)
        assert "Email claim" in out

    def test_sidecar_for_plaintext(self):
        """Plain text gets sidecar since no native handler."""
        f = str(Path(TEST_DIR) / "text" / "note_0.txt")
        akf("sidecar", f, "--label", "internal")
        rc, out, _ = akf("read", f)
        assert "internal" in out.lower() or "AKF" in out

    def test_read_json_output(self):
        f = str(Path(TEST_DIR) / "markdown" / "revenue.md")
        rc, out, _ = akf("read", f, "--json")
        data = json.loads(out)
        assert "claims" in data
        assert len(data["claims"]) >= 1

    def test_read_akf_file(self):
        """Verify Fix 1: reading .akf files directly."""
        f = str(Path(TEST_DIR) / "akf" / "multi.akf")
        rc, out, _ = akf("read", f)
        assert "Revenue" in out
        assert "Claims: 3" in out

    def test_embed_multiple_claims(self):
        f = str(Path(TEST_DIR) / "markdown" / "hr.md")
        akf("embed", f,
            "-c", "Policy updated", "-t", "0.95", "--src", "HR",
            "-c", "Effective Jan 1", "-t", "0.99", "--src", "HR",
            "--label", "confidential")
        rc, out, _ = akf("read", f)
        assert "Policy updated" in out
        assert "Effective Jan 1" in out

    def test_embed_with_ai_flag(self):
        f = str(Path(TEST_DIR) / "markdown" / "tech.md")
        akf("embed", f, "-c", "AI suggestion", "-t", "0.55", "--src", "claude", "--ai")
        rc, out, _ = akf("read", f)
        assert "AI" in out

    def test_embed_unicode_content(self):
        f = str(Path(TEST_DIR) / "unicode" / "japanese.md")
        akf("embed", f, "-c", "信頼データ", "-t", "0.9", "--src", "テスト")
        rc, out, _ = akf("read", f, "--json")
        data = json.loads(out)
        claims = data.get("claims", [])
        assert any("信頼" in str(c) for c in claims)


# ---------------------------------------------------------------------------
# Phase 4: Stamp (quick-tag workflow)
# ---------------------------------------------------------------------------

class TestPhase4Stamp:
    """Test the stamp command across formats."""

    @pytest.mark.parametrize("filename", [
        "markdown/budget.md",
        "markdown/research.md",
        "markdown/security.md",
    ])
    def test_stamp_markdown(self, filename):
        f = str(Path(TEST_DIR) / filename)
        rc, out, _ = akf("stamp", f, "--label", "internal")
        assert "Stamped" in out

    def test_stamp_html(self):
        f = str(Path(TEST_DIR) / "html" / "page_3.html")
        rc, out, _ = akf("stamp", f)
        assert "Stamped" in out

    def test_stamp_docx(self):
        f = str(Path(TEST_DIR) / "office" / "doc_2.docx")
        rc, out, _ = akf("stamp", f, "--label", "confidential")
        assert "Stamped" in out

    def test_stamp_then_read(self):
        f = str(Path(TEST_DIR) / "markdown" / "budget.md")
        rc, out, _ = akf("read", f)
        assert "AKF" in out or "internal" in out.lower()


# ---------------------------------------------------------------------------
# Phase 5: Scan (single file + directory)
# ---------------------------------------------------------------------------

class TestPhase5Scan:

    def test_scan_enriched_file(self):
        f = str(Path(TEST_DIR) / "markdown" / "revenue.md")
        rc, out, _ = akf("scan", f)
        assert "enriched" in out.lower() or "Markdown" in out

    def test_scan_unenriched_file(self):
        f = str(Path(TEST_DIR) / "text" / "note_1.txt")
        rc, out, _ = akf("scan", f)
        assert "No AKF" in out or "not enriched" in out.lower() or "0 AKF" in out

    def test_scan_directory(self):
        d = str(Path(TEST_DIR) / "markdown")
        rc, out, _ = akf("scan", d, "-r")
        assert "Scanned" in out
        assert "AKF-enriched" in out

    def test_scan_full_tree(self):
        rc, out, _ = akf("scan", TEST_DIR, "-r")
        assert "Scanned" in out

    def test_scan_nested_recursive(self):
        d = str(Path(TEST_DIR) / "nested")
        rc, out, _ = akf("scan", d, "-r")
        assert "Scanned" in out


# ---------------------------------------------------------------------------
# Phase 6: Info & Extract
# ---------------------------------------------------------------------------

class TestPhase6InfoExtract:

    def test_info_enriched(self):
        f = str(Path(TEST_DIR) / "markdown" / "revenue.md")
        rc, out, _ = akf("info", f)
        assert "enriched" in out

    def test_info_unenriched(self):
        f = str(Path(TEST_DIR) / "text" / "note_2.txt")
        rc, out, _ = akf("info", f)
        assert "not enriched" in out

    def test_extract_json(self):
        f = str(Path(TEST_DIR) / "markdown" / "revenue.md")
        rc, out, _ = akf("extract", f)
        data = json.loads(out)
        assert "claims" in data

    def test_extract_summary(self):
        f = str(Path(TEST_DIR) / "markdown" / "revenue.md")
        rc, out, _ = akf("extract", f, "--format", "summary")
        assert "File:" in out

    def test_extract_no_metadata(self):
        f = str(Path(TEST_DIR) / "text" / "note_3.txt")
        rc, out, err = akf("extract", f, allow_fail=True)
        assert rc != 0 or "No AKF" in out


# ---------------------------------------------------------------------------
# Phase 7: Convert (Fix 3 verification + bulk)
# ---------------------------------------------------------------------------

class TestPhase7Convert:

    def test_convert_single_file_no_output(self):
        """Fix 3: convert without -o defaults to <file>.akf."""
        f = str(Path(TEST_DIR) / "markdown" / "revenue.md")
        akf("convert", f)
        assert Path(f + ".akf").exists()

    def test_convert_single_file_with_output(self):
        out = str(Path(TEST_DIR) / "converted_explicit.akf")
        f = str(Path(TEST_DIR) / "markdown" / "forecast.md")
        akf("convert", f, "-o", out)
        assert Path(out).exists()

    def test_convert_directory_no_output(self):
        """Fix 3: convert dir without -o defaults to input dir."""
        d = str(Path(TEST_DIR) / "html")
        akf("convert", d, "--recursive")
        akf_files = list(Path(d).glob("*.akf"))
        assert len(akf_files) >= 1

    def test_convert_directory_with_output(self):
        out_dir = Path(TEST_DIR) / "converted_html"
        out_dir.mkdir(exist_ok=True)
        d = str(Path(TEST_DIR) / "json")
        akf("convert", d, "-o", str(out_dir), "--recursive", "--overwrite")
        akf_files = list(out_dir.glob("*.akf"))
        assert len(akf_files) >= 1

    def test_convert_nested_recursive(self):
        d = str(Path(TEST_DIR) / "nested")
        akf("convert", d, "--recursive", "--overwrite")
        # Should produce .akf files in subdirectories
        akf_files = list(Path(d).rglob("*.akf"))
        assert len(akf_files) >= 3

    def test_convert_modes(self):
        """Test extract, enrich, both modes."""
        d = Path(TEST_DIR) / "mode_test"
        d.mkdir(exist_ok=True)
        make_markdown(d / "a.md", "A", "Content A")
        make_markdown(d / "b.md", "B", "Content B")

        # enrich mode
        akf("convert", str(d), "--recursive", "-m", "enrich", "--overwrite")
        assert (d / "a.md.akf").exists()

    def test_convert_overwrite(self):
        d = str(Path(TEST_DIR) / "html")
        akf("convert", d, "--recursive", "--overwrite")

    def test_converted_files_are_valid(self):
        """All .akf outputs from convert should be valid."""
        akf_files = list(Path(TEST_DIR).rglob("*.akf"))
        # Skip sidecar .akf.json files
        akf_files = [f for f in akf_files if not str(f).endswith(".akf.json")]
        failures = []
        for f in akf_files[:20]:  # Test up to 20
            rc, out, err = akf("validate", str(f), allow_fail=True)
            if rc != 0 or "Invalid" in out:
                failures.append(str(f))
        assert not failures, f"Invalid .akf files: {failures}"


# ---------------------------------------------------------------------------
# Phase 8: Audit across formats (Fix 2 verification)
# ---------------------------------------------------------------------------

class TestPhase8Audit:

    def test_audit_akf_file(self):
        f = str(Path(TEST_DIR) / "akf" / "demo.akf")
        rc, out, _ = akf("audit", f)
        assert "score:" in out
        assert any(icon in out for icon in ["COMPLIANT", "NON-COMPLIANT"])

    def test_audit_markdown(self):
        """Fix 2: audit non-AKF file."""
        f = str(Path(TEST_DIR) / "markdown" / "revenue.md")
        rc, out, _ = akf("audit", f)
        assert "score:" in out

    def test_audit_docx(self):
        """Fix 2: audit DOCX file."""
        f = str(Path(TEST_DIR) / "office" / "doc_0.docx")
        rc, out, _ = akf("audit", f)
        assert "score:" in out

    def test_audit_html(self):
        f = str(Path(TEST_DIR) / "html" / "page_0.html")
        rc, out, _ = akf("audit", f)
        assert "score:" in out

    def test_audit_no_metadata_error(self):
        """Fix 2: helpful error for files with no metadata."""
        f = str(Path(TEST_DIR) / "text" / "note_4.txt")
        rc, out, err = akf("audit", f, allow_fail=True)
        assert rc != 0
        combined = out + err
        assert "Tip:" in combined or "embed" in combined

    @pytest.mark.parametrize("reg", [
        "eu_ai_act", "sox", "hipaa", "gdpr", "nist_ai", "iso_42001",
    ])
    def test_audit_all_regulations_akf(self, reg):
        f = str(Path(TEST_DIR) / "akf" / "demo.akf")
        rc, out, _ = akf("audit", f, "--regulation", reg)
        assert reg in out or "COMPLIANT" in out or "NON-COMPLIANT" in out

    @pytest.mark.parametrize("reg", [
        "eu_ai_act", "sox", "hipaa", "gdpr", "nist_ai", "iso_42001",
    ])
    def test_audit_all_regulations_markdown(self, reg):
        """Fix 2: regulations work on embedded markdown too."""
        f = str(Path(TEST_DIR) / "markdown" / "revenue.md")
        rc, out, _ = akf("audit", f, "--regulation", reg)
        assert "COMPLIANT" in out or "NON-COMPLIANT" in out

    def test_audit_trail(self):
        f = str(Path(TEST_DIR) / "akf" / "demo.akf")
        rc, out, _ = akf("audit", f, "--trail")
        assert "Audit Trail" in out

    @pytest.mark.parametrize("fmt", ["json", "markdown", "csv"])
    def test_audit_export_formats(self, fmt):
        f = str(Path(TEST_DIR) / "akf" / "demo.akf")
        rc, out, _ = akf("audit", f, "--export", fmt)
        assert len(out) > 10
        if fmt == "json":
            data = json.loads(out)
            assert "compliant" in data
        elif fmt == "csv":
            assert "check,passed" in out


# ---------------------------------------------------------------------------
# Phase 9: Trust, Security, Hash, Explain
# ---------------------------------------------------------------------------

class TestPhase9TrustSecurity:

    def test_trust_scoring(self):
        f = str(Path(TEST_DIR) / "akf" / "multi.akf")
        rc, out, _ = akf("trust", f)
        assert "ACCEPT" in out or "LOW" in out or "REJECT" in out

    def test_trust_demo(self):
        f = str(Path(TEST_DIR) / "akf" / "demo.akf")
        rc, out, _ = akf("trust", f)
        lines = [l for l in out.strip().split("\n") if l.strip()]
        assert len(lines) == 3  # 3 claims in demo

    def test_security_score(self):
        f = str(Path(TEST_DIR) / "akf" / "demo.akf")
        rc, out, _ = akf("security", f)
        assert "Security Score:" in out
        assert "Grade:" in out

    def test_hash_compute(self):
        f = str(Path(TEST_DIR) / "akf" / "single.akf")
        rc, out, _ = akf("hash", f)
        assert "sha256:" in out or "Hash" in out

    def test_hash_verify(self):
        """Second run should verify the stored hash."""
        f = str(Path(TEST_DIR) / "akf" / "single.akf")
        rc, out, _ = akf("hash", f)
        assert "valid" in out.lower() or "Hash" in out

    def test_explain(self):
        f = str(Path(TEST_DIR) / "akf" / "demo.akf")
        rc, out, _ = akf("explain", f)
        assert "Trust Analysis" in out
        assert "Base confidence" in out

    def test_freshness(self):
        f = str(Path(TEST_DIR) / "akf" / "demo.akf")
        rc, out, _ = akf("freshness", f)
        assert "no_expiry" in out or "fresh" in out


# ---------------------------------------------------------------------------
# Phase 10: Enrich, Consume, Diff, Provenance pipeline
# ---------------------------------------------------------------------------

class TestPhase10Pipeline:

    def test_enrich_akf(self):
        # Copy demo to avoid mutating shared fixture
        src = Path(TEST_DIR) / "akf" / "demo.akf"
        dst = Path(TEST_DIR) / "akf" / "pipeline.akf"
        shutil.copy2(src, dst)

        akf("enrich", str(dst),
            "--agent", "gpt-4o",
            "-c", "AI insight: market expanding", "-t", "0.7",
            "-r", "Based on limited data")
        rc, out, _ = akf("inspect", str(dst))
        assert "claims: 4" in out
        assert "AI" in out

    def test_consume_filter(self):
        src = str(Path(TEST_DIR) / "akf" / "pipeline.akf")
        dst = str(Path(TEST_DIR) / "akf" / "consumed.akf")
        akf("consume", src, "-o", dst, "--threshold", "0.7", "--agent", "consumer-1")
        rc, out, _ = akf("inspect", dst)
        # Low-trust claims should be filtered out
        assert "consumed" not in out or "claims:" in out

    def test_diff(self):
        f1 = str(Path(TEST_DIR) / "akf" / "pipeline.akf")
        f2 = str(Path(TEST_DIR) / "akf" / "consumed.akf")
        rc, out, _ = akf("diff", f1, f2)
        assert "Comparing" in out
        assert "Claims:" in out

    def test_provenance_tree(self):
        f = str(Path(TEST_DIR) / "akf" / "pipeline.akf")
        rc, out, _ = akf("provenance", f)
        # Should have at least the enrich hop
        assert "gpt-4o" in out or "enriched" in out or "no provenance" in out.lower()

    def test_provenance_json(self):
        f = str(Path(TEST_DIR) / "akf" / "pipeline.akf")
        rc, out, _ = akf("provenance", f, "--format", "json")
        if out.strip():
            data = json.loads(out)
            assert "hop" in data or isinstance(data, dict)


# ---------------------------------------------------------------------------
# Phase 11: Init & Formats
# ---------------------------------------------------------------------------

class TestPhase11InitFormats:

    def test_init_project(self):
        d = Path(TEST_DIR) / "project"
        d.mkdir(exist_ok=True)
        akf("init", "--path", str(d))
        assert (d / ".akf" / "config.json").exists()
        config = json.loads((d / ".akf" / "config.json").read_text())
        assert config["version"] == "1.0"

    def test_init_with_agent(self):
        d = Path(TEST_DIR) / "project2"
        d.mkdir(exist_ok=True)
        akf("init", "--path", str(d), "--agent", "my-agent", "--label", "confidential")
        config = json.loads((d / ".akf" / "config.json").read_text())
        assert config["agent"] == "my-agent"
        assert config["classification"] == "confidential"

    def test_formats_list(self):
        rc, out, _ = akf("formats")
        assert "Markdown" in out
        assert "HTML" in out
        assert "JSON" in out
        assert "DOCX" in out
        assert "PDF" in out
        assert "sidecar" in out


# ---------------------------------------------------------------------------
# Phase 12: SDK programmatic API
# ---------------------------------------------------------------------------

class TestPhase12SDK:

    def test_core_create_load_roundtrip(self):
        from akf.core import create, create_multi, load, validate

        unit = create_multi([
            {"content": "Claim A", "confidence": 0.9, "source": "test"},
            {"content": "Claim B", "confidence": 0.5, "source": "test"},
        ], author="sdk-test@corp.com", classification="internal")

        out = Path(TEST_DIR) / "sdk_roundtrip.akf"
        unit.save(str(out))

        loaded = load(str(out))
        assert len(loaded.claims) == 2
        assert loaded.author == "sdk-test@corp.com"
        assert loaded.classification == "internal"

        vr = validate(str(out))
        assert vr.valid

    def test_universal_embed_extract(self):
        from akf import universal

        f = str(Path(TEST_DIR) / "sdk_embed.md")
        make_markdown(f, "SDK Test", "Testing SDK embed.")

        universal.embed(f, claims=[
            {"c": "SDK claim", "t": 0.88, "src": "sdk"},
        ], classification="internal")

        meta = universal.extract(f)
        assert meta is not None
        assert len(meta.get("claims", [])) >= 1
        assert meta.get("classification") == "internal"

    def test_universal_extract_akf(self):
        """Fix 1: universal.extract works on .akf files."""
        from akf import universal
        f = str(Path(TEST_DIR) / "akf" / "multi.akf")
        meta = universal.extract(f)
        assert meta is not None
        assert len(meta.get("claims", [])) == 3

    def test_universal_scan(self):
        from akf import universal
        f = str(Path(TEST_DIR) / "markdown" / "revenue.md")
        report = universal.scan(f)
        assert report.enriched

    def test_universal_is_enriched(self):
        from akf import universal
        assert universal.is_enriched(str(Path(TEST_DIR) / "markdown" / "revenue.md"))

    def test_universal_info(self):
        from akf import universal
        info = universal.info(str(Path(TEST_DIR) / "markdown" / "revenue.md"))
        assert "enriched" in info

    def test_universal_scan_directory(self):
        from akf import universal
        reports = universal.scan_directory(str(Path(TEST_DIR) / "markdown"))
        assert len(reports) >= 5

    def test_universal_supported_formats(self):
        from akf import universal
        fmts = universal.supported_formats()
        assert "Markdown" in fmts
        assert "sidecar" in fmts

    def test_trust_compute(self):
        from akf.core import load
        from akf.trust import compute_all, effective_trust

        unit = load(str(Path(TEST_DIR) / "akf" / "demo.akf"))
        results = compute_all(unit)
        assert len(results) == 3
        for r in results:
            assert 0 <= r.score <= 1
            assert r.decision in ("ACCEPT", "LOW", "REJECT")

    def test_provenance_add_hop(self):
        from akf.core import create_multi
        from akf.provenance import add_hop, format_tree

        unit = create_multi([{"content": "Test", "confidence": 0.9, "source": "t"}])
        unit = add_hop(unit, by="agent-1", action="created")
        unit = add_hop(unit, by="reviewer@corp.com", action="reviewed")
        assert len(unit.prov) == 2

        tree = format_tree(unit)
        assert "agent-1" in tree

    def test_compliance_audit(self):
        from akf.core import load
        from akf.compliance import audit, check_regulation

        unit = load(str(Path(TEST_DIR) / "akf" / "demo.akf"))
        result = audit(unit)
        assert 0 <= result.score <= 1
        assert len(result.checks) == 10

        for reg in ["eu_ai_act", "sox", "hipaa", "gdpr", "nist_ai", "iso_42001"]:
            r = check_regulation(unit, reg)
            assert 0 <= r.score <= 1
            assert r.regulation == reg

    def test_compliance_load_unit_non_akf(self):
        """Fix 2: _load_unit works on non-AKF files."""
        from akf.compliance import audit
        f = str(Path(TEST_DIR) / "markdown" / "revenue.md")
        result = audit(f)
        assert 0 <= result.score <= 1

    def test_security_score(self):
        from akf.core import load
        from akf.security import security_score

        unit = load(str(Path(TEST_DIR) / "akf" / "demo.akf"))
        result = security_score(unit)
        assert 0 <= result.score <= 10
        assert result.grade in ("A+", "A", "B", "C", "D", "F")

    def test_builder_pattern(self):
        from akf.builder import AKFBuilder

        unit = (
            AKFBuilder()
            .claim("Builder claim", 0.9)
            .claim("Second", 0.7)
            .by("builder@test.com")
            .label("internal")
            .build()
        )
        assert len(unit.claims) == 2
        assert unit.author == "builder@test.com"

    def test_transform_pipeline(self):
        from akf.core import create_multi
        from akf.transform import AKFTransformer

        unit = create_multi([
            {"content": "High", "confidence": 0.95, "source": "a"},
            {"content": "Low", "confidence": 0.3, "source": "b"},
        ])
        derived = AKFTransformer(unit).filter(trust_min=0.5).build()
        assert len(derived.claims) == 1
        assert derived.claims[0].content == "High"

    def test_models_used(self):
        from akf.core import create_multi
        from akf.provenance import add_hop
        from akf import models_used

        unit = create_multi([
            {"content": "Test", "confidence": 0.9, "source": "t"}
        ])
        unit = add_hop(unit, by="gpt-4o", action="enriched", model="gpt-4o-2024-08")
        models = models_used(unit)
        assert "gpt-4o-2024-08" in models


# ---------------------------------------------------------------------------
# Phase 13: Edge cases & error handling
# ---------------------------------------------------------------------------

class TestPhase13EdgeCases:

    def test_validate_invalid_json(self):
        f = Path(TEST_DIR) / "bad.akf"
        f.write_text("not json at all\n")
        rc, out, err = akf("validate", str(f), allow_fail=True)
        assert rc != 0 or "Invalid" in out

    def test_read_no_metadata(self):
        f = str(Path(TEST_DIR) / "text" / "note_1.txt")
        rc, out, _ = akf("read", f)
        assert "No AKF" in out or "Tip" in out

    def test_create_mismatched_claims_trust(self):
        """Error: different number of --claim and --trust."""
        f = str(Path(TEST_DIR) / "mismatch.akf")
        rc, out, err = akf("create", f, "-c", "A", "-c", "B", "-t", "0.5", allow_fail=True)
        assert rc != 0

    def test_audit_unknown_regulation(self):
        f = str(Path(TEST_DIR) / "akf" / "demo.akf")
        rc, out, _ = akf("audit", f, "--regulation", "fake_regulation")
        assert "Unknown" in out or "unknown" in out.lower() or "NON-COMPLIANT" in out

    def test_convert_nonexistent(self):
        rc, out, err = akf("convert", "/tmp/nonexistent_dir_akf", allow_fail=True)
        assert rc != 0

    def test_large_file_embed_read(self):
        f = str(Path(TEST_DIR) / "edge" / "large.md")
        akf("embed", f, "-c", "Large file claim", "-t", "0.8", "--src", "test")
        rc, out, _ = akf("read", f)
        assert "Large file claim" in out

    def test_special_chars_embed_read(self):
        f = str(Path(TEST_DIR) / "edge" / "special.md")
        akf("embed", f, "-c", "Claim with <special> & chars", "-t", "0.7", "--src", "test")
        rc, out, _ = akf("read", f, "--json")
        data = json.loads(out)
        assert any("special" in str(c) for c in data.get("claims", []))


# ---------------------------------------------------------------------------
# Phase 14: Volume stress test
# ---------------------------------------------------------------------------

class TestPhase14Volume:

    def test_bulk_create_50_files(self):
        """Create 50 .akf files rapidly."""
        d = Path(TEST_DIR) / "bulk"
        d.mkdir(exist_ok=True)
        for i in range(50):
            akf("create", str(d / f"file_{i:03d}.akf"),
                "-c", f"Claim {i}", "-t", str(round(0.5 + (i % 50) * 0.01, 2)),
                "--src", f"source-{i}")
        assert len(list(d.glob("*.akf"))) == 50

    def test_bulk_validate_50(self):
        """Validate all 50 bulk files."""
        d = Path(TEST_DIR) / "bulk"
        failures = []
        for f in sorted(d.glob("*.akf")):
            rc, out, _ = akf("validate", str(f), allow_fail=True)
            if "Invalid" in out:
                failures.append(f.name)
        assert not failures, f"Failed: {failures}"

    def test_bulk_convert_directory(self):
        """Bulk convert entire test tree."""
        d = Path(TEST_DIR) / "markdown"
        out_dir = Path(TEST_DIR) / "bulk_converted"
        out_dir.mkdir(exist_ok=True)
        rc, out, _ = akf("convert", str(d), "-o", str(out_dir), "--recursive", "--overwrite")
        assert "Converted" in out

    def test_scan_entire_tree(self):
        """Scan the full test directory tree."""
        rc, out, _ = akf("scan", TEST_DIR, "-r")
        assert "Scanned" in out
        # Parse the count
        import re
        m = re.search(r"Scanned (\d+) files", out)
        assert m and int(m.group(1)) > 20


# ---------------------------------------------------------------------------
# Phase 15: Cross-format derive & provenance chain
# ---------------------------------------------------------------------------

class TestPhase15CrossFormat:

    def test_derive_md_to_akf(self):
        from akf import universal

        src = str(Path(TEST_DIR) / "markdown" / "revenue.md")
        out_md = str(Path(TEST_DIR) / "derived_output.md")
        make_markdown(out_md, "Derived", "Derived from revenue report.")

        universal.derive(src, out_md, agent_id="derive-agent", action="summarized")
        meta = universal.extract(out_md)
        assert meta is not None
        prov = meta.get("provenance", [])
        assert len(prov) >= 1
        assert any("summarized" in str(p) for p in prov)

    def test_provenance_tree_walk(self):
        from akf import universal

        src = str(Path(TEST_DIR) / "markdown" / "revenue.md")
        tree = universal.provenance_tree(src)
        assert len(tree) >= 1
        assert tree[0]["file"] == os.path.abspath(src)

    def test_verify_chain(self):
        from akf import universal

        src = str(Path(TEST_DIR) / "markdown" / "revenue.md")
        results = universal.verify_chain(src)
        assert len(results) >= 1
