"""Tests for AKF compliance module."""

import pytest
from akf.builder import AKFBuilder
from akf.compliance import audit, audit_trail, check_regulation, verify_human_oversight
from akf.core import create


class TestAudit:
    def test_minimal_unit(self):
        unit = create("test", confidence=0.5)
        result = audit(unit)
        assert isinstance(result.score, float)
        assert 0.0 <= result.score <= 1.0
        assert len(result.checks) > 0

    def test_full_unit_scores_high(self):
        unit = (
            AKFBuilder()
            .by("sarah@test.com")
            .label("confidential")
            .claim("Revenue $4.2B", 0.98, source="SEC", authority_tier=1, verified=True)
            .build()
        )
        result = audit(unit)
        assert result.score >= 0.5
        assert result.compliant or len(result.recommendations) > 0

    def test_bool_conversion(self):
        unit = create("test", confidence=0.5)
        result = audit(unit)
        assert isinstance(bool(result), bool)


class TestCheckRegulation:
    def test_eu_ai_act(self):
        unit = (
            AKFBuilder()
            .by("sarah@test.com")
            .claim("AI claim", 0.7, ai_generated=True, source="model")
            .build()
        )
        result = check_regulation(unit, "eu_ai_act")
        assert result.regulation == "eu_ai_act"
        assert len(result.checks) > 0

    def test_sox(self):
        unit = (
            AKFBuilder()
            .by("user@test.com")
            .label("confidential")
            .claim("Financial data", 0.9, source="SEC")
            .build()
        )
        result = check_regulation(unit, "sox")
        assert result.regulation == "sox"

    def test_hipaa(self):
        unit = create("PHI data", confidence=0.9, source="hospital")
        result = check_regulation(unit, "hipaa")
        assert result.regulation == "hipaa"

    def test_gdpr(self):
        unit = create("User data", confidence=0.8)
        result = check_regulation(unit, "gdpr")
        assert result.regulation == "gdpr"

    def test_nist_ai(self):
        unit = (
            AKFBuilder()
            .by("user@test.com")
            .claim("AI output", 0.7, source="model", ai_generated=True)
            .build()
        )
        result = check_regulation(unit, "nist_ai")
        assert result.regulation == "nist_ai"

    def test_unknown_regulation(self):
        unit = create("test", confidence=0.5)
        result = check_regulation(unit, "unknown_reg")
        assert not result.compliant


class TestAuditTrail:
    def test_text_format(self):
        unit = (
            AKFBuilder()
            .by("sarah@test.com")
            .claim("test", 0.5)
            .build()
        )
        trail = audit_trail(unit, format="text")
        assert "Audit Trail" in trail
        assert "sarah@test.com" in trail

    def test_markdown_format(self):
        unit = (
            AKFBuilder()
            .by("sarah@test.com")
            .claim("test", 0.5)
            .build()
        )
        trail = audit_trail(unit, format="markdown")
        assert "# Audit Trail" in trail


class TestVerifyHumanOversight:
    def test_with_review(self):
        from akf.provenance import add_hop
        unit = (
            AKFBuilder()
            .by("sarah@test.com")
            .claim("test", 0.5, verified=True)
            .build()
        )
        unit = add_hop(unit, by="sarah@test.com", action="reviewed")
        result = verify_human_oversight(unit)
        assert result["has_human_oversight"] is True
        assert "sarah@test.com" in result["human_actors"]

    def test_without_review(self):
        unit = create("test", confidence=0.5)
        result = verify_human_oversight(unit)
        assert isinstance(result["has_human_oversight"], bool)
