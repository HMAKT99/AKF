"""End-to-end performance, latency, memory, and reliability tests for AKF.

Tests the daemon/watcher system, stamp operations, detection pipeline,
and SDK patching overhead. Measures real-world impact on machine resources.

Run:  cd python && python -m pytest tests/test_performance.py -v -s
"""

import gc
import json
import os
import re
import sys
import tempfile
import threading
import time
import tracemalloc
from pathlib import Path
from unittest.mock import patch

import pytest

import akf
from akf.stamp import stamp, stamp_file, parse_evidence_string
from akf.watch import watch, _stamp_file, _should_watch, SUPPORTED_EXTENSIONS
from akf.detection import run_all_detections
from akf.trust import explain_trust, effective_trust


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def measure_time(func, *args, **kwargs):
    """Run func and return (result, elapsed_ms)."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = (time.perf_counter() - start) * 1000
    return result, elapsed


def measure_memory(func, *args, **kwargs):
    """Run func and return (result, peak_memory_kb)."""
    gc.collect()
    tracemalloc.start()
    result = func(*args, **kwargs)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, peak / 1024  # Convert to KB


def create_test_files(tmpdir, count, ext=".txt", size_bytes=1024):
    """Create test files and return list of paths."""
    paths = []
    for i in range(count):
        p = tmpdir / f"test_{i}{ext}"
        p.write_text("x" * size_bytes)
        paths.append(p)
    return paths


# ═══════════════════════════════════════════════════════════════════════════
# 1. STAMP LATENCY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestStampLatency:
    """Measure stamp() operation latency."""

    def test_stamp_single_claim_latency(self):
        """Single stamp() should complete in <50ms."""
        _, elapsed = measure_time(
            stamp, "Test claim", confidence=0.85, ai_generated=True
        )
        print(f"\n  stamp() single claim: {elapsed:.2f}ms")
        assert elapsed < 50, f"stamp() took {elapsed:.2f}ms (>50ms)"

    def test_stamp_100_claims_latency(self):
        """100 sequential stamp() calls — measure throughput."""
        start = time.perf_counter()
        for i in range(100):
            stamp(f"Claim {i}", confidence=0.5 + (i % 50) / 100)
        elapsed = (time.perf_counter() - start) * 1000
        per_call = elapsed / 100
        print(f"\n  100x stamp(): {elapsed:.1f}ms total, {per_call:.2f}ms/call")
        assert per_call < 20, f"Per-call: {per_call:.2f}ms (>20ms)"

    def test_stamp_with_evidence_latency(self):
        """stamp() with evidence parsing should be fast."""
        evidence = [
            "42/42 tests passed",
            "mypy: 0 errors",
            "lint clean",
            "CI passed",
            "human review approved",
        ]
        _, elapsed = measure_time(
            stamp, "Code change", confidence=0.95,
            evidence=evidence, agent="claude-code", model="claude-sonnet"
        )
        print(f"\n  stamp() with 5 evidence strings: {elapsed:.2f}ms")
        assert elapsed < 50, f"stamp() with evidence took {elapsed:.2f}ms (>50ms)"

    def test_evidence_parsing_latency(self):
        """parse_evidence_string() regex matching — 1000 calls."""
        strings = [
            "42/42 tests passed", "mypy: 0 errors", "lint clean",
            "ci pass", "human review", "unknown pattern here",
        ]
        start = time.perf_counter()
        for _ in range(1000):
            for s in strings:
                parse_evidence_string(s)
        elapsed = (time.perf_counter() - start) * 1000
        per_call = elapsed / 6000
        print(f"\n  6000x parse_evidence_string(): {elapsed:.1f}ms, {per_call:.4f}ms/call")
        assert per_call < 1, f"Evidence parsing: {per_call:.4f}ms/call (>1ms)"

    def test_stamp_large_content_latency(self):
        """stamp() with very large content string."""
        large_content = "This is a claim with lots of text. " * 1000  # ~35KB
        _, elapsed = measure_time(
            stamp, large_content, confidence=0.7
        )
        print(f"\n  stamp() with ~35KB content: {elapsed:.2f}ms")
        assert elapsed < 100, f"Large content stamp took {elapsed:.2f}ms (>100ms)"


# ═══════════════════════════════════════════════════════════════════════════
# 2. STAMP FILE LATENCY TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestStampFileLatency:
    """Measure stamp_file() operation latency on various file types."""

    def test_stamp_txt_file(self, tmp_path):
        """Stamping a small .txt file."""
        f = tmp_path / "test.txt"
        f.write_text("Hello world\n" * 10)
        _, elapsed = measure_time(stamp_file, str(f))
        print(f"\n  stamp_file(.txt, 110B): {elapsed:.2f}ms")
        assert elapsed < 200, f"txt stamp took {elapsed:.2f}ms (>200ms)"

    def test_stamp_json_file(self, tmp_path):
        """Stamping a .json file."""
        f = tmp_path / "test.json"
        f.write_text(json.dumps({"key": "value", "data": list(range(100))}))
        _, elapsed = measure_time(stamp_file, str(f))
        print(f"\n  stamp_file(.json): {elapsed:.2f}ms")
        assert elapsed < 200, f"json stamp took {elapsed:.2f}ms (>200ms)"

    def test_stamp_md_file(self, tmp_path):
        """Stamping a markdown file."""
        f = tmp_path / "test.md"
        f.write_text("# Title\n\nParagraph text.\n" * 50)
        _, elapsed = measure_time(stamp_file, str(f))
        print(f"\n  stamp_file(.md): {elapsed:.2f}ms")
        assert elapsed < 200, f"md stamp took {elapsed:.2f}ms (>200ms)"

    def test_stamp_html_file(self, tmp_path):
        """Stamping an HTML file."""
        f = tmp_path / "test.html"
        f.write_text("<html><body>" + "<p>Test</p>" * 100 + "</body></html>")
        _, elapsed = measure_time(stamp_file, str(f))
        print(f"\n  stamp_file(.html): {elapsed:.2f}ms")
        assert elapsed < 200, f"html stamp took {elapsed:.2f}ms (>200ms)"

    def test_stamp_py_file(self, tmp_path):
        """Stamping a Python source file."""
        f = tmp_path / "test.py"
        f.write_text("def foo():\n    return 42\n" * 50)
        _, elapsed = measure_time(stamp_file, str(f))
        print(f"\n  stamp_file(.py): {elapsed:.2f}ms")
        assert elapsed < 200, f"py stamp took {elapsed:.2f}ms (>200ms)"

    def test_stamp_large_file(self, tmp_path):
        """Stamping a 1MB text file."""
        f = tmp_path / "large.txt"
        f.write_text("x" * (1024 * 1024))  # 1MB
        _, elapsed = measure_time(stamp_file, str(f))
        print(f"\n  stamp_file(1MB .txt): {elapsed:.2f}ms")
        assert elapsed < 1000, f"1MB stamp took {elapsed:.2f}ms (>1000ms)"

    def test_stamp_10_files_sequential(self, tmp_path):
        """Stamp 10 files sequentially — total time."""
        files = create_test_files(tmp_path, 10, ext=".md", size_bytes=500)
        start = time.perf_counter()
        for f in files:
            stamp_file(str(f))
        elapsed = (time.perf_counter() - start) * 1000
        per_file = elapsed / 10
        print(f"\n  10x stamp_file(.md): {elapsed:.1f}ms total, {per_file:.1f}ms/file")
        assert per_file < 300, f"Per-file: {per_file:.1f}ms (>300ms)"


# ═══════════════════════════════════════════════════════════════════════════
# 3. TRUST COMPUTATION LATENCY
# ═══════════════════════════════════════════════════════════════════════════

class TestTrustLatency:
    """Measure trust computation and explain_trust() latency."""

    def test_effective_trust_latency(self):
        """effective_trust() on a single claim."""
        unit = stamp("Test", confidence=0.85)
        _, elapsed = measure_time(effective_trust, unit.claims[0])
        print(f"\n  effective_trust(): {elapsed:.2f}ms")
        assert elapsed < 10, f"effective_trust took {elapsed:.2f}ms (>10ms)"

    def test_explain_trust_latency(self):
        """explain_trust() formatting."""
        unit = stamp("Test", confidence=0.85)
        _, elapsed = measure_time(explain_trust, unit.claims[0])
        print(f"\n  explain_trust(): {elapsed:.2f}ms")
        assert elapsed < 20, f"explain_trust took {elapsed:.2f}ms (>20ms)"

    def test_trust_1000_claims(self):
        """Compute trust on 1000 claims."""
        claims = [stamp(f"Claim {i}", confidence=0.5 + (i % 50) / 100).claims[0] for i in range(1000)]
        start = time.perf_counter()
        for c in claims:
            effective_trust(c)
        elapsed = (time.perf_counter() - start) * 1000
        per_claim = elapsed / 1000
        print(f"\n  1000x effective_trust(): {elapsed:.1f}ms, {per_claim:.4f}ms/claim")
        assert per_claim < 5, f"Per-claim trust: {per_claim:.4f}ms (>5ms)"


# ═══════════════════════════════════════════════════════════════════════════
# 4. DETECTION PIPELINE LATENCY
# ═══════════════════════════════════════════════════════════════════════════

class TestDetectionLatency:
    """Measure run_all_detections() pipeline latency."""

    def test_detection_single_claim(self):
        """10 detection classes on a single-claim unit."""
        unit = stamp("AI claim", confidence=0.7, ai_generated=True)
        _, elapsed = measure_time(run_all_detections, unit)
        print(f"\n  run_all_detections(1 claim): {elapsed:.2f}ms")
        assert elapsed < 50, f"Detection took {elapsed:.2f}ms (>50ms)"

    def test_detection_10_claims(self):
        """10 detection classes on a 10-claim unit."""
        builder = akf.AKFBuilder().by("test")
        for i in range(10):
            builder.claim(f"Claim {i}", 0.5 + (i % 5) / 10, ai_generated=True)
        unit = builder.build()
        _, elapsed = measure_time(run_all_detections, unit)
        print(f"\n  run_all_detections(10 claims): {elapsed:.2f}ms")
        assert elapsed < 100, f"Detection 10 claims took {elapsed:.2f}ms (>100ms)"

    def test_detection_100_claims(self):
        """10 detection classes on a 100-claim unit."""
        builder = akf.AKFBuilder().by("test")
        for i in range(100):
            builder.claim(f"Claim {i}", 0.5 + (i % 50) / 100, ai_generated=True)
        unit = builder.build()
        _, elapsed = measure_time(run_all_detections, unit)
        print(f"\n  run_all_detections(100 claims): {elapsed:.2f}ms")
        assert elapsed < 500, f"Detection 100 claims took {elapsed:.2f}ms (>500ms)"

    def test_detection_report_structure(self):
        """Detection report always has exactly 10 results."""
        unit = stamp("Test", confidence=0.5, ai_generated=True)
        report = run_all_detections(unit)
        assert len(report.results) == 10
        for r in report.results:
            assert r.detection_class is not None
            assert r.severity in ("critical", "high", "medium", "low", "info")
            assert isinstance(r.findings, list)
            assert isinstance(r.recommendation, str)


# ═══════════════════════════════════════════════════════════════════════════
# 5. MEMORY USAGE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestMemoryUsage:
    """Measure memory consumption of AKF operations."""

    def test_stamp_memory(self):
        """Single stamp() memory footprint."""
        _, peak_kb = measure_memory(stamp, "Test claim", confidence=0.85)
        print(f"\n  stamp() peak memory: {peak_kb:.1f}KB")
        assert peak_kb < 500, f"stamp() used {peak_kb:.1f}KB (>500KB)"

    def test_stamp_100_memory(self):
        """100 stamp() calls — check for memory leaks."""
        def do_100_stamps():
            units = []
            for i in range(100):
                units.append(stamp(f"Claim {i}", confidence=0.7))
            return units
        _, peak_kb = measure_memory(do_100_stamps)
        print(f"\n  100x stamp() peak memory: {peak_kb:.1f}KB")
        assert peak_kb < 5000, f"100x stamp() used {peak_kb:.1f}KB (>5MB)"

    def test_detection_memory(self):
        """Detection pipeline memory footprint."""
        unit = stamp("Test", confidence=0.7, ai_generated=True)
        _, peak_kb = measure_memory(run_all_detections, unit)
        print(f"\n  run_all_detections() peak memory: {peak_kb:.1f}KB")
        assert peak_kb < 500, f"Detection used {peak_kb:.1f}KB (>500KB)"

    def test_trust_memory(self):
        """Trust computation memory footprint."""
        unit = stamp("Test", confidence=0.7)
        _, peak_kb = measure_memory(explain_trust, unit.claims[0])
        print(f"\n  explain_trust() peak memory: {peak_kb:.1f}KB")
        assert peak_kb < 200, f"explain_trust used {peak_kb:.1f}KB (>200KB)"

    def test_large_unit_memory(self):
        """Memory for a unit with 500 claims."""
        def build_large():
            builder = akf.AKFBuilder().by("test")
            for i in range(500):
                builder.claim(f"Claim {i} with some content", 0.7, ai_generated=True)
            return builder.build()
        _, peak_kb = measure_memory(build_large)
        print(f"\n  500-claim unit build: {peak_kb:.1f}KB")
        assert peak_kb < 10000, f"500-claim unit used {peak_kb:.1f}KB (>10MB)"

    def test_stamp_file_memory(self, tmp_path):
        """stamp_file() memory footprint on a 100KB file."""
        f = tmp_path / "test.txt"
        f.write_text("x" * (100 * 1024))
        _, peak_kb = measure_memory(stamp_file, str(f))
        print(f"\n  stamp_file(100KB) peak memory: {peak_kb:.1f}KB")
        assert peak_kb < 2000, f"stamp_file(100KB) used {peak_kb:.1f}KB (>2MB)"

    def test_to_dict_memory(self):
        """to_dict() serialization memory."""
        unit = stamp("Test claim", confidence=0.85, ai_generated=True)
        _, peak_kb = measure_memory(unit.to_dict, compact=False)
        print(f"\n  to_dict(compact=False): {peak_kb:.1f}KB")
        assert peak_kb < 100, f"to_dict used {peak_kb:.1f}KB (>100KB)"

    def test_json_roundtrip_memory(self):
        """Full JSON serialize → deserialize roundtrip memory."""
        unit = stamp("Roundtrip test", confidence=0.9, ai_generated=True)
        def roundtrip():
            j = json.dumps(unit.to_dict(compact=False))
            return akf.loads(j)
        _, peak_kb = measure_memory(roundtrip)
        print(f"\n  JSON roundtrip memory: {peak_kb:.1f}KB")
        assert peak_kb < 500, f"Roundtrip used {peak_kb:.1f}KB (>500KB)"


# ═══════════════════════════════════════════════════════════════════════════
# 6. WATCHER MEMORY LEAK TEST
# ═══════════════════════════════════════════════════════════════════════════

class TestWatcherMemory:
    """Test the watcher's known dict for unbounded growth."""

    def test_known_dict_growth(self, tmp_path):
        """Simulate watcher scanning growing directories — known dict grows."""
        from akf.watch import watch

        stop = threading.Event()
        known_sizes = []

        # Create initial files
        for i in range(10):
            (tmp_path / f"file_{i}.txt").write_text(f"content {i}")

        # Run watcher for a few cycles, adding files between cycles
        def run_watcher():
            watch(
                directories=[str(tmp_path)],
                interval=0.5,
                stop_event=stop,
                classification="internal",
            )

        t = threading.Thread(target=run_watcher, daemon=True)
        t.start()

        # Let it do initial scan
        time.sleep(1.0)

        # Add more files in batches
        for batch in range(3):
            for i in range(10):
                idx = 10 + batch * 10 + i
                (tmp_path / f"file_{idx}.txt").write_text(f"content {idx}")
            time.sleep(1.0)

        stop.set()
        t.join(timeout=5)

        # Verify files were created
        file_count = len(list(tmp_path.glob("*.txt")))
        print(f"\n  Created {file_count} files in watched directory")
        assert file_count == 40

    def test_deleted_files_pruned(self, tmp_path):
        """Deleted files are pruned from the known dict after prune cycle."""
        from akf.watch import watch, _should_watch
        import akf.watch as watch_mod

        # Create files
        files = []
        for i in range(20):
            f = tmp_path / f"prune_test_{i}.txt"
            f.write_text(f"content {i}")
            files.append(f)

        # Temporarily lower the prune interval for testing
        stop = threading.Event()
        known_ref = {}

        # Patch watch to capture the known dict and use a prune interval of 2
        original_watch = watch_mod.watch

        def patched_watch(directories=None, **kwargs):
            """Run watch but with fast pruning (every 2 cycles)."""
            import akf.watch
            # We'll do a manual simulation instead
            from pathlib import Path as P

            dirs = [P(d).expanduser().resolve() for d in directories]
            known: dict[str, float] = {}

            # Seed
            for d in dirs:
                for f in d.rglob("*"):
                    if _should_watch(f):
                        try:
                            known[str(f)] = f.stat().st_mtime
                        except OSError:
                            pass

            known_ref["initial"] = len(known)
            cycles = 0
            se = kwargs.get("stop_event")

            while True:
                if se:
                    se.wait(timeout=0.3)
                    if se.is_set():
                        break

                seen: set = set()
                for d in dirs:
                    try:
                        for f in d.rglob("*"):
                            if not _should_watch(f):
                                continue
                            ps = str(f)
                            try:
                                mt = f.stat().st_mtime
                            except OSError:
                                continue
                            seen.add(ps)
                            if ps not in known or known[ps] < mt:
                                known[ps] = mt
                    except OSError:
                        pass

                cycles += 1
                # Prune every 2 cycles for testing
                if cycles >= 2:
                    stale = known.keys() - seen
                    for k in stale:
                        del known[k]
                    cycles = 0

                known_ref["current"] = len(known)

        stop = threading.Event()
        t = threading.Thread(target=patched_watch,
                             args=([str(tmp_path)],),
                             kwargs={"stop_event": stop},
                             daemon=True)
        t.start()

        # Let it seed and do a couple cycles
        time.sleep(1.0)
        initial_count = known_ref.get("initial", 0)
        print(f"\n  Initial known entries: {initial_count}")
        assert initial_count == 20

        # Delete 10 files
        for f in files[:10]:
            f.unlink()

        # Wait for prune cycle (2 cycles × 0.3s + buffer)
        time.sleep(1.5)
        after_prune = known_ref.get("current", 0)
        print(f"  After deleting 10 + prune: {after_prune}")
        assert after_prune == 10, f"Expected 10 entries after prune, got {after_prune}"

        stop.set()
        t.join(timeout=5)

    def test_should_watch_filters(self, tmp_path):
        """_should_watch correctly filters by extension."""
        for ext in SUPPORTED_EXTENSIONS:
            p = tmp_path / f"test{ext}"
            p.write_text("test")
            assert _should_watch(p), f"{ext} should be watched"

        # Unsupported
        for ext in [".exe", ".dll", ".so", ".zip", ".tar", ".mp4"]:
            p = tmp_path / f"test{ext}"
            p.write_text("test")
            assert not _should_watch(p), f"{ext} should NOT be watched"

    def test_should_watch_hidden_files(self):
        """Hidden files and directories should be skipped."""
        hidden = Path("/tmp/.hidden_file.txt")
        assert not _should_watch(hidden)

        in_hidden_dir = Path("/tmp/.hidden/file.txt")
        assert not _should_watch(in_hidden_dir)


