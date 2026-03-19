"""Tests for content-based AI detection heuristics."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from akf.ai_detect import (
    AI_CREATOR_APPS,
    AiDetectionResult,
    _detect_creator_app,
    _scan_code_signals,
    _scan_text_signals,
    detect_ai_content,
)


# ---------------------------------------------------------------------------
# Text signal scanning
# ---------------------------------------------------------------------------

class TestTextSignals:
    def test_strong_ai_self_reference(self):
        text = "As an AI language model, I cannot help with that."
        score, signals = _scan_text_signals(text)
        assert score >= 0.3
        assert any("ai-self-reference" in s for s in signals)

    def test_formulaic_opening(self):
        text = "Certainly! I'd be happy to help you with that request."
        score, signals = _scan_text_signals(text)
        assert score >= 0.2
        assert len(signals) >= 2

    def test_closing_phrases(self):
        text = "I hope this helps! Feel free to ask if you have more questions."
        score, signals = _scan_text_signals(text)
        assert score >= 0.1

    def test_plain_text_low_score(self):
        text = "The quarterly revenue was $4.2B, up 12% year-over-year."
        score, signals = _scan_text_signals(text)
        assert score < 0.1

    def test_many_bullets(self):
        text = "\n".join(f"- Item {i}" for i in range(15))
        score, signals = _scan_text_signals(text)
        assert any("many-bullets" in s for s in signals)

    def test_many_headers(self):
        text = "\n".join(f"## Section {i}\nContent" for i in range(8))
        score, signals = _scan_text_signals(text)
        assert any("many-headers" in s for s in signals)

    def test_combined_signals_accumulate(self):
        text = (
            "Certainly! I'd be happy to help you with that.\n\n"
            "Here's a comprehensive overview:\n\n"
            "## Introduction\n"
            "It's worth noting that this is important.\n\n"
            "## Key Points\n"
            "- Point 1\n- Point 2\n- Point 3\n\n"
            "In summary, I hope this helps!\n"
            "Feel free to ask if you need anything else."
        )
        score, signals = _scan_text_signals(text)
        assert score >= 0.4
        assert len(signals) >= 4


# ---------------------------------------------------------------------------
# Code signal scanning
# ---------------------------------------------------------------------------

class TestCodeSignals:
    def test_narrating_comments(self):
        code = (
            "# Import necessary libraries\n"
            "import os\n\n"
            "# Define the main function\n"
            "def main():\n"
            "    # Initialize the configuration\n"
            "    config = {}\n"
        )
        score, signals = _scan_code_signals(code)
        assert score > 0
        assert any("narrating-comment" in s for s in signals)

    def test_every_func_docstringed(self):
        code = (
            'def foo():\n    """Foo."""\n    pass\n\n'
            'def bar():\n    """Bar."""\n    pass\n\n'
            'def baz():\n    """Baz."""\n    pass\n'
        )
        score, signals = _scan_code_signals(code)
        assert any("every-func-docstringed" in s for s in signals)

    def test_normal_code_low_score(self):
        code = (
            "def add(a, b):\n"
            "    return a + b\n\n"
            "result = add(1, 2)\n"
            "print(result)\n"
        )
        score, signals = _scan_code_signals(code)
        assert score < 0.15


# ---------------------------------------------------------------------------
# Creator app detection
# ---------------------------------------------------------------------------

class TestCreatorApp:
    def test_non_darwin_returns_none(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("data")
        with patch("akf.ai_detect.platform") as mock_platform:
            mock_platform.system.return_value = "Linux"
            assert _detect_creator_app(f) is None

    @pytest.mark.skipif(
        __import__("platform").system() != "Darwin",
        reason="xattr-based creator detection requires macOS",
    )
    def test_darwin_with_ai_creator(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("data")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '"Claude"\n2024-01-01'

        with patch("akf.ai_detect.platform") as mock_platform, \
             patch("akf.ai_detect.subprocess.run", return_value=mock_result):
            mock_platform.system.return_value = "Darwin"
            result = _detect_creator_app(f)
            assert result is not None
            assert "claude" in result

    def test_darwin_with_non_ai_creator(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("data")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '"Microsoft Word"'

        with patch("akf.ai_detect.platform") as mock_platform, \
             patch("akf.ai_detect.subprocess.run", return_value=mock_result):
            mock_platform.system.return_value = "Darwin"
            result = _detect_creator_app(f)
            assert result is None

    def test_darwin_null_creator(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("data")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "(null)"

        with patch("akf.ai_detect.platform") as mock_platform, \
             patch("akf.ai_detect.subprocess.run", return_value=mock_result):
            mock_platform.system.return_value = "Darwin"
            assert _detect_creator_app(f) is None


# ---------------------------------------------------------------------------
# Full detection
# ---------------------------------------------------------------------------

class TestDetectAiContent:
    def test_obvious_ai_text(self, tmp_path):
        f = tmp_path / "response.md"
        f.write_text(
            "As an AI language model, I'd be happy to help!\n\n"
            "Here's a comprehensive overview:\n\n"
            "## Introduction\n"
            "It's important to note that...\n\n"
            "## Conclusion\n"
            "I hope this helps! Feel free to ask more questions.\n"
        )
        result = detect_ai_content(f)
        assert result.likely_ai is True
        assert result.score >= 0.5
        assert len(result.signals) >= 3

    def test_human_text(self, tmp_path):
        f = tmp_path / "notes.txt"
        f.write_text(
            "Meeting notes 2024-03-15\n"
            "Discussed Q1 targets. Revenue tracking at $4.2B.\n"
            "Action items: ship v2, hire 3 engineers.\n"
        )
        result = detect_ai_content(f)
        assert result.likely_ai is False
        assert result.score < 0.3

    def test_code_file(self, tmp_path):
        f = tmp_path / "script.py"
        f.write_text(
            "# Import necessary libraries\n"
            "import os\n\n"
            '# Define the main function\n'
            'def main():\n'
            '    """Main entry point for the application."""\n'
            '    # Initialize configuration\n'
            '    config = load_config()\n\n'
            'def load_config():\n'
            '    """Load the configuration from disk."""\n'
            '    return {}\n\n'
            'def process_data():\n'
            '    """Process the input data."""\n'
            '    pass\n\n'
            'if __name__ == "__main__":\n'
            '    main()\n'
        )
        result = detect_ai_content(f)
        assert len(result.signals) >= 2

    def test_binary_file_skipped(self, tmp_path):
        f = tmp_path / "image.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        result = detect_ai_content(f)
        assert result.score == 0.0

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("")
        result = detect_ai_content(f)
        assert result.likely_ai is False

    def test_nonexistent_file(self, tmp_path):
        f = tmp_path / "missing.txt"
        result = detect_ai_content(f)
        assert result.likely_ai is False

    @pytest.mark.skipif(
        __import__("platform").system() != "Darwin",
        reason="xattr-based creator detection requires macOS",
    )
    def test_creator_app_sets_high_score(self, tmp_path):
        f = tmp_path / "output.txt"
        f.write_text("Some plain text")

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '"ChatGPT"'

        with patch("akf.ai_detect.platform") as mock_platform, \
             patch("akf.ai_detect.subprocess.run", return_value=mock_result):
            mock_platform.system.return_value = "Darwin"
            result = detect_ai_content(f)

        assert result.likely_ai is True
        assert result.creator_app is not None
