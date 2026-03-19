"""Tests for agent-to-agent trust delegation."""

from datetime import datetime, timezone, timedelta

import pytest

import akf
from akf.models import AKF, Claim, DelegationPolicy, ProvHop
from akf.delegation import delegate, validate_delegation
from akf.trust import effective_trust


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_parent(**overrides):
    """Create a simple parent AKF unit for delegation tests."""
    defaults = dict(
        version="1.1",
        claims=[
            Claim(content="Revenue is $4.2B", confidence=0.9, source="10-K"),
        ],
        author="agent-alpha",
        classification="internal",
    )
    defaults.update(overrides)
    return AKF(**defaults)


def _make_policy(**overrides):
    """Create a delegation policy with sensible defaults."""
    defaults = dict(
        delegator="agent-alpha",
        delegate="agent-beta",
        trust_ceiling=0.7,
    )
    defaults.update(overrides)
    return DelegationPolicy(**defaults)


# ---------------------------------------------------------------------------
# DelegationPolicy model tests
# ---------------------------------------------------------------------------

class TestDelegationPolicyModel:
    def test_basic_creation(self):
        policy = DelegationPolicy(
            delegator="a", delegate="b", trust_ceiling=0.8
        )
        assert policy.delegator == "a"
        assert policy.delegate == "b"
        assert policy.trust_ceiling == 0.8
        assert policy.allowed_actions is None
        assert policy.expires is None
        assert policy.scope is None

    def test_full_creation(self):
        policy = DelegationPolicy(
            delegator="a",
            delegate="b",
            trust_ceiling=0.6,
            allowed_actions=["summarize", "translate"],
            expires="2030-01-01T00:00:00Z",
            scope="financial",
        )
        assert policy.allowed_actions == ["summarize", "translate"]
        assert policy.expires == "2030-01-01T00:00:00Z"
        assert policy.scope == "financial"

    def test_compact_alias_input(self):
        """Accept compact wire-format aliases on input."""
        policy = DelegationPolicy(**{
            "from": "a",
            "to": "b",
            "ceil": 0.5,
            "actions": ["read"],
            "exp": "2030-12-31T00:00:00Z",
        })
        assert policy.delegator == "a"
        assert policy.delegate == "b"
        assert policy.trust_ceiling == 0.5
        assert policy.allowed_actions == ["read"]

    def test_to_dict_descriptive(self):
        policy = _make_policy()
        d = policy.to_dict(compact=False)
        assert d["delegator"] == "agent-alpha"
        assert d["delegate"] == "agent-beta"
        assert d["trust_ceiling"] == 0.7

    def test_to_dict_compact(self):
        policy = _make_policy()
        d = policy.to_dict(compact=True)
        assert "from" in d
        assert "to" in d
        assert "ceil" in d
        assert d["from"] == "agent-alpha"
        assert d["to"] == "agent-beta"
        assert d["ceil"] == 0.7

    def test_ceiling_validation_bounds(self):
        """trust_ceiling must be between 0.0 and 1.0."""
        with pytest.raises(Exception):
            DelegationPolicy(delegator="a", delegate="b", trust_ceiling=1.5)
        with pytest.raises(Exception):
            DelegationPolicy(delegator="a", delegate="b", trust_ceiling=-0.1)

    def test_edge_ceiling_values(self):
        p0 = DelegationPolicy(delegator="a", delegate="b", trust_ceiling=0.0)
        assert p0.trust_ceiling == 0.0
        p1 = DelegationPolicy(delegator="a", delegate="b", trust_ceiling=1.0)
        assert p1.trust_ceiling == 1.0


# ---------------------------------------------------------------------------
# validate_delegation tests
# ---------------------------------------------------------------------------

class TestValidateDelegation:
    def test_valid_policy_no_warnings(self):
        policy = _make_policy()
        warnings = validate_delegation(policy)
        assert warnings == []

    def test_valid_policy_with_future_expiry(self):
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        policy = _make_policy(expires=future)
        warnings = validate_delegation(policy)
        assert warnings == []

    def test_expired_policy_returns_warning(self):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        policy = _make_policy(expires=past)
        warnings = validate_delegation(policy)
        assert len(warnings) == 1
        assert "expired" in warnings[0]

    def test_invalid_expires_format(self):
        policy = _make_policy(expires="not-a-date")
        warnings = validate_delegation(policy)
        assert len(warnings) == 1
        assert "invalid expires format" in warnings[0]


# ---------------------------------------------------------------------------
# delegate() tests
# ---------------------------------------------------------------------------