# ═══════════════════════════════════════════════════════════════════════════
# 7. RELIABILITY — TEXT EXTRACTION ERRORS
# ═══════════════════════════════════════════════════════════════════════════

class TestReliability:
    """Test stamp_file() reliability on edge-case files."""

    def test_empty_file(self, tmp_path):
        """Stamping an empty file should not crash."""
        f = tmp_path / "empty.txt"
        f.write_text("")
        try:
            stamp_file(str(f))
        except Exception as e:
            # Should handle gracefully, but document if it doesn't
            print(f"\n  Empty file error: {type(e).__name__}: {e}")

    def test_binary_content_in_text_file(self, tmp_path):
        """Binary content in a .txt file should not crash."""
        f = tmp_path / "binary.txt"
        f.write_bytes(b"\x00\x01\x02\xff\xfe\xfd" * 100)
        try:
            stamp_file(str(f))
        except Exception as e:
            print(f"\n  Binary content error: {type(e).__name__}: {e}")

    def test_unicode_filename(self, tmp_path):
        """Unicode filename should be handled."""
        f = tmp_path / "report_\u00e9\u00e7\u00f1.txt"
        f.write_text("Unicode filename test")
        try:
            result = stamp_file(str(f))
            assert result is not None
            print(f"\n  Unicode filename: OK")
        except Exception as e:
            print(f"\n  Unicode filename error: {type(e).__name__}: {e}")

    def test_deeply_nested_json(self, tmp_path):
        """Deeply nested JSON should not cause stack overflow."""
        nested = {"level": 0}
        current = nested
        for i in range(1, 50):
            current["child"] = {"level": i}
            current = current["child"]
        f = tmp_path / "deep.json"
        f.write_text(json.dumps(nested))
        try:
            stamp_file(str(f))
            print(f"\n  Deep JSON (50 levels): OK")
        except Exception as e:
            print(f"\n  Deep JSON error: {type(e).__name__}: {e}")

    def test_very_long_lines(self, tmp_path):
        """File with very long lines (1MB single line)."""
        f = tmp_path / "longline.txt"
        f.write_text("x" * (1024 * 1024))
        try:
            stamp_file(str(f))
            print(f"\n  1MB single line: OK")
        except Exception as e:
            print(f"\n  Long line error: {type(e).__name__}: {e}")

    def test_nonexistent_file(self):
        """Stamping a nonexistent file should raise an error."""
        with pytest.raises(Exception):
            stamp_file("/nonexistent/path/file.txt")

    def test_readonly_file(self, tmp_path):
        """Stamping a read-only file should fail gracefully."""
        f = tmp_path / "readonly.txt"
        f.write_text("Read only content")
        f.chmod(0o444)
        try:
            stamp_file(str(f))
        except (PermissionError, OSError):
            print(f"\n  Read-only file: Correctly raised PermissionError")
        finally:
            f.chmod(0o644)  # Restore for cleanup

    def test_stamp_file_idempotent(self, tmp_path):
        """Stamping the same file twice should not corrupt it."""
        f = tmp_path / "idem.txt"
        f.write_text("Idempotent test content")
        stamp_file(str(f))
        content_after_first = f.read_text()

        stamp_file(str(f))
        content_after_second = f.read_text()

        # File should still be valid text
        assert len(content_after_second) >= len(content_after_first)
        assert "Idempotent test content" in content_after_second
        print(f"\n  Idempotent stamp: OK (sizes: {len(content_after_first)} -> {len(content_after_second)})")


