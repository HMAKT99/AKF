"""Tests for AKF smart context detection."""

from __future__ import annotations

import json
import os
import subprocess
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from akf.context import (
    FileContext,
    KNOWN_DOMAINS,
    _compute_confidence,
    _detect_ai_generated,
    _detect_download_source,
    _detect_git_author,
    _download_source_cache,
    _git_repo_cache,
    _is_in_git_repo,
    _is_known_domain,
    _match_rules,
    _rules_cache,
    infer_context,
    load_project_rules,
)


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear all detection caches between tests."""
    _git_repo_cache.clear()
    _rules_cache.clear()
    _download_source_cache.clear()
    yield
    _git_repo_cache.clear()
    _rules_cache.clear()
    _download_source_cache.clear()


# ---------------------------------------------------------------------------
# Feature 1: Git Author Detection
# ---------------------------------------------------------------------------

class TestGitAuthorDetection:
    def test_detects_author_in_git_repo(self, tmp_path):
        """Real git init + commit → detects author."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=tmp_path, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test Author"],
            cwd=tmp_path, capture_output=True,
        )
        f = tmp_path / "file.txt"
        f.write_text("content")
        subprocess.run(["git", "add", "file.txt"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=tmp_path, capture_output=True,
        )

        author = _detect_git_author(f)
        assert author == "Test Author <test@example.com>"

    def test_untracked_file_returns_none(self, tmp_path):
        """File in git repo but not committed → None."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        f = tmp_path / "untracked.txt"
        f.write_text("data")

        author = _detect_git_author(f)
        assert author is None

    def test_non_git_dir_returns_none(self, tmp_path):
        """File outside git repo → None."""
        f = tmp_path / "file.txt"
        f.write_text("data")
        author = _detect_git_author(f)
        assert author is None

    def test_git_repo_check_cached(self, tmp_path):
        """Repeated calls use cache instead of running subprocess."""
        f = tmp_path / "file.txt"
        f.write_text("data")

        # First call populates cache
        _is_in_git_repo(f)
        assert str(f.parent) in _git_repo_cache

        # Modify cache to return True — should use cached value
        _git_repo_cache[str(f.parent)] = (True, time.monotonic())
        assert _is_in_git_repo(f) is True


# ---------------------------------------------------------------------------
# Feature 2: Download Source Detection
# ---------------------------------------------------------------------------

class TestDownloadSourceDetection:
    def test_non_darwin_returns_none(self, tmp_path):
        """Non-macOS platform → None."""
        f = tmp_path / "file.pdf"
        f.write_text("data")
        with patch("akf.context.platform") as mock_platform:
            mock_platform.system.return_value = "Linux"
            result = _detect_download_source(f)
        assert result is None

    @pytest.mark.skipif(
        __import__("platform").system() != "Darwin",
        reason="xattr-based download source detection requires macOS",
    )
    def test_darwin_with_xattr(self, tmp_path):
        """macOS with download xattr → returns URL."""
        import plistlib
        f = tmp_path / "file.pdf"
        f.write_text("data")

        urls = ["https://example.com/file.pdf", "https://example.com/"]
        plist_bytes = plistlib.dumps(urls)
        hex_output = plist_bytes.hex()
        # Format as xattr -px output (space-separated pairs)
        spaced_hex = " ".join(
            hex_output[i:i+2] for i in range(0, len(hex_output), 2)
        )

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = spaced_hex

        with patch("akf.context.platform") as mock_platform, \
             patch("akf.context.subprocess.run", return_value=mock_result):
            mock_platform.system.return_value = "Darwin"
            result = _detect_download_source(f)

        assert result == "https://example.com/file.pdf"

    def test_darwin_no_xattr(self, tmp_path):
        """macOS file without download xattr → None."""
        f = tmp_path / "file.txt"
        f.write_text("data")

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("akf.context.platform") as mock_platform, \
             patch("akf.context.subprocess.run", return_value=mock_result):
            mock_platform.system.return_value = "Darwin"
            result = _detect_download_source(f)

        assert result is None

    def test_subprocess_failure(self, tmp_path):
        """xattr subprocess failure → None (no crash)."""
        f = tmp_path / "file.txt"
        f.write_text("data")

        with patch("akf.context.platform") as mock_platform, \
             patch("akf.context.subprocess.run", side_effect=FileNotFoundError):
            mock_platform.system.return_value = "Darwin"
            result = _detect_download_source(f)

        assert result is None


# ---------------------------------------------------------------------------
# Feature 3: Project Rules
# ---------------------------------------------------------------------------

class TestProjectRules:
    def test_loads_rules_from_project_config(self, tmp_path):
        """Finds .akf/config.json walking up from file."""
        akf_dir = tmp_path / ".akf"
        akf_dir.mkdir()
        config = {
            "rules": [
                {"pattern": "*/finance/*", "classification": "confidential", "tier": 2}
            ]
        }
        (akf_dir / "config.json").write_text(json.dumps(config))

        sub = tmp_path / "finance"
        sub.mkdir()
        f = sub / "report.xlsx"
        f.write_text("data")

        rules = load_project_rules(f)
        assert len(rules) >= 1
        assert rules[0]["classification"] == "confidential"

    def test_match_rules_first_wins(self, tmp_path):
        """First matching rule wins."""
        rules = [
            {"pattern": "*/secret/*", "classification": "top-secret", "tier": 1},
            {"pattern": "*", "classification": "public", "tier": 3},
        ]
        f = tmp_path / "secret" / "doc.md"
        f.parent.mkdir(parents=True)
        f.write_text("data")

        cls, tier = _match_rules(f, rules)
        assert cls == "top-secret"
        assert tier == 1

    def test_no_match_returns_none(self, tmp_path):
        """No matching rule → (None, None)."""
        rules = [
            {"pattern": "*/finance/*", "classification": "confidential", "tier": 2},
        ]
        f = tmp_path / "public" / "readme.md"
        f.parent.mkdir(parents=True)
        f.write_text("data")

        cls, tier = _match_rules(f, rules)
        assert cls is None
        assert tier is None

    def test_empty_rules(self, tmp_path):
        """Empty rules list → (None, None)."""
        f = tmp_path / "file.txt"
        f.write_text("data")
        cls, tier = _match_rules(f, [])
        assert cls is None
        assert tier is None

    def test_global_rules_fallback(self, tmp_path, monkeypatch):
        """Rules from ~/.akf/watch.json are loaded as fallback."""
        # Create a fake home with watch.json
        fake_home = tmp_path / "fakehome"
        fake_home.mkdir()
        akf_dir = fake_home / ".akf"
        akf_dir.mkdir()
        (akf_dir / "watch.json").write_text(json.dumps({
            "rules": [
                {"pattern": "*/docs/*", "classification": "public", "tier": 3}
            ]
        }))
        monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

        f = tmp_path / "project" / "docs" / "readme.md"
        f.parent.mkdir(parents=True)
        f.write_text("data")

        rules = load_project_rules(f)
        assert any(r.get("classification") == "public" for r in rules)


# ---------------------------------------------------------------------------
# Feature 4: AI-Generated Content Detection
# ---------------------------------------------------------------------------

class TestAIGenDetection:
    def test_within_window(self, tmp_path):
        """File mtime within 60s of tracking timestamp → ai_generated=True."""
        f = tmp_path / "output.md"
        f.write_text("AI output")

        now = datetime.now(timezone.utc)
        tracking = {
            "model": "gpt-4o",
            "timestamp": now.isoformat(),
        }
        # Touch file to current time
        os.utime(f, (now.timestamp(), now.timestamp()))

        ai_gen, model = _detect_ai_generated(f, tracking)
        assert ai_gen is True
        assert model == "gpt-4o"

    def test_outside_window(self, tmp_path):
        """File mtime >60s from tracking timestamp → None."""
        f = tmp_path / "old.md"
        f.write_text("old content")

        old_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        tracking = {
            "model": "gpt-4o",
            "timestamp": old_time.isoformat(),
        }

        ai_gen, model = _detect_ai_generated(f, tracking)
        assert ai_gen is None

    def test_no_tracking(self, tmp_path):
        """No tracking context → (None, None)."""
        f = tmp_path / "file.txt"
        f.write_text("data")

        ai_gen, model = _detect_ai_generated(f, None)
        assert ai_gen is None
        assert model is None


# ---------------------------------------------------------------------------
# Feature 5: Smart Confidence Scoring
# ---------------------------------------------------------------------------

class TestSmartConfidence:
    def test_base_only(self):
        assert _compute_confidence(0.7) == 0.7

    def test_source_boost(self):
        assert _compute_confidence(0.7, has_source=True) == 0.8

    def test_git_boost(self):
        assert _compute_confidence(0.7, in_git_with_commits=True) == 0.75

    def test_verified_download_boost(self):
        assert _compute_confidence(0.7, is_verified_download=True) == 0.8

    def test_ai_no_source_penalty(self):
        assert _compute_confidence(0.7, ai_generated_no_source=True) == 0.6

    def test_evidence_boost_capped(self):
        # 5 evidence signals × 0.05 = 0.25, but capped at 0.15
        assert _compute_confidence(0.7, evidence_count=5) == 0.85

    def test_clamp_to_range(self):
        # Very low base with penalty → clamped to 0.1
        assert _compute_confidence(0.1, ai_generated_no_source=True) == 0.1
        # Very high base with all boosts → clamped to 1.0
        result = _compute_confidence(
            0.9,
            has_source=True,
            in_git_with_commits=True,
            is_verified_download=True,
            evidence_count=5,
        )
        assert result == 1.0

    @pytest.mark.parametrize("base,kwargs,expected", [
        (0.7, {"has_source": True, "in_git_with_commits": True}, 0.85),
        (0.7, {"has_source": True, "ai_generated_no_source": True}, 0.7),
        (0.5, {"evidence_count": 2}, 0.6),
    ])
    def test_combinations(self, base, kwargs, expected):
        assert _compute_confidence(base, **kwargs) == expected


# ---------------------------------------------------------------------------
# Known Domains
# ---------------------------------------------------------------------------

class TestKnownDomains:
    @pytest.mark.parametrize("url", [
        "https://github.com/user/repo",
        "https://arxiv.org/abs/2301.00001",
        "https://drive.google.com/file/d/abc",
        "https://www.dropbox.com/s/file",
        "https://huggingface.co/model",
        "https://pypi.org/project/akf/",
    ])
    def test_known(self, url):
        assert _is_known_domain(url) is True

    @pytest.mark.parametrize("url", [
        "https://example.com/file.pdf",
        "https://random-site.org/doc",
        "https://evil.com/phishing",
        "ftp://files.example.net/data",
    ])
    def test_unknown(self, url):
        assert _is_known_domain(url) is False


# ---------------------------------------------------------------------------
# Integration: infer_context
# ---------------------------------------------------------------------------

class TestInferContext:
    def test_defaults_without_signals(self, tmp_path):
        """No git, no xattr, no rules → uses base values."""
        f = tmp_path / "plain.txt"
        f.write_text("content")

        ctx = infer_context(f)
        assert isinstance(ctx, FileContext)
        assert ctx.classification == "internal"
        assert ctx.source is None
        assert ctx.author is None

    def test_git_author_included(self, tmp_path):
        """File in git repo with commit → author populated."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "dev@corp.com"],
            cwd=tmp_path, capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Dev User"],
            cwd=tmp_path, capture_output=True,
        )
        f = tmp_path / "code.py"
        f.write_text("print('hello')")
        subprocess.run(["git", "add", "code.py"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "add code"],
            cwd=tmp_path, capture_output=True,
        )

        ctx = infer_context(f)
        assert ctx.author == "Dev User <dev@corp.com>"
        # Git author should boost confidence above base
        assert ctx.confidence > 0.7

    def test_project_rules_override_classification(self, tmp_path):
        """Project rules override base classification."""
        akf_dir = tmp_path / ".akf"
        akf_dir.mkdir()
        (akf_dir / "config.json").write_text(json.dumps({
            "rules": [
                {"pattern": "*/secret/*", "classification": "top-secret", "tier": 1}
            ]
        }))

        secret_dir = tmp_path / "secret"
        secret_dir.mkdir()
        f = secret_dir / "plans.md"
        f.write_text("classified info")

        ctx = infer_context(f)
        assert ctx.classification == "top-secret"
        assert ctx.authority_tier == 1

    def test_ai_generated_with_tracking(self, tmp_path):
        """Recent tracking timestamp → ai_generated=True + model set."""
        f = tmp_path / "response.md"
        f.write_text("AI response content")

        now = datetime.now(timezone.utc)
        os.utime(f, (now.timestamp(), now.timestamp()))

        tracking = {
            "model": "claude-sonnet-4-20250514",
            "provider": "anthropic",
            "timestamp": now.isoformat(),
        }

        ctx = infer_context(f, tracking_last=tracking)
        assert ctx.ai_generated is True
        assert ctx.model == "claude-sonnet-4-20250514"
        # AI without source → penalty
        assert ctx.confidence < 0.7
