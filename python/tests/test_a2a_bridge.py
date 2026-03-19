"""Tests for A2A Protocol Bridge (Feature 5)."""

import json
import os
import tempfile

import pytest

from akf.a2a_bridge import (
    discover_a2a_cards,
    from_a2a_card,
    save_a2a_card,
    to_a2a_card,
)
from akf.agent_card import AgentCard, create_agent_card, verify_agent_card


class TestToA2ACard:
    def test_basic_conversion(self):
        card = create_agent_card(
            name="Test Bot",
            platform="claude-code",
            capabilities=["search", "summarize"],
            trust_ceiling=0.95,
            model="claude-opus-4-20250514",
            provider="anthropic",
        )
        a2a = to_a2a_card(card)
        assert a2a["name"] == "Test Bot"
        assert len(a2a["skills"]) == 2
        assert a2a["skills"][0]["name"] == "search"
        assert a2a["provider"]["organization"] == "anthropic"
        assert a2a["provider"]["model"] == "claude-opus-4-20250514"
        assert a2a["provider"]["platform"] == "claude-code"
        assert a2a["securityPolicy"]["trustCeiling"] == 0.95
        assert a2a["metadata"]["akf_id"] == card.id

    def test_minimal_card(self):
        card = create_agent_card(name="Minimal")
        a2a = to_a2a_card(card)
        assert a2a["name"] == "Minimal"
        assert "skills" not in a2a
        assert "provider" not in a2a
        assert "securityPolicy" not in a2a

    def test_preserves_hash(self):
        card = create_agent_card(name="Hashed", platform="test")
        a2a = to_a2a_card(card)
        assert a2a["metadata"]["akf_hash"] == card.card_hash


class TestFromA2ACard:
    def test_round_trip(self):
        original = create_agent_card(
            name="Round Trip",
            platform="cursor",
            capabilities=["edit", "refactor"],
            trust_ceiling=0.8,
            model="gpt-4o",
            provider="openai",
            version="2.0",
        )
        a2a = to_a2a_card(original)
        restored = from_a2a_card(a2a)

        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.platform == original.platform
        assert restored.capabilities == original.capabilities
        assert restored.trust_ceiling == original.trust_ceiling
        assert restored.model == original.model
        assert restored.provider == original.provider

    def test_from_pure_a2a(self):
        """Import a card that wasn't created by AKF."""
        a2a = {
            "name": "External Bot",
            "version": "1.0",
            "skills": [{"id": "code", "name": "code"}],
            "provider": {"organization": "example.com"},
        }
        card = from_a2a_card(a2a)
        assert card.name == "External Bot"
        assert card.capabilities == ["code"]
        assert card.provider == "example.com"
        assert card.id  # auto-generated

    def test_with_security_policy(self):
        a2a = {
            "name": "Secure Bot",
            "securityPolicy": {"trustCeiling": 0.6},
        }
        card = from_a2a_card(a2a)
        assert card.trust_ceiling == 0.6


class TestSaveAndDiscover:
    def test_save_a2a_card(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            card = create_agent_card(name="Save Test", platform="test")
            path = os.path.join(tmpdir, "card.json")
            result = save_a2a_card(card, path=path)

            assert result == path
            assert os.path.exists(path)

            with open(path) as f:
                data = json.load(f)
            assert data["name"] == "Save Test"

    def test_save_default_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            orig_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                card = create_agent_card(name="Default Path")
                path = save_a2a_card(card)
                assert os.path.exists(path)
                assert ".akf/agent-cards/" in path
            finally:
                os.chdir(orig_cwd)

    def test_discover_cards(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cards_dir = os.path.join(tmpdir, "cards")
            os.makedirs(cards_dir)

            # Save 2 cards
            c1 = create_agent_card(name="Bot A", platform="claude-code")
            c2 = create_agent_card(name="Bot B", platform="cursor")
            save_a2a_card(c1, os.path.join(cards_dir, "a.json"))
            save_a2a_card(c2, os.path.join(cards_dir, "b.json"))

            # Write an invalid file
            with open(os.path.join(cards_dir, "invalid.json"), "w") as f:
                f.write("not json")

            discovered = discover_a2a_cards(cards_dir)
            assert len(discovered) == 2
            names = {c.name for c in discovered}
            assert names == {"Bot A", "Bot B"}

    def test_discover_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cards = discover_a2a_cards(tmpdir)
            assert cards == []

    def test_discover_nonexistent_dir(self):
        cards = discover_a2a_cards("/nonexistent/path")
        assert cards == []


class TestA2ARoundTrip:
    def test_full_round_trip_with_file(self):
        """Save → discover → verify the complete flow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cards_dir = os.path.join(tmpdir, "cards")
            os.makedirs(cards_dir)

            original = create_agent_card(
                name="Full Trip",
                platform="codex",
                capabilities=["generate", "test"],
                trust_ceiling=0.85,
                model="codex-v1",
                provider="openai",
            )
            save_a2a_card(original, os.path.join(cards_dir, f"{original.id}.json"))

            discovered = discover_a2a_cards(cards_dir)
            assert len(discovered) == 1
            restored = discovered[0]
            assert restored.name == original.name
            assert restored.platform == original.platform
            assert restored.capabilities == original.capabilities
