"""Tests for AKF trust computation."""

import pytest
from akf.models import Claim
from akf.trust import effective_trust, compute_all, AUTHORITY_WEIGHTS
from akf.core import create


class TestEffectiveTrust:
    def test_tier1_high_trust(self):
        claim = Claim(c="Revenue $4.2B", t=0.98, tier=1)
        result = effective_trust(claim)
        assert result.score == pytest.approx(0.98, abs=0.01)
        assert result.decision == "ACCEPT"

    def test_tier2(self):
        claim = Claim(c="Growth 15%", t=0.85, tier=2)
        result = effective_trust(claim)
        expected = 0.85 * 0.85  # 0.7225
        assert result.score == pytest.approx(expected, abs=0.01)
        assert result.decision == "ACCEPT"

    def test_tier3_default(self):
        claim = Claim(c="test", t=0.7)  # tier defaults to 3
        result = effective_trust(claim)
        expected = 0.7 * 0.70  # 0.49
        assert result.score == pytest.approx(expected, abs=0.01)
        assert result.decision == "LOW"

    def test_tier4(self):
        claim = Claim(c="Pipeline strong", t=0.72, tier=4)
        result = effective_trust(claim)
        expected = 0.72 * 0.50  # 0.36
        assert result.score == pytest.approx(expected, abs=0.01)
        assert result.decision == "REJECT"

    def test_tier5_low_trust(self):
        claim = Claim(c="AI inference", t=0.63, tier=5)
        result = effective_trust(claim)
        expected = 0.63 * 0.30  # 0.189
        assert result.score == pytest.approx(expected, abs=0.01)
        assert result.decision == "REJECT"

    def test_temporal_decay_half_life(self):
        claim = Claim(c="test", t=1.0, tier=1, decay=30)
        # At exactly half-life, should be 0.5
        result = effective_trust(claim, age_days=30)
        assert result.score == pytest.approx(0.5, abs=0.01)

    def test_temporal_decay_double_half_life(self):
        claim = Claim(c="test", t=1.0, tier=1, decay=30)
        result = effective_trust(claim, age_days=60)
        assert result.score == pytest.approx(0.25, abs=0.01)

    def test_no_decay_no_reduction(self):
        claim = Claim(c="test", t=0.9, tier=1)
        result = effective_trust(claim, age_days=365)
        assert result.score == pytest.approx(0.9, abs=0.01)

    def test_penalty_reduces_score(self):
        claim = Claim(c="test", t=0.98, tier=1)
        result = effective_trust(claim, penalty=-0.1)
        expected = 0.98 * 1.0 * 1.0 * 0.9  # 0.882
        assert result.score == pytest.approx(expected, abs=0.01)

    def test_edge_trust_zero(self):
        claim = Claim(c="nothing", t=0.0, tier=1)
        result = effective_trust(claim)
        assert result.score == 0.0
        assert result.decision == "REJECT"

    def test_edge_trust_one(self):
        claim = Claim(c="certain", t=1.0, tier=1)
        result = effective_trust(claim)
        assert result.score == 1.0
        assert result.decision == "ACCEPT"

    def test_decision_thresholds(self):
        # >= 0.7 -> ACCEPT
        claim = Claim(c="test", t=0.7, tier=1)
        assert effective_trust(claim).decision == "ACCEPT"

        # >= 0.4 -> LOW
        claim = Claim(c="test", t=0.6, tier=3)  # 0.6 * 0.7 = 0.42
        assert effective_trust(claim).decision == "LOW"

        # < 0.4 -> REJECT
        claim = Claim(c="test", t=0.5, tier=5)  # 0.5 * 0.3 = 0.15
        assert effective_trust(claim).decision == "REJECT"

    def test_breakdown(self):
        claim = Claim(c="test", t=0.85, tier=2)
        result = effective_trust(claim)
        assert result.breakdown["confidence"] == 0.85
        assert result.breakdown["authority"] == 0.85
        assert result.breakdown["tier"] == 2

    def test_all_authority_weights(self):
        for tier, weight in AUTHORITY_WEIGHTS.items():
            claim = Claim(c="test", t=1.0, tier=tier)
            result = effective_trust(claim)
            assert result.score == pytest.approx(weight, abs=0.01)


class TestComputeAll:
    def test_multiple_claims(self):
        unit = create("test", t=0.5)
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
