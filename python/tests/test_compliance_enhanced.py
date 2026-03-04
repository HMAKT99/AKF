"""Tests for v1.1 compliance enhancements: check_explainability, check_fairness,
export_audit, continuous_audit, iso_42001, enhanced audit checks.
"""

import json
import pytest
from akf.models import AKF, Claim, Origin, Review, ReasoningChain, Evidence, Freshness
from akf.compliance import (
    audit, check_regulation, check_explainability, check_fairness,
    export_audit, continuous_audit,
)


class TestEnhancedAudit:
    def test_audit_has_10_checks(self):
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        result = audit(unit)
        assert len(result.checks) == 10

    def test_origin_tracking_check(self):
        unit = AKF(version="1.0", claims=[
            Claim(content="AI claim", confidence=0.7, ai_generated=True,
                  origin=Origin(type="ai", model="test")),
        ])
        result = audit(unit)
        origin_check = next(c for c in result.checks if c["check"] == "origin_tracking")
        assert origin_check["passed"] is True

    def test_origin_tracking_fails(self):
        unit = AKF(version="1.0", claims=[
            Claim(content="AI claim", confidence=0.7, ai_generated=True),
        ])
        result = audit(unit)
        origin_check = next(c for c in result.checks if c["check"] == "origin_tracking")
        assert origin_check["passed"] is False

    def test_review_present_check(self):
        unit = AKF(version="1.0",
                   claims=[Claim(content="x", confidence=0.5)],
                   reviews=[Review(reviewer="mgr", verdict="approved")])
        result = audit(unit)
        review_check = next(c for c in result.checks if c["check"] == "review_present")
        assert review_check["passed"] is True

    def test_freshness_valid_check(self):
        unit = AKF(version="1.0", claims=[
            Claim(content="Fresh", confidence=0.9,
                  freshness=Freshness(valid_until="2099-12-31T23:59:59Z")),
        ])
        result = audit(unit)
        fresh_check = next(c for c in result.checks if c["check"] == "freshness_valid")
        assert fresh_check["passed"] is True

    def test_freshness_expired_check(self):
        unit = AKF(version="1.0", claims=[
            Claim(content="Stale", confidence=0.9,
                  freshness=Freshness(valid_until="2020-01-01T00:00:00Z")),
        ])
        result = audit(unit)
        fresh_check = next(c for c in result.checks if c["check"] == "freshness_valid")
        assert fresh_check["passed"] is False


class TestISO42001:
    def test_basic_iso42001(self):
        result = check_regulation(
            AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)]),
            "iso_42001",
        )
        assert result.regulation == "iso_42001"
        assert len(result.checks) == 4

    def test_iso42001_full_compliance(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(
                content="AI output",
                confidence=0.8,
                ai_generated=True,
                risk="low risk",
                origin=Origin(type="ai", model="test"),
                reasoning=ReasoningChain(steps=["step1"], conclusion="done"),
            )],
            prov=[{
                "hop": 0, "by": "admin@co.com",
                "do": "created", "at": "2024-01-01T00:00:00Z",
            }],
            integrity_hash="sha256:abc",
        )
        result = check_regulation(unit, "iso_42001")
        assert result.compliant is True
        assert result.score == 1.0


class TestCheckExplainability:
    def test_explainable_ai(self):
        unit = AKF(version="1.0", claims=[
            Claim(content="AI output", confidence=0.8, ai_generated=True,
                  origin=Origin(type="ai"),
                  reasoning=ReasoningChain(steps=["step1"], conclusion="done"),
                  risk="low risk"),
        ])
        result = check_explainability(unit)
        assert result.compliant is True

    def test_unexplainable_ai(self):
        unit = AKF(version="1.0", claims=[
            Claim(content="Black box", confidence=0.8, ai_generated=True),
        ])
        result = check_explainability(unit)
        assert result.compliant is False

    def test_no_ai_claims(self):
        unit = AKF(version="1.0", claims=[
            Claim(content="Human claim", confidence=0.9),
        ])
        result = check_explainability(unit)
        assert result.compliant is True


class TestCheckFairness:
    def test_diverse_sources(self):
        unit = AKF(version="1.0", claims=[
            Claim(content="A", confidence=0.9, source="source1"),
            Claim(content="B", confidence=0.8, source="source2"),
        ])
        result = check_fairness(unit)
        source_check = next(c for c in result.checks if c["check"] == "source_diversity")
        assert source_check["passed"] is True

    def test_single_source_dominance(self):
        unit = AKF(version="1.0", claims=[
            Claim(content="A", confidence=0.9, source="same"),
            Claim(content="B", confidence=0.8, source="same"),
            Claim(content="C", confidence=0.7, source="same"),
            Claim(content="D", confidence=0.6, source="same"),
            Claim(content="E", confidence=0.5, source="same"),
        ])
        result = check_fairness(unit)
        dom_check = next(c for c in result.checks if c["check"] == "no_source_dominance")
        assert dom_check["passed"] is False

    def test_ai_grounded(self):
        unit = AKF(version="1.0", claims=[
            Claim(content="AI", confidence=0.7, ai_generated=True,
                  evidence=[Evidence(type="test_pass", detail="ok")]),
        ])
        result = check_fairness(unit)
        ground_check = next(c for c in result.checks if c["check"] == "ai_claims_grounded")
        assert ground_check["passed"] is True


class TestExportAudit:
    def test_export_json(self):
        from akf.compliance import audit
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        result = audit(unit)
        exported = export_audit(result, format="json")
        data = json.loads(exported)
        assert "compliant" in data
        assert "score" in data
        assert "checks" in data

    def test_export_markdown(self):
        from akf.compliance import audit
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        result = audit(unit)
        exported = export_audit(result, format="markdown")
        assert "# Audit Report" in exported
        assert "COMPLIANT" in exported or "NON-COMPLIANT" in exported

    def test_export_csv(self):
        from akf.compliance import audit
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        result = audit(unit)
        exported = export_audit(result, format="csv")
        assert "check,passed" in exported
        lines = exported.strip().split("\n")
        assert len(lines) > 1  # header + checks


class TestContinuousAudit:
    def test_multiple_regulations(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="x", confidence=0.5, ai_generated=True)],
            classification="internal",
            prov=[{"hop": 0, "by": "admin@co.com", "do": "created", "at": "2024-01-01T00:00:00Z"}],
            integrity_hash="sha256:abc",
        )
        result = continuous_audit(unit, ["eu_ai_act", "sox", "gdpr"])
        assert "overall_compliant" in result
        assert "overall_score" in result
        assert "eu_ai_act" in result["results"]
        assert "sox" in result["results"]
        assert "gdpr" in result["results"]

    def test_empty_regulations(self):
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        result = continuous_audit(unit, [])
        assert result["overall_compliant"] is True
        assert result["overall_score"] == 0.0
