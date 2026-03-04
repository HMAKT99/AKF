"""AKF v1.0 — Presets, decay constants, and templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import AKF, Claim
from .builder import AKFBuilder


DECAY_PRESETS: dict[str, float] = {
    "realtime": 0.001,
    "daily": 1,
    "weekly": 7,
    "monthly": 30,
    "quarterly": 90,
    "annual": 365,
    "legal": 1825,
    "scientific": 3650,
    "permanent": 365000,
}


@dataclass
class Template:
    """A pre-configured AKF template."""

    name: str
    label: str | None = None
    inherit: bool | None = None
    ext: bool | None = None
    ttl: int | None = None
    decay: int | None = None
    ai_default: bool = False
    defaults: dict[str, Any] = field(default_factory=dict)

    def create(self, claims: list[dict], by: str | None = None, **kwargs) -> AKF:
        """Create an AKF unit from this template."""
        builder = AKFBuilder()
        if by:
            builder.by(by)
        if self.label:
            builder.label(self.label)
        if self.inherit is not None:
            builder.inherit(self.inherit)
        if self.ext is not None:
            builder.ext(self.ext)
        if self.ttl is not None:
            builder.ttl(self.ttl)

        for c in claims:
            claim_kwargs = {**self.defaults, **c}
            if self.decay and "decay" not in claim_kwargs and "decay_half_life" not in claim_kwargs:
                claim_kwargs["decay_half_life"] = self.decay
            if self.ai_default and "ai" not in claim_kwargs and "ai_generated" not in claim_kwargs:
                claim_kwargs["ai_generated"] = True
            # Support both compact and descriptive content/confidence keys
            content = claim_kwargs.pop("content", None) or claim_kwargs.pop("c", None)
            trust = claim_kwargs.pop("confidence", None) or claim_kwargs.pop("t", None)
            if content is None or trust is None:
                raise ValueError("Each claim must have content/c and confidence/t")
            builder.claim(content, trust, **claim_kwargs)

        return builder.build()


TEMPLATES: dict[str, Template] = {
    "financial_report": Template(
        name="financial_report",
        label="confidential",
        inherit=True,
        decay=90,
    ),
    "research_brief": Template(
        name="research_brief",
        label="internal",
        decay=30,
    ),
    "public_knowledge": Template(
        name="public_knowledge",
        label="public",
        ext=True,
    ),
    "legal_document": Template(
        name="legal_document",
        label="restricted",
        inherit=True,
        ttl=2555,
        decay=1825,
    ),
    "ai_output": Template(
        name="ai_output",
        ai_default=True,
    ),
    "meeting_notes": Template(
        name="meeting_notes",
        label="internal",
        decay=30,
        defaults={"authority_tier": 4},
    ),
    "incident_report": Template(
        name="incident_report",
        label="confidential",
        inherit=True,
        decay=365,
        defaults={"authority_tier": 2},
    ),
    "research_paper": Template(
        name="research_paper",
        label="internal",
        decay=3650,
        defaults={"authority_tier": 1},
    ),
    "press_release": Template(
        name="press_release",
        label="public",
        ext=True,
        defaults={"authority_tier": 2},
    ),
}


def register(name: str, template: Template) -> None:
    """Register a custom template."""
    TEMPLATES[name] = template


def get_template(name: str) -> Template:
    """Get a template by name. Raises KeyError if not found."""
    if name not in TEMPLATES:
        raise KeyError(f"Unknown template: {name}. Available: {', '.join(TEMPLATES.keys())}")
    return TEMPLATES[name]


def list_templates() -> list[str]:
    """Return list of available template names."""
    return list(TEMPLATES.keys())
