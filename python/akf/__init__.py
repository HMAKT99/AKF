"""AKF — Agent Knowledge Format v1.0.

Lightweight, LLM-native file format for structured knowledge exchange
with built-in trust, provenance, and security metadata.

Usage:
    import akf

    # Create
    unit = akf.create("Revenue $4.2B", t=0.98)
    unit.save("out.akf")

    # Load
    unit = akf.load("out.akf")

    # Validate
    result = akf.validate("out.akf")
"""

from .models import AKF, Claim, Fidelity, ProvHop
from .core import create, create_multi, load, loads, validate
from .builder import AKFBuilder
from .trust import effective_trust, compute_all, TrustResult, AUTHORITY_WEIGHTS
from .provenance import add_hop, format_tree, compute_integrity_hash
from .security import validate_inheritance, can_share_external, inherit_label
from .transform import AKFTransformer

__version__ = "1.0.0"
__all__ = [
    "AKF",
    "AKFBuilder",
    "AKFTransformer",
    "AUTHORITY_WEIGHTS",
    "Claim",
    "Fidelity",
    "ProvHop",
    "TrustResult",
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
]
