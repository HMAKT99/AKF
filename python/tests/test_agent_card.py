"""Tests for cross-platform agent identity (AgentCard + AgentRegistry)."""

import json
import os
import tempfile

import pytest
from click.testing import CliRunner

from akf.agent_card import (
    AgentCard,
    AgentRegistry,
    create_agent_card,
    to_agent_profile,
    verify_agent_card,
)
from akf.cli import main
from akf.models import AgentProfile


# ---------------------------------------------------------------------------
# AgentCard creation
# ---------------------------------------------------------------------------


class TestCreateAgentCard:
    def test_create_with_all_fields(self):
        card = create_agent_card(
            name="Research Bot",
            platform="claude-code",
            capabilities=["search", "summarize"],
            trust_ceiling=0.95,
            model="claude-opus-4-20250514",
            version="2.0",
            provider="anthropic",
        )
        assert card.name == "Research Bot"
        assert card.platform == "claude-code"
        assert card.capabilities == ["search", "summarize"]
        assert card.trust_ceiling == 0.95
        assert card.model == "claude-opus-4-20250514"
        assert card.version == "2.0"
        assert card.provider == "anthropic"
        assert card.id is not None
        assert len(card.id) == 16
        assert card.created_at is not None
        assert card.card_hash is not None

    def test_create_minimal(self):
        card = create_agent_card(name="Simple Agent")
        assert card.name == "Simple Agent"
        assert card.id is not None
        assert card.card_hash is not None
        assert card.platform is None
        assert card.capabilities is None

    def test_unique_ids(self):
        c1 = create_agent_card(name="Agent A")
        c2 = create_agent_card(name="Agent B")
        assert c1.id != c2.id


# ---------------------------------------------------------------------------
# Hash verification
# ---------------------------------------------------------------------------


class TestVerifyAgentCard:
    def test_valid_card(self):
        card = create_agent_card(name="Valid Bot", platform="test")
        assert verify_agent_card(card) is True

    def test_tampered_name(self):
        card = create_agent_card(name="Original")
        card.name = "Tampered"
        assert verify_agent_card(card) is False

    def test_tampered_trust_ceiling(self):
        card = create_agent_card(name="Bot", trust_ceiling=0.5)
        card.trust_ceiling = 1.0
        assert verify_agent_card(card) is False

    def test_no_hash_returns_false(self):
        card = AgentCard(id="test-id", name="No Hash")
        assert verify_agent_card(card) is False


# ---------------------------------------------------------------------------
# AgentRegistry CRUD
# ---------------------------------------------------------------------------


class TestAgentRegistry:
    @pytest.fixture
    def registry(self, tmp_path):
        base = str(tmp_path / ".akf")
        return AgentRegistry(base_dir=base)

    def test_register_and_get(self, registry):
        card = create_agent_card(name="Reg Bot", platform="test")
        registry.register(card)
        retrieved = registry.get(card.id)
        assert retrieved is not None
        assert retrieved.id == card.id
        assert retrieved.name == "Reg Bot"

    def test_get_missing(self, registry):
        assert registry.get("nonexistent") is None

    def test_list_empty(self, registry):
        assert registry.list() == []

    def test_list_multiple(self, registry):
        c1 = create_agent_card(name="A")
        c2 = create_agent_card(name="B")
        registry.register(c1)
        registry.register(c2)
        cards = registry.list()
        assert len(cards) == 2
        names = {c.name for c in cards}
        assert names == {"A", "B"}

    def test_remove(self, registry):
        card = create_agent_card(name="Removable")
        registry.register(card)
        assert registry.remove(card.id) is True
        assert registry.get(card.id) is None

    def test_remove_missing(self, registry):
        assert registry.remove("no-such-id") is False

    def test_persistence(self, tmp_path):
        base = str(tmp_path / ".akf")
        reg1 = AgentRegistry(base_dir=base)
        card = create_agent_card(name="Persistent")
        reg1.register(card)

        reg2 = AgentRegistry(base_dir=base)
        retrieved = reg2.get(card.id)
        assert retrieved is not None
        assert retrieved.name == "Persistent"


# ---------------------------------------------------------------------------
# to_agent_profile conversion
# ---------------------------------------------------------------------------


class TestToAgentProfile:
    def test_conversion(self):
        card = create_agent_card(
            name="Profile Bot",
            capabilities=["code", "review"],
            trust_ceiling=0.8,
            model="gpt-4o",
            version="1.0",
        )
        profile = to_agent_profile(card)
        assert isinstance(profile, AgentProfile)
        assert profile.id == card.id
        assert profile.name == "Profile Bot"
        assert profile.model == "gpt-4o"
        assert profile.version == "1.0"
        assert profile.capabilities == ["code", "review"]
        assert profile.trust_ceiling == 0.8

    def test_minimal_conversion(self):
        card = create_agent_card(name="Minimal")
        profile = to_agent_profile(card)
        assert profile.id == card.id
        assert profile.name == "Minimal"
        assert profile.model is None


# ---------------------------------------------------------------------------
# Alias deserialization
# ---------------------------------------------------------------------------


class TestAliases:
    def test_compact_aliases(self):
        card = AgentCard.model_validate({
            "id": "test",
            "name": "Alias Bot",
            "caps": ["search"],
            "ceil": 0.9,
            "plat": "copilot",
            "ver": "3.0",
            "prov": "microsoft",
            "at": "2025-01-01T00:00:00Z",
            "h": "abc123",
        })
        assert card.capabilities == ["search"]
        assert card.trust_ceiling == 0.9
        assert card.platform == "copilot"
        assert card.version == "3.0"
        assert card.provider == "microsoft"
        assert card.created_at == "2025-01-01T00:00:00Z"
        assert card.card_hash == "abc123"


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------


class TestAgentCLI:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_agent_create(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(main, [
            "agent", "create",
            "--name", "CLI Bot",
            "--platform", "claude-code",
            "--capabilities", "search,summarize",
        ])
        assert result.exit_code == 0
        assert "Registered agent:" in result.output
        assert "CLI Bot" in result.output

    def test_agent_list_empty(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(main, ["agent", "list"])
        assert result.exit_code == 0
        assert "No agents registered" in result.output

    def test_agent_create_then_list(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(main, [
            "agent", "create", "--name", "Bot A",
        ])
        result = runner.invoke(main, ["agent", "list"])
        assert result.exit_code == 0
        assert "Bot A" in result.output
        assert "1" in result.output  # count

    def test_agent_verify_valid(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        create_result = runner.invoke(main, [
            "agent", "create", "--name", "Verify Bot",
        ])
        # Extract agent ID from output
        for line in create_result.output.splitlines():
            if "Registered agent:" in line:
                agent_id = line.split("Registered agent:")[1].strip()
                break

        result = runner.invoke(main, ["agent", "verify", agent_id])
        assert result.exit_code == 0
        assert "PASS" in result.output

    def test_agent_verify_missing(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(main, ["agent", "verify", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_agent_create_no_register(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(main, [
            "agent", "create", "--name", "Unregistered", "--no-register",
        ])
        assert result.exit_code == 0
        assert "Created agent:" in result.output
        # Should not appear in list
        list_result = runner.invoke(main, ["agent", "list"])
        assert "No agents registered" in list_result.output