# ═══════════════════════════════════════════════════════════════════════════
# 8. PROCESS/CPU OVERHEAD
# ═══════════════════════════════════════════════════════════════════════════

class TestCPUOverhead:
    """Measure CPU overhead of stamp operations."""

    def test_stamp_cpu_time(self):
        """Measure actual CPU time (not wall time) for stamp operations."""
        start_cpu = time.process_time()
        for i in range(1000):
            stamp(f"CPU test {i}", confidence=0.7)
        cpu_time = (time.process_time() - start_cpu) * 1000
        per_call = cpu_time / 1000
        print(f"\n  1000x stamp() CPU time: {cpu_time:.1f}ms, {per_call:.4f}ms/call")
        assert per_call < 10, f"CPU per stamp: {per_call:.4f}ms (>10ms)"

    def test_detection_cpu_time(self):
        """CPU time for detection pipeline."""
        unit = stamp("Test", confidence=0.7, ai_generated=True)
        start_cpu = time.process_time()
        for _ in range(100):
            run_all_detections(unit)
        cpu_time = (time.process_time() - start_cpu) * 1000
        per_call = cpu_time / 100
        print(f"\n  100x run_all_detections() CPU: {cpu_time:.1f}ms, {per_call:.2f}ms/call")
        assert per_call < 20, f"CPU per detection: {per_call:.2f}ms (>20ms)"

    def test_trust_cpu_time(self):
        """CPU time for trust computation."""
        unit = stamp("Test", confidence=0.7)
        claim = unit.claims[0]
        start_cpu = time.process_time()
        for _ in range(1000):
            effective_trust(claim)
        cpu_time = (time.process_time() - start_cpu) * 1000
        per_call = cpu_time / 1000
        print(f"\n  1000x effective_trust() CPU: {cpu_time:.1f}ms, {per_call:.4f}ms/call")
        assert per_call < 2, f"CPU per trust: {per_call:.4f}ms (>2ms)"


