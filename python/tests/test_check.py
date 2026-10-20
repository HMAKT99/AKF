"""Tests for akf check — the one-line agent trust check."""

import json
import os
import time
import tempfile

import pytest
from click.testing import CliRunner

from akf.check import check_file
from akf.cli import main
from akf.stamp import stamp_file


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def stamped_md(tmp_path):
    """A markdown file stamped with strong evidence."""
    path = tmp_path / "report.md"
    path.write_text("# Report\n\nAll good.\n")
    stamp_file(
        str(path),
        agent="claude-code",
        trust_score=0.9,
        evidence=["42/42 tests passed"],
    )
    return str(path)


class TestCheckFile:
    def test_ok_on_fresh_stamp(self, stamped_md):
        result = check_file(stamped_md)
        assert result.status == "OK"
        assert result.exit_code == 0
        assert result.agent == "claude-code"
        assert result.trust is not None and result.trust >= 0.6
        assert "test_pass" in result.evidence
        assert result.age_days == 0

    def test_unstamped(self, tmp_path):
        path = tmp_path / "plain.md"
        path.write_text("no metadata here\n")
        result = check_file(str(path))
        assert result.status == "UNSTAMPED"
        assert result.exit_code == 2
        assert result.reason == "no_metadata"

    def test_stale_after_modification(self, stamped_md):
        # Modify the file well past the mtime tolerance window.
        with open(stamped_md, "a") as f:
            f.write("\nedited later\n")
        future = time.time() + 3600
        os.utime(stamped_md, (future, future))
        result = check_file(stamped_md)
        assert result.status == "STALE"
        assert result.exit_code == 1
        assert result.reason == "modified_after_stamp"

    def test_low_trust(self, tmp_path):
        path = tmp_path / "guess.md"
        path.write_text("# Guess\n")
        stamp_file(str(path), agent="claude-code", trust_score=0.2)
        result = check_file(str(path))
        assert result.status == "LOW"
        assert result.exit_code == 1
        assert result.reason == "below_threshold"

    def test_bare_ai_stamp_is_low(self, tmp_path):
        # No verification evidence: stays at tier 5 (AI inference) -> LOW.
        path = tmp_path / "bare.md"
        path.write_text("# Bare\n")
        stamp_file(str(path), agent="claude-code", trust_score=0.9)
        result = check_file(str(path))
        assert result.status == "LOW"

    def test_default_stamp_with_tests_is_ok(self, tmp_path):
        # The documented flow: akf stamp <file> --evidence "tests pass"
        # (default confidence 0.7) must clear the default threshold.
        path = tmp_path / "default.md"
        path.write_text("# D\n")
        stamp_file(str(path), agent="claude-code", evidence=["tests pass"])
        result = check_file(str(path))
        assert result.status == "OK"

    def test_weak_evidence_alone_stays_low(self, tmp_path):
        path = tmp_path / "linted.md"
        path.write_text("# L\n")
        stamp_file(str(path), agent="claude-code", evidence=["lint: clean"])
        assert check_file(str(path)).status == "LOW"

    def test_human_review_scores_above_tests(self, tmp_path):
        tested = tmp_path / "tested.md"
        tested.write_text("# T\n")
        stamp_file(str(tested), agent="claude-code", trust_score=0.9,
                   evidence=["42/42 tests passed"])
        reviewed = tmp_path / "reviewed.md"
        reviewed.write_text("# R\n")
        stamp_file(str(reviewed), agent="claude-code", trust_score=0.9,
                   evidence=["reviewed by @sarah"])
        assert check_file(str(reviewed)).trust > check_file(str(tested)).trust

    def test_threshold_is_respected(self, tmp_path):
        path = tmp_path / "mid.md"
        path.write_text("# Mid\n")
        stamp_file(str(path), agent="claude-code", trust_score=0.9)
        strict = check_file(str(path), threshold=0.99)
        assert strict.status == "LOW"

    def test_summary_line_is_compact(self, stamped_md):
        line = check_file(stamped_md).summary_line()
        assert line.startswith("OK trust=")
        assert "agent=claude-code" in line
        assert len(line) < 120


