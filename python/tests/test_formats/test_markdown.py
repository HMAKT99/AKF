"""Tests for the Markdown format handler."""

import json
import os
import tempfile
from typing import Optional

import pytest

from akf.formats.markdown import MarkdownHandler, render


@pytest.fixture
def handler() -> MarkdownHandler:
    return MarkdownHandler()


@pytest.fixture
def tmp_md(tmp_path):
    """Helper that returns a factory for temp Markdown files."""

    def _make(content: str, name: str = "test.md") -> str:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return str(p)

    return _make


# --------------------------------------------------------------------------
# Class attributes
# --------------------------------------------------------------------------


class TestMarkdownHandlerAttributes:
    def test_format_name(self, handler: MarkdownHandler) -> None:
        assert handler.FORMAT_NAME == "Markdown"

    def test_extensions(self, handler: MarkdownHandler) -> None:
        assert ".md" in handler.EXTENSIONS
        assert ".markdown" in handler.EXTENSIONS

    def test_mode(self, handler: MarkdownHandler) -> None:
        assert handler.MODE == "embedded"

    def test_no_dependencies(self, handler: MarkdownHandler) -> None:
        assert handler.DEPENDENCIES == []


# --------------------------------------------------------------------------
# embed / extract round-trip -- no existing frontmatter
# --------------------------------------------------------------------------


class TestEmbedExtractNoFrontmatter:
    def test_round_trip(self, handler: MarkdownHandler, tmp_md) -> None:
        filepath = tmp_md("# Hello\n\nSome content here.\n")
        metadata = {"akf": "1.0", "overall_trust": 0.85, "claims": []}

        handler.embed(filepath, metadata)
        result = handler.extract(filepath)

        assert result is not None
        assert result["akf"] == "1.0"
        assert result["overall_trust"] == 0.85

    def test_body_preserved(self, handler: MarkdownHandler, tmp_md) -> None:
        original_body = "# Hello\n\nSome content here.\n"
        filepath = tmp_md(original_body)
        metadata = {"akf": "1.0", "claims": []}

        handler.embed(filepath, metadata)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # The original body should appear after the frontmatter
        assert original_body in content


# --------------------------------------------------------------------------
# embed / extract round-trip -- existing frontmatter
# --------------------------------------------------------------------------


class TestEmbedExtractWithFrontmatter:
    def test_round_trip(self, handler: MarkdownHandler, tmp_md) -> None:
        filepath = tmp_md("---\ntitle: My Doc\nauthor: Alice\n---\n# Hello\n")
        metadata = {"akf": "1.0", "overall_trust": 0.9, "claims": []}

        handler.embed(filepath, metadata)
        result = handler.extract(filepath)

        assert result is not None
        assert result["akf"] == "1.0"
        assert result["overall_trust"] == 0.9

    def test_existing_fields_preserved(self, handler: MarkdownHandler, tmp_md) -> None:
        filepath = tmp_md("---\ntitle: My Doc\nauthor: Alice\n---\n# Hello\n")
        metadata = {"akf": "1.0", "claims": []}

        handler.embed(filepath, metadata)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # The original frontmatter keys should still be present
        assert "title:" in content
        assert "author:" in content

    def test_body_preserved(self, handler: MarkdownHandler, tmp_md) -> None:
        filepath = tmp_md("---\ntitle: My Doc\n---\n# Hello\n\nParagraph.\n")
        metadata = {"akf": "1.0", "claims": []}

        handler.embed(filepath, metadata)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "# Hello" in content
        assert "Paragraph." in content

    def test_re_embed_replaces(self, handler: MarkdownHandler, tmp_md) -> None:
        filepath = tmp_md("# Test\n")
        handler.embed(filepath, {"akf": "1.0", "overall_trust": 0.5, "claims": []})
        handler.embed(filepath, {"akf": "1.0", "overall_trust": 0.9, "claims": []})

        result = handler.extract(filepath)
        assert result is not None
        assert result["overall_trust"] == 0.9


# --------------------------------------------------------------------------
# is_enriched
# --------------------------------------------------------------------------


