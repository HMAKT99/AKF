"""Tests for akf scan --badge and self-documenting sidecars."""

import json

import pytest
from click.testing import CliRunner

from akf.cli import main, _build_badge
from akf.formats.base import ScanReport
from akf.stamp import stamp_file
from akf import sidecar


@pytest.fixture
def runner():
    return CliRunner()


class TestBuildBadge:
    def test_empty_scan(self):
        badge = _build_badge([])
        assert badge["schemaVersion"] == 1
        assert badge["color"] == "lightgrey"

    def test_no_enriched_files(self):
        reports = [ScanReport(enriched=False) for _ in range(3)]
        assert _build_badge(reports)["message"] == "no trust metadata"

    def test_stamped_percentage_and_trust(self):
        reports = [
            ScanReport(enriched=True, overall_trust=0.9),
            ScanReport(enriched=True, overall_trust=0.7),
            ScanReport(enriched=False),
            ScanReport(enriched=False),
        ]
        badge = _build_badge(reports)
        assert badge["message"] == "50% stamped · trust 0.80"
        assert badge["color"] == "brightgreen"

    def test_low_trust_is_red(self):
        reports = [ScanReport(enriched=True, overall_trust=0.2)]
        assert _build_badge(reports)["color"] == "red"


class TestScanBadgeCli:
    def test_badge_to_stdout(self, runner, tmp_path):
        f = tmp_path / "a.md"
        f.write_text("# A\n")
        stamp_file(str(f), agent="claude-code", evidence=["tests pass"])
        result = runner.invoke(main, ["scan", str(tmp_path), "--badge", "-"])
        assert result.exit_code == 0
        badge = json.loads(result.output)
        assert badge["schemaVersion"] == 1
        assert "stamped" in badge["message"]

    def test_badge_to_file(self, runner, tmp_path):
        f = tmp_path / "a.md"
        f.write_text("# A\n")
        out = tmp_path / "badge.json"
        result = runner.invoke(main, ["scan", str(tmp_path), "--badge", str(out)])
        assert result.exit_code == 0
        assert json.loads(out.read_text())["label"] == "AKF"


class TestSidecarSpecKey:
    def test_sidecar_is_self_documenting(self, tmp_path):
        f = tmp_path / "data.bin"
        f.write_bytes(b"\x00\x01")
        sc = sidecar.create(str(f), {"claims": [{"c": "binary artifact", "t": 0.8}]})
        data = json.loads(open(sc).read())
        assert data["spec"] == "https://akf.dev"
        assert data["akf"] == "1.0"
