"""AKF v1.0 — Security classification and inheritance."""

from __future__ import annotations

from .models import AKF

HIERARCHY: dict[str, int] = {
    "public": 0,
    "internal": 1,
    "confidential": 2,
    "highly-confidential": 3,
    "restricted": 4,
}


def label_rank(label: str | None) -> int:
    """Return numeric rank for a classification label. Defaults to 0 (public)."""
    if label is None:
        return 0
    return HIERARCHY.get(label, 0)


def validate_inheritance(parent: AKF, child: AKF) -> bool:
    """Check child label >= parent label when parent.inherit is true.

    Returns True if inheritance is valid, False if child is less restrictive.
    """
    if parent.inherit is False:
        return True  # No inheritance constraint
    return label_rank(child.label) >= label_rank(parent.label)


def can_share_external(unit: AKF) -> bool:
    """Check if the unit can be shared externally."""
    if unit.ext is True:
        return True
    if unit.label in ("confidential", "highly-confidential", "restricted"):
        return False
    return unit.ext is not False and label_rank(unit.label) <= HIERARCHY["internal"]


def inherit_label(parent: AKF) -> dict:
    """Return security fields to copy to a derived .akf."""
    fields: dict = {}
    if parent.inherit is not False and parent.label:
        fields["label"] = parent.label
        fields["inherit"] = parent.inherit
    if parent.ext is not None:
        fields["ext"] = parent.ext
    return fields
