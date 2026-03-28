"""AKF v1.0 — Universal format-agnostic API.

Auto-detects file format from extension and dispatches to the correct
handler. Falls back to sidecar mode for unsupported formats.

Usage:
    from akf import universal

    universal.embed("report.md", claims=[...], classification="internal")
    meta = universal.extract("report.md")
    report = universal.scan("report.md")
"""

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .formats.base import AKFFormatHandler, ScanReport
from . import sidecar as _sidecar


# ---------------------------------------------------------------------------
# Format registry
# ---------------------------------------------------------------------------

_FORMAT_REGISTRY: Dict[str, Callable[[], AKFFormatHandler]] = {}
_HANDLER_CACHE: Dict[str, AKFFormatHandler] = {}


def _register_builtin_formats() -> None:
    """Register built-in format handlers (lazy factories)."""

    def _markdown_factory() -> AKFFormatHandler:
        from .formats.markdown import MarkdownHandler
        return MarkdownHandler()

    def _html_factory() -> AKFFormatHandler:
        from .formats.html import HTMLHandler
        return HTMLHandler()

    def _json_factory() -> AKFFormatHandler:
        from .formats.json_format import JSONHandler
        return JSONHandler()

    def _docx_factory() -> AKFFormatHandler:
        from .formats.docx import DOCXHandler
        return DOCXHandler()

    def _xlsx_factory() -> AKFFormatHandler:
        from .formats.xlsx import XLSXHandler
        return XLSXHandler()

    def _pptx_factory() -> AKFFormatHandler:
        from .formats.pptx import PPTXHandler
        return PPTXHandler()

    def _pdf_factory() -> AKFFormatHandler:
        from .formats.pdf import PDFHandler
        return PDFHandler()

    def _image_factory() -> AKFFormatHandler:
        from .formats.image import ImageHandler
        return ImageHandler()

    def _email_factory() -> AKFFormatHandler:
        from .formats.email import EmailHandler
        return EmailHandler()

    # Markdown
    for ext in ("md", "markdown", "mdx"):
        _FORMAT_REGISTRY[ext] = _markdown_factory

    # HTML
    for ext in ("html", "htm"):
        _FORMAT_REGISTRY[ext] = _html_factory

    # JSON
    for ext in ("json",):
        _FORMAT_REGISTRY[ext] = _json_factory

    # Office
    _FORMAT_REGISTRY["docx"] = _docx_factory
    _FORMAT_REGISTRY["xlsx"] = _xlsx_factory
    _FORMAT_REGISTRY["pptx"] = _pptx_factory

    # PDF
    _FORMAT_REGISTRY["pdf"] = _pdf_factory

    # Images
    for ext in ("png", "jpg", "jpeg", "tiff", "webp"):
        _FORMAT_REGISTRY[ext] = _image_factory

    # Email
    for ext in ("eml",):
        _FORMAT_REGISTRY[ext] = _email_factory

    def _video_factory() -> AKFFormatHandler:
        from .formats.video import VideoHandler
        return VideoHandler()

    def _audio_factory() -> AKFFormatHandler:
        from .formats.audio import AudioHandler
        return AudioHandler()

    # Video
    for ext in ("mp4", "mov", "webm", "mkv"):
        _FORMAT_REGISTRY[ext] = _video_factory

    # Audio
    for ext in ("mp3", "wav", "flac", "ogg"):
        _FORMAT_REGISTRY[ext] = _audio_factory

    def _toml_factory() -> AKFFormatHandler:
        from .formats.toml_format import TOMLHandler
        return TOMLHandler()

    def _code_factory() -> AKFFormatHandler:
        from .formats.code_format import CodeHandler
        return CodeHandler()

    # TOML
    _FORMAT_REGISTRY["toml"] = _toml_factory

    # Code (Go, Python, JS, TS, etc)
    for ext in ("go", "py", "js", "ts", "sh", "rb", "c", "cpp", "rs"):
        _FORMAT_REGISTRY[ext] = _code_factory


# Initialize built-in formats
_register_builtin_formats()