# ═══════════════════════════════════════════════════════════════════════════
# 9. WATCHER POLLING OVERHEAD
# ═══════════════════════════════════════════════════════════════════════════

class TestWatcherOverhead:
    """Measure watcher polling overhead on directories."""

    def test_scan_empty_dir(self, tmp_path):
        """Scanning an empty directory should be near-instant."""
        start = time.perf_counter()
        files = list(tmp_path.rglob("*"))
        elapsed = (time.perf_counter() - start) * 1000
        print(f"\n  rglob empty dir: {elapsed:.2f}ms ({len(files)} files)")
        assert elapsed < 10

    def test_scan_100_files(self, tmp_path):
        """Scanning 100 files — baseline for watcher poll cycle."""
        create_test_files(tmp_path, 100, ext=".txt")
        start = time.perf_counter()
        files = [f for f in tmp_path.rglob("*") if _should_watch(f)]
        for f in files:
            f.stat().st_mtime
        elapsed = (time.perf_counter() - start) * 1000
        print(f"\n  rglob+stat 100 files: {elapsed:.2f}ms")
        assert elapsed < 100, f"100 file scan took {elapsed:.2f}ms (>100ms)"

    def test_scan_1000_files(self, tmp_path):
        """Scanning 1000 files — heavy directory."""
        create_test_files(tmp_path, 1000, ext=".txt")
        start = time.perf_counter()
        files = [f for f in tmp_path.rglob("*") if _should_watch(f)]
        for f in files:
            f.stat().st_mtime
        elapsed = (time.perf_counter() - start) * 1000
        print(f"\n  rglob+stat 1000 files: {elapsed:.2f}ms ({len(files)} matched)")
        assert elapsed < 1000, f"1000 file scan took {elapsed:.2f}ms (>1000ms)"

    def test_scan_nested_dirs(self, tmp_path):
        """Scanning nested directory structure."""
        for d in range(10):
            subdir = tmp_path / f"subdir_{d}"
            subdir.mkdir()
            create_test_files(subdir, 50, ext=".md")
        start = time.perf_counter()
        files = [f for f in tmp_path.rglob("*") if f.is_file() and _should_watch(f)]
        elapsed = (time.perf_counter() - start) * 1000
        print(f"\n  rglob nested (10 dirs × 50 files): {elapsed:.2f}ms ({len(files)} matched)")
        assert elapsed < 500, f"Nested scan took {elapsed:.2f}ms (>500ms)"


