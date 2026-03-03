"""AKF — Agent Knowledge Format v1.0.

The trust metadata standard for every file AI touches.

Usage:
    import akf

    # Standalone .akf
    unit = akf.create("Revenue $4.2B", t=0.98)
    unit.save("out.akf")

    # Universal: embed into any format
    akf.embed("report.docx", claims=[...], classification="confidential")
    akf.extract("report.docx")
    akf.scan("report.docx")
    akf.info("report.docx")
"""

from .models import AKF, Claim, Fidelity, ProvHop
from .core import create, create_multi, load, loads, validate
from .builder import AKFBuilder
from .trust import effective_trust, compute_all, TrustResult, AUTHORITY_WEIGHTS
from .provenance import add_hop, format_tree, compute_integrity_hash
from .security import validate_inheritance, can_share_external, inherit_label
from .transform import AKFTransformer

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

__version__ = "1.0.0"
__all__ = [
    # Models
    "AKF",
    "AKFBuilder",
    "AKFTransformer",
    "AUTHORITY_WEIGHTS",
    "Claim",
    "Fidelity",
    "ProvHop",
    "TrustResult",
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
    # Universal format layer
    "embed",
    "extract",
    "info",
    "is_enriched",
    "scan",
]