def _get_extension(filepath: str) -> str:
    """Extract lowercase extension without the dot."""
    _, ext = os.path.splitext(filepath)
    return ext.lstrip(".").lower()


def _resolve_handler(filepath: str) -> Optional[AKFFormatHandler]:
    """Resolve the handler for a file, using cache for performance."""
    ext = _get_extension(filepath)
    if ext not in _FORMAT_REGISTRY:
        return None

    if ext not in _HANDLER_CACHE:
        try:
            _HANDLER_CACHE[ext] = _FORMAT_REGISTRY[ext]()
        except ImportError:
            # Handler's dependencies not installed; fall back to sidecar
            return None

    return _HANDLER_CACHE[ext]


# ---------------------------------------------------------------------------
# Sidecar fallback handler
# ---------------------------------------------------------------------------

class _SidecarFallbackHandler(AKFFormatHandler):
    """Fallback handler using sidecar files for unsupported formats."""

    FORMAT_NAME = "sidecar"
    EXTENSIONS = ["*"]
    MODE = "sidecar"
    MECHANISM = "companion .akf.json file"

    def embed(self, filepath: str, metadata: dict) -> None:
        _sidecar.create(filepath, metadata)

    def extract(self, filepath: str) -> Optional[dict]:
        return _sidecar.read(filepath)

    def is_enriched(self, filepath: str) -> bool:
        return _sidecar.read(filepath) is not None


_SIDECAR_HANDLER = _SidecarFallbackHandler()

MAX_CLAIM_SIZE = 100_000  # 100KB per claim field
MAX_CLAIMS = 1_000


def _sanitize_string(value: str) -> str:
    """Strip path traversal sequences from string values."""
    return value.replace("../", "").replace("..\\", "")


