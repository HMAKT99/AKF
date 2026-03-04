"""Tests for v1.1 i18n module."""

from akf.i18n import t, MESSAGES


class TestTranslation:
    def test_known_key(self):
        result = t("provenance_present")
        assert result == "Provenance chain present"

    def test_trust_levels(self):
        assert t("trust_accept") == "Claim meets trust threshold for use"
        assert "low trust" in t("trust_low")
        assert "minimum trust" in t("trust_reject")

    def test_unknown_key_returns_key(self):
        result = t("nonexistent_key")
        assert result == "nonexistent_key"

    def test_english_default(self):
        result = t("confidence", locale="en")
        assert result == "Base confidence"

    def test_unknown_locale_falls_back_to_english(self):
        result = t("confidence", locale="fr")
        assert result == "Base confidence"

    def test_recommendations(self):
        assert "provenance" in t("rec_add_provenance")
        assert "hash" in t("rec_add_hash").lower()

    def test_regulation_names(self):
        assert t("eu_ai_act") == "EU AI Act"
        assert t("iso_42001") == "ISO 42001"

    def test_security_grades(self):
        assert "Excellent" in t("grade_a")
        assert "Critical" in t("grade_f")

    def test_messages_dict_not_empty(self):
        assert len(MESSAGES["en"]) > 20
