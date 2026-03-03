"""Tests for the HTML format handler."""

import json
from typing import Optional

import pytest

from akf.formats.html import HTMLHandler, default_css, render


@pytest.fixture
def handler() -> HTMLHandler:
    return HTMLHandler()


@pytest.fixture
def tmp_html(tmp_path):
    """Helper that returns a factory for temp HTML files."""

    def _make(content: str, name: str = "test.html") -> str:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return str(p)

    return _make


SIMPLE_HTML = """\
<!DOCTYPE html>
<html>
<body>
<h1>Hello</h1>
<p>World</p>
</body>
</html>
"""

HTML_WITH_HEAD = """\
<!DOCTYPE html>
<html>
<head>
<title>Test</title>
</head>
<body>
<h1>Hello</h1>
</body>
</html>
"""


# --------------------------------------------------------------------------
# Class attributes
# --------------------------------------------------------------------------


class TestHTMLHandlerAttributes:
    def test_format_name(self, handler: HTMLHandler) -> None:
        assert handler.FORMAT_NAME == "HTML"

    def test_extensions(self, handler: HTMLHandler) -> None:
        assert ".html" in handler.EXTENSIONS
        assert ".htm" in handler.EXTENSIONS

    def test_mode(self, handler: HTMLHandler) -> None:
        assert handler.MODE == "embedded"

    def test_mechanism(self, handler: HTMLHandler) -> None:
        assert handler.MECHANISM == "JSON-LD script tag"

    def test_no_dependencies(self, handler: HTMLHandler) -> None:
        assert handler.DEPENDENCIES == []


# --------------------------------------------------------------------------
# embed / extract round-trip -- simple HTML (no <head>)
# --------------------------------------------------------------------------


class TestEmbedExtractSimple:
    def test_round_trip(self, handler: HTMLHandler, tmp_html) -> None:
        filepath = tmp_html(SIMPLE_HTML)
        metadata = {"akf": "1.0", "overall_trust": 0.85, "claims": []}

        handler.embed(filepath, metadata)
        result = handler.extract(filepath)

        assert result is not None
        assert result["akf"] == "1.0"
        assert result["overall_trust"] == 0.85

    def test_body_preserved(self, handler: HTMLHandler, tmp_html) -> None:
        filepath = tmp_html(SIMPLE_HTML)
        metadata = {"akf": "1.0", "claims": []}

        handler.embed(filepath, metadata)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "<h1>Hello</h1>" in content
        assert "<p>World</p>" in content


# --------------------------------------------------------------------------
# embed / extract round-trip -- HTML with <head>
# --------------------------------------------------------------------------


class TestEmbedExtractWithHead:
    def test_round_trip(self, handler: HTMLHandler, tmp_html) -> None:
        filepath = tmp_html(HTML_WITH_HEAD)
        metadata = {"akf": "1.0", "overall_trust": 0.9, "claims": []}

        handler.embed(filepath, metadata)
        result = handler.extract(filepath)

        assert result is not None
        assert result["akf"] == "1.0"
        assert result["overall_trust"] == 0.9

    def test_script_in_head(self, handler: HTMLHandler, tmp_html) -> None:
        filepath = tmp_html(HTML_WITH_HEAD)
        metadata = {"akf": "1.0", "claims": []}

        handler.embed(filepath, metadata)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Script tag should be before </head>
        script_pos = content.find('application/akf+json')
        head_close_pos = content.find("</head>")
        assert script_pos < head_close_pos


# --------------------------------------------------------------------------
# embed replaces existing AKF metadata
# --------------------------------------------------------------------------


class TestEmbedReplaces:
    def test_replace_existing(self, handler: HTMLHandler, tmp_html) -> None:
        filepath = tmp_html(HTML_WITH_HEAD)

        handler.embed(filepath, {"akf": "1.0", "overall_trust": 0.5, "claims": []})
        handler.embed(filepath, {"akf": "1.0", "overall_trust": 0.95, "claims": []})

        result = handler.extract(filepath)
        assert result is not None
        assert result["overall_trust"] == 0.95

    def test_only_one_script_tag_after_replace(self, handler: HTMLHandler, tmp_html) -> None:
        filepath = tmp_html(HTML_WITH_HEAD)

        handler.embed(filepath, {"akf": "1.0", "claims": []})
        handler.embed(filepath, {"akf": "1.0", "claims": []})

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        count = content.count('application/akf+json')
        assert count == 1


# --------------------------------------------------------------------------
# render()
# --------------------------------------------------------------------------