class TestIsEnriched:
    def test_enriched_file(self, handler: MarkdownHandler, tmp_md) -> None:
        filepath = tmp_md("# Hello\n")
        handler.embed(filepath, {"akf": "1.0", "claims": []})
        assert handler.is_enriched(filepath) is True

    def test_non_enriched_file(self, handler: MarkdownHandler, tmp_md) -> None:
        filepath = tmp_md("# Hello\n\nJust plain markdown.\n")
        assert handler.is_enriched(filepath) is False


# --------------------------------------------------------------------------
# HTML comment fallback extraction
# --------------------------------------------------------------------------


class TestHtmlCommentFallback:
    def test_extract_from_comment(self, handler: MarkdownHandler, tmp_md) -> None:
        akf_data = {"akf": "1.0", "claims": []}
        comment = "<!-- akf:{} -->".format(json.dumps(akf_data))
        filepath = tmp_md(comment + "\n# Hello\n")

        result = handler.extract(filepath)
        assert result is not None
        assert result["akf"] == "1.0"


# --------------------------------------------------------------------------
# render()
# --------------------------------------------------------------------------


class TestRender:
    def test_basic_render(self) -> None:
        akf_unit = {
            "claims": [
                {"c": "Revenue was $1M.", "t": 0.98, "src": "SEC 10-Q", "ver": True},
                {"c": "Projected growth 10%.", "t": 0.6, "ai": True},
            ]
        }

        output = render(akf_unit)

        assert "Revenue was $1M." in output
        assert "Projected growth 10%." in output
        assert "<!-- akf:" in output

    def test_render_with_annotations(self) -> None:
        akf_unit = {
            "claims": [
                {"c": "Claim 1", "t": 0.98, "src": "Source A", "ver": True, "tier": 1},
            ]
        }

        output = render(akf_unit)
        # The HTML comment should contain the trust info as JSON
        assert '"t":0.98' in output
        assert '"src":"Source A"' in output
        assert '"ver":true' in output

    def test_render_without_comments(self) -> None:
        akf_unit = {
            "claims": [
                {"c": "Claim 1", "t": 0.9},
            ]
        }

        output = render(akf_unit, include_comments=False)
        assert "<!-- akf:" not in output
        assert "Claim 1" in output


# --------------------------------------------------------------------------
# auto_enrich (inherited from base)
# --------------------------------------------------------------------------


class TestAutoEnrich:
    def test_auto_enrich_creates_metadata(self, handler: MarkdownHandler, tmp_md) -> None:
        filepath = tmp_md("# Auto-generated doc\n\nSome AI content.\n")

        handler.auto_enrich(filepath, agent_id="test-agent-v1")

        result = handler.extract(filepath)
        assert result is not None
        assert result["akf"] == "1.0"
        assert result["ai_contribution"] == 1.0
        assert len(result["provenance"]) == 1
        assert result["provenance"][0]["actor"] == "test-agent-v1"

    def test_auto_enrich_with_classification(self, handler: MarkdownHandler, tmp_md) -> None:
        filepath = tmp_md("# Confidential doc\n")

        handler.auto_enrich(filepath, agent_id="agent", classification="confidential")

        result = handler.extract(filepath)
        assert result is not None
        assert result["classification"] == "confidential"


# --------------------------------------------------------------------------
# scan (inherited from base)
# --------------------------------------------------------------------------


class TestScan:
    def test_scan_enriched(self, handler: MarkdownHandler, tmp_md) -> None:
        filepath = tmp_md("# Test\n")
        handler.embed(
            filepath,
            {
                "akf": "1.0",
                "overall_trust": 0.85,
                "claims": [{"c": "Claim", "t": 0.9, "ai": True}],
            },
        )

        report = handler.scan(filepath)
        assert report.enriched is True
        assert report.claim_count == 1
        assert report.format == "Markdown"

    def test_scan_non_enriched(self, handler: MarkdownHandler, tmp_md) -> None:
        filepath = tmp_md("# Plain markdown\n")

        report = handler.scan(filepath)
        assert report.enriched is False


# --------------------------------------------------------------------------
# Module-level convenience functions
# --------------------------------------------------------------------------


class TestModuleConvenience:
    def test_module_embed_extract(self, tmp_md) -> None:
        from akf.formats.markdown import embed as md_embed
        from akf.formats.markdown import extract as md_extract

        filepath = tmp_md("# Test\n")
        md_embed(filepath, {"akf": "1.0", "claims": []})
        result = md_extract(filepath)
        assert result is not None
        assert result["akf"] == "1.0"
