"""Tests for AKF secure defaults.

New units created via create() and AKFBuilder are born secure:
- classification defaults to "internal"
- inherit_classification defaults to True
- allow_external defaults to False
- Claims: source="unspecified", authority_tier=3, verified=False, ai_generated=False
"""

from akf.core import create
from akf.builder import AKFBuilder
from akf.security import can_share_external


class TestCreateSecureDefaults:
    def test_classification_defaults_internal(self):
        unit = create("test", confidence=0.5)
        assert unit.classification == "internal"

    def test_inherit_defaults_true(self):
        unit = create("test", confidence=0.5)
        assert unit.inherit_classification is True

    def test_ext_defaults_false(self):
        unit = create("test", confidence=0.5)
        assert unit.allow_external is False

    def test_source_defaults_unspecified(self):
        unit = create("test", confidence=0.5)
        assert unit.claims[0].source == "unspecified"

    def test_authority_tier_defaults_3(self):
        unit = create("test", confidence=0.5)
        assert unit.claims[0].authority_tier == 3

    def test_verified_defaults_false(self):
        unit = create("test", confidence=0.5)
        assert unit.claims[0].verified is False

    def test_ai_generated_defaults_false(self):
        unit = create("test", confidence=0.5)
        assert unit.claims[0].ai_generated is False

    def test_explicit_values_override_defaults(self):
        unit = create("test", confidence=0.5, source="SEC", authority_tier=1, verified=True)
        assert unit.claims[0].source == "SEC"
        assert unit.claims[0].authority_tier == 1
        assert unit.claims[0].verified is True

    def test_cannot_share_by_default(self):
        unit = create("test", confidence=0.5)
        # internal + ext=False -> can share based on label_rank but ext is False
        assert can_share_external(unit) is False


class TestBuilderSecureDefaults:
    def test_classification_defaults_internal(self):
        unit = AKFBuilder().claim("test", 0.5).build()
        assert unit.classification == "internal"

    def test_inherit_defaults_true(self):
        unit = AKFBuilder().claim("test", 0.5).build()
        assert unit.inherit_classification is True

    def test_ext_defaults_false(self):
        unit = AKFBuilder().claim("test", 0.5).build()
        assert unit.allow_external is False

    def test_explicit_label_overrides(self):
        unit = AKFBuilder().label("confidential").claim("test", 0.5).build()
        assert unit.classification == "confidential"

    def test_explicit_ext_overrides(self):
        unit = AKFBuilder().ext(True).claim("test", 0.5).build()
        assert unit.allow_external is True

    def test_explicit_inherit_overrides(self):
        unit = AKFBuilder().inherit(False).claim("test", 0.5).build()
        assert unit.inherit_classification is False