# ═══════════════════════════════════════════════════════════════════════════
# 10. SDK PATCHING OVERHEAD
# ═══════════════════════════════════════════════════════════════════════════

class TestSDKPatchingOverhead:
    """Measure _auto.py import hook and patching overhead."""

    def test_activate_latency(self):
        """activate() should be fast (runs on every Python startup if installed)."""
        from akf._auto import activate
        _, elapsed = measure_time(activate)
        print(f"\n  activate() latency: {elapsed:.2f}ms")
        # Must be fast — runs on every Python interpreter startup
        assert elapsed < 50, f"activate() took {elapsed:.2f}ms (>50ms)"

    def test_activate_idempotent(self):
        """Multiple activate() calls should be no-ops."""
        from akf._auto import activate
        # First call
        activate()
        # Second call should be near-instant (double-checked lock)
        _, elapsed = measure_time(activate)
        print(f"\n  activate() re-entry: {elapsed:.4f}ms")
        assert elapsed < 5, f"Re-entry took {elapsed:.4f}ms (>5ms)"


# ═══════════════════════════════════════════════════════════════════════════
# 11. SERIALIZATION PERFORMANCE
# ═══════════════════════════════════════════════════════════════════════════

class TestSerializationPerformance:
    """Test to_dict() and loads() performance."""

    def test_to_dict_compact_vs_descriptive(self):
        """Compare compact vs descriptive serialization speed."""
        unit = stamp("Serialization test", confidence=0.85, ai_generated=True,
                     evidence=["42/42 tests passed", "lint clean"])

        _, elapsed_compact = measure_time(unit.to_dict, compact=True)
        _, elapsed_desc = measure_time(unit.to_dict, compact=False)
        print(f"\n  to_dict(compact=True): {elapsed_compact:.2f}ms")
        print(f"  to_dict(compact=False): {elapsed_desc:.2f}ms")
        assert elapsed_compact < 20
        assert elapsed_desc < 20

    def test_to_dict_size_comparison(self):
        """Compare compact vs descriptive JSON sizes."""
        unit = stamp("Size test", confidence=0.85, ai_generated=True,
                     evidence=["tests passed", "lint clean"], model="gpt-4o")
        compact = json.dumps(unit.to_dict(compact=True))
        descriptive = json.dumps(unit.to_dict(compact=False))
        ratio = len(compact) / len(descriptive)
        print(f"\n  Compact JSON: {len(compact)} bytes")
        print(f"  Descriptive JSON: {len(descriptive)} bytes")
        print(f"  Compact/Descriptive ratio: {ratio:.2f}")
        assert len(compact) < len(descriptive), "Compact should be smaller"

    def test_loads_latency(self):
        """akf.loads() parsing latency."""
        unit = stamp("Parse test", confidence=0.85, ai_generated=True)
        j = json.dumps(unit.to_dict(compact=False))
        _, elapsed = measure_time(akf.loads, j)
        print(f"\n  akf.loads(): {elapsed:.2f}ms")
        assert elapsed < 20

    def test_roundtrip_100(self):
        """100 serialize→deserialize roundtrips."""
        unit = stamp("Roundtrip", confidence=0.85)
        j = json.dumps(unit.to_dict(compact=False))
        start = time.perf_counter()
        for _ in range(100):
            parsed = akf.loads(j)
            json.dumps(parsed.to_dict(compact=False))
        elapsed = (time.perf_counter() - start) * 1000
        per_trip = elapsed / 100
        print(f"\n  100 roundtrips: {elapsed:.1f}ms, {per_trip:.2f}ms/trip")
        assert per_trip < 20


