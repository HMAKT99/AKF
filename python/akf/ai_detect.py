"""Content-based AI-generated text detection.

Heuristic analysis of file content to estimate the likelihood that text
was produced by an LLM.  Also queries macOS Spotlight metadata for the
creating application (e.g. "Claude", "ChatGPT").

All detection is best-effort — no external dependencies, no ML models.
The ``mdls`` subprocess call is cached per file so repeated analysis of
the same directory only pays the cost once.
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Known AI creator applications (macOS kMDItemCreator values)
# ---------------------------------------------------------------------------

AI_CREATOR_APPS = frozenset({
    "claude",
    "chatgpt",
    "cursor",
    "windsurf",
    "codeium",
    "google gemini",
    "copilot",
    "aider",
    "continue",
})

# ---------------------------------------------------------------------------
# Text-based signal patterns
# ---------------------------------------------------------------------------

# (compiled_regex, weight, label)
# Weight represents contribution to AI probability score.

_TEXT_SIGNALS: List[Tuple[re.Pattern, float, str]] = [
    # --- Very strong: explicit AI self-reference ---
    (re.compile(r"as an ai\b", re.I), 0.30, "ai-self-reference"),
    (re.compile(r"as a large language model", re.I), 0.30, "llm-self-reference"),
    (re.compile(r"i'?m an ai assistant", re.I), 0.30, "ai-assistant-ref"),
    (re.compile(r"as an? (?:artificial intelligence|language model)", re.I), 0.30, "ai-model-ref"),

    # --- Strong: formulaic AI openings/closings ---
    (re.compile(r"(?:i'?d be|i'?m) happy to help", re.I), 0.15, "happy-to-help"),
    (re.compile(r"i'?ll help you with", re.I), 0.15, "ill-help-you"),
    (re.compile(r"(?:^|\n)\s*certainly[!.]", re.I), 0.12, "certainly"),
    (re.compile(r"(?:^|\n)\s*absolutely[!.]", re.I), 0.12, "absolutely"),
    (re.compile(r"here'?s a comprehensive", re.I), 0.12, "heres-comprehensive"),
    (re.compile(r"(?:^|\n)\s*great question", re.I), 0.12, "great-question"),

    # --- Moderate: common AI phrasings ---
    (re.compile(r"i hope this helps", re.I), 0.08, "hope-this-helps"),
    (re.compile(r"feel free to (?:ask|reach|let)", re.I), 0.08, "feel-free"),
    (re.compile(r"let me know if you (?:have|need|want)", re.I), 0.08, "let-me-know"),
    (re.compile(r"don'?t hesitate to", re.I), 0.08, "dont-hesitate"),
    (re.compile(r"(?:it'?s|it is) worth noting", re.I), 0.08, "worth-noting"),
    (re.compile(r"(?:it'?s|it is) important to (?:note|remember|understand)", re.I), 0.08, "important-to-note"),
    (re.compile(r"here are (?:some|the|a few) key", re.I), 0.08, "here-are-key"),
    (re.compile(r"(?:in summary|to summarize|key takeaways)", re.I), 0.06, "summary-phrase"),
    (re.compile(r"(?:in conclusion|to conclude|wrapping up)", re.I), 0.06, "conclusion-phrase"),
    (re.compile(r"(?:overall|in general),? (?:this|the|it)", re.I), 0.05, "overall-phrase"),

    # --- Weak: structural tells (only meaningful in aggregate) ---
    (re.compile(r"(?:^|\n)## ", re.M), 0.02, "markdown-h2"),
    (re.compile(r"(?:^|\n)\d+\.\s", re.M), 0.02, "numbered-list"),
    (re.compile(r"\*\*[^*]+\*\*:"), 0.02, "bold-label"),
]

# Structural signals that depend on counts
_BULLET_RE = re.compile(r"^[\s]*[-•*]\s", re.M)
_HEADER_RE = re.compile(r"^#{1,4}\s", re.M)

# ---------------------------------------------------------------------------
# Code-specific signals
# ---------------------------------------------------------------------------

_CODE_SIGNALS: List[Tuple[re.Pattern, float, str]] = [
    (re.compile(r'"""[^"]{10,}"""', re.S), 0.03, "docstring"),
    (re.compile(r"# (?:Import|Define|Initialize|Create|Set up) ", re.I), 0.06, "narrating-comment"),
    (re.compile(r"# Example usage", re.I), 0.06, "example-usage-comment"),
    (re.compile(r"# This (?:function|method|class|module) ", re.I), 0.05, "this-function-comment"),
    (re.compile(r'if __name__\s*==\s*["\']__main__["\']'), 0.02, "main-guard"),
]

_CODE_EXTENSIONS = frozenset({
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".rb", ".php", ".swift", ".kt", ".c", ".cpp", ".cs",
})


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class AiDetectionResult:
    """Result of AI content detection analysis."""
    score: float = 0.0
    signals: List[str] = field(default_factory=list)
    creator_app: Optional[str] = None
    likely_ai: bool = False


# ---------------------------------------------------------------------------
# Creator app detection (macOS Spotlight) — cached per file
# ---------------------------------------------------------------------------

_IS_DARWIN = platform.system() == "Darwin"
_creator_cache: Dict[str, Tuple[Optional[str], float]] = {}
_CREATOR_CACHE_TTL = 300  # 5 minutes
_SENTINEL = object()


