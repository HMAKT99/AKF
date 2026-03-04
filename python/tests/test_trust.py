"""Tests for AKF trust computation."""

import pytest
from akf.models import Claim
from akf.trust import effective_trust, compute_all, explain_trust, TrustLevel, AUTHORITY_WEIGHTS
from akf.core import create


class TestEffectiveTrust:
    def test_tier1_high_trust(self):
        claim = Claim(content="Revenue $4.2B", confidence=0.98, authority_tier=1)
        result = effective_trust(claim)
        assert result.score == pytest.approx(0.98, abs=0.01)
        assert result.decision == "ACCEPT"

    def test_tier2(self):
        claim = Claim(content="Growth 15%", confidence=0.85, authority_tier=2)
        result = effective_trust(claim)
        expected = 0.85 * 0.85  # 0.7225
        assert result.score == pytest.approx(expected, abs=0.01)
        assert result.decision == "ACCEPT"

    def test_tier3_default(self):
        claim = Claim(content="test", confidence=0.7)  # tier defaults to 3
        result = effective_trust(claim)
        expected = 0.7 * 0.70  # 0.49
        assert result.score == pytest.approx(expected, abs=0.01)
        assert result.decision == "LOW"

    def test_tier4(self):
        claim = Claim(content="Pipeline strong", confidence=0.72, authority_tier=4)
        result = effective_trust(claim)
        expected = 0.72 * 0.50  # 0.36
        assert result.score == pytest.approx(expected, abs=0.01)
        assert result.decision == "REJECT"

    def test_tier5_low_trust(self):
        claim = Claim(content="AI inference", confidence=0.63, authority_tier=5)
        result = effective_trust(claim)
        expected = 0.63 * 0.30  # 0.189
        assert result.score == pytest.approx(expected, abs=0.01)
        assert result.decision == "REJECT"

    def test_temporal_decay_half_life(self):
        claim = Claim(content="test", confidence=1.0, authority_tier=1, decay_half_life=30)
        # At exactly half-life, should be 0.5
        result = effective_trust(claim, age_days=30)
        assert result.score == pytest.approx(0.5, abs=0.01)

    def test_temporal_decay_double_half_life(self):
        claim = Claim(content="test", confidence=1.0, authority_tier=1, decay_half_life=30)
        result = effective_trust(claim, age_days=60)
        assert result.score == pytest.approx(0.25, abs=0.01)

    def test_no_decay_no_reduction(self):
        claim = Claim(content="test", confidence=0.9, authority_tier=1)
        result = effective_trust(claim, age_days=365)
        assert result.score == pytest.approx(0.9, abs=0.01)

    def test_penalty_reduces_score(self):
        claim = Claim(content="test", confidence=0.98, authority_tier=1)
        result = effective_trust(claim, penalty=-0.1)
        expected = 0.98 * 1.0 * 1.0 * 0.9  # 0.882
        assert result.score == pytest.approx(expected, abs=0.01)

    def test_edge_trust_zero(self):
        claim = Claim(content="nothing", confidence=0.0, authority_tier=1)
        result = effective_trust(claim)
        assert result.score == 0.0
        assert result.decision == "REJECT"

    def test_edge_trust_one(self):
        claim = Claim(content="certain", confidence=1.0, authority_tier=1)
        result = effective_trust(claim)
        assert result.score == 1.0
        assert result.decision == "ACCEPT"

    def test_decision_thresholds(self):
        # >= 0.7 -> ACCEPT
        claim = Claim(content="test", confidence=0.7, authority_tier=1)
        assert effective_trust(claim).decision == "ACCEPT"

        # >= 0.4 -> LOW
        claim = Claim(content="test", confidence=0.6, authority_tier=3)  # 0.6 * 0.7 = 0.42
        assert effective_trust(claim).decision == "LOW"

        # < 0.4 -> REJECT
        claim = Claim(content="test", confidence=0.5, authority_tier=5)  # 0.5 * 0.3 = 0.15
        assert effective_trust(claim).decision == "REJECT"

    def test_breakdown(self):
        claim = Claim(content="test", confidence=0.85, authority_tier=2)
        result = effective_trust(claim)
        assert result.breakdown["confidence"] == 0.85
        assert result.breakdown["authority"] == 0.85
        assert result.breakdown["tier"] == 2

    def test_all_authority_weights(self):
        for tier, weight in AUTHORITY_WEIGHTS.items():
            claim = Claim(content="test", confidence=1.0, authority_tier=tier)
            result = effective_trust(claim)
            assert result.score == pytest.approx(weight, abs=0.01)


class TestComputeAll:
    def test_multiple_claims(self):
        unit = create("test", confidence=0.5)
        results = compute_all(unit)
        assert len(results) == 1

    def test_with_threshold(self):
        from akf.core import create_multi
        unit = create_multi([
            {"c": "high", "t": 0.98, "tier": 1},
            {"c": "low", "t": 0.3, "tier": 5},
        ])
        results = compute_all(unit)
        assert len(results) == 2
        assert results[0].decision == "ACCEPT"
        assert results[1].decision == "REJECT"


class TestTrustLevel:
    def test_from_score_accept(self):
        assert TrustLevel.from_score(0.7) == TrustLevel.ACCEPT
        assert TrustLevel.from_score(0.95) == TrustLevel.ACCEPT

    def test_from_score_low(self):
        assert TrustLevel.from_score(0.4) == TrustLevel.LOW
        assert TrustLevel.from_score(0.6) == TrustLevel.LOW

    def test_from_score_reject(self):
        assert TrustLevel.from_score(0.0) == TrustLevel.REJECT
        assert TrustLevel.from_score(0.39) == TrustLevel.REJECT

    def test_threshold(self):
        assert TrustLevel.ACCEPT.threshold == 0.7
        assert TrustLevel.LOW.threshold == 0.4
        assert TrustLevel.REJECT.threshold == 0.0

    def test_result_level_property(self):
        claim = Claim(content="test", confidence=0.98, authority_tier=1)
        result = effective_trust(claim)
        assert result.level == TrustLevel.ACCEPT


class TestExplainTrust:
    def test_basic_explanation(self):
        claim = Claim(content="Revenue $4.2B", confidence=0.98, authority_tier=1)
        explanation = explain_trust(claim)
        assert "Revenue $4.2B" in explanation
        assert "0.98" in explanation
        assert "ACCEPT" in explanation

    def test_with_decay(self):
        claim = Claim(content="test", confidence=1.0, authority_tier=1, decay_half_life=30)
        explanation = explain_trust(claim, age_days=30)
        assert "decay" in explanation.lower()
        assert "half-life" in explanation.lower()

    def test_with_penalty(self):
        claim = Claim(content="test", confidence=0.9, authority_tier=1)
        explanation = explain_trust(claim, penalty=-0.1)
        assert "Penalty" in explanation

    def test_low_trust_advice(self):
        claim = Claim(content="test", confidence=0.6, authority_tier=3)
        explanation = explain_trust(claim)
        assert "caution" in explanation.lower()
