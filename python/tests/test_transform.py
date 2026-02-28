"""Tests for AKF transformer."""

import pytest
from akf.builder import AKFBuilder
from akf.core import validate
from akf.transform import AKFTransformer
from akf.security import validate_inheritance


class TestAKFTransformer:
    def _make_parent(self):
        return (
            AKFBuilder()
            .by("sarah@woodgrove.com")
            .label("confidential")
            .inherit(True)
            .claim("Revenue $4.2B", 0.98, src="SEC 10-Q", tier=1, ver=True)
            .claim("Cloud growth 15-18%", 0.85, src="Gartner", tier=2)
            .claim("Pipeline strong", 0.72, src="estimate", tier=4)
            .claim("AI inference", 0.63, src="inference", tier=5, ai=True)
            .build()
        )

    def test_basic_filter(self):
        parent = self._make_parent()
        derived = (
            AKFTransformer(parent)
            .filter(trust_min=0.5)
            .by("research-agent")
            .build()
        )
        # Tier 5 with t=0.63 has effective trust 0.63*0.3=0.189, below 0.5
        # Tier 4 with t=0.72 has effective trust 0.72*0.5=0.36, below 0.5
        # Tier 2 with t=0.85 has effective trust 0.85*0.85=0.7225, above 0.5
        # Tier 1 with t=0.98 has effective trust 0.98*1.0=0.98, above 0.5
        assert len(derived.claims) == 2

    def test_penalty_applied(self):
        parent = self._make_parent()
        derived = (
            AKFTransformer(parent)
            .filter(trust_min=0.3)
            .penalty(-0.03)
            .by("agent")
            .build()
        )
        # All claims should have t reduced by 0.03
        for orig, deriv in zip(parent.claims, derived.claims):
            if deriv.id == orig.id:
                assert deriv.t == pytest.approx(orig.t - 0.03, abs=0.001)

    def test_inherits_classification(self):
        parent = self._make_parent()
        derived = (
            AKFTransformer(parent)
            .filter(trust_min=0.3)
            .by("agent")
            .build()
        )
        assert derived.label == "confidential"
        assert validate_inheritance(parent, derived) is True

    def test_provenance_extended(self):
        parent = self._make_parent()
        derived = (
            AKFTransformer(parent)
            .filter(trust_min=0.3)
            .by("research-agent")
            .build()
        )
        # Parent has 1 hop, derived should have 2
        assert len(derived.prov) == len(parent.prov) + 1
        last_hop = derived.prov[-1]
        assert last_hop.by == "research-agent"
        assert last_hop.do == "consumed"

    def test_derived_validates(self):
        parent = self._make_parent()
        derived = (
            AKFTransformer(parent)
            .filter(trust_min=0.3)
            .by("agent")
            .build()
        )
        result = validate(derived)
        assert result.valid

    def test_parent_id_in_meta(self):
        parent = self._make_parent()
        derived = (
            AKFTransformer(parent)
            .filter(trust_min=0.3)
            .by("agent")
            .build()
        )
        assert derived.meta is not None
        assert derived.meta["parent_id"] == parent.id

    def test_empty_after_filter_raises(self):
        parent = self._make_parent()
        with pytest.raises(ValueError, match="No claims survived"):
            (
                AKFTransformer(parent)
                .filter(trust_min=0.99)
                .by("agent")
                .build()
            )

    def test_integrity_hash_updated(self):
        parent = self._make_parent()
        derived = (
            AKFTransformer(parent)
            .filter(trust_min=0.3)
            .by("agent")
            .build()
        )
        assert derived.hash is not None
        assert derived.hash != parent.hash
