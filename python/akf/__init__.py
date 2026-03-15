"""AKF — Agent Knowledge Format v1.1.

The trust metadata standard for every file AI touches.

Usage:
    import akf

    # Standalone .akf
    unit = akf.create("Revenue $4.2B", confidence=0.98)
    unit.save("out.akf")

    # Universal: embed into any format
    akf.embed("report.docx", claims=[...], classification="confidential")
    akf.extract("report.docx")
    akf.scan("report.docx")
    akf.info("report.docx")
"""

from .models import (
    AKF, Claim, Evidence, Fidelity, ProvHop,
    Origin, GenerationParams, MadeBy, Review, SourceDetail,
    ReasoningChain, Annotation, Freshness, CostMetadata, AgentProfile,
    Calibration,
)
from .core import create, create_multi, load, loads, validate, ValidationResult
from .universal import ConvertResult
from .builder import AKFBuilder
from .trust import (
    effective_trust, compute_all, explain_trust, TrustResult, TrustLevel,
    AUTHORITY_WEIGHTS, calibrated_trust, resolve_conflict, trust_summary,
    is_expired, freshness_status,
)
from .provenance import add_hop, format_tree, compute_integrity_hash, models_used
from .security import (
    validate_inheritance, can_share_external, inherit_label, security_score,
    purview_signals, detect_laundering, SecurityScore, SecurityReport,
    check_access, verify_trust_anchor, redaction_report, compute_security_hash,
    full_report,
)
from .transform import AKFTransformer
from .agent import (
    consume, derive, generation_prompt, validate_output,
    response_schema, from_tool_call, to_context, detect,
)
from .compliance import (
    audit, check_regulation, audit_trail, verify_human_oversight, AuditResult,
    check_explainability, check_fairness, export_audit, continuous_audit,
)
from .view import show, to_html, to_markdown, executive_summary
from .data import load_dataset, quality_report, merge, filter_claims
from .report import enterprise_report, EnterpriseReport, FileReport, register_renderer, RENDERERS
from .knowledge_base import KnowledgeBase
from .stamp import stamp, stamp_file
from .git_ops import stamp_commit, read_commit, trust_log
from .streaming import StreamSession, AKFStream, stream_start, stream_claim, stream_end, collect_stream, iter_stream
from .detection import (
    detect_ai_without_review, detect_trust_below_threshold,
    detect_hallucination_risk, detect_knowledge_laundering,
    detect_classification_downgrade, detect_stale_claims,
    detect_ungrounded_claims, detect_trust_degradation_chain,
    detect_excessive_ai_concentration, detect_provenance_gap,
    run_all_detections, DetectionResult, DetectionReport,
)
from .i18n import t as translate

# Universal format layer — lazy imports to avoid optional dependency issues
def save(unit, filepath, compact=True):
    """Save an AKF unit to a file."""
    unit.save(filepath, compact=compact)


def embed(filepath, **kwargs):
    """Embed AKF metadata into any supported file format."""
    from .universal import embed as _embed
    return _embed(filepath, **kwargs)

def extract(filepath):
    """Extract AKF metadata from any supported file format."""
    from .universal import extract as _extract
    return _extract(filepath)

def scan(filepath):
    """Security scan any file for AKF metadata."""
    from .universal import scan as _scan
    return _scan(filepath)

def info(filepath):
    """Quick info check on any file's AKF metadata."""
    from .universal import info as _info
    return _info(filepath)

def is_enriched(filepath):
    """Check if any file has AKF metadata."""
    from .universal import is_enriched as _is_enriched
    return _is_enriched(filepath)

def convert_directory(dirpath, **kwargs):
    """Convert all files in a directory to standalone .akf files."""
    from .universal import convert_directory as _convert_directory
    return _convert_directory(dirpath, **kwargs)

def init(path=".", git_hooks=False, agent=None, classification="internal"):
    """Initialize AKF in a project directory.

    Args:
        path: Project root directory.
        git_hooks: Install post-commit hook for stamp-commit.
        agent: Default AI agent ID.
        classification: Default security classification.

    Returns:
        Path to created config file.
    """
    import json as _json
    from pathlib import Path as _Path

    root = _Path(path).resolve()
    akf_dir = root / ".akf"
    akf_dir.mkdir(exist_ok=True)

    config = {
        "version": "1.0",
        "classification": classification,
        "auto_embed": True,
    }
    if agent:
        config["agent"] = agent

    config_path = akf_dir / "config.json"
    config_path.write_text(_json.dumps(config, indent=2) + "\n")

    if git_hooks:
        hooks_dir = root / ".git" / "hooks"
        if hooks_dir.parent.exists():
            hooks_dir.mkdir(exist_ok=True)
            hook = hooks_dir / "post-commit"
            hook.write_text("#!/bin/sh\nakf stamp-commit\n")
            hook.chmod(0o755)

    return str(config_path)


def stream(output_path=None, *, agent=None, model=None, confidence=0.7, **kwargs):
    """Create a streaming context manager for incremental trust metadata.

    Usage::

        with akf.stream("output.md", model="gpt-4o") as s:
            for chunk in llm.generate():
                s.write(chunk)

    Args:
        output_path: Path for the output file.
        agent: Agent identifier.
        model: AI model identifier.
        confidence: Default confidence for each write.
        **kwargs: Additional stream parameters.

    Returns:
        AKFStream context manager.
    """
    return AKFStream(output_path, agent=agent, model=model, confidence=confidence, **kwargs)


def keygen(**kwargs):
    """Generate an Ed25519 keypair for signing AKF units."""
    from .signing import keygen as _keygen
    return _keygen(**kwargs)

