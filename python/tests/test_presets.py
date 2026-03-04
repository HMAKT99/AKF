"""Tests for AKF presets module."""

import pytest
from akf.presets import TEMPLATES, Template, register, get_template, list_templates


class TestTemplates:
    def test_financial_report(self):
        t = TEMPLATES["financial_report"]
        assert t.label == "confidential"
        assert t.inherit is True
        assert t.decay == 90

    def test_meeting_notes(self):
        t = TEMPLATES["meeting_notes"]
        assert t.label == "internal"
        assert t.decay == 30
        assert t.defaults["authority_tier"] == 4

    def test_incident_report(self):
        t = TEMPLATES["incident_report"]
        assert t.label == "confidential"
        assert t.inherit is True
        assert t.defaults["authority_tier"] == 2

    def test_research_paper(self):
        t = TEMPLATES["research_paper"]
        assert t.label == "internal"
        assert t.decay == 3650
        assert t.defaults["authority_tier"] == 1

    def test_press_release(self):
        t = TEMPLATES["press_release"]
        assert t.label == "public"
        assert t.ext is True

    def test_create_from_template(self):
        t = TEMPLATES["financial_report"]
        unit = t.create(
            [{"content": "Revenue $4.2B", "confidence": 0.98, "source": "SEC"}],
            by="sarah@test.com",
        )
        assert len(unit.claims) == 1
        assert unit.classification == "confidential"
        assert unit.claims[0].decay_half_life == 90

    def test_template_applies_defaults(self):
        t = TEMPLATES["meeting_notes"]
        unit = t.create([{"content": "Action item", "confidence": 0.7}])
        assert unit.claims[0].authority_tier == 4


class TestRegister:
    def test_register_custom(self):
        register("custom", Template(name="custom", label="internal"))
        assert "custom" in TEMPLATES
        del TEMPLATES["custom"]

    def test_get_template(self):
        t = get_template("financial_report")
        assert t.name == "financial_report"

    def test_get_unknown_raises(self):
        with pytest.raises(KeyError):
            get_template("nonexistent")

    def test_list_templates(self):
        names = list_templates()
        assert "financial_report" in names
        assert "meeting_notes" in names
        assert len(names) >= 9