def _validate_metadata(meta: Dict[str, Any]) -> None:
    """Validate metadata before embedding — size limits and sanitization."""
    claims = meta.get("claims", [])
    if len(claims) > MAX_CLAIMS:
        raise ValueError(f"Too many claims ({len(claims)}). Maximum is {MAX_CLAIMS}.")

    for claim in claims:
        for key in ("c", "content", "src", "source"):
            val = claim.get(key)
            if isinstance(val, str):
                if len(val) > MAX_CLAIM_SIZE:
                    raise ValueError(
                        f"Claim field '{key}' exceeds {MAX_CLAIM_SIZE:,} byte limit "
                        f"({len(val):,} bytes)."
                    )
                claim[key] = _sanitize_string(val)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def embed(
    filepath: str,
    claims: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    classification: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Embed AKF metadata into a file.

    Dispatches to the correct format handler based on file extension.
    Falls back to sidecar if format is unsupported.

    Supports multiple calling conventions:
        embed(filepath, metadata={...})
        embed(filepath, claims=[...], classification="confidential")
        embed(filepath, claims=[...], metadata={"overall_trust": 0.9})

    Args:
        filepath: Path to the file to enrich.
        claims: List of claim dicts to embed.
        metadata: Full metadata dict. If both claims and metadata are given,
                  claims are merged into metadata.
        classification: Security classification label.
        **kwargs: Additional metadata fields.
    """
    # Build normalized metadata
    meta = dict(metadata) if metadata else {}

    if claims is not None:
        meta["claims"] = claims

    if classification is not None:
        meta["classification"] = classification

    # Merge any extra kwargs
    for key, value in kwargs.items():
        meta[key] = value

    # Input validation
    _validate_metadata(meta)

    handler = _resolve_handler(filepath)
    if handler is not None:
        handler.embed(filepath, meta)
    else:
        _SIDECAR_HANDLER.embed(filepath, meta)


def extract(filepath: str) -> Optional[Dict[str, Any]]:
    """Extract AKF metadata from a file.

    Tries the format-specific handler first, then falls back to sidecar.

    Args:
        filepath: Path to the file.

    Returns:
        Metadata dict, or None if no AKF metadata found.
    """
    # Native .akf files: load directly via core
    ext = _get_extension(filepath)
    if ext == "akf":
        from .core import load as _load_akf
        try:
            unit = _load_akf(filepath)
            return json.loads(unit.model_dump_json(by_alias=True, exclude_none=True))
        except Exception:
            return None

    handler = _resolve_handler(filepath)
    if handler is not None:
        result = handler.extract(filepath)
        if result is not None:
            return result

    # Fall back to sidecar
    return _SIDECAR_HANDLER.extract(filepath)


def scan(filepath: str) -> ScanReport:
    """Security scan a file for AKF metadata.

    Args:
        filepath: Path to the file.

    Returns:
        ScanReport with enrichment details.
    """
    handler = _resolve_handler(filepath)
    if handler is not None:
        report = handler.scan(filepath)
        if report.enriched:
            return report

    # Fall back to sidecar scan
    return _SIDECAR_HANDLER.scan(filepath)


def is_enriched(filepath: str) -> bool:
    """Check if a file has AKF metadata (embedded or sidecar).

    Args:
        filepath: Path to the file.

    Returns:
        True if AKF metadata is present.
    """
    handler = _resolve_handler(filepath)
    if handler is not None:
        if handler.is_enriched(filepath):
            return True

    return _SIDECAR_HANDLER.is_enriched(filepath)


def auto_enrich(filepath: str, agent_id: str, **kwargs: Any) -> None:
    """Auto-add AKF metadata to an AI-generated file.

    Args:
        filepath: Path to the file.
        agent_id: Identifier for the AI agent.
        **kwargs: Passed to handler's auto_enrich (default_tier, classification).
    """
    handler = _resolve_handler(filepath)
    if handler is not None:
        handler.auto_enrich(filepath, agent_id, **kwargs)
    else:
        _SIDECAR_HANDLER.auto_enrich(filepath, agent_id, **kwargs)


def to_akf(filepath: str, output: str) -> None:
    """Extract metadata from any file and create a standalone .akf file.

    Args:
        filepath: Path to the source file.
        output: Path for the output .akf file.
    """
    meta = extract(filepath)
    if meta is None:
        raise ValueError("No AKF metadata found in {}".format(filepath))

    # Convert to AKF format
    from .core import create_multi
    from .provenance import compute_integrity_hash

    claims = meta.get("claims", [])
    if not claims:
        # Create a minimal claim from the metadata
        claims = [{"c": "Extracted from {}".format(os.path.basename(filepath)), "t": 0.5}]

    envelope: Dict[str, Any] = {}
    if meta.get("classification"):
        envelope["label"] = meta["classification"]

    unit = create_multi(claims, **envelope)

    # Attach provenance if available
    if meta.get("provenance"):
        from .models import ProvHop
        hops = []
        for i, p in enumerate(meta["provenance"]):
            hop_data = {
                "hop": i,
                "actor": p.get("actor", p.get("by", "unknown")),
                "action": p.get("action", p.get("do", "unknown")),
                "timestamp": p.get("at", p.get("timestamp", "")),
            }
            if p.get("hash") or p.get("h"):
                hop_data["hash"] = p.get("hash", p.get("h"))
            hops.append(ProvHop(**hop_data))
        unit = unit.model_copy(update={"prov": hops})

    # Compute and set integrity hash
    integrity = compute_integrity_hash(unit)
    unit = unit.model_copy(update={"integrity_hash": integrity})

    unit.save(output)


def create_sidecar(filepath: str, metadata: Dict[str, Any]) -> str:
    """Explicitly create a sidecar file for any file.

    Args:
        filepath: Path to the original file.
        metadata: AKF metadata dict.

    Returns:
        Path to the created sidecar file.
    """
    return _sidecar.create(filepath, metadata)


_SKIP_DIRS = {
    "node_modules", "__pycache__", ".git", ".svn", ".hg", "venv", ".venv",
    "env", ".env", ".tox", "dist", "build", ".cache", ".npm", ".yarn",
    "Library", "Applications", ".Trash", "Pictures", "Music", "Movies",
}


def scan_directory(
    dirpath: str,
    recursive: bool = True,
    max_files: int = 10000,
    on_progress=None,
) -> List[ScanReport]:
    """Scan a directory for AKF-enriched files.

    Args:
        dirpath: Directory to scan.
        recursive: Whether to scan subdirectories.
        max_files: Maximum number of files to scan (default 10000).
        on_progress: Optional callback(scanned: int, enriched: int) for progress.

    Returns:
        List of ScanReports for all files found.
    """
    reports: List[ScanReport] = []
    scanned = 0

    if not os.path.isdir(dirpath):
        return reports

    if recursive:
        for root, dirs, files in os.walk(dirpath):
            # Skip hidden directories and known-heavy directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in _SKIP_DIRS]
            for filename in sorted(files):
                if filename.startswith(".") or filename.endswith(".akf.json"):
                    continue
                if scanned >= max_files:
                    return reports
                filepath = os.path.join(root, filename)
                scanned += 1
                if on_progress and scanned % 100 == 0:
                    enriched = sum(1 for r in reports if r.enriched)
                    on_progress(scanned, enriched)
                try:
                    report = scan(filepath)
                    report.format = report.format or _get_extension(filepath)
                    reports.append(report)
                except Exception:
                    pass
    else:
        for entry in sorted(os.listdir(dirpath)):
            if entry.startswith(".") or entry.endswith(".akf.json"):
                continue
            filepath = os.path.join(dirpath, entry)
            if not os.path.isfile(filepath):
                continue
            if scanned >= max_files:
                return reports
            scanned += 1
            try:
                report = scan(filepath)
                report.format = report.format or _get_extension(filepath)
                reports.append(report)
            except Exception:
                pass

    return reports


def supported_formats() -> Dict[str, Dict[str, Any]]:
    """Return information about all supported formats.

    Returns:
        Dict mapping format name to info dict with keys:
        extensions, mode, mechanism, dependencies.
    """
    formats: Dict[str, Dict[str, Any]] = {}
    seen_factories: Dict[int, bool] = {}

    for ext, factory in _FORMAT_REGISTRY.items():
        factory_id = id(factory)
        if factory_id in seen_factories:
            continue
        seen_factories[factory_id] = True

        try:
            handler = factory()
            formats[handler.FORMAT_NAME] = {
                "extensions": list(handler.EXTENSIONS),
                "mode": handler.MODE,
                "mechanism": handler.MECHANISM,
                "dependencies": list(handler.DEPENDENCIES),
            }
        except ImportError:
            # Handler available but deps missing; still report it
            pass

    # Always include sidecar
    formats["sidecar"] = {
        "extensions": ["*"],
        "mode": "sidecar",
        "mechanism": "companion .akf.json file",
        "dependencies": [],
    }

    return formats


def register_format(extension: str, handler: AKFFormatHandler) -> None:
    """Register a custom format handler for an extension.

    Args:
        extension: File extension (without dot), e.g. "csv".
        handler: An AKFFormatHandler instance.
    """
    ext = extension.lstrip(".").lower()
    _FORMAT_REGISTRY[ext] = lambda: handler
    _HANDLER_CACHE[ext] = handler


def info(filepath: str) -> str:
    """Return a formatted string summary of a file's AKF metadata.

    Args:
        filepath: Path to the file.

    Returns:
        Human-readable summary string.
    """
    meta = extract(filepath)
    filename = os.path.basename(filepath)
    ext = _get_extension(filepath)

    lines: List[str] = []
    lines.append("File: {}".format(filename))
    lines.append("Format: {}".format(ext or "unknown"))

    if meta is None:
        lines.append("AKF: not enriched")
        return "\n".join(lines)

    lines.append("AKF: enriched")
    mode = meta.get("mode", "embedded")
    lines.append("Mode: {}".format(mode))

    if meta.get("classification"):
        lines.append("Classification: {}".format(meta["classification"]))

    if meta.get("overall_trust") is not None:
        lines.append("Overall trust: {:.2f}".format(meta["overall_trust"]))

    if meta.get("ai_contribution") is not None:
        lines.append("AI contribution: {:.0%}".format(meta["ai_contribution"]))

    claims = meta.get("claims", [])
    lines.append("Claims: {}".format(len(claims)))

    ai_claims = [c for c in claims if c.get("ai") or c.get("ai_generated")]
    if ai_claims:
        lines.append("  AI-generated: {}".format(len(ai_claims)))

    verified = [c for c in claims if c.get("ver") or c.get("verified")]
    if verified:
        lines.append("  Verified: {}".format(len(verified)))

    prov = meta.get("provenance", [])
    if prov:
        lines.append("Provenance depth: {}".format(len(prov)))

    if meta.get("integrity_hash"):
        lines.append("Integrity hash: {}".format(meta["integrity_hash"][:30] + "..."))

    return "\n".join(lines)


def derive(
    source: str,
    output: str,
    agent_id: str,
    action: str = "derived",
    claims: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """Create a derived file with cross-format provenance.

    Links the output file's metadata to the source file's provenance chain,
    inheriting classification and adding a new provenance hop.

    Args:
        source: Path to the source file.
        output: Path to the output file (must already exist).
        agent_id: Identifier for the agent performing derivation.
        action: Action label for the provenance hop.
        claims: Optional new claims to add.
    """
    import hashlib
    from datetime import datetime, timezone

    source_meta = extract(source)
    now = datetime.now(timezone.utc).isoformat()

    # Compute source file hash
    with open(source, "rb") as f:
        source_hash = "sha256:" + hashlib.sha256(f.read()).hexdigest()

    # Build provenance chain
    source_prov = []
    if source_meta and source_meta.get("provenance"):
        source_prov = list(source_meta["provenance"])

    new_hop = {
        "actor": agent_id,
        "action": action,
        "at": now,
        "parent_file": os.path.basename(source),
        "parent_hash": source_hash,
    }
    prov_chain = source_prov + [new_hop]

    # Build new metadata
    new_meta: Dict[str, Any] = {
        "akf": "1.0",
        "generated_at": now,
        "provenance": prov_chain,
        "parent_file": os.path.basename(source),
        "parent_hash": source_hash,
    }

    # Inherit classification from source
    if source_meta and source_meta.get("classification"):
        new_meta["classification"] = source_meta["classification"]

    # Inherit trust info
    if source_meta:
        if source_meta.get("overall_trust") is not None:
            new_meta["overall_trust"] = source_meta["overall_trust"]
        if source_meta.get("ai_contribution") is not None:
            new_meta["ai_contribution"] = source_meta["ai_contribution"]

    # Add claims
    if claims:
        new_meta["claims"] = claims
    else:
        new_meta["claims"] = []

    embed(output, metadata=new_meta)


def provenance_tree(filepath: str) -> List[Dict[str, Any]]:
    """Walk parent_file links recursively to build a provenance tree.

    Args:
        filepath: Path to start from.

    Returns:
        List of dicts with file, metadata, and parent info.
    """
    tree: List[Dict[str, Any]] = []
    visited: set = set()
    current = os.path.abspath(filepath)

    while current and current not in visited:
        visited.add(current)
        meta = extract(current)
        entry: Dict[str, Any] = {
            "file": current,
            "metadata": meta,
        }
        tree.append(entry)

        if meta is None:
            break

        parent_file = meta.get("parent_file")
        if not parent_file:
            break

        # Resolve parent path relative to current file's directory
        parent_dir = os.path.dirname(current)
        current = os.path.join(parent_dir, parent_file)
        if not os.path.isfile(current):
            break

    return tree


def verify_chain(filepath: str) -> List[Dict[str, Any]]:
    """Verify integrity at each hop in the provenance chain.

    Args:
        filepath: Path to start from.

    Returns:
        List of dicts with file path and integrity_valid boolean.
    """
    results: List[Dict[str, Any]] = []
    tree = provenance_tree(filepath)

    for entry in tree:
        fpath = entry["file"]
        meta = entry["metadata"]

        result: Dict[str, Any] = {"file": fpath, "integrity_valid": None}

        if meta and meta.get("integrity_hash"):
            actual_hash = _sidecar._compute_file_hash(fpath)
            result["integrity_valid"] = (actual_hash == meta["integrity_hash"])

        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Batch directory conversion
# ---------------------------------------------------------------------------

@dataclass
class ConvertResult:
    """Result of a batch directory conversion."""
    converted: int = 0
    skipped: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.failed == 0


def _enrich_to_akf(filepath: str, output: str, agent: Optional[str] = None) -> None:
    """Generate a baseline .akf for a file WITHOUT existing AKF metadata.

    Creates three claims (file exists, SHA-256 hash, detected format)
    and a provenance hop.
    """
    from .core import create_multi
    from .provenance import compute_integrity_hash

    with open(filepath, "rb") as f:
        file_hash = "sha256:" + hashlib.sha256(f.read()).hexdigest()

    ext = _get_extension(filepath) or "unknown"
    basename = os.path.basename(filepath)

    claims = [
        {"content": "File exists: {}".format(basename), "confidence": 1.0},
        {"content": "SHA-256: {}".format(file_hash), "confidence": 1.0},
        {"content": "Detected format: {}".format(ext), "confidence": 0.9},
    ]

    actor = agent or "akf-convert"
    now = datetime.now(timezone.utc).isoformat()

    unit = create_multi(claims)

    from .models import ProvHop
    hop = ProvHop(
        hop=0,
        actor=actor,
        action="enrich",
        timestamp=now,
        hash=file_hash,
    )
    unit = unit.model_copy(update={"prov": [hop]})

    integrity = compute_integrity_hash(unit)
    unit = unit.model_copy(update={"integrity_hash": integrity})

    unit.save(output)


def convert_directory(
    dirpath: str,
    output_dir: Optional[str] = None,
    recursive: bool = True,
    mode: str = "both",
    overwrite: bool = False,
    agent: Optional[str] = None,
) -> ConvertResult:
    """Convert all files in a directory to standalone .akf files.

    Args:
        dirpath: Input directory to convert.
        output_dir: Output directory. Defaults to ``dirpath``.
        mode: ``"extract"`` (metadata only), ``"enrich"`` (baseline only),
              or ``"both"`` (extract if metadata, enrich otherwise).
        recursive: Walk subdirectories.
        overwrite: Overwrite existing .akf outputs.
        agent: Agent ID for enrich-mode provenance.

    Returns:
        ConvertResult with counts and per-file errors.
    """
    result = ConvertResult()

    if not os.path.isdir(dirpath):
        result.failed += 1
        result.errors.append("Directory not found: {}".format(dirpath))
        return result

    if output_dir is None:
        output_dir = dirpath

    def _should_skip(filename: str) -> bool:
        if filename.startswith("."):
            return True
        if filename.endswith(".akf.json"):
            return True
        if filename.endswith(".akf"):
            return True
        return False

    def _process_file(filepath: str, rel_dir: str) -> None:
        filename = os.path.basename(filepath)
        out_subdir = os.path.join(output_dir, rel_dir)
        os.makedirs(out_subdir, exist_ok=True)
        out_path = os.path.join(out_subdir, filename + ".akf")

        if os.path.exists(out_path) and not overwrite:
            result.skipped += 1
            return

        try:
            has_meta = is_enriched(filepath)

            if mode == "extract":
                if not has_meta:
                    result.skipped += 1
                    return
                to_akf(filepath, out_path)
                result.converted += 1

            elif mode == "enrich":
                if has_meta:
                    result.skipped += 1
                    return
                _enrich_to_akf(filepath, out_path, agent)
                result.converted += 1

            else:  # both
                if has_meta:
                    to_akf(filepath, out_path)
                else:
                    _enrich_to_akf(filepath, out_path, agent)
                result.converted += 1

        except Exception as exc:
            result.failed += 1
            result.errors.append("{}: {}".format(filepath, exc))

    if recursive:
        for root, dirs, files in os.walk(dirpath):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            rel_dir = os.path.relpath(root, dirpath)
            if rel_dir == ".":
                rel_dir = ""
            for filename in sorted(files):
                if _should_skip(filename):
                    continue
                _process_file(os.path.join(root, filename), rel_dir)
    else:
        for entry in sorted(os.listdir(dirpath)):
            if _should_skip(entry):
                continue
            filepath = os.path.join(dirpath, entry)
            if not os.path.isfile(filepath):
                continue
            _process_file(filepath, "")

    return result