class TestDelegate:
    def test_ceiling_caps_trust(self):
        """Claim with confidence 0.9 + ceiling 0.7 -> capped at 0.7."""
        parent = _make_parent()
        policy = _make_policy(trust_ceiling=0.7)

        result = delegate(parent, policy)

        # All claims should be capped at the ceiling
        for claim in result.claims:
            assert claim.confidence <= 0.7

    def test_ceiling_does_not_raise_low_confidence(self):
        """Claims below ceiling should keep original confidence (not be raised)."""
        parent = _make_parent(
            claims=[
                Claim(content="Moderate claim", confidence=0.8, source="estimate", authority_tier=1)
            ]
        )
        # Ceiling is higher than claim confidence, so claim should not be raised
        policy = _make_policy(trust_ceiling=0.95)

        result = delegate(parent, policy)

        # The claim confidence should stay at or below original,
        # and should NOT be raised to the ceiling.
        for claim in result.claims:
            assert claim.confidence <= 0.8

    def test_delegation_policy_in_provenance(self):
        """delegation_policy should be attached to the provenance hop."""
        parent = _make_parent()
        policy = _make_policy()

        result = delegate(parent, policy)

        assert result.prov is not None
        # At least one hop should have delegation_policy
        deleg_hops = [h for h in result.prov if h.delegation_policy is not None]
        assert len(deleg_hops) >= 1
        assert deleg_hops[-1].delegation_policy.trust_ceiling == 0.7

    def test_expired_policy_raises(self):
        """Delegating with an expired policy should raise ValueError."""
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        parent = _make_parent()
        policy = _make_policy(expires=past)

        with pytest.raises(ValueError, match="expired"):
            delegate(parent, policy)

    def test_delegate_with_new_claims(self):
        """New claims added during delegation should also be capped."""
        parent = _make_parent()
        policy = _make_policy(trust_ceiling=0.6)

        new_claims = [
            {"content": "New high-trust claim", "confidence": 0.95, "source": "analysis"},
        ]
        result = delegate(parent, policy, claims=new_claims)

        for claim in result.claims:
            assert claim.confidence <= 0.6

    def test_zero_ceiling(self):
        """A ceiling of 0.0 should cap everything to 0."""
        parent = _make_parent()
        policy = _make_policy(trust_ceiling=0.0)

        result = delegate(parent, policy)

        for claim in result.claims:
            assert claim.confidence == 0.0


# ---------------------------------------------------------------------------
# effective_trust with delegation_ceiling
# ---------------------------------------------------------------------------

class TestEffectiveTrustDelegationCeiling:
    def test_ceiling_caps_score(self):
        claim = Claim(content="Test", confidence=0.9, source="src")
        result = effective_trust(claim, delegation_ceiling=0.5)
        assert result.score <= 0.5

    def test_ceiling_in_breakdown(self):
        claim = Claim(content="Test", confidence=0.9, source="src")
        result = effective_trust(claim, delegation_ceiling=0.5)
        assert "delegation_ceiling" in result.breakdown
        assert result.breakdown["delegation_ceiling"] == 0.5

    def test_no_ceiling_no_key(self):
        claim = Claim(content="Test", confidence=0.9, source="src")
        result = effective_trust(claim)
        assert "delegation_ceiling" not in result.breakdown

    def test_ceiling_above_score_no_effect(self):
        """Ceiling above the natural score should not change the score."""
        claim = Claim(content="Test", confidence=0.5, source="src")
        result_without = effective_trust(claim)
        result_with = effective_trust(claim, delegation_ceiling=0.99)
        assert result_with.score == result_without.score

    def test_ceiling_changes_decision(self):
        """A ceiling can push a claim from ACCEPT to LOW or REJECT."""
        claim = Claim(content="Test", confidence=0.95, source="src")
        result = effective_trust(claim, delegation_ceiling=0.3)
        assert result.decision == "REJECT"


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_consume_still_works(self):
        """Existing consume() should work unchanged."""
        parent = _make_parent()
        result = akf.consume(parent, agent_id="consumer-agent")
        assert isinstance(result, AKF)
        assert len(result.claims) > 0

    def test_derive_still_works(self):
        """Existing derive() should work unchanged."""
        parent = _make_parent()
        result = akf.derive(parent, agent_id="deriver-agent")
        assert isinstance(result, AKF)
        assert len(result.claims) > 0

    def test_effective_trust_without_ceiling(self):
        """effective_trust without delegation_ceiling should be unchanged."""
        claim = Claim(content="Test", confidence=0.85, source="src")
        result = effective_trust(claim)
        assert result.score > 0
        assert "delegation_ceiling" not in result.breakdown

    def test_provhop_without_delegation_policy(self):
        """ProvHop should still work without delegation_policy."""
        hop = ProvHop(
            hop=1,
            actor="agent-a",
            action="consumed",
            timestamp="2026-01-01T00:00:00Z",
        )
        assert hop.delegation_policy is None
        d = hop.to_dict()
        assert "delegation_policy" not in d
