"""Tests for v1.1 trust enhancements: origin_weight, grounding_bonus,
review_bonus, chain_penalty, calibrated_trust, resolve_conflict, trust_summary.
"""

import pytest
from akf.models import AKF, Claim, Origin, Review, Evidence
from akf.trust import (
    effective_trust, calibrated_trust, resolve_conflict, trust_summary,
    ORIGIN_WEIGHTS, GROUNDING_BONUS, REVIEW_BONUS,
)


class TestOriginWeight:
    def test_human_origin_weight(self):
        c = Claim(content="Human claim", confidence=0.9, origin=Origin(type="human"))
        r = effective_trust(c)
        assert r.breakdown["origin_weight"] == 1.0

    def test_ai_origin_weight(self):
        c = Claim(content="AI claim", confidence=0.9, origin=Origin(type="ai"))
        r = effective_trust(c)
        assert r.breakdown["origin_weight"] == 0.7

    def test_ai_chain_origin_weight(self):
        c = Claim(content="Chain claim", confidence=0.9, origin=Origin(type="ai_chain"))
        r = effective_trust(c)
        assert r.breakdown["origin_weight"] == 0.5

    def test_ai_supervised_origin_weight(self):
        c = Claim(content="Supervised", confidence=0.9, origin=Origin(type="ai_supervised_by_human"))
        r = effective_trust(c)
        assert r.breakdown["origin_weight"] == 0.9

    def test_no_origin_default_weight(self):
        c = Claim(content="No origin", confidence=0.9)
        r = effective_trust(c)
        assert r.breakdown["origin_weight"] == 1.0

    def test_origin_affects_score(self):
        c_human = Claim(content="Human", confidence=0.9, origin=Origin(type="human"))
        c_ai = Claim(content="AI", confidence=0.9, origin=Origin(type="ai"))
        r_human = effective_trust(c_human)
        r_ai = effective_trust(c_ai)
        assert r_human.score > r_ai.score


class TestGroundingBonus:
    def test_single_evidence_bonus(self):
        c = Claim(content="Grounded", confidence=0.7,
                  evidence=[Evidence(type="test_pass", detail="ok")])
        r = effective_trust(c)
        assert r.breakdown["grounding_bonus"] == 0.05

    def test_multiple_evidence_bonus(self):
        evs = [Evidence(type="test_pass", detail=f"test {i}") for i in range(3)]
        c = Claim(content="Well-grounded", confidence=0.7, evidence=evs)
        r = effective_trust(c)
        assert r.breakdown["grounding_bonus"] == 0.15  # max cap

    def test_bonus_capped_at_015(self):
        evs = [Evidence(type="test_pass", detail=f"test {i}") for i in range(5)]
        c = Claim(content="Very grounded", confidence=0.7, evidence=evs)
        r = effective_trust(c)
        assert r.breakdown["grounding_bonus"] == 0.15  # capped

    def test_no_evidence_no_bonus(self):
        c = Claim(content="Ungrounded", confidence=0.7)
        r = effective_trust(c)
        assert r.breakdown["grounding_bonus"] == 0.0


class TestReviewBonus:
    def test_approved_review_bonus(self):
        c = Claim(content="Reviewed", confidence=0.7,
                  reviews=[Review(reviewer="alice", verdict="approved")])
        r = effective_trust(c)
        assert r.breakdown["review_bonus"] == 0.1

    def test_rejected_review_penalty(self):
        c = Claim(content="Rejected", confidence=0.7,
                  reviews=[Review(reviewer="bob", verdict="rejected")])
        r = effective_trust(c)
        assert r.breakdown["review_bonus"] == -0.2

    def test_needs_changes_no_bonus(self):
        c = Claim(content="Needs work", confidence=0.7,
                  reviews=[Review(reviewer="carol", verdict="needs_changes")])
        r = effective_trust(c)
        assert r.breakdown["review_bonus"] == 0.0

    def test_multiple_reviews_accumulate(self):
        c = Claim(content="Multi-reviewed", confidence=0.7, reviews=[
            Review(reviewer="alice", verdict="approved"),
            Review(reviewer="bob", verdict="approved"),
        ])
        r = effective_trust(c)
        assert r.breakdown["review_bonus"] == 0.2


class TestCalibratedTrust:
    def test_no_contradiction(self):
        c = Claim(content="Safe claim", confidence=0.8)
        refs = [Claim(content="Other", confidence=0.9)]
        r = calibrated_trust(c, refs)
        assert r.score == effective_trust(c).score

    def test_contradiction_penalty(self):
        high = Claim(content="Authoritative", confidence=0.95)
        low = Claim(content="Contradicting", confidence=0.7, contradicts=high.id)
        r = calibrated_trust(low, [high])
        assert r.score < effective_trust(low).score
        assert r.breakdown.get("calibration_penalty") == -0.15

    def test_contradiction_no_penalty_if_higher(self):
        low = Claim(content="Weak", confidence=0.3)
        high = Claim(content="Strong contra", confidence=0.95, contradicts=low.id)
        r = calibrated_trust(high, [low])
        # High is stronger than low, no penalty
        assert r.score == effective_trust(high).score


class TestResolveConflict:
    def test_basic_resolution(self):
        c1 = Claim(content="A", confidence=0.9, authority_tier=1)
        c2 = Claim(content="B", confidence=0.5, authority_tier=3)
        result = resolve_conflict([c1, c2])
        assert result["winner"].content == "A"
        assert len(result["scores"]) == 2

    def test_empty_claims(self):
        result = resolve_conflict([])
        assert result["winner"] is None

    def test_resolution_explanation(self):
        c1 = Claim(content="Winner", confidence=0.95)
        c2 = Claim(content="Loser", confidence=0.3)
        result = resolve_conflict([c1, c2])
        assert "winner" in result["explanation"]

    def test_scores_ordered(self):
        claims = [
            Claim(content="Low", confidence=0.3),
            Claim(content="High", confidence=0.9),
            Claim(content="Mid", confidence=0.6),
        ]
        result = resolve_conflict(claims)
        scores = [s["score"] for s in result["scores"]]
        assert scores == sorted(scores, reverse=True)


class TestTrustSummary:
    def test_basic_summary(self):
        unit = AKF(version="1.0", claims=[
            Claim(content="A", confidence=0.9),
            Claim(content="B", confidence=0.5),
            Claim(content="C", confidence=0.7),
        ])
        s = trust_summary(unit)
        assert s["min"] <= s["mean"] <= s["max"]
        assert s["median"] > 0

    def test_grounded_pct(self):
        unit = AKF(version="1.0", claims=[
            Claim(content="A", confidence=0.9, evidence=[Evidence(type="test_pass", detail="ok")]),
            Claim(content="B", confidence=0.5),
        ])
        s = trust_summary(unit)
        assert s["grounded_pct"] == 0.5

    def test_ai_pct(self):
        unit = AKF(version="1.0", claims=[
            Claim(content="A", confidence=0.9, ai_generated=True),
            Claim(content="B", confidence=0.5),
            Claim(content="C", confidence=0.7, origin=Origin(type="ai")),
        ])
        s = trust_summary(unit)
        assert s["ai_pct"] == pytest.approx(2/3, abs=0.01)

    def test_empty_unit_summary(self):
        # Can't create AKF with zero claims, but trust_summary handles it
        # Test with a minimal unit
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        s = trust_summary(unit)
        assert s["min"] == s["max"] == s["mean"] == s["median"]