def sign_unit(unit, **kwargs):
    """Sign an AKF unit with an Ed25519 private key."""
    from .signing import sign as _sign
    return _sign(unit, **kwargs)

def verify_signature(unit, **kwargs):
    """Verify the Ed25519 signature on an AKF unit."""
    from .signing import verify as _verify
    return _verify(unit, **kwargs)

def install(user=True):
    """Activate AKF auto-tracking for all LLM calls in this Python environment.

    Writes a .pth file so every Python process auto-patches LLM SDKs.
    Use ``akf uninstall`` or ``uninstall()`` to reverse.

    Args:
        user: Install for current user (True) or system-wide (False).

    Returns:
        Path to the created .pth file.
    """
    from ._auto import install as _install
    return _install(user=user)


def uninstall():
    """Remove AKF auto-tracking (reverses ``install()``).

    Returns:
        Path of the removed .pth file, or None if not found.
    """
    from ._auto import uninstall as _uninstall
    return _uninstall()


def track(client, **kwargs):
    """Wrap an LLM client to auto-track model/provider on every API call.

    Supported: OpenAI, Anthropic, Mistral, Google GenerativeAI.
    For OpenAI-compatible APIs (Groq, Together), pass provider= to override.

    Usage::

        client = akf.track(openai.OpenAI())
        response = client.chat.completions.create(model="gpt-4o", ...)
        unit = akf.create("claim", confidence=0.95)
        # unit.origin.model == "gpt-4o" — automatic
    """
    from .tracking import track as _track
    return _track(client, **kwargs)


def get_last_model():
    """Return the last tracked LLM model/provider, or None."""
    from .tracking import get_last_model as _get
    return _get()


def get_tracking_history():
    """Return all tracked LLM calls in this thread."""
    from .tracking import get_tracking_history as _get
    return _get()


def clear_tracking():
    """Reset LLM tracking context."""
    from .tracking import clear_tracking as _clear
    _clear()


def read(filepath):
    """Read AKF trust metadata from any file.

    Extracts metadata and attempts to parse it as a full AKF model.

    Args:
        filepath: Path to any supported file.

    Returns:
        AKF model if parseable, raw metadata dict otherwise, or None.
    """
    from .universal import extract as _extract

    meta = _extract(filepath)
    if meta is None:
        return None

    # Try to parse as full AKF model
    try:
        return AKF.model_validate(meta)
    except Exception:
        return meta


__version__ = "1.1.0"
__all__ = [
    # Models
    "AKF",
    "AKFBuilder",
    "AKFTransformer",
    "AUTHORITY_WEIGHTS",
    "AuditResult",
    "Claim",
    "Evidence",
    "Fidelity",
    "KnowledgeBase",
    "ProvHop",
    "SecurityScore",
    "TrustLevel",
    "TrustResult",
    "ValidationResult",
    "Calibration",
    # v1.1 models
    "Origin",
    "GenerationParams",
    "MadeBy",
    "Review",
    "SourceDetail",
    "ReasoningChain",
    "Annotation",
    "Freshness",
    "CostMetadata",
    "AgentProfile",
    # Core
    "add_hop",
    "can_share_external",
    "compute_all",
    "compute_integrity_hash",
    "create",
    "create_multi",
    "effective_trust",
    "format_tree",
    "models_used",
    "inherit_label",
    "load",
    "loads",
    "save",
    "validate",
    "validate_inheritance",
    # Trust extras
    "explain_trust",
    "calibrated_trust",
    "resolve_conflict",
    "trust_summary",
    "is_expired",
    "freshness_status",
    # Security extras
    "check_access",
    "compute_security_hash",
    "detect_laundering",
    "purview_signals",
    "redaction_report",
    "security_score",
    "SecurityReport",
    "full_report",
    "verify_trust_anchor",
    # Agent
    "consume",
    "derive",
    "detect",
    "from_tool_call",
    "generation_prompt",
    "response_schema",
    "to_context",
    "validate_output",
    # Compliance
    "audit",
    "audit_trail",
    "check_explainability",
    "check_fairness",
    "check_regulation",
    "continuous_audit",
    "export_audit",
    "verify_human_oversight",
    # Streaming
    "AKFStream",
    "StreamSession",
    "collect_stream",
    "iter_stream",
    "stream_claim",
    "stream_end",
    "stream_start",
    # Detection classes
    "DetectionReport",
    "DetectionResult",
    "detect_ai_without_review",
    "detect_classification_downgrade",
    "detect_excessive_ai_concentration",
    "detect_hallucination_risk",
    "detect_knowledge_laundering",
    "detect_provenance_gap",
    "detect_stale_claims",
    "detect_trust_below_threshold",
    "detect_trust_degradation_chain",
    "detect_ungrounded_claims",
    "run_all_detections",
    # Convenience
    "stream",
    # i18n
    "translate",
    # View
    "executive_summary",
    "show",
    "to_html",
    "to_markdown",
    # Data
    "filter_claims",
    "load_dataset",
    "merge",
    "quality_report",
    # Report
    "enterprise_report",
    "EnterpriseReport",
    "FileReport",
    "register_renderer",
    "RENDERERS",
    # Stamp & Git
    "stamp",
    "stamp_file",
    "stamp_commit",
    "read_commit",
    "trust_log",
    # Signing
    "keygen",
    "sign_unit",
    "verify_signature",
    # Auto-tracking
    "install",
    "uninstall",
    # Tracking
    "track",
    "get_last_model",
    "get_tracking_history",
    "clear_tracking",
    # Universal format layer
    "ConvertResult",
    "convert_directory",
    "embed",
    "extract",
    "info",
    "init",
    "is_enriched",
    "read",
    "scan",
]
