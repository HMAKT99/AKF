"""Tests for Delta 3: Origin weight in trust computation."""

from akf.models import Claim, Origin, Evidence, Review
from akf.trust import effective_trust, explain_trust


class TestOriginWeights:
    def test_human_origin_no_penalty(self):
        c = Claim(content="t", confidence=0.90, authority_tier=1, origin=Origin(type="human"))
        result = effective_trust(c)
        assert result.score >= 0.85

    def test_ai_origin_penalty(self):
        c = Claim(content="t", confidence=0.90, origin=Origin(type="ai"))
        result = effective_trust(c)
        assert result.score < 0.90

    def test_ai_chain_heavy_penalty(self):
        c = Claim(content="t", confidence=0.90, origin=Origin(type="ai_chain"))
        result = effective_trust(c)
        assert result.score < 0.65

    def test_collaboration_origin(self):
        c = Claim(content="t", confidence=0.90, origin=Origin(type="collaboration"))
        result = effective_trust(c)
        assert result.breakdown["origin_weight"] == 0.85

    def test_multi_agent_origin(self):
        c = Claim(content="t", confidence=0.90, origin=Origin(type="multi_agent"))
        result = effective_trust(c)
        assert result.breakdown["origin_weight"] == 0.60


class TestGroundingBonus:
    def test_evidence_adds_grounding_bonus(self):
        c = Claim(content="t", confidence=0.80, origin=Origin(type="ai"),
                  evidence=[Evidence(type="test_pass", detail="ok")])
        result = effective_trust(c)
        c_no = Claim(content="t", confidence=0.80, origin=Origin(type="ai"))
        result_no = effective_trust(c_no)
        assert result.score > result_no.score

    def test_grounding_bonus_capped(self):
        c = Claim(content="t", confidence=0.80, origin=Origin(type="human"),
                  evidence=[Evidence(type="test_pass", detail=f"e{i}") for i in range(10)])
        result = effective_trust(c)
        assert result.score <= 1.0
        assert result.breakdown["grounding_bonus"] == 0.15


class TestReviewBonus:
    def test_approved_review_adds_bonus(self):
        c = Claim(content="t", confidence=0.70, origin=Origin(type="ai"),
                  reviews=[Review(reviewer="x", verdict="approved")])
        result = effective_trust(c)
        c_no = Claim(content="t", confidence=0.70, origin=Origin(type="ai"))
        result_no = effective_trust(c_no)
        assert result.score > result_no.score

    def test_rejected_review_subtracts(self):
        c = Claim(content="t", confidence=0.90, origin=Origin(type="ai"),
                  reviews=[Review(reviewer="x", verdict="rejected")])
        result = effective_trust(c)
        c_no = Claim(content="t", confidence=0.90, origin=Origin(type="ai"))
        result_no = effective_trust(c_no)
        assert result.score < result_no.score


class TestTrustBounds:
    def test_trust_capped_at_1(self):
        c = Claim(content="t", confidence=0.99, origin=Origin(type="human"),
                  evidence=[Evidence(type="t", detail="d") for _ in range(5)],
                  reviews=[Review(reviewer="x", verdict="approved")])
        result = effective_trust(c)
        assert result.score <= 1.0

    def test_trust_floor_at_0(self):
        c = Claim(content="t", confidence=0.10, origin=Origin(type="ai_chain"),
                  reviews=[Review(reviewer="x", verdict="rejected")])
        result = effective_trust(c)
        assert result.score >= 0.0


class TestExplainTrustFormat:
    def test_explain_trust_shows_components(self):
        c = Claim(content="t", confidence=0.82,
                  origin=Origin(type="ai"),
                  authority_tier=1,
                  evidence=[Evidence(type="test_pass", detail="ok")],
                  reviews=[Review(reviewer="x", verdict="approved")])
        explanation = explain_trust(c)
        assert "confidence" in explanation.lower() or "Base confidence" in explanation
        assert "origin" in explanation.lower() or "Origin" in explanation
        assert "trust" in explanation.lower()
