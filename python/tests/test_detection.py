"""Tests for all 10 AKF detection classes and aggregate detection."""

import pytest

from akf.builder import AKFBuilder
from akf.models import AKF, Evidence, ProvHop, ReasoningChain
from akf.provenance import add_hop
from akf.detection import (
    DetectionReport,
    DetectionResult,
    detect_ai_without_review,
    detect_classification_downgrade,
    detect_excessive_ai_concentration,
    detect_hallucination_risk,
    detect_knowledge_laundering,
    detect_provenance_gap,
    detect_stale_claims,
    detect_trust_below_threshold,
    detect_trust_degradation_chain,
    detect_ungrounded_claims,
    run_all_detections,
)


@pytest.fixture
def clean_unit():
    """A well-formed unit that should pass all detections."""
    unit = (
        AKFBuilder()
        .by("analyst@corp.com")
        .label("internal")
        .claim(
            "Revenue $4.2B",
            0.98,
            source="SEC 10-Q",
            authority_tier=1,
            verified=True,
        )
        .build()
    )
    return add_hop(unit, by="analyst@corp.com", action="created")


@pytest.fixture
def risky_unit():
    """A unit that should trigger many detections."""
    return (
        AKFBuilder()
        .label("public")
        .claim(
            "AI predicted growth of 50%",
            0.3,
            authority_tier=5,
            ai_generated=True,
        )
        .build()
    )


# ---------------------------------------------------------------------------
# Detection Class 1: AI Without Review
# ---------------------------------------------------------------------------

class TestAIWithoutReview:
    def test_triggered(self, risky_unit):
        result = detect_ai_without_review(risky_unit)
        assert result.triggered is True
        assert result.severity == "high"

    def test_clean(self, clean_unit):
        result = detect_ai_without_review(clean_unit)
        assert result.triggered is False


# ---------------------------------------------------------------------------
# Detection Class 2: Trust Below Threshold
# ---------------------------------------------------------------------------

class TestTrustBelowThreshold:
    def test_triggered(self, risky_unit):
        result = detect_trust_below_threshold(risky_unit, threshold=0.7)
        assert result.triggered is True

    def test_clean(self, clean_unit):
        result = detect_trust_below_threshold(clean_unit, threshold=0.7)
        assert result.triggered is False


# ---------------------------------------------------------------------------
# Detection Class 3: Hallucination Risk
# ---------------------------------------------------------------------------

class TestHallucinationRisk:
    def test_triggered(self, risky_unit):
        result = detect_hallucination_risk(risky_unit)
        assert result.triggered is True
        assert result.severity == "critical"

    def test_clean_ai_with_evidence(self):
        unit = (
            AKFBuilder()
            .label("internal")
            .claim(
                "Market size $10B",
                0.85,
                source="Gartner Report",
                authority_tier=2,
                ai_generated=True,
                evidence=[Evidence(type="document", detail="gartner-2025.pdf")],
            )
            .build()
        )
        result = detect_hallucination_risk(unit)
        assert result.triggered is False


# ---------------------------------------------------------------------------
# Detection Class 4: Knowledge Laundering
# ---------------------------------------------------------------------------

class TestKnowledgeLaundering:
    def test_triggered(self, risky_unit):
        result = detect_knowledge_laundering(risky_unit)
        assert result.triggered is True
        assert result.severity == "critical"

    def test_clean(self, clean_unit):
        result = detect_knowledge_laundering(clean_unit)
        assert result.triggered is False


# ---------------------------------------------------------------------------
# Detection Class 5: Classification Downgrade
# ---------------------------------------------------------------------------

class TestClassificationDowngrade:
    def test_triggered_inherit_false(self):
        unit = (
            AKFBuilder()
            .label("public")
            .claim("Safe data", 0.9)
            .build()
        )
        # Manually set inherit_classification to False
        unit = unit.model_copy(update={"inherit_classification": False})
        result = detect_classification_downgrade(unit)
        assert result.triggered is True

    def test_clean(self, clean_unit):
        result = detect_classification_downgrade(clean_unit)
        assert result.triggered is False


# ---------------------------------------------------------------------------
# Detection Class 6: Stale Claims
# ---------------------------------------------------------------------------

class TestStaleClaims:
    def test_triggered_ttl_expired(self):
        from datetime import datetime, timedelta, timezone
        old_time = (datetime.now(timezone.utc) - timedelta(hours=100)).isoformat()
        unit = (
            AKFBuilder()
            .label("internal")
            .claim("Old data", 0.9)
            .build()
        )
        unit = unit.model_copy(update={"created": old_time, "ttl": 1})
        result = detect_stale_claims(unit)
        assert result.triggered is True

    def test_clean(self, clean_unit):
        result = detect_stale_claims(clean_unit)
        assert result.triggered is False


