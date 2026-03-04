"""AKF — Agent Knowledge Format v1.0.

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
)
from .core import create, create_multi, load, loads, validate, ValidationResult
from .universal import ConvertResult
from .builder import AKFBuilder
from .trust import (
    effective_trust, compute_all, explain_trust, TrustResult, TrustLevel,
    AUTHORITY_WEIGHTS, calibrated_trust, resolve_conflict, trust_summary,
)
from .provenance import add_hop, format_tree, compute_integrity_hash
from .security import (
    validate_inheritance, can_share_external, inherit_label, security_score,
    purview_signals, detect_laundering, SecurityScore,
    check_access, verify_trust_anchor, redaction_report, compute_security_hash,
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
from .knowledge_base import KnowledgeBase
from .stamp import stamp
from .git_ops import stamp_commit, read_commit, trust_log
from .streaming import StreamSession, stream_start, stream_claim, stream_end, collect_stream, iter_stream
from .i18n import t as translate

# Universal format layer — lazy imports to avoid optional dependency issues
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
    "inherit_label",
    "load",
    "loads",
    "validate",
    "validate_inheritance",
    # Trust extras
    "explain_trust",
    "calibrated_trust",
    "resolve_conflict",
    "trust_summary",
    # Security extras
    "check_access",
    "compute_security_hash",
    "detect_laundering",
    "purview_signals",
    "redaction_report",
    "security_score",
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
    "StreamSession",
    "collect_stream",
    "iter_stream",
    "stream_claim",
    "stream_end",
    "stream_start",
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
    # Stamp & Git
    "stamp",
    "stamp_commit",
    "read_commit",
    "trust_log",
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