class TestCheckCmd:
    def test_cli_ok_exit_zero(self, runner, stamped_md):
        result = runner.invoke(main, ["check", stamped_md])
        assert result.exit_code == 0
        assert result.output.startswith("OK ")

    def test_cli_unstamped_exit_two(self, runner, tmp_path):
        path = tmp_path / "plain.txt"
        path.write_text("nothing\n")
        result = runner.invoke(main, ["check", str(path)])
        assert result.exit_code == 2
        assert "UNSTAMPED" in result.output

    def test_cli_json(self, runner, stamped_md):
        result = runner.invoke(main, ["check", stamped_md, "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["status"] == "OK"
        assert payload["agent"] == "claude-code"


class TestReceiptStrengthScaling:
    """#125 — evidence weight scales with receipt strength, additively."""

    def test_bare_tests_pass_unchanged(self, tmp_path):
        # The documented hero flow must not regress.
        p = tmp_path / "hero.md"
        p.write_text("# H\n")
        stamp_file(str(p), agent="claude-code", evidence=["tests pass"])
        assert check_file(str(p)).status == "OK"

    def test_full_pass_fraction_keeps_strong_floor(self, tmp_path):
        p = tmp_path / "full.md"
        p.write_text("# F\n")
        stamp_file(str(p), agent="claude-code", evidence=["42/42 tests passed"])
        assert check_file(str(p)).status == "OK"

    def test_partial_pass_fraction_weakens(self, tmp_path):
        p = tmp_path / "partial.md"
        p.write_text("# P\n")
        stamp_file(str(p), agent="claude-code", evidence=["40/42 tests passed"])
        result = check_file(str(p))
        assert result.status == "LOW"

    def test_low_coverage_weakens(self, tmp_path):
        p = tmp_path / "lowcov.md"
        p.write_text("# L\n")
        stamp_file(str(p), agent="claude-code",
                   evidence=["tests pass, coverage: 12%"])
        assert check_file(str(p)).status == "LOW"

    def test_high_coverage_keeps_strong_floor(self, tmp_path):
        p = tmp_path / "hicov.md"
        p.write_text("# H\n")
        stamp_file(str(p), agent="claude-code",
                   evidence=["tests pass, coverage: 85%"])
        assert check_file(str(p)).status == "OK"

    def test_replayable_evidence_keeps_strong_floor(self, tmp_path):
        p = tmp_path / "rep.md"
        p.write_text("# R\n")
        stamp_file(str(p), agent="claude-code", replay="true")
        # replay recipe of "true" classifies as type other, but replayability
        # itself earns the strong floor
        assert check_file(str(p)).status == "OK"


class TestContentHashStaleness:
    """mtime alone must not make unchanged content STALE (fresh checkouts)."""

    def _touch_future(self, path):
        future = time.time() + 3600
        os.utime(path, (future, future))

    def test_markdown_mtime_only_change_is_ok(self, stamped_md):
        self._touch_future(stamped_md)
        assert check_file(stamped_md).status == "OK"

    def test_markdown_copy_is_ok(self, stamped_md, tmp_path):
        import shutil
        copy = str(tmp_path / "clone.md")
        shutil.copy(stamped_md, copy)
        self._touch_future(copy)
        assert check_file(copy).status == "OK"

    def test_markdown_with_frontmatter_mtime_only_is_ok(self, tmp_path):
        path = tmp_path / "skill.md"
        path.write_text("---\nname: demo\ntags: [a, b]\n---\n\n# Demo\n")
        stamp_file(str(path), agent="claude-code", trust_score=0.9,
                   evidence=["reviewed by @someone"])
        self._touch_future(str(path))
        assert check_file(str(path)).status == "OK"

    def test_markdown_restamp_then_mtime_only_is_ok(self, stamped_md):
        stamp_file(stamped_md, agent="claude-code", trust_score=0.9,
                   evidence=["reviewed by @someone"])
        self._touch_future(stamped_md)
        assert check_file(stamped_md).status == "OK"

    def test_markdown_body_edit_is_stale(self, stamped_md):
        with open(stamped_md, "a") as f:
            f.write("\nedited later\n")
        self._touch_future(stamped_md)
        assert check_file(stamped_md).status == "STALE"

    def test_markdown_frontmatter_edit_is_stale(self, tmp_path):
        path = tmp_path / "skill.md"
        path.write_text("---\nname: demo\n---\n\n# Demo\n")
        stamp_file(str(path), agent="claude-code", trust_score=0.9,
                   evidence=["reviewed by @someone"])
        path.write_text(path.read_text().replace("name: demo", "name: changed"))
        self._touch_future(str(path))
        assert check_file(str(path)).status == "STALE"

    def test_sidecar_file_mtime_only_is_ok(self, tmp_path):
        path = tmp_path / "mod.py"
        path.write_text("x = 1\n")
        stamp_file(str(path), agent="claude-code", trust_score=0.9,
                   evidence=["42/42 tests passed"])
        self._touch_future(str(path))
        assert check_file(str(path)).status == "OK"

    def test_sidecar_file_edit_is_stale(self, tmp_path):
        path = tmp_path / "mod.py"
        path.write_text("x = 1\n")
        stamp_file(str(path), agent="claude-code", trust_score=0.9,
                   evidence=["42/42 tests passed"])
        path.write_text("x = 2\n")
        self._touch_future(str(path))
        assert check_file(str(path)).status == "STALE"


class TestContentHashBinaryFormats:
    """Embedded-stamp binary formats: mtime-only change is OK, a real edit is STALE."""

    @staticmethod
    def _future(path):
        t = time.time() + 3600
        os.utime(path, (t, t))

    @staticmethod
    def _stamp(path):
        stamp_file(str(path), agent="claude-code", trust_score=0.9,
                   evidence=["reviewed by @someone"])

    def _assert_ok_then_stale(self, path, edit):
        self._stamp(path)
        assert check_file(str(path)).status == "OK"
        self._future(str(path))
        assert check_file(str(path)).status == "OK", "mtime-only change must stay OK"
        from akf import universal
        old_meta = universal.extract(str(path))
        edit(path)
        # Rewriting an embedded-stamp file usually drops its stamp; put the
        # old one back so the test models "stamped, then edited".
        if universal.extract(str(path)) is None:
            universal.embed(str(path), metadata=old_meta)
        self._future(str(path))
        assert check_file(str(path)).status == "STALE"

    def test_docx(self, tmp_path):
        docx = pytest.importorskip("docx")
        path = tmp_path / "r.docx"
        d = docx.Document()
        d.add_paragraph("Revenue was 4.2B")
        d.save(str(path))

        def edit(p):
            doc = docx.Document(str(p))
            doc.add_paragraph("edited later")
            doc.save(str(p))

        self._assert_ok_then_stale(path, edit)

    def test_docx_restamp_is_ok(self, tmp_path):
        docx = pytest.importorskip("docx")
        path = tmp_path / "r.docx"
        d = docx.Document()
        d.add_paragraph("hello")
        d.save(str(path))
        self._stamp(path)
        self._stamp(path)
        self._future(str(path))
        assert check_file(str(path)).status == "OK"

    def test_xlsx(self, tmp_path):
        openpyxl = pytest.importorskip("openpyxl")
        path = tmp_path / "b.xlsx"
        wb = openpyxl.Workbook()
        wb.active["A1"] = 1
        wb.save(str(path))

        def edit(p):
            wb2 = openpyxl.load_workbook(str(p))
            wb2.active["A1"] = 2
            wb2.save(str(p))

        self._assert_ok_then_stale(path, edit)

    def test_pptx(self, tmp_path):
        pptx = pytest.importorskip("pptx")
        path = tmp_path / "s.pptx"
        prs = pptx.Presentation()
        prs.slides.add_slide(prs.slide_layouts[0]).shapes.title.text = "one"
        prs.save(str(path))

        def edit(p):
            prs2 = pptx.Presentation(str(p))
            prs2.slides[0].shapes.title.text = "two"
            prs2.save(str(p))

        self._assert_ok_then_stale(path, edit)

    def test_pdf(self, tmp_path):
        pytest.importorskip("pypdf")
        Image = pytest.importorskip("PIL.Image")
        path = tmp_path / "d.pdf"
        Image.new("RGB", (8, 8), (255, 0, 0)).save(str(path))

        def edit(p):
            Image.new("RGB", (16, 16), (0, 255, 0)).save(str(p))

        self._assert_ok_then_stale(path, edit)

    def test_png(self, tmp_path):
        Image = pytest.importorskip("PIL.Image")
        path = tmp_path / "i.png"
        Image.new("RGB", (8, 8), (255, 0, 0)).save(str(path))

        def edit(p):
            Image.new("RGB", (16, 16), (0, 0, 255)).save(str(p))

        self._assert_ok_then_stale(path, edit)

    def test_jpeg_sidecar(self, tmp_path):
        Image = pytest.importorskip("PIL.Image")
        path = tmp_path / "i.jpg"
        Image.new("RGB", (8, 8), (255, 0, 0)).save(str(path))

        def edit(p):
            Image.new("RGB", (16, 16), (0, 0, 255)).save(str(p))

        self._assert_ok_then_stale(path, edit)