# ---------------------------------------------------------------------------
# Detection Class 7: Ungrounded Claims
# ---------------------------------------------------------------------------

class TestUngroundedClaims:
    def test_triggered(self, risky_unit):
        result = detect_ungrounded_claims(risky_unit)
        assert result.triggered is True

    def test_clean(self):
        unit = (
            AKFBuilder()
            .label("internal")
            .claim(
                "Verified fact",
                0.95,
                source="Official Report",
                ai_generated=True,
                evidence=[Evidence(type="document", detail="report.pdf")],
                reasoning=ReasoningChain(steps=["Step 1", "Step 2"], conclusion="Valid"),
            )
            .build()
        )
        result = detect_ungrounded_claims(unit)
        assert result.triggered is False


# ---------------------------------------------------------------------------
# Detection Class 8: Trust Degradation Chain
# ---------------------------------------------------------------------------

class TestTrustDegradationChain:
    def test_triggered(self):
        unit = (
            AKFBuilder()
            .label("internal")
            .claim("Data point", 0.9)
            .build()
        )
        unit = add_hop(unit, by="user-a", action="created")
        unit = add_hop(unit, by="user-b", action="transformed", penalty=-0.15)
        unit = add_hop(unit, by="user-c", action="transformed", penalty=-0.15)
        result = detect_trust_degradation_chain(unit)
        assert result.triggered is True

    def test_clean_no_provenance(self):
        unit = AKFBuilder().label("internal").claim("Simple fact", 0.9).build()
        result = detect_trust_degradation_chain(unit)
        assert result.triggered is False


# ---------------------------------------------------------------------------
# Detection Class 9: Excessive AI Concentration
# ---------------------------------------------------------------------------

class TestExcessiveAIConcentration:
    def test_triggered(self):
        unit = (
            AKFBuilder()
            .label("internal")
            .claim("AI fact 1", 0.8, ai_generated=True)
            .claim("AI fact 2", 0.7, ai_generated=True)
            .claim("AI fact 3", 0.6, ai_generated=True)
            .claim("AI fact 4", 0.5, ai_generated=True)
            .claim("AI fact 5", 0.4, ai_generated=True)
            .build()
        )
        result = detect_excessive_ai_concentration(unit, max_ai_ratio=0.8)
        assert result.triggered is True

    def test_clean(self):
        unit = (
            AKFBuilder()
            .label("internal")
            .claim("Human fact", 0.95, verified=True)
            .claim("AI fact", 0.8, ai_generated=True)
            .claim("Human fact 2", 0.9)
            .claim("Human fact 3", 0.85)
            .build()
        )
        result = detect_excessive_ai_concentration(unit, max_ai_ratio=0.8)
        assert result.triggered is False


# ---------------------------------------------------------------------------
# Detection Class 10: Provenance Gap
# ---------------------------------------------------------------------------

class TestProvenanceGap:
    def test_triggered_no_provenance(self, risky_unit):
        result = detect_provenance_gap(risky_unit)
        assert result.triggered is True
        assert any("untraceable" in f.lower() or "no provenance" in f.lower()
                    for f in result.findings)

    def test_clean(self, clean_unit):
        result = detect_provenance_gap(clean_unit)
        assert result.triggered is False


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

class TestRunAllDetections:
    def test_risky(self, risky_unit):
        report = run_all_detections(risky_unit)
        assert isinstance(report, DetectionReport)
        assert report.triggered_count > 0
        assert report.clean is False

    def test_clean(self, clean_unit):
        report = run_all_detections(clean_unit)
        assert isinstance(report, DetectionReport)
        # A clean unit may still trigger provenance gap since it has only 1 hop
        # but should have 0 critical issues
        assert report.critical_count == 0


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class TestDataStructures:
    def test_result_to_dict(self):
        r = DetectionResult(
            detection_class="test",
            triggered=True,
            severity="high",
            findings=["finding 1"],
            affected_claims=["c1"],
            recommendation="fix it",
        )
        d = r.to_dict()
        assert d["detection_class"] == "test"
        assert d["triggered"] is True
        assert d["severity"] == "high"
        assert len(d["findings"]) == 1

    def test_report_to_dict(self):
        r = DetectionResult(
            detection_class="test",
            triggered=True,
            severity="high",
        )
        report = DetectionReport(
            results=[r],
            triggered_count=1,
            critical_count=0,
            high_count=1,
        )
        d = report.to_dict()
        assert d["triggered_count"] == 1
        assert d["clean"] is False
        assert len(d["results"]) == 1

    def test_clean_property(self):
        report = DetectionReport(triggered_count=0)
        assert report.clean is True
        report2 = DetectionReport(triggered_count=1)
        assert report2.clean is False
