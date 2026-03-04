"""Tests for AKF security."""

import pytest
from akf.builder import AKFBuilder
from akf.core import create
from akf.models import AKF, Claim
from akf.security import (
    can_share_external,
    detect_laundering,
    inherit_label,
    label_rank,
    purview_signals,
    security_score,
    validate_inheritance,
    HIERARCHY,
)


class TestLabelRank:
    def test_all_labels(self):
        assert label_rank("public") == 0
        assert label_rank("internal") == 1
        assert label_rank("confidential") == 2
        assert label_rank("highly-confidential") == 3
        assert label_rank("restricted") == 4

    def test_none_defaults_public(self):
        assert label_rank(None) == 0

    def test_hierarchy_order(self):
        labels = sorted(HIERARCHY.keys(), key=lambda x: HIERARCHY[x])
        assert labels == ["public", "internal", "confidential", "highly-confidential", "restricted"]


class TestValidateInheritance:
    def test_valid_same_level(self):
        parent = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="confidential", inherit_classification=True)
        child = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="confidential")
        assert validate_inheritance(parent, child) is True

    def test_valid_higher_level(self):
        parent = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="confidential", inherit_classification=True)
        child = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="restricted")
        assert validate_inheritance(parent, child) is True

    def test_invalid_lower_level(self):
        parent = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="confidential", inherit_classification=True)
        child = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="public")
        assert validate_inheritance(parent, child) is False

    def test_no_inherit_skips_check(self):
        parent = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="confidential", inherit_classification=False)
        child = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="public")
        assert validate_inheritance(parent, child) is True

    def test_confidential_parent_internal_child_invalid(self):
        parent = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="confidential", inherit_classification=True)
        child = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="internal")
        assert validate_inheritance(parent, child) is False


class TestCanShareExternal:
    def test_public_can_share(self):
        unit = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="public")
        assert can_share_external(unit) is True

    def test_confidential_cannot_share(self):
        unit = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="confidential")
        assert can_share_external(unit) is False

    def test_restricted_cannot_share(self):
        unit = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="restricted")
        assert can_share_external(unit) is False

    def test_ext_true_overrides(self):
        unit = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="public", allow_external=True)
        assert can_share_external(unit) is True


class TestInheritLabel:
    def test_inherits_classification(self):
        parent = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="confidential", inherit_classification=True)
        fields = inherit_label(parent)
        assert fields["classification"] == "confidential"
        assert fields["inherit_classification"] is True

    def test_no_inherit_returns_empty(self):
        parent = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="confidential", inherit_classification=False)
        fields = inherit_label(parent)
        assert "classification" not in fields

    def test_inherits_ext(self):
        parent = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)], classification="public", allow_external=False)
        fields = inherit_label(parent)
        assert fields["allow_external"] is False


class TestSecurityScore:
    def test_full_unit_scores_high(self):
        unit = (
            AKFBuilder()
            .by("sarah@test.com")
            .label("confidential")
            .claim("Revenue", 0.98, source="SEC", authority_tier=1, verified=True)
            .build()
        )
        result = security_score(unit)
        assert result.score >= 6.0
        assert result.grade in ("A", "B")

    def test_minimal_unit_scores_low(self):
        unit = AKF(version="1.0", claims=[Claim(content="t", confidence=0.5)])
        result = security_score(unit)
        assert result.score < 5.0
        assert len(result.issues) > 0

    def test_grade_ranges(self):
        from akf.security import SecurityScore
        assert SecurityScore(score=9.0).grade == "A"
        assert SecurityScore(score=7.0).grade == "B"
        assert SecurityScore(score=5.0).grade == "C"
        assert SecurityScore(score=3.0).grade == "D"
        assert SecurityScore(score=1.0).grade == "F"


class TestPurviewSignals:
    def test_basic(self):
        unit = (
            AKFBuilder()
            .by("user@test.com")
            .label("confidential")
            .claim("test", 0.9, source="SEC", verified=True)
            .claim("AI output", 0.7, ai_generated=True)
            .build()
        )
        signals = purview_signals(unit)
        assert signals["sensitivity_label"] == "confidential"
        assert signals["sensitivity_rank"] == 2
        assert signals["claim_count"] == 2
        assert signals["ai_generated_count"] == 1
        assert signals["verified_count"] == 1
        assert "min_trust" in signals
        assert "max_trust" in signals
        assert "avg_trust" in signals


class TestDetectLaundering:
    def test_no_issues(self):
        unit = (
            AKFBuilder()
            .by("user@test.com")
            .label("confidential")
            .claim("test", 0.9, source="SEC", authority_tier=1)
            .build()
        )
        warnings = detect_laundering(unit)
        assert len(warnings) == 0

    def test_high_authority_in_public(self):
        unit = AKF(
            version="1.0",
            classification="public",
            claims=[Claim(content="secret", confidence=0.9, authority_tier=1)],
        )
        warnings = detect_laundering(unit)
        assert any("high-authority" in w for w in warnings)

    def test_ai_in_public_without_risk(self):
        unit = AKF(
            version="1.0",
            classification="public",
            claims=[Claim(content="AI output", confidence=0.7, ai_generated=True)],
        )
        warnings = detect_laundering(unit)
        assert any("AI-generated" in w for w in warnings)

    def test_external_on_confidential(self):
        unit = AKF(
            version="1.0",
            classification="confidential",
            allow_external=True,
            claims=[Claim(content="t", confidence=0.5)],
        )
        warnings = detect_laundering(unit)
        assert any("External sharing" in w for w in warnings)
