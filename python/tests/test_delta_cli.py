"""Tests for Delta 4 & 6: CLI stamp and freshness commands."""

from click.testing import CliRunner

from akf.cli import main


class TestStampCommand:
    def test_stamp_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["stamp", "--help"])
        assert result.exit_code == 0
        assert "trust metadata" in result.output or "Stamps" in result.output

    def test_embed_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["embed", "--help"])
        assert result.exit_code == 0


class TestFreshnessCommand:
    def test_freshness_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["freshness", "--help"])
        assert result.exit_code == 0
        assert "freshness" in result.output.lower() or "claims" in result.output.lower()
