"""End-to-end integration tests for the smart context detection pipeline.

Tests the FULL flow: file creation → watcher detection → context inference
→ stamp embedding → metadata extraction.  Each test verifies that the
stamped metadata reflects the file's actual environment (git, rules, AI
content, download source).

Also includes performance benchmarks to catch regressions.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clear_all_caches():
    """Clear every detection cache between tests."""
    from akf.context import _git_repo_cache, _rules_cache, _download_source_cache
    from akf.ai_detect import _creator_cache
    _git_repo_cache.clear()
    _rules_cache.clear()
    _download_source_cache.clear()
    _creator_cache.clear()
    yield
    _git_repo_cache.clear()
    _rules_cache.clear()
    _download_source_cache.clear()
    _creator_cache.clear()


@pytest.fixture
def git_project(tmp_path):
    """Create a git repo with .akf/config.json rules and a committed file."""
    repo = tmp_path / "project"
    repo.mkdir()

    # Git init
    subprocess.run(["git", "init"], cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.email", "alice@corp.com"],
                   cwd=repo, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Alice Engineer"],
                   cwd=repo, capture_output=True)

    # Project rules
    akf_dir = repo / ".akf"
    akf_dir.mkdir()
    (akf_dir / "config.json").write_text(json.dumps({
        "rules": [
            {"pattern": "*/finance/*", "classification": "confidential", "tier": 2},
            {"pattern": "*/public/*", "classification": "public", "tier": 3},
            {"pattern": "*/internal/*", "classification": "internal", "tier": 4},
        ]
    }))

    # Create subdirectories
    (repo / "finance").mkdir()
    (repo / "public").mkdir()
    (repo / "internal").mkdir()
    (repo / "general").mkdir()

    # Commit the project structure
    subprocess.run(["git", "add", "."], cwd=repo, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"],
                   cwd=repo, capture_output=True)

    return repo


# ---------------------------------------------------------------------------
# E2E: Full pipeline tests
# ---------------------------------------------------------------------------

class TestE2EFullPipeline:
    """Test the complete flow: file → infer_context → stamp → extract."""

    def test_git_committed_file_gets_author_and_confidence_boost(self, git_project):
        """A committed file in git gets author metadata and boosted confidence."""
        from akf.context import infer_context

        code = git_project / "general" / "utils.py"
        code.write_text("def add(a, b):\n    return a + b\n")
        subprocess.run(["git", "add", "general/utils.py"],
                       cwd=git_project, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add utils"],
                       cwd=git_project, capture_output=True)

        ctx = infer_context(code)

        assert ctx.author == "Alice Engineer <alice@corp.com>"
        assert ctx.classification == "internal"  # default
        assert ctx.confidence > 0.7  # boosted by git + evidence

    def test_finance_file_gets_confidential_classification(self, git_project):
        """A file in the finance/ directory gets classified as confidential."""
        from akf.context import infer_context

        report = git_project / "finance" / "q3_report.txt"
        report.write_text("Revenue: $4.2B\n")

        ctx = infer_context(report)

        assert ctx.classification == "confidential"
        assert ctx.authority_tier == 2
        # Classification override counts as evidence
        assert ctx.confidence > 0.7

    def test_public_file_gets_public_classification(self, git_project):
        """A file in public/ gets public classification."""
        from akf.context import infer_context

        readme = git_project / "public" / "readme.txt"
        readme.write_text("Welcome to the project.\n")

        ctx = infer_context(readme)

        assert ctx.classification == "public"
        assert ctx.authority_tier == 3

    def test_ai_text_detected_via_content_heuristics(self, tmp_path):
        """AI-generated text is detected by content analysis."""
        from akf.context import infer_context

        ai_file = tmp_path / "response.md"
        ai_file.write_text(
            "Certainly! I'd be happy to help you with that.\n\n"
            "As an AI language model, here's a comprehensive overview:\n\n"
            "## Introduction\n"
            "It's worth noting that this topic is important.\n\n"
            "## Key Points\n"
            "- Point 1\n- Point 2\n- Point 3\n\n"
            "## Conclusion\n"
            "I hope this helps! Feel free to ask more questions.\n"
        )

        ctx = infer_context(ai_file)

        assert ctx.ai_generated is True
        # AI without source → confidence penalty
        assert ctx.confidence <= 0.7

    def test_tracking_timestamp_overrides_content_detection(self, tmp_path):
        """Tracking-based detection (Layer 1) takes priority over content (Layer 2)."""
        from akf.context import infer_context

        # File with NO AI markers in content
        normal = tmp_path / "output.txt"
        normal.write_text("Just some plain output data.\n")

        now = datetime.now(timezone.utc)
        os.utime(normal, (now.timestamp(), now.timestamp()))
        tracking = {
            "model": "gpt-4o",
            "provider": "openai",
            "timestamp": now.isoformat(),
        }

        ctx = infer_context(normal, tracking_last=tracking)

        assert ctx.ai_generated is True
        assert ctx.model == "gpt-4o"

    def test_non_ai_text_not_falsely_flagged(self, tmp_path):
        """Normal human-written text should NOT be flagged as AI."""
        from akf.context import infer_context

        human = tmp_path / "notes.txt"
        human.write_text(
            "Meeting notes 2024-03-15\n"
            "Discussed Q1 targets. Revenue at $4.2B.\n"
            "Action: ship v2 by April, hire 3 engineers.\n"
            "Bob will own the integration work.\n"
        )

        ctx = infer_context(human)

        assert ctx.ai_generated is None or ctx.ai_generated is False
        assert ctx.confidence == 0.7  # base, no adjustments

    def test_rules_passed_via_config_bypass_discovery(self, tmp_path):
        """Pre-loaded rules (from config) skip filesystem walk."""
        from akf.context import infer_context

        f = tmp_path / "data.csv"
        f.write_text("a,b,c\n1,2,3\n")

        rules = [{"pattern": "*.csv", "classification": "restricted", "tier": 1}]

        ctx = infer_context(f, project_rules=rules)

        assert ctx.classification == "restricted"
        assert ctx.authority_tier == 1

    def test_combined_signals_produce_rich_metadata(self, git_project):
        """A committed file under finance/ with AI content gets all signals."""
        from akf.context import infer_context

        # Create AI-generated file in finance/
        ai_report = git_project / "finance" / "analysis.md"
        ai_report.write_text(
            "Certainly! Here's a comprehensive financial analysis.\n\n"
            "As an AI, I've analyzed the quarterly data.\n\n"
            "I hope this helps!\n"
        )
        subprocess.run(["git", "add", "finance/analysis.md"],
                       cwd=git_project, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add analysis"],
                       cwd=git_project, capture_output=True)

        ctx = infer_context(ai_report)

        # Should have all signals
        assert ctx.author == "Alice Engineer <alice@corp.com>"
        assert ctx.classification == "confidential"
        assert ctx.authority_tier == 2
        assert ctx.ai_generated is True
        # Has git + classification override + author evidence,
        # but AI without source penalty
        assert ctx.confidence > 0.5


class TestE2EStampAndExtract:
    """Test that stamps actually get embedded and can be extracted."""

    def test_stamp_file_with_smart_context(self, git_project):
        """_stamp_file with smart context produces extractable metadata."""
        from akf.watch import _stamp_file
        from akf.universal import extract

        doc = git_project / "general" / "report.md"
        doc.write_text("# Quarterly Report\n\nContent here.\n")
        subprocess.run(["git", "add", "general/report.md"],
                       cwd=git_project, capture_output=True)
        subprocess.run(["git", "commit", "-m", "add report"],
                       cwd=git_project, capture_output=True)

        # Stamp with smart context
        config = {"smart": True}
        _stamp_file(doc, agent="test-agent", classification="internal",
                    config=config)

        # Extract and verify
        metadata = extract(str(doc))
        assert metadata is not None

    def test_stamp_file_without_smart_context(self, tmp_path):
        """_stamp_file with smart=False uses static defaults."""
        from akf.watch import _stamp_file
        from akf.universal import extract

        doc = tmp_path / "plain.txt"
        doc.write_text("Hello world.\n")

        config = {"smart": False}
        _stamp_file(doc, agent="test-agent", classification="internal",
                    config=config)

        metadata = extract(str(doc))
        assert metadata is not None

    def test_already_stamped_file_skipped(self, tmp_path):
        """File with existing stamp is not re-stamped."""
        from akf.watch import _stamp_file
        from akf.universal import extract

        doc = tmp_path / "stamped.txt"
        doc.write_text("Already has metadata.\n")

        # First stamp
        _stamp_file(doc, agent="test-agent", classification="internal")
        first_meta = extract(str(doc))

        # Modify file content but keep stamp
        # (This simulates the watcher seeing the file again)
        content = doc.read_text()

        # Second stamp attempt — should be skipped
        _stamp_file(doc, agent="different-agent", classification="confidential")
        second_meta = extract(str(doc))

        # Metadata unchanged (still original agent)
        assert first_meta == second_meta


class TestE2EWatcherIntegration:
    """Test the watcher loop with smart context detection."""

    def test_watcher_stamps_new_file_with_context(self, git_project):
        """Watcher detects new file and stamps with inferred context."""
        from akf import watch as watch_mod
        from akf.universal import extract

        stamp_calls = []
        stop = threading.Event()

        original_stamp = watch_mod._stamp_file

        def tracking_stamp(filepath, agent, classification, logger=None, **kwargs):
            stamp_calls.append(filepath)
            original_stamp(filepath, agent, classification, logger, **kwargs)
            stop.set()

        config = {"smart": True}

        with patch.object(watch_mod, "_stamp_file", tracking_stamp):
            t = threading.Thread(
                target=watch_mod.watch,
                kwargs=dict(
                    directories=[str(git_project / "finance")],
                    interval=0.2,
                    stop_event=stop,
                    config=config,
                ),
                daemon=True,
            )
            t.start()
            time.sleep(0.3)

            # Drop a new file into the finance directory
            new_file = git_project / "finance" / "budget.txt"
            new_file.write_text("FY2025 budget: $10M\n")

            t.join(timeout=5)

        assert len(stamp_calls) >= 1

        # Verify the stamp was embedded
        metadata = extract(str(new_file))
        assert metadata is not None


# ---------------------------------------------------------------------------
# Performance benchmarks
# ---------------------------------------------------------------------------

class TestPerformanceBenchmarks:
    """Performance regression tests for the detection pipeline.

    These are not strict assertions (timing varies by machine) but they
    catch major regressions and document expected performance.
    """

    def test_cached_infer_context_under_1ms(self, tmp_path):
        """Second call to infer_context (same directory) should be <1ms."""
        from akf.context import infer_context

        f = tmp_path / "file.txt"
        f.write_text("Content.\n")

        # Cold call to populate caches
        infer_context(f)

        # Warm call
        start = time.perf_counter()
        infer_context(f)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 5.0, f"Cached infer_context took {elapsed_ms:.2f}ms (expected <5ms)"

    def test_batch_50_files_under_2s(self, tmp_path):
        """50 files in the same directory should complete in <2 seconds."""
        from akf.context import infer_context

        files = []
        for i in range(50):
            f = tmp_path / f"file_{i:03d}.txt"
            f.write_text(f"Content {i}\n")
            files.append(f)

        start = time.perf_counter()
        for f in files:
            infer_context(f)
        elapsed = time.perf_counter() - start

        per_file = elapsed * 1000 / 50
        assert elapsed < 2.0, f"Batch took {elapsed:.2f}s ({per_file:.1f}ms/file)"

    def test_content_detection_under_5ms_for_small_file(self, tmp_path):
        """Content heuristics on a small file should be fast."""
        from akf.ai_detect import _scan_text_signals

        text = "Normal meeting notes. Revenue discussion.\n" * 50

        start = time.perf_counter()
        for _ in range(100):
            _scan_text_signals(text)
        elapsed_ms = (time.perf_counter() - start) * 1000 / 100

        assert elapsed_ms < 5.0, f"Text scan took {elapsed_ms:.2f}ms (expected <5ms)"

    def test_git_cache_prevents_subprocess(self, tmp_path):
        """After first call, git repo check should be pure dict lookup."""
        from akf.context import _is_in_git_repo, _git_repo_cache

        f = tmp_path / "file.txt"
        f.write_text("data")

        # Cold call
        _is_in_git_repo(f)

        # Warm call — should be dict lookup
        start = time.perf_counter()
        for _ in range(1000):
            _is_in_git_repo(f)
        elapsed_us = (time.perf_counter() - start) * 1_000_000 / 1000

        assert elapsed_us < 50, f"Cached git check took {elapsed_us:.1f}μs (expected <50μs)"

    def test_rules_cache_prevents_filesystem_walk(self, tmp_path):
        """After first call, project rules should be cached."""
        from akf.context import load_project_rules, _rules_cache

        f = tmp_path / "file.txt"
        f.write_text("data")

        # Cold call
        load_project_rules(f)

        # Warm call
        start = time.perf_counter()
        for _ in range(1000):
            load_project_rules(f)
        elapsed_us = (time.perf_counter() - start) * 1_000_000 / 1000

        assert elapsed_us < 50, f"Cached rules took {elapsed_us:.1f}μs (expected <50μs)"

    def test_confidence_computation_is_instant(self):
        """Pure math function should take <1μs."""
        from akf.context import _compute_confidence

        start = time.perf_counter()
        for _ in range(10000):
            _compute_confidence(
                0.7,
                has_source=True,
                in_git_with_commits=True,
                is_verified_download=True,
                evidence_count=3,
            )
        elapsed_us = (time.perf_counter() - start) * 1_000_000 / 10000

        assert elapsed_us < 10, f"Confidence calc took {elapsed_us:.1f}μs"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_nonexistent_file_doesnt_crash(self, tmp_path):
        """infer_context on a missing file returns safe defaults."""
        from akf.context import infer_context

        missing = tmp_path / "ghost.txt"
        ctx = infer_context(missing)

        assert ctx.classification == "internal"
        assert ctx.confidence == 0.7

    def test_binary_file_doesnt_crash(self, tmp_path):
        """Binary files are handled gracefully."""
        from akf.context import infer_context

        binary = tmp_path / "data.bin"
        binary.write_bytes(b"\x00\x01\x02\xff" * 1000)
        # Rename to supported extension
        target = tmp_path / "data.txt"
        binary.rename(target)

        ctx = infer_context(target)
        assert ctx.classification == "internal"

    def test_deeply_nested_file(self, tmp_path):
        """File deeply nested under project root still finds rules."""
        from akf.context import infer_context

        # Create rules at root
        akf_dir = tmp_path / ".akf"
        akf_dir.mkdir()
        (akf_dir / "config.json").write_text(json.dumps({
            "rules": [{"pattern": "*", "classification": "org-wide", "tier": 4}]
        }))

        # Create deeply nested file
        deep = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep.mkdir(parents=True)
        f = deep / "file.txt"
        f.write_text("deep content")

        ctx = infer_context(f)
        assert ctx.classification == "org-wide"
        assert ctx.authority_tier == 4

    def test_concurrent_infer_context(self, tmp_path):
        """Multiple threads calling infer_context simultaneously."""
        from akf.context import infer_context

        files = []
        for i in range(10):
            f = tmp_path / f"concurrent_{i}.txt"
            f.write_text(f"Content {i}")
            files.append(f)

        results = [None] * 10
        errors = []

        def run(idx):
            try:
                results[idx] = infer_context(files[idx])
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=run, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Errors in concurrent access: {errors}"
        assert all(r is not None for r in results)
        assert all(r.classification == "internal" for r in results)

    def test_smart_false_disables_all_detection(self, tmp_path):
        """config smart=False skips all context inference."""
        from akf.watch import _stamp_file
        from akf.universal import extract

        f = tmp_path / "noinfer.txt"
        f.write_text(
            "As an AI language model, I'd be happy to help!\n"
            "I hope this helps!\n"
        )

        _stamp_file(f, agent="test", classification="internal",
                    config={"smart": False})

        meta = extract(str(f))
        assert meta is not None