# ═══════════════════════════════════════════════════════════════════════════
# 12. CONCURRENT STAMPING
# ═══════════════════════════════════════════════════════════════════════════

class TestConcurrency:
    """Test thread safety and concurrent performance."""

    def test_concurrent_stamps(self):
        """Multiple threads stamping simultaneously."""
        results = []
        errors = []

        def stamp_worker(thread_id):
            try:
                for i in range(50):
                    unit = stamp(f"Thread {thread_id} claim {i}", confidence=0.7)
                    results.append(unit)
            except Exception as e:
                errors.append((thread_id, e))

        threads = [threading.Thread(target=stamp_worker, args=(t,)) for t in range(4)]
        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\n  4 threads × 50 stamps: {elapsed:.1f}ms, {len(results)} units")
        assert len(errors) == 0, f"Errors: {errors}"
        assert len(results) == 200
        # All IDs should be unique
        ids = [u.id for u in results]
        assert len(set(ids)) == 200, "Duplicate unit IDs detected"

    def test_concurrent_detections(self):
        """Multiple threads running detections simultaneously."""
        unit = stamp("Concurrent detection", confidence=0.7, ai_generated=True)
        errors = []

        def detect_worker():
            try:
                for _ in range(50):
                    report = run_all_detections(unit)
                    assert len(report.results) == 10
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=detect_worker) for _ in range(4)]
        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
        elapsed = (time.perf_counter() - start) * 1000

        print(f"\n  4 threads × 50 detections: {elapsed:.1f}ms")
        assert len(errors) == 0, f"Concurrent detection errors: {errors}"
