"""AKF v1.1 — Internationalization skeleton.

Minimal i18n support for audit messages and trust labels.
"""

from __future__ import annotations

from typing import Optional

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        # Audit check names
        "provenance_present": "Provenance chain present",
        "integrity_hash": "Integrity hash computed",
        "classification_set": "Security classification set",
        "all_claims_sourced": "All claims have source attribution",
        "ai_claims_labeled": "AI-generated claims labeled",
        "ai_risk_described": "AI risk descriptions provided",
        "valid_structure": "Valid AKF structure",
        "origin_tracking": "AI origin tracking present",
        "review_present": "Reviews present",
        "freshness_valid": "Claim freshness valid",
        # Trust levels
        "trust_accept": "Claim meets trust threshold for use",
        "trust_low": "Claim has low trust \u2014 use with caution",
        "trust_reject": "Claim does not meet minimum trust \u2014 consider discarding",
        # Trust breakdown
        "confidence": "Base confidence",
        "authority": "Authority weight",
        "origin_weight": "Origin weight",
        "decay": "Temporal decay",
        "penalty": "Transform penalty",
        "grounding_bonus": "Evidence grounding bonus",
        "review_bonus": "Review bonus",
        # Recommendations
        "rec_add_provenance": "Add provenance to track data lineage",
        "rec_add_hash": "Compute integrity hash for tamper detection",
        "rec_set_classification": "Set security classification",
        "rec_add_sources": "Add source attribution to all claims",
        "rec_add_risk": "Add risk descriptions to AI-generated speculative claims",
        "rec_add_origin": "Add origin fields to AI-generated claims for transparency",
        "rec_add_reviews": "Add reviews for human oversight verification",
        "rec_refresh_claims": "Refresh or remove expired claims",
        # Security grades
        "grade_a": "Excellent security posture",
        "grade_b": "Good security posture",
        "grade_c": "Fair security posture \u2014 improvements needed",
        "grade_d": "Poor security posture \u2014 significant gaps",
        "grade_f": "Critical security gaps \u2014 immediate action required",
        # Regulation names
        "eu_ai_act": "EU AI Act",
        "sox": "Sarbanes-Oxley (SOX)",
        "hipaa": "HIPAA",
        "gdpr": "GDPR",
        "nist_ai": "NIST AI RMF",
        "iso_42001": "ISO 42001",
        # Status
        "compliant": "Compliant",
        "non_compliant": "Non-compliant",
    },
}


def t(key: str, locale: str = "en") -> str:
    """Translate a message key to the specified locale.

    Falls back to English if the locale or key is not found.
    Falls back to the key itself if not found in English.

    Args:
        key: Message key.
        locale: Locale code (default "en").

    Returns:
        Translated string.
    """
    messages = MESSAGES.get(locale, MESSAGES.get("en", {}))
    result = messages.get(key)
    if result is not None:
        return result
    # Fallback to English
    if locale != "en":
        en_messages = MESSAGES.get("en", {})
        result = en_messages.get(key)
        if result is not None:
            return result
    # Final fallback: return the key
    return key
