"""Tests for AKF view module."""

from akf.builder import AKFBuilder
from akf.core import create
from akf.view import executive_summary, show, to_html, to_markdown


class TestShow:
    def test_show_runs(self, capsys):
        unit = create("test claim", confidence=0.8)
        show(unit)
        captured = capsys.readouterr()
        assert "test claim" in captured.out


class TestToHtml:
    def test_basic(self):
        unit = (
            AKFBuilder()
            .by("sarah@test.com")
            .label("confidential")
            .claim("Revenue $4.2B", 0.98, source="SEC", authority_tier=1, verified=True)
            .claim("AI insight", 0.7, ai_generated=True)
            .build()
        )
        html = to_html(unit)
        assert "<!DOCTYPE html>" in html
        assert "Revenue" in html
        assert "Verified" in html
        assert "AI" in html
        assert "confidential" in html

    def test_minimal(self):
        unit = create("test", confidence=0.5)
        html = to_html(unit)
        assert "<html" in html


class TestToMarkdown:
    def test_basic(self):
        unit = (
            AKFBuilder()
            .by("sarah@test.com")
            .claim("Revenue $4.2B", 0.98, source="SEC")
            .build()
        )
        md = to_markdown(unit)
        assert "# AKF" in md
        assert "Revenue" in md
        assert "sarah@test.com" in md
        assert "Source: SEC" in md

    def test_with_provenance(self):
        unit = (
            AKFBuilder()
            .by("user@test.com")
            .claim("test", 0.5)
            .build()
        )
        md = to_markdown(unit)
        assert "Provenance" in md


class TestExecutiveSummary:
    def test_high_confidence(self):
        unit = create("High confidence claim", confidence=0.95, source="SEC", verified=True)
        summary = executive_summary(unit)
        assert "Executive Summary" in summary
        assert "HIGH" in summary

    def test_with_ai_claims(self):
        unit = (
            AKFBuilder()
            .by("user@test.com")
            .claim("Human claim", 0.9, source="SEC")
            .claim("AI claim", 0.7, ai_generated=True, source="model")
            .build()
        )
        summary = executive_summary(unit)
        assert "AI-generated" in summary

    def test_low_confidence(self):
        unit = create("Low confidence", confidence=0.3)
        summary = executive_summary(unit)
        assert "LOW" in summary or "caution" in summary.lower()
