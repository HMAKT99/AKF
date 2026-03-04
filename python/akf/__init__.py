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

from .models import AKF, Claim, Evidence, Fidelity, ProvHop
from .core import create, create_multi, load, loads, validate, ValidationResult
from .universal import ConvertResult
from .builder import AKFBuilder
from .trust import effective_trust, compute_all, explain_trust, TrustResult, TrustLevel, AUTHORITY_WEIGHTS
from .provenance import add_hop, format_tree, compute_integrity_hash
from .security import validate_inheritance, can_share_external, inherit_label, security_score, purview_signals, detect_laundering, SecurityScore
from .transform import AKFTransformer
from .agent import (
    consume, derive, generation_prompt, validate_output,
    response_schema, from_tool_call, to_context, detect,
)
from .compliance import audit, check_regulation, audit_trail, verify_human_oversight, AuditResult
from .view import show, to_html, to_markdown, executive_summary
from .data import load_dataset, quality_report, merge, filter_claims
from .knowledge_base import KnowledgeBase
from .stamp import stamp
from .git_ops import stamp_commit, read_commit, trust_log

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

__version__ = "1.0.0"
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
    # Security extras
    "detect_laundering",
    "purview_signals",
    "security_score",
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
    "check_regulation",
    "verify_human_oversight",
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
    "is_enriched",
    "scan",
]