class TestRender:
    def test_basic_render(self) -> None:
        akf_unit = {
            "claims": [
                {"c": "Revenue was $1M.", "t": 0.98, "src": "SEC 10-Q", "ver": True, "tier": 1},
                {"c": "Projected growth 10%.", "t": 0.6, "ai": True, "tier": 3},
            ]
        }

        output = render(akf_unit)
        assert "<p " in output
        assert "Revenue was $1M." in output
        assert "Projected growth 10%." in output

    def test_data_attributes(self) -> None:
        akf_unit = {
            "claims": [
                {"c": "Test claim.", "t": 0.98, "src": "SEC 10-Q", "ver": True, "tier": 1},
            ]
        }

        output = render(akf_unit)
        assert 'data-akf-trust="0.98"' in output
        assert 'data-akf-source="SEC 10-Q"' in output
        assert 'data-akf-verified="true"' in output
        assert 'data-akf-tier="1"' in output

    def test_trust_high_class(self) -> None:
        akf_unit = {"claims": [{"c": "High trust.", "t": 0.9}]}
        output = render(akf_unit)
        assert "akf-trust-high" in output

    def test_trust_medium_class(self) -> None:
        akf_unit = {"claims": [{"c": "Medium trust.", "t": 0.5}]}
        output = render(akf_unit)
        assert "akf-trust-medium" in output

    def test_trust_low_class(self) -> None:
        akf_unit = {"claims": [{"c": "Low trust.", "t": 0.2}]}
        output = render(akf_unit)
        assert "akf-trust-low" in output

    def test_ai_class(self) -> None:
        akf_unit = {"claims": [{"c": "AI claim.", "t": 0.5, "ai": True}]}
        output = render(akf_unit)
        assert "akf-ai" in output

    def test_verified_class(self) -> None:
        akf_unit = {"claims": [{"c": "Verified.", "t": 0.9, "ver": True}]}
        output = render(akf_unit)
        assert "akf-verified" in output

    def test_html_escaping(self) -> None:
        akf_unit = {"claims": [{"c": "x < y & z > w", "t": 0.5}]}
        output = render(akf_unit)
        assert "&lt;" in output
        assert "&amp;" in output
        assert "&gt;" in output


# --------------------------------------------------------------------------
# default_css()
# --------------------------------------------------------------------------


class TestDefaultCSS:
    def test_returns_string(self) -> None:
        css = default_css()
        assert isinstance(css, str)
        assert len(css) > 0

    def test_contains_trust_classes(self) -> None:
        css = default_css()
        assert ".akf-trust-high" in css
        assert ".akf-trust-medium" in css
        assert ".akf-trust-low" in css

    def test_contains_ai_class(self) -> None:
        css = default_css()
        assert ".akf-ai" in css

    def test_contains_verified_class(self) -> None:
        css = default_css()
        assert ".akf-verified" in css


# --------------------------------------------------------------------------
# is_enriched
# --------------------------------------------------------------------------


class TestIsEnriched:
    def test_enriched(self, handler: HTMLHandler, tmp_html) -> None:
        filepath = tmp_html(HTML_WITH_HEAD)
        handler.embed(filepath, {"akf": "1.0", "claims": []})
        assert handler.is_enriched(filepath) is True

    def test_not_enriched(self, handler: HTMLHandler, tmp_html) -> None:
        filepath = tmp_html(SIMPLE_HTML)
        assert handler.is_enriched(filepath) is False


# --------------------------------------------------------------------------
# auto_enrich (inherited from base)
# --------------------------------------------------------------------------


class TestAutoEnrich:
    def test_auto_enrich_creates_metadata(self, handler: HTMLHandler, tmp_html) -> None:
        filepath = tmp_html("<html><body><p>AI content</p></body></html>")

        handler.auto_enrich(filepath, agent_id="test-agent-v1")

        result = handler.extract(filepath)
        assert result is not None
        assert result["akf"] == "1.0"
        assert result["ai_contribution"] == 1.0
        assert len(result["provenance"]) == 1
        assert result["provenance"][0]["actor"] == "test-agent-v1"

    def test_auto_enrich_with_classification(self, handler: HTMLHandler, tmp_html) -> None:
        filepath = tmp_html("<html><body></body></html>")

        handler.auto_enrich(filepath, agent_id="agent", classification="internal")

        result = handler.extract(filepath)
        assert result is not None
        assert result["classification"] == "internal"


# --------------------------------------------------------------------------
# scan (inherited from base)
# --------------------------------------------------------------------------


class TestScan:
    def test_scan_enriched(self, handler: HTMLHandler, tmp_html) -> None:
        filepath = tmp_html(HTML_WITH_HEAD)
        handler.embed(
            filepath,
            {
                "akf": "1.0",
                "overall_trust": 0.85,
                "claims": [{"c": "Claim", "t": 0.9}],
            },
        )

        report = handler.scan(filepath)
        assert report.enriched is True
        assert report.claim_count == 1
        assert report.format == "HTML"

    def test_scan_non_enriched(self, handler: HTMLHandler, tmp_html) -> None:
        filepath = tmp_html(SIMPLE_HTML)
        report = handler.scan(filepath)
        assert report.enriched is False


# --------------------------------------------------------------------------
# Module-level convenience functions
# --------------------------------------------------------------------------


class TestModuleConvenience:
    def test_module_embed_extract(self, tmp_html) -> None:
        from akf.formats.html import embed as html_embed
        from akf.formats.html import extract as html_extract

        filepath = tmp_html(HTML_WITH_HEAD)
        html_embed(filepath, {"akf": "1.0", "claims": []})
        result = html_extract(filepath)
        assert result is not None
        assert result["akf"] == "1.0"
