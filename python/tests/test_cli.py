"""Tests for AKF CLI."""

import json
import os
import tempfile
import pytest
from click.testing import CliRunner
from akf.cli import main
from akf.core import create, load


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_file():
    """Create a sample .akf file for testing."""
    from akf.builder import AKFBuilder
    unit = (
        AKFBuilder()
        .by("sarah@test.com")
        .label("confidential")
        .claim("Revenue $4.2B", 0.98, src="SEC 10-Q", tier=1, ver=True)
        .claim("Growth 15%", 0.85, src="Gartner", tier=2)
        .claim("AI inference", 0.63, src="inference", tier=5, ai=True,
               risk="AI extrapolation")
        .build()
    )
    with tempfile.NamedTemporaryFile(suffix=".akf", delete=False, mode="w") as f:
        f.write(unit.to_json())
        f.write("\n")
        path = f.name
    yield path
    os.unlink(path)


class TestCreateCmd:
    def test_create_single(self, runner):
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False) as f:
            path = f.name
        try:
            result = runner.invoke(main, [
                "create", path,
                "--claim", "Revenue $4.2B",
                "--trust", "0.98",
                "--src", "SEC 10-Q",
            ])
            assert result.exit_code == 0
            assert "Created" in result.output
            unit = load(path)
            assert unit.claims[0].c == "Revenue $4.2B"
        finally:
            os.unlink(path)

    def test_create_multi(self, runner):
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False) as f:
            path = f.name
        try:
            result = runner.invoke(main, [
                "create", path,
                "--claim", "Claim 1", "--trust", "0.9",
                "--claim", "Claim 2", "--trust", "0.8",
                "--by", "user@test.com",
                "--label", "internal",
            ])
            assert result.exit_code == 0
            unit = load(path)
            assert len(unit.claims) == 2
            assert unit.by == "user@test.com"
        finally:
            os.unlink(path)


class TestValidateCmd:
    def test_valid_file(self, runner, sample_file):
        result = runner.invoke(main, ["validate", sample_file])
        assert result.exit_code == 0
        assert "Valid AKF" in result.output

    def test_invalid_file(self, runner):
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False, mode="w") as f:
            json.dump({"v": "1.0", "claims": [{"c": "test", "t": 0.5}], "label": "top-secret"}, f)
            path = f.name
        try:
            result = runner.invoke(main, ["validate", path])
            assert "Invalid AKF" in result.output
        finally:
            os.unlink(path)


class TestInspectCmd:
    def test_inspect(self, runner, sample_file):
        result = runner.invoke(main, ["inspect", sample_file])
        assert result.exit_code == 0
        assert "Revenue" in result.output
        assert "sarah@test.com" in result.output


class TestTrustCmd:
    def test_trust(self, runner, sample_file):
        result = runner.invoke(main, ["trust", sample_file])
        assert result.exit_code == 0
        assert "ACCEPT" in result.output or "REJECT" in result.output


class TestConsumeCmd:
    def test_consume(self, runner, sample_file):
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False) as f:
            output_path = f.name
        try:
            result = runner.invoke(main, [
                "consume", sample_file,
                "--output", output_path,
                "--threshold", "0.5",
                "--agent", "test-agent",
            ])
            assert result.exit_code == 0
            assert "Consumed" in result.output
            derived = load(output_path)
            assert len(derived.claims) > 0
        finally:
            os.unlink(output_path)


class TestProvenanceCmd:
    def test_tree(self, runner, sample_file):
        result = runner.invoke(main, ["provenance", sample_file])
        assert result.exit_code == 0
        assert "sarah@test.com" in result.output

    def test_json_format(self, runner, sample_file):
        result = runner.invoke(main, ["provenance", sample_file, "--format", "json"])
        assert result.exit_code == 0


class TestEnrichCmd:
    def test_enrich(self, runner, sample_file):
        result = runner.invoke(main, [
            "enrich", sample_file,
            "--agent", "copilot-m365",
            "--claim", "New AI insight",
            "--trust", "0.75",
        ])
        assert result.exit_code == 0
        assert "Enriched" in result.output
        unit = load(sample_file)
        assert any(c.c == "New AI insight" for c in unit.claims)


class TestDiffCmd:
    def test_diff(self, runner, sample_file):
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False) as f:
            output_path = f.name
        try:
            # Create derived file
            runner.invoke(main, [
                "consume", sample_file,
                "--output", output_path,
                "--threshold", "0.5",
                "--agent", "agent",
            ])
            result = runner.invoke(main, ["diff", sample_file, output_path])
            assert result.exit_code == 0
            assert "Comparing" in result.output
        finally:
            os.unlink(output_path)
