"""AKF v1.0 -- HTML format handler.

Embeds AKF metadata as a JSON-LD ``<script type="application/akf+json">`` tag.
Renders claims as ``<p>`` elements with ``data-akf-*`` attributes.

No external dependencies -- uses stdlib json and re modules only.
"""

import json
import re
from typing import Any, Dict, List, Optional

from .base import AKFFormatHandler, ScanReport


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_AKF_SCRIPT_RE = re.compile(
    r'<script\s+type="application/akf\+json"\s*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)

_HEAD_CLOSE_RE = re.compile(r"</head>", re.IGNORECASE)


# ---------------------------------------------------------------------------
# HTMLHandler
# ---------------------------------------------------------------------------


class HTMLHandler(AKFFormatHandler):
    """HTML format handler -- JSON-LD script tag + data attributes."""

    FORMAT_NAME = "HTML"
    EXTENSIONS = [".html", ".htm"]
    MODE = "embedded"
    MECHANISM = "JSON-LD script tag"
    DEPENDENCIES: List[str] = []

    def embed(self, filepath: str, metadata: dict) -> None:
        """Embed AKF metadata into an HTML file via a script tag."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        akf_json = json.dumps(metadata, separators=(",", ":"), ensure_ascii=False)
        # Escape </script> sequences to prevent XSS — standard practice for inline JSON
        akf_json = akf_json.replace("</", "<\\/")
        script_tag = '<script type="application/akf+json">{}</script>'.format(akf_json)

        # If an AKF script tag already exists, replace it
        if _AKF_SCRIPT_RE.search(content):
            content = _AKF_SCRIPT_RE.sub(script_tag, content, count=1)
        elif _HEAD_CLOSE_RE.search(content):
            # Insert just before </head>
            content = _HEAD_CLOSE_RE.sub(
                script_tag + "\n</head>", content, count=1
            )
        else:
            # No </head> -- prepend to file
            content = script_tag + "\n" + content

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def extract(self, filepath: str) -> Optional[dict]:
        """Extract AKF metadata from an HTML file."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        m = _AKF_SCRIPT_RE.search(content)
        if m:
            try:
                return json.loads(m.group(1).strip())  # type: ignore[no-any-return]
            except json.JSONDecodeError:
                pass
        return None

    def is_enriched(self, filepath: str) -> bool:
        """Return True if the file contains AKF metadata."""
        return self.extract(filepath) is not None


# ---------------------------------------------------------------------------
# Trust-level helpers
# ---------------------------------------------------------------------------


def _trust_class(trust: float) -> str:
    """Return the CSS class for a given trust score."""
    if trust >= 0.7:
        return "akf-trust-high"
    elif trust >= 0.4:
        return "akf-trust-medium"
    else:
        return "akf-trust-low"


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def render(akf_unit: dict, template: str = "default") -> str:
    """Render an AKF unit as HTML paragraphs with data attributes.

    Parameters
    ----------
    akf_unit : dict
        A dict with at minimum ``claims`` (list of claim dicts).
    template : str
        Reserved for future template support.  Currently ignored.

    Returns
    -------
    str
        HTML fragment with annotated ``<p>`` elements.
    """
    parts: List[str] = []
    claims = akf_unit.get("claims", [])

    for claim in claims:
        trust = claim.get("t", 0.0)
        source = claim.get("src", "")
        verified = claim.get("ver", False)
        tier = claim.get("tier", "")
        is_ai = claim.get("ai", False)
        text = claim.get("c", "")

        css_classes: List[str] = [_trust_class(trust)]
        if is_ai:
            css_classes.append("akf-ai")
        if verified:
            css_classes.append("akf-verified")

        attrs: List[str] = [
            'data-akf-trust="{:.2f}"'.format(trust),
        ]
        if source:
            attrs.append('data-akf-source="{}"'.format(_escape_attr(source)))
        attrs.append('data-akf-verified="{}"'.format(str(verified).lower()))
        if tier:
            attrs.append('data-akf-tier="{}"'.format(tier))
        attrs.append('class="{}"'.format(" ".join(css_classes)))

        p = "<p {}>{}</p>".format(" ".join(attrs), _escape_html(text))
        parts.append(p)

    return "\n".join(parts)


def _escape_html(text: str) -> str:
    """Minimal HTML escaping."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _escape_attr(text: str) -> str:
    """Escape for use inside double-quoted HTML attributes."""
    return (
        text.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ---------------------------------------------------------------------------
# Default CSS
# ---------------------------------------------------------------------------


def default_css() -> str:
    """Return a CSS string with styles for AKF trust-level classes.

    Returns
    -------
    str
        CSS stylesheet text.
    """
    return """\
.akf-trust-high {
  border-left: 4px solid #22c55e;
  padding-left: 0.75em;
  background: rgba(34, 197, 94, 0.05);
}
.akf-trust-medium {
  border-left: 4px solid #eab308;
  padding-left: 0.75em;
  background: rgba(234, 179, 8, 0.05);
}
.akf-trust-low {
  border-left: 4px solid #ef4444;
  padding-left: 0.75em;
  background: rgba(239, 68, 68, 0.05);
}
.akf-ai {
  font-style: italic;
}
.akf-ai::after {
  content: " [AI]";
  font-size: 0.75em;
  color: #6b7280;
}
.akf-verified::before {
  content: "\\2713 ";
  color: #22c55e;
}"""


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

_handler = HTMLHandler()
embed = _handler.embed
extract = _handler.extract
is_enriched = _handler.is_enriched
scan = _handler.scan
auto_enrich = _handler.auto_enrich
