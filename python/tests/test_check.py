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
