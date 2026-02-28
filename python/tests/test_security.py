"""Tests for AKF security."""

import pytest
from akf.models import AKF, Claim
from akf.security import (
    can_share_external,
    inherit_label,
    label_rank,
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
        parent = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="confidential", inherit=True)
        child = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="confidential")
        assert validate_inheritance(parent, child) is True

    def test_valid_higher_level(self):
        parent = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="confidential", inherit=True)
        child = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="restricted")
        assert validate_inheritance(parent, child) is True

    def test_invalid_lower_level(self):
        parent = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="confidential", inherit=True)
        child = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="public")
        assert validate_inheritance(parent, child) is False

    def test_no_inherit_skips_check(self):
        parent = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="confidential", inherit=False)
        child = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="public")
        assert validate_inheritance(parent, child) is True

    def test_confidential_parent_internal_child_invalid(self):
        parent = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="confidential", inherit=True)
        child = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="internal")
        assert validate_inheritance(parent, child) is False


class TestCanShareExternal:
    def test_public_can_share(self):
        unit = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="public")
        assert can_share_external(unit) is True

    def test_confidential_cannot_share(self):
        unit = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="confidential")
        assert can_share_external(unit) is False

    def test_restricted_cannot_share(self):
        unit = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="restricted")
        assert can_share_external(unit) is False

    def test_ext_true_overrides(self):
        unit = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="public", ext=True)
        assert can_share_external(unit) is True


class TestInheritLabel:
    def test_inherits_classification(self):
        parent = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="confidential", inherit=True)
        fields = inherit_label(parent)
        assert fields["label"] == "confidential"
        assert fields["inherit"] is True

    def test_no_inherit_returns_empty(self):
        parent = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="confidential", inherit=False)
        fields = inherit_label(parent)
        assert "label" not in fields

    def test_inherits_ext(self):
        parent = AKF(v="1.0", claims=[Claim(c="t", t=0.5)], label="public", ext=False)
        fields = inherit_label(parent)
        assert fields["ext"] is False