def _cache_get(cache, key):
    entry = cache.get(key)
    if entry and (time.monotonic() - entry[1]) < _CREATOR_CACHE_TTL:
        return entry[0]
    return _SENTINEL


def _detect_creator_app(filepath: Path) -> Optional[str]:
    """Query macOS Spotlight for the application that created a file.

    Returns the app name (lowered) if it matches a known AI tool, else None.
    Results are cached per file path.
    """
    if not _IS_DARWIN:
        return None

    path_str = str(filepath)
    cached = _cache_get(_creator_cache, path_str)
    if cached is not _SENTINEL:
        return cached

    creator_result = None
    try:
        result = subprocess.run(
            ["mdls", "-name", "kMDItemCreator", "-raw", str(filepath)],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            creator = result.stdout.strip().strip('"').lower()
            if creator and creator != "(null)":
                for app in AI_CREATOR_APPS:
                    if app in creator:
                        creator_result = creator
                        break
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    _creator_cache[path_str] = (creator_result, time.monotonic())
    return creator_result


# ---------------------------------------------------------------------------
# Content scanning
# ---------------------------------------------------------------------------

def _scan_text_signals(text: str) -> Tuple[float, List[str]]:
    """Scan text content for AI-generated signals.

    Returns (score, list_of_signal_labels).
    """
    score = 0.0
    signals: List[str] = []

    for pattern, weight, label in _TEXT_SIGNALS:
        matches = pattern.findall(text)
        if matches:
            # Cap repeated weak signals at 3 matches
            count = min(len(matches), 3)
            contribution = weight * count
            score += contribution
            signals.append(f"{label}(x{count})" if count > 1 else label)

    # Structural: excessive bullets
    bullet_count = len(_BULLET_RE.findall(text))
    if bullet_count > 10:
        score += 0.05
        signals.append(f"many-bullets({bullet_count})")

    # Structural: excessive headers
    header_count = len(_HEADER_RE.findall(text))
    if header_count > 5:
        score += 0.05
        signals.append(f"many-headers({header_count})")

    return score, signals


def _scan_code_signals(text: str) -> Tuple[float, List[str]]:
    """Scan code content for AI-generated signals.

    Returns (score, list_of_signal_labels).
    """
    score = 0.0
    signals: List[str] = []

    for pattern, weight, label in _CODE_SIGNALS:
        matches = pattern.findall(text)
        if matches:
            count = min(len(matches), 5)
            contribution = weight * count
            # Cap code signal contribution to avoid false positives
            contribution = min(contribution, 0.15)
            score += contribution
            signals.append(f"{label}(x{count})" if count > 1 else label)

    # Heuristic: docstring-to-function ratio
    func_count = len(re.findall(r"(?:^|\n)\s*(?:def|function|func|fn)\s", text))
    docstring_count = len(re.findall(r'"""[^"]+"""', text, re.S))
    if func_count >= 3 and docstring_count >= func_count:
        score += 0.08
        signals.append("every-func-docstringed")

    return score, signals


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

# Maximum bytes to read for content analysis (first 32 KB)
_MAX_READ_BYTES = 32 * 1024

# Binary/non-text extensions to skip
_SKIP_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp",
    ".pdf", ".docx", ".xlsx", ".pptx", ".zip", ".tar", ".gz",
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv",
    ".exe", ".dll", ".so", ".dylib", ".wasm",
})


def detect_ai_content(filepath: os.PathLike) -> AiDetectionResult:
    """Analyze a file for signs of AI-generated content.

    Combines three detection methods:
    1. macOS creator app metadata (definitive if matched)
    2. Text content heuristics (phrase patterns, structure)
    3. Code content heuristics (docstrings, narrating comments)

    Returns an ``AiDetectionResult`` with score, signals, and verdict.
    The score is in [0, 1]; ``likely_ai`` is True when score >= 0.5
    or a known AI creator app is detected.
    """
    filepath = Path(filepath)
    result = AiDetectionResult()

    # Check creator app (macOS)
    try:
        creator = _detect_creator_app(filepath)
        if creator:
            result.creator_app = creator
            result.score = max(result.score, 0.8)
            result.signals.append(f"creator-app:{creator}")
    except Exception:
        pass

    # Skip binary files
    if filepath.suffix.lower() in _SKIP_EXTENSIONS:
        result.likely_ai = result.score >= 0.5
        return result

    # Read file content (first 32 KB)
    try:
        text = filepath.read_text(errors="replace")[:_MAX_READ_BYTES]
    except (OSError, UnicodeDecodeError):
        result.likely_ai = result.score >= 0.5
        return result

    if not text.strip():
        result.likely_ai = result.score >= 0.5
        return result

    # Text signals
    try:
        text_score, text_signals = _scan_text_signals(text)
        result.score += text_score
        result.signals.extend(text_signals)
    except Exception:
        pass

    # Code signals (only for code files)
    if filepath.suffix.lower() in _CODE_EXTENSIONS:
        try:
            code_score, code_signals = _scan_code_signals(text)
            result.score += code_score
            result.signals.extend(code_signals)
        except Exception:
            pass

    # Clamp score to [0, 1]
    result.score = min(1.0, max(0.0, round(result.score, 3)))
    result.likely_ai = result.score >= 0.5

    return result
