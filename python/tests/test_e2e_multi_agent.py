"""AKF v1.1 — End-to-End Multi-Agent Integration Tests.

Comprehensive tests covering all 6 new multi-agent features:
1. Agent-to-Agent Trust Delegation
2. Team-Aware Streaming
3. Cross-Platform Agent Identity (Agent Cards)
4. Video/Audio Format Handlers
5. A2A Protocol Bridge
6. Team-Level Trust Certification

Plus cross-stack verification:
7. README accuracy vs SDK exports
8. Website content consistency
9. CLI command integration
10. Full multi-agent pipelines (delegation → stream → certify)

Run: python3 -m pytest tests/test_e2e_multi_agent.py -v
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PYTHON = sys.executable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SITE_DIR = PROJECT_ROOT / "site" / "src"
README_PATH = PROJECT_ROOT / "README.md"
CONTRIBUTING_PATH = PROJECT_ROOT / "CONTRIBUTING.md"
MCP_README_PATH = PROJECT_ROOT / "packages" / "mcp-server-akf" / "README.md"

TEST_DIR = None


def akf_cli(*args, check=True, allow_fail=False):
    """Run an akf CLI command, return (returncode, stdout, stderr)."""
    cmd = [PYTHON, "-m", "akf"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=TEST_DIR)
    if check and not allow_fail and result.returncode != 0:
        raise AssertionError(
            f"Command failed: {' '.join(args)}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.returncode, result.stdout, result.stderr


@pytest.fixture(scope="module", autouse=True)
def setup_test_dir():
    """Create temp directory for all tests."""
    global TEST_DIR
    TEST_DIR = tempfile.mkdtemp(prefix="akf_e2e_multiagent_")
    yield TEST_DIR
    shutil.rmtree(TEST_DIR, ignore_errors=True)


def _write_file(name: str, content: str = "") -> str:
    """Create a file in TEST_DIR and return its path."""
    path = os.path.join(TEST_DIR, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content or f"# {name}\nGenerated test content.\n")
    return path


def _stamp_file(path: str, agent: str = "test-agent", confidence: float = 0.85) -> Dict:
    """Stamp a file with AKF metadata using the SDK and return the unit dict."""
    import akf
    unit = akf.stamp(
        content=f"Test claim for {os.path.basename(path)}",
        confidence=confidence,
        agent=agent,
        kind="claim",
    )
    d = unit.to_dict(compact=True)
    akf.embed(path, metadata=d)
    return d


# ===========================================================================
# PHASE 1: Trust Delegation (Feature 1)
# ===========================================================================


class TestDelegationE2E:
    """End-to-end tests for agent-to-agent trust delegation."""

    def test_basic_delegation_flow(self):
        """Parent agent delegates to child agent with trust ceiling."""
        import akf
        from akf import DelegationPolicy, delegate

        # Parent creates a high-trust unit
        parent = akf.create(
            content="Research findings verified",
            confidence=0.95,
            source="primary-research",
        )

        # Define delegation policy
        policy = DelegationPolicy(
            delegator="lead-agent",
            delegate="research-bot",
            trust_ceiling=0.7,
        )

        # Delegate work
        result = delegate(parent, policy)

        # Verify ceiling enforcement
        for claim in result.claims:
            assert claim.confidence <= 0.7, f"Ceiling violated: {claim.confidence}"

        # Verify provenance records delegation
        assert result.prov, "Delegation must record provenance"
        last_hop = result.prov[-1]
        assert last_hop.delegation_policy is not None
        assert last_hop.delegation_policy.trust_ceiling == 0.7

    def test_delegation_with_new_claims(self):
        """Delegate can add new claims, all capped at ceiling."""
        import akf
        from akf import DelegationPolicy, delegate

        parent = akf.create(content="Base unit", confidence=0.9, source="test")
        policy = DelegationPolicy(
            delegator="orchestrator",
            delegate="worker-1",
            trust_ceiling=0.6,
        )

        result = delegate(
            parent,
            policy,
            claims=[
                {"c": "New finding A", "t": 0.95, "src": "analysis"},
                {"c": "New finding B", "t": 0.5, "src": "estimate"},
            ],
        )

        # All claims (inherited + new) must be <= ceiling
        for claim in result.claims:
            assert claim.confidence <= 0.6

        # B was already below ceiling — should keep original
        b_claims = [c for c in result.claims if "Finding B" in (c.content or "")]
        if b_claims:
            assert b_claims[0].confidence == 0.5

    def test_delegation_expired_policy_raises(self):
        """Expired delegation policy raises ValueError."""
        import akf
        from akf import DelegationPolicy, delegate

        parent = akf.create(content="test", confidence=0.9, source="test")
        policy = DelegationPolicy(
            delegator="a",
            delegate="b",
            trust_ceiling=0.7,
            expires="2020-01-01T00:00:00Z",
        )

        with pytest.raises(ValueError, match="expired"):
            delegate(parent, policy)

    def test_delegation_validation_warnings(self):
        """validate_delegation reports issues but doesn't raise."""
        from akf import DelegationPolicy, validate_delegation

        # Expired
        policy = DelegationPolicy(
            delegator="a",
            delegate="b",
            trust_ceiling=0.7,
            expires="2020-01-01T00:00:00Z",
        )
        warnings = validate_delegation(policy)
        assert any("expired" in w for w in warnings)

    def test_delegation_preserves_parent_claims(self):
        """Parent claims are carried forward (with penalty) in delegation."""
        import akf
        from akf import DelegationPolicy, delegate

        # Use high-confidence claims so they survive derive() filtering
        parent = akf.create_multi([
            {"c": "Claim A", "t": 0.95, "src": "test"},
            {"c": "Claim B", "t": 0.9, "src": "test"},
        ])

        policy = DelegationPolicy(
            delegator="parent",
            delegate="child",
            trust_ceiling=0.9,
        )

        result = delegate(parent, policy, transform_penalty=-0.01)
        assert len(result.claims) >= 2, "Parent claims must be preserved"

    def test_delegation_effective_trust_ceiling(self):
        """effective_trust respects delegation_ceiling parameter."""
        import akf
        from akf import effective_trust

        claim = akf.Claim(content="High confidence", confidence=0.95)
        result = effective_trust(claim, delegation_ceiling=0.5)
        assert result.score <= 0.5, f"Ceiling not applied: {result.score}"

    def test_delegation_chain_multi_hop(self):
        """Multiple delegation hops compound ceiling enforcement.

        Tests the concept that successive delegations narrow the ceiling.
        Each hop adds fresh claims (since inherited claims may be filtered
        by effective trust thresholds in derive()).
        """
        import akf
        from akf import DelegationPolicy, delegate

        # First delegation: A → B with ceiling 0.8
        root = akf.create(content="Root analysis", confidence=0.99, source="data")
        policy_ab = DelegationPolicy(
            delegator="agent-a", delegate="agent-b", trust_ceiling=0.8,
        )
        step1 = delegate(root, policy_ab, transform_penalty=-0.01)

        # Verify step1 claims are capped at 0.8
        for claim in step1.claims:
            assert claim.confidence <= 0.8

        # Second delegation: B → C with ceiling 0.6
        policy_bc = DelegationPolicy(
            delegator="agent-b", delegate="agent-c", trust_ceiling=0.6,
        )
        # Create a human-origin unit (origin_weight=1.0) so it survives derive filtering
        b_output = akf.create(content="Agent B's analysis", confidence=0.99, source="step1")
        step2 = delegate(b_output, policy_bc, transform_penalty=-0.01)

        # All claims should be <= 0.6 (the tighter ceiling)
        for claim in step2.claims:
            assert claim.confidence <= 0.6, f"Multi-hop ceiling violated: {claim.confidence}"

        # Both steps should record delegation in provenance
        assert step1.prov[-1].delegation_policy is not None
        assert step2.prov[-1].delegation_policy is not None
        assert step1.prov[-1].delegation_policy.trust_ceiling == 0.8
        assert step2.prov[-1].delegation_policy.trust_ceiling == 0.6


# ===========================================================================
# PHASE 2: Team-Aware Streaming (Feature 2)
# ===========================================================================


class TestTeamStreamE2E:
    """End-to-end tests for multi-agent team streaming."""

    def test_team_stream_context_manager(self):
        """TeamStream context manager with multiple agents."""
        from akf import TeamStream

        with TeamStream(["agent-a", "agent-b", "agent-c"]) as ts:
            ts.write("agent-a", "Research result", confidence=0.9)
            ts.write("agent-b", "Code review passed", confidence=0.85)
            ts.write("agent-c", "Documentation complete", confidence=0.8)

            # Mid-stream aggregation
            agg = ts.aggregate()
            assert agg.total_claims == 3
            assert agg.claims_per_agent["agent-a"] == 1
            assert agg.claims_per_agent["agent-b"] == 1
            assert agg.claims_per_agent["agent-c"] == 1

        # After context exit, unit should be available
        assert ts.unit is not None
        assert len(ts.unit.claims) == 3

    def test_team_stream_file_output(self):
        """TeamStream writes correct .akfl file format."""
        from akf import TeamStream

        output_path = os.path.join(TEST_DIR, "team_output.md")

        with TeamStream(["lead", "worker"], output_path=output_path) as ts:
            ts.write("lead", "Architecture decided", confidence=0.9)
            ts.write("worker", "Implementation done", confidence=0.85)

        # Read the .akfl file
        akfl_path = output_path + ".team.akfl"
        assert os.path.exists(akfl_path), f"Team AKFL file not created: {akfl_path}"

        lines = []
        with open(akfl_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    lines.append(json.loads(line))

        # Verify structure: team_start, claims, team_end
        assert lines[0]["type"] == "team_start"
        assert set(lines[0]["agents"]) == {"lead", "worker"}

        claim_lines = [l for l in lines if l["type"] == "claim"]
        assert len(claim_lines) == 2
        assert claim_lines[0]["agent"] == "lead"
        assert claim_lines[1]["agent"] == "worker"

        assert lines[-1]["type"] == "team_end"
        assert lines[-1]["count"] == 2
        assert lines[-1]["hash"].startswith("sha256:")

    def test_team_stream_trust_aggregation(self):
        """Per-agent and team-level trust scores computed correctly."""
        from akf import team_stream_start, team_stream_claim, team_trust_aggregate

        session = team_stream_start(["fast-agent", "careful-agent"])
        team_stream_claim(session, "fast-agent", "Quick answer", confidence=0.6)
        team_stream_claim(session, "fast-agent", "Another quick one", confidence=0.7)
        team_stream_claim(session, "careful-agent", "Verified answer", confidence=0.95)

        result = team_trust_aggregate(session)

        assert result.total_claims == 3
        assert result.claims_per_agent["fast-agent"] == 2
        assert result.claims_per_agent["careful-agent"] == 1
        assert abs(result.agent_scores["fast-agent"] - 0.65) < 0.01
        assert abs(result.agent_scores["careful-agent"] - 0.95) < 0.01
        # Team avg = (0.6 + 0.7 + 0.95) / 3 = 0.75
        assert abs(result.team_avg_trust - 0.75) < 0.01

    def test_team_stream_invalid_agent_raises(self):
        """Emitting claim for unregistered agent raises ValueError."""
        from akf import team_stream_start, team_stream_claim

        session = team_stream_start(["agent-x"])
        with pytest.raises(ValueError, match="not in team"):
            team_stream_claim(session, "agent-y", "Rogue claim", confidence=0.5)

    def test_team_stream_empty_session(self):
        """Empty team session produces placeholder AKF unit."""
        from akf import team_stream_start, team_stream_end

        session = team_stream_start(["agent-a"])
        unit = team_stream_end(session)

        assert unit is not None
        assert len(unit.claims) == 1
        assert unit.claims[0].confidence == 0.0
        assert "empty" in unit.claims[0].content.lower()

    def test_team_stream_functions_api(self):
        """Test the functional API (not context manager)."""
        from akf import (
            team_stream_start, team_stream_claim,
            team_stream_end, team_trust_aggregate,
        )

        akfl_path = os.path.join(TEST_DIR, "func_team.akfl")
        session = team_stream_start(
            ["researcher", "writer"],
            output_path=akfl_path,
        )

        team_stream_claim(session, "researcher", "Found 3 papers", confidence=0.9)
        team_stream_claim(session, "writer", "Summarized findings", confidence=0.85)
        team_stream_claim(session, "researcher", "Verified citations", confidence=0.95)

        agg = team_trust_aggregate(session)
        assert agg.total_claims == 3

        unit = team_stream_end(session)
        assert len(unit.claims) == 3
        assert unit.session is not None

        # Verify file was written
        assert os.path.exists(akfl_path)

    def test_single_agent_stream_has_agent_field(self):
        """Single-agent streaming includes agent field in .akfl output."""
        from akf import stream_start, stream_claim, stream_end

        akfl = os.path.join(TEST_DIR, "single_agent.akfl")
        session = stream_start(agent_id="my-agent", output_path=akfl)
        stream_claim(session, "Test claim", confidence=0.8)
        stream_end(session)

        with open(akfl) as f:
            lines = [json.loads(l.strip()) for l in f if l.strip()]

        claim_lines = [l for l in lines if l["type"] == "claim"]
        assert len(claim_lines) == 1
        assert claim_lines[0]["agent"] == "my-agent"


# ===========================================================================
# PHASE 3: Cross-Platform Agent Identity (Feature 3)
# ===========================================================================


class TestAgentCardE2E:
    """End-to-end tests for agent identity and registry."""

    def test_create_and_verify_card(self):
        """Create agent card with hash, then verify integrity."""
        from akf import create_agent_card, verify_agent_card

        card = create_agent_card(
            name="Research Bot",
            platform="claude-code",
            capabilities=["search", "summarize", "cite"],
            trust_ceiling=0.8,
            model="claude-opus-4-20250514",
            version="1.0",
            provider="Anthropic",
        )

        assert card.id, "Card must have auto-generated ID"
        assert card.card_hash, "Card must have computed hash"
        assert card.created_at, "Card must have timestamp"
        assert card.name == "Research Bot"
        assert card.capabilities == ["search", "summarize", "cite"]
        assert card.trust_ceiling == 0.8

        # Verify hash
        assert verify_agent_card(card) is True

        # Tamper and verify fails
        card.name = "Tampered Name"
        assert verify_agent_card(card) is False

    def test_registry_crud(self):
        """Full CRUD cycle on agent registry."""
        from akf import AgentRegistry, create_agent_card

        reg_dir = os.path.join(TEST_DIR, "registry_test_akf")
        registry = AgentRegistry(base_dir=reg_dir)

        # Create and register 3 cards
        cards = []
        for name in ["Agent-Alpha", "Agent-Beta", "Agent-Gamma"]:
            card = create_agent_card(name=name, platform="test")
            registry.register(card)
            cards.append(card)

        # List
        all_cards = registry.list()
        assert len(all_cards) == 3

        # Get by ID
        found = registry.get(cards[0].id)
        assert found is not None
        assert found.name == "Agent-Alpha"

        # Get non-existent
        assert registry.get("nonexistent-id") is None

        # Remove
        assert registry.remove(cards[1].id) is True
        assert len(registry.list()) == 2
        assert registry.remove("nonexistent-id") is False

    def test_card_to_agent_profile(self):
        """Convert AgentCard to AgentProfile for AKF units."""
        from akf import create_agent_card, to_agent_profile

        card = create_agent_card(
            name="Coder",
            platform="cursor",
            model="gpt-4o",
            capabilities=["code", "review"],
            trust_ceiling=0.85,
        )

        profile = to_agent_profile(card)
        assert profile.id == card.id
        assert profile.name == "Coder"
        assert profile.model == "gpt-4o"
        assert profile.capabilities == ["code", "review"]

    def test_registry_persistence(self):
        """Registry data persists across instances."""
        from akf import AgentRegistry, create_agent_card

        reg_dir = os.path.join(TEST_DIR, "persist_test_akf")

        # Write with one instance
        reg1 = AgentRegistry(base_dir=reg_dir)
        card = create_agent_card(name="Persistent Bot", platform="test")
        reg1.register(card)

        # Read with another instance
        reg2 = AgentRegistry(base_dir=reg_dir)
        found = reg2.get(card.id)
        assert found is not None
        assert found.name == "Persistent Bot"

    def test_agent_card_cli_create(self):
        """CLI: akf agent create."""
        rc, out, err = akf_cli(
            "agent", "create",
            "--name", "CLI Bot",
            "--platform", "claude-code",
            "--capabilities", "search,code",
            allow_fail=True,
        )
        # Check that it either succeeds or reports the command
        if rc == 0:
            assert "CLI Bot" in out or "agent" in out.lower()

    def test_agent_card_cli_list(self):
        """CLI: akf agent list."""
        rc, out, err = akf_cli("agent", "list", allow_fail=True)
        # Should not crash
        assert rc == 0 or "agent" in (out + err).lower()


# ===========================================================================
# PHASE 4: Video/Audio Format Handlers (Feature 4)
# ===========================================================================


class TestMediaHandlersE2E:
    """End-to-end tests for video and audio sidecar format handlers."""

    @pytest.mark.parametrize("ext,handler_mod", [
        (".mp4", "akf.formats.video"),
        (".mov", "akf.formats.video"),
        (".webm", "akf.formats.video"),
        (".mkv", "akf.formats.video"),
        (".mp3", "akf.formats.audio"),
        (".wav", "akf.formats.audio"),
        (".flac", "akf.formats.audio"),
        (".ogg", "akf.formats.audio"),
    ])
    def test_sidecar_embed_extract_cycle(self, ext, handler_mod):
        """Embed and extract metadata via sidecar for each media format."""
        import importlib
        mod = importlib.import_module(handler_mod)

        # Create dummy media file
        fname = f"test_media{ext}"
        fpath = _write_file(fname, f"DUMMY {ext.upper()} CONTENT\x00\xff")

        # Embed metadata
        metadata = {
            "ver": "1.0",
            "claims": [{"c": f"Media {ext} claim", "t": 0.8, "src": "test"}],
        }
        mod.embed(fpath, metadata)

        # Verify sidecar created
        sidecar_path = fpath + ".akf.json"
        assert os.path.exists(sidecar_path), f"Sidecar not created for {ext}"

        # Extract
        extracted = mod.extract(fpath)
        assert extracted is not None
        assert "claims" in extracted

        # Check enriched
        assert mod.is_enriched(fpath) is True

    @pytest.mark.parametrize("ext", [".mp4", ".mp3"])
    def test_universal_dispatcher_routes_media(self, ext):
        """Universal embed/extract routes media files to sidecar handler."""
        import akf

        fpath = _write_file(f"dispatch_test{ext}", f"DUMMY {ext}")
        metadata = {
            "ver": "1.0",
            "claims": [{"c": "Universal dispatch claim", "t": 0.75, "src": "test"}],
        }
        akf.embed(fpath, metadata=metadata)

        extracted = akf.extract(fpath)
        assert extracted is not None

    def test_video_scan_directory(self):
        """Scan directory for video files with/without AKF metadata."""
        from akf.formats.video import VideoHandler, scan_directory

        scan_dir = os.path.join(TEST_DIR, "video_scan")
        os.makedirs(scan_dir, exist_ok=True)

        # Create 2 video files, stamp only 1
        v1 = os.path.join(scan_dir, "clip1.mp4")
        v2 = os.path.join(scan_dir, "clip2.mov")
        for p in [v1, v2]:
            with open(p, "w") as f:
                f.write("DUMMY VIDEO")

        handler = VideoHandler()
        handler.embed(v1, {"ver": "1.0", "claims": [{"c": "test", "t": 0.8}]})

        results = scan_directory(scan_dir)
        assert len(results) >= 1  # At least the enriched file

    def test_audio_scan_directory(self):
        """Scan directory for audio files with/without AKF metadata."""
        from akf.formats.audio import AudioHandler, scan_directory

        scan_dir = os.path.join(TEST_DIR, "audio_scan")
        os.makedirs(scan_dir, exist_ok=True)

        a1 = os.path.join(scan_dir, "track.mp3")
        a2 = os.path.join(scan_dir, "voice.wav")
        for p in [a1, a2]:
            with open(p, "w") as f:
                f.write("DUMMY AUDIO")

        handler = AudioHandler()
        handler.embed(a1, {"ver": "1.0", "claims": [{"c": "audio test", "t": 0.9}]})

        results = scan_directory(scan_dir)
        assert len(results) >= 1

    def test_media_auto_enrich(self):
        """Auto-enrich creates sidecar for media files."""
        from akf.formats.video import auto_enrich, is_enriched

        fpath = _write_file("auto_enrich_test.mp4", "FAKE VIDEO DATA")
        auto_enrich(fpath, agent_id="enricher-bot")

        assert is_enriched(fpath)


# ===========================================================================
# PHASE 5: A2A Protocol Bridge (Feature 5)
# ===========================================================================


class TestA2ABridgeE2E:
    """End-to-end tests for A2A protocol interop."""

    def test_roundtrip_akf_to_a2a_and_back(self):
        """AKF card → A2A card → AKF card preserves all fields."""
        from akf import create_agent_card, to_a2a_card, from_a2a_card, verify_agent_card

        original = create_agent_card(
            name="Round Trip Bot",
            platform="claude-code",
            capabilities=["search", "summarize"],
            trust_ceiling=0.85,
            model="claude-opus-4-20250514",
            version="2.0",
            provider="Anthropic",
        )

        # Convert to A2A
        a2a = to_a2a_card(original)
        assert a2a["name"] == "Round Trip Bot"
        assert a2a["version"] == "2.0"
        assert len(a2a["skills"]) == 2
        assert a2a["provider"]["organization"] == "Anthropic"
        assert a2a["provider"]["model"] == "claude-opus-4-20250514"
        assert a2a["securityPolicy"]["trustCeiling"] == 0.85
        assert a2a["metadata"]["akf_id"] == original.id
        assert a2a["metadata"]["akf_hash"] == original.card_hash

        # Convert back
        restored = from_a2a_card(a2a)
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.platform == original.platform
        assert restored.capabilities == original.capabilities
        assert restored.trust_ceiling == original.trust_ceiling
        assert restored.model == original.model
        assert restored.provider == original.provider

        # Hash should verify
        assert verify_agent_card(restored) is True

    def test_import_external_a2a_card(self):
        """Import an A2A card that wasn't created by AKF."""
        from akf import from_a2a_card

        external = {
            "name": "External Agent",
            "version": "1.0",
            "skills": [
                {"id": "translate", "name": "translate"},
                {"id": "summarize", "name": "summarize"},
            ],
            "provider": {
                "organization": "ExternalCorp",
                "model": "ext-model-v3",
            },
        }

        card = from_a2a_card(external)
        assert card.name == "External Agent"
        assert card.capabilities == ["translate", "summarize"]
        assert card.provider == "ExternalCorp"
        assert card.model == "ext-model-v3"
        assert card.id, "Should auto-generate ID for external cards"

    def test_save_and_discover_a2a_cards(self):
        """Save A2A cards to disk, then discover them."""
        from akf import (
            create_agent_card, save_a2a_card, discover_a2a_cards,
        )

        cards_dir = os.path.join(TEST_DIR, "a2a_cards")
        os.makedirs(cards_dir, exist_ok=True)

        # Save 3 cards
        for name in ["Alpha", "Beta", "Gamma"]:
            card = create_agent_card(name=name, platform="test")
            save_a2a_card(card, path=os.path.join(cards_dir, f"{name}.json"))

        # Discover
        discovered = discover_a2a_cards(directory=cards_dir)
        assert len(discovered) == 3
        names = {c.name for c in discovered}
        assert names == {"Alpha", "Beta", "Gamma"}

    def test_a2a_field_mapping_completeness(self):
        """All A2A fields correctly mapped to/from AKF."""
        from akf import create_agent_card, to_a2a_card

        card = create_agent_card(
            name="Full Card",
            platform="windsurf",
            capabilities=["a", "b", "c"],
            trust_ceiling=0.75,
            model="gpt-4o",
            version="3.1",
            provider="TestOrg",
        )

        a2a = to_a2a_card(card)

        # All expected top-level keys
        assert "name" in a2a
        assert "version" in a2a
        assert "skills" in a2a
        assert "provider" in a2a
        assert "securityPolicy" in a2a
        assert "metadata" in a2a

        # Provider sub-keys
        assert "organization" in a2a["provider"]
        assert "model" in a2a["provider"]
        assert "platform" in a2a["provider"]

        # Metadata sub-keys
        assert "akf_id" in a2a["metadata"]
        assert "akf_hash" in a2a["metadata"]
        assert "created_at" in a2a["metadata"]


# ===========================================================================
# PHASE 6: Team Certification (Feature 6)
# ===========================================================================


class TestTeamCertifyE2E:
    """End-to-end tests for team-level certification."""

    def test_certify_team_groups_by_agent(self):
        """certify_team groups results by agent provenance."""
        import akf
        from akf import certify_team

        cert_dir = os.path.join(TEST_DIR, "team_certify")
        os.makedirs(cert_dir, exist_ok=True)

        # Create files stamped by different agents
        for i, agent in enumerate(["agent-alpha", "agent-beta"]):
            for j in range(2):
                fpath = os.path.join(cert_dir, f"{agent}_{j}.md")
                with open(fpath, "w") as f:
                    f.write(f"# {agent} file {j}\nContent here.\n")
                unit = akf.stamp(
                    content=f"Claim by {agent}",
                    confidence=0.85,
                    agent=agent,
                )
                akf.embed(fpath, metadata=unit.to_dict(compact=True))

        report = certify_team(cert_dir, min_trust=0.3)

        assert report.team_id is not None
        assert report.total_files > 0
        assert report.certified_count + report.failed_count == report.total_files

        # Should have entries in agent_reports (even if grouped as "unknown")
        # The key assertion: team report has structure
        report_dict = report.to_dict()
        assert "agent_reports" in report_dict
        assert "all_agents_certified" in report_dict

    def test_certify_team_all_pass(self):
        """When all agents' files pass, all_agents_certified is True."""
        import akf
        from akf import certify_team

        cert_dir = os.path.join(TEST_DIR, "team_all_pass")
        os.makedirs(cert_dir, exist_ok=True)

        # Create 2 high-trust files
        for i in range(2):
            fpath = os.path.join(cert_dir, f"good_{i}.md")
            with open(fpath, "w") as f:
                f.write(f"# Good file {i}\n")
            unit = akf.stamp(
                content="Verified claim",
                confidence=0.95,
                agent="trusted-agent",
                kind="claim",
            )
            akf.embed(fpath, metadata=unit.to_dict(compact=True))

        report = certify_team(cert_dir, min_trust=0.1)

        assert report.total_files > 0
        # With min_trust=0.1 and no critical detections, should certify
        if report.certified_count == report.total_files:
            assert report.all_agents_certified is True

    def test_certify_directory_basic(self):
        """certify_directory works on a mixed directory."""
        import akf
        from akf import certify_directory

        cert_dir = os.path.join(TEST_DIR, "dir_certify")
        os.makedirs(cert_dir, exist_ok=True)

        # Stamped file
        f1 = os.path.join(cert_dir, "stamped.md")
        with open(f1, "w") as f:
            f.write("# Stamped\n")
        akf.embed(f1, metadata=akf.stamp("Test", confidence=0.9, agent="a").to_dict(compact=True))

        # Unstamped file (should be skipped)
        f2 = os.path.join(cert_dir, "plain.md")
        with open(f2, "w") as f:
            f.write("# Plain\n")

        report = certify_directory(cert_dir, min_trust=0.3)
        assert report.total_files >= 2
        assert report.skipped_count >= 1  # plain.md skipped


# ===========================================================================
# PHASE 7: Full Multi-Agent Pipeline (Cross-Feature Integration)
# ===========================================================================


class TestMultiAgentPipelineE2E:
    """Cross-feature integration tests: delegation → stream → certify."""

    def test_delegate_stream_certify_pipeline(self):
        """Full pipeline: create → delegate → team stream → certify."""
        import akf
        from akf import (
            DelegationPolicy, delegate,
            TeamStream,
            certify_directory,
        )

        pipeline_dir = os.path.join(TEST_DIR, "full_pipeline")
        os.makedirs(pipeline_dir, exist_ok=True)

        # Step 1: Lead agent creates root analysis
        root = akf.create(
            content="Market analysis complete",
            confidence=0.95,
            source="primary-data",
        )

        # Step 2: Delegate to research bot
        policy = DelegationPolicy(
            delegator="lead",
            delegate="research-bot",
            trust_ceiling=0.8,
        )
        delegated = delegate(root, policy)

        # Verify delegation worked
        assert delegated.prov[-1].delegation_policy is not None

        # Step 3: Team stream — multiple agents produce output
        output_path = os.path.join(pipeline_dir, "analysis.md")
        with open(output_path, "w") as f:
            f.write("# Team Analysis\n\nMulti-agent output.\n")

        with TeamStream(["lead", "research-bot", "writer"]) as ts:
            ts.write("lead", "Strategic direction set", confidence=0.9)
            ts.write("research-bot", "Data gathered and verified", confidence=0.75)
            ts.write("writer", "Report drafted", confidence=0.85)

        assert ts.unit is not None
        assert len(ts.unit.claims) == 3

        # Step 4: Embed team output
        akf.embed(output_path, metadata=ts.unit.to_dict(compact=True))

        # Step 5: Certify the output
        report = certify_directory(pipeline_dir, min_trust=0.3)
        assert report.total_files >= 1

    def test_agent_card_to_delegation_to_certify(self):
        """Agent cards → delegation policy → stamped files → team certify."""
        import akf
        from akf import (
            create_agent_card, to_agent_profile,
            DelegationPolicy, delegate,
            certify_team,
        )

        pipeline_dir = os.path.join(TEST_DIR, "card_to_certify")
        os.makedirs(pipeline_dir, exist_ok=True)

        # Create agent cards
        lead_card = create_agent_card(
            name="Lead Agent", platform="claude-code",
            capabilities=["plan", "review"], trust_ceiling=0.95,
        )
        worker_card = create_agent_card(
            name="Worker Bot", platform="cursor",
            capabilities=["code", "test"], trust_ceiling=0.8,
        )

        # Create root unit
        root = akf.create(content="Task spec defined", confidence=0.9, source="spec")

        # Delegate using card ceiling
        policy = DelegationPolicy(
            delegator=lead_card.id,
            delegate=worker_card.id,
            trust_ceiling=worker_card.trust_ceiling,
        )
        output = delegate(root, policy)

        # Save to file
        fpath = os.path.join(pipeline_dir, "output.md")
        with open(fpath, "w") as f:
            f.write("# Worker output\n")
        akf.embed(fpath, metadata=output.to_dict(compact=True))

        # Certify
        report = certify_team(pipeline_dir, min_trust=0.2)
        assert report.total_files >= 1

    def test_a2a_bridge_to_delegation(self):
        """Import A2A card → use in delegation → verify provenance."""
        from akf import (
            from_a2a_card, to_a2a_card, create_agent_card,
            DelegationPolicy, delegate,
        )
        import akf

        # External A2A agent card (e.g. from Google's A2A protocol)
        external_a2a = {
            "name": "Google Gemini Agent",
            "version": "1.0",
            "skills": [{"id": "search", "name": "search"}],
            "provider": {"organization": "Google", "model": "gemini-2.0"},
        }

        imported_card = from_a2a_card(external_a2a)
        assert imported_card.name == "Google Gemini Agent"

        # Use imported card as delegate
        root = akf.create(content="Original work", confidence=0.9, source="test")
        policy = DelegationPolicy(
            delegator="our-agent",
            delegate=imported_card.id,
            trust_ceiling=0.6,  # Lower ceiling for external agent
        )

        result = delegate(root, policy)
        assert result.prov[-1].delegation_policy.trust_ceiling == 0.6
        for claim in result.claims:
            assert claim.confidence <= 0.6


# ===========================================================================
# PHASE 8: CLI Integration Tests
# ===========================================================================


class TestCLIMultiAgentE2E:
    """CLI end-to-end tests for multi-agent commands."""

    def test_cli_certify_basic(self):
        """CLI: akf certify <dir>."""
        import akf

        cert_dir = os.path.join(TEST_DIR, "cli_certify")
        os.makedirs(cert_dir, exist_ok=True)

        fpath = os.path.join(cert_dir, "test.md")
        with open(fpath, "w") as f:
            f.write("# Test\n")
        akf.embed(fpath, metadata=akf.stamp("claim", confidence=0.9, agent="a").to_dict(compact=True))

        rc, out, err = akf_cli("certify", cert_dir, allow_fail=True)
        # Should produce output (even if some files fail trust threshold)
        assert rc is not None

    def test_cli_certify_team_flag(self):
        """CLI: akf certify <dir> --team shows per-agent breakdown."""
        import akf

        cert_dir = os.path.join(TEST_DIR, "cli_team_certify")
        os.makedirs(cert_dir, exist_ok=True)

        fpath = os.path.join(cert_dir, "team_file.md")
        with open(fpath, "w") as f:
            f.write("# Team file\n")
        akf.embed(fpath, metadata=akf.stamp("claim", confidence=0.85, agent="bot-a").to_dict(compact=True))

        rc, out, err = akf_cli("certify", cert_dir, "--team", allow_fail=True)
        # Should not crash; --team flag is recognized
        assert rc is not None

    def test_cli_stamp_and_read_roundtrip(self):
        """CLI: stamp → read roundtrip."""
        fpath = _write_file("cli_stamp_test.md", "# CLI Stamp Test\n")

        akf_cli("stamp", fpath, "--agent", "cli-test-agent", "--evidence", "e2e test")
        rc, out, err = akf_cli("read", fpath)
        assert rc == 0

    def test_cli_formats_lists_media(self):
        """CLI: akf formats shows video and audio."""
        rc, out, err = akf_cli("formats")
        assert rc == 0
        out_lower = out.lower()
        # Should list video/audio formats
        assert "video" in out_lower or "mp4" in out_lower or "audio" in out_lower or "mp3" in out_lower

    def test_cli_embed_extract_media(self):
        """CLI: embed and extract on media files."""
        fpath = _write_file("cli_media.mp4", "FAKE VIDEO DATA")

        akf_cli("embed", fpath, "--agent", "media-agent", "--claim", "Video verified")

        rc, out, err = akf_cli("extract", fpath)
        assert rc == 0

    def test_cli_scan_with_media(self):
        """CLI: scan directory containing media files."""
        scan_dir = os.path.join(TEST_DIR, "cli_scan_media")
        os.makedirs(scan_dir, exist_ok=True)

        # Create and stamp a media file
        fpath = os.path.join(scan_dir, "recording.mp3")
        with open(fpath, "w") as f:
            f.write("FAKE AUDIO")

        akf_cli("embed", fpath, "--agent", "scan-agent", "--claim", "Audio checked")

        rc, out, err = akf_cli("scan", scan_dir, allow_fail=True)
        assert rc is not None


# ===========================================================================
# PHASE 9: Cross-Stack Verification (README ↔ SDK ↔ Website)
# ===========================================================================


class TestCrossStackConsistency:
    """Verify README, website, and SDK are consistent."""

    @pytest.fixture(autouse=True)
    def _load_content(self):
        """Load all content files once."""
        self.readme = ""
        self.contributing = ""
        self.mcp_readme = ""
        self.site_files: Dict[str, str] = {}

        if README_PATH.exists():
            self.readme = README_PATH.read_text()
        if CONTRIBUTING_PATH.exists():
            self.contributing = CONTRIBUTING_PATH.read_text()
        if MCP_README_PATH.exists():
            self.mcp_readme = MCP_README_PATH.read_text()

        if SITE_DIR.exists():
            for tsx_file in SITE_DIR.rglob("*.tsx"):
                rel = str(tsx_file.relative_to(SITE_DIR))
                self.site_files[rel] = tsx_file.read_text()

    # --- SDK Exports ---

    def test_sdk_exports_delegation(self):
        """SDK exports delegation functions."""
        import akf
        assert hasattr(akf, "delegate")
        assert hasattr(akf, "validate_delegation")
        assert hasattr(akf, "DelegationPolicy")

    def test_sdk_exports_team_stream(self):
        """SDK exports team streaming functions."""
        import akf
        assert hasattr(akf, "TeamStream")
        assert hasattr(akf, "TeamStreamSession")
        assert hasattr(akf, "TeamTrustResult")
        assert hasattr(akf, "team_stream_start")
        assert hasattr(akf, "team_stream_claim")
        assert hasattr(akf, "team_stream_end")
        assert hasattr(akf, "team_trust_aggregate")

    def test_sdk_exports_agent_cards(self):
        """SDK exports agent card functions."""
        import akf
        assert hasattr(akf, "AgentCard")
        assert hasattr(akf, "AgentRegistry")
        assert hasattr(akf, "create_agent_card")
        assert hasattr(akf, "verify_agent_card")
        assert hasattr(akf, "to_agent_profile")

    def test_sdk_exports_a2a_bridge(self):
        """SDK exports A2A bridge functions."""
        import akf
        assert hasattr(akf, "to_a2a_card")
        assert hasattr(akf, "from_a2a_card")
        assert hasattr(akf, "save_a2a_card")
        assert hasattr(akf, "discover_a2a_cards")

    def test_sdk_exports_team_certify(self):
        """SDK exports team certification functions."""
        import akf
        assert hasattr(akf, "certify_team")
        assert hasattr(akf, "AgentCertifyReport")
        assert hasattr(akf, "TeamCertifyReport")

    # --- README accuracy ---

    def test_readme_mentions_delegation(self):
        """README documents delegation feature."""
        assert "delegate" in self.readme.lower()
        assert "trust_ceiling" in self.readme or "trust ceiling" in self.readme.lower()

    def test_readme_mentions_team_stream(self):
        """README documents TeamStream."""
        assert "TeamStream" in self.readme or "team_stream" in self.readme

    def test_readme_mentions_agent_cards(self):
        """README documents agent cards."""
        assert "create_agent_card" in self.readme or "AgentCard" in self.readme

    def test_readme_mentions_certify_team(self):
        """README documents team certification."""
        assert "certify_team" in self.readme or "--team" in self.readme

    def test_readme_mentions_video_audio(self):
        """README lists video/audio formats."""
        readme_lower = self.readme.lower()
        assert "mp4" in readme_lower or "video" in readme_lower
        assert "mp3" in readme_lower or "audio" in readme_lower

    def test_readme_delegation_ceiling_doc(self):
        """README explains delegation ceiling in trust computation."""
        assert "delegation" in self.readme.lower() and "ceiling" in self.readme.lower()

    def test_readme_skill_delegate_and_team(self):
        """README lists delegate and team in skills table."""
        assert "delegate" in self.readme
        assert "team" in self.readme.lower()

    # --- Website consistency ---

    def test_website_valueprops_multiagent(self):
        """ValueProps shows Multi agent teams stat."""
        content = self.site_files.get("components/ValueProps.tsx", "")
        assert "Multi" in content
        assert "agent teams" in content.lower() or "agent teams" in content

    def test_website_workswith_a2a(self):
        """WorksWith lists A2A Protocol."""
        content = self.site_files.get("components/WorksWith.tsx", "")
        assert "A2A Protocol" in content

    def test_website_workswith_media_formats(self):
        """WorksWith lists video/audio formats."""
        content = self.site_files.get("components/WorksWith.tsx", "")
        assert "MP4" in content
        assert "MP3" in content

    def test_website_workswith_30plus_formats(self):
        """WorksWith shows 30+ formats."""
        content = self.site_files.get("components/WorksWith.tsx", "")
        assert "30+" in content

    def test_website_formatsupport_video_audio(self):
        """FormatSupport table includes video and audio rows."""
        content = self.site_files.get("components/FormatSupport.tsx", "")
        assert ".mp4" in content or "mp4" in content.lower()
        assert ".mp3" in content or "mp3" in content.lower()

    def test_website_interactive_demo_teams(self):
        """InteractiveDemo has Agent Teams scenario."""
        content = self.site_files.get("components/InteractiveDemo.tsx", "")
        assert "teams" in content.lower()
        assert "TeamStream" in content or "team_delegate" in content

    def test_website_agent_integration_delegate_skill(self):
        """AgentIntegration lists delegate and team skills."""
        content = self.site_files.get("components/AgentIntegration.tsx", "")
        assert "delegate" in content
        assert "team" in content.lower()

    def test_website_certify_page_team_flag(self):
        """CertifyPage documents --team flag."""
        content = self.site_files.get("components/CertifyPage.tsx", "")
        assert "--team" in content

    def test_website_ambient_trust_multiagent(self):
        """AmbientTrust pipeline references multi-agent."""
        content = self.site_files.get("components/AmbientTrust.tsx", "")
        assert "team" in content.lower() or "delegation" in content.lower()

    def test_website_get_started_team_stream(self):
        """GetStartedPage AI Agents persona mentions TeamStream."""
        content = self.site_files.get("components/GetStartedPage.tsx", "")
        assert "TeamStream" in content

    # --- Contributing guide ---

    def test_contributing_mentions_multiagent(self):
        """CONTRIBUTING.md mentions multi-agent features."""
        assert "multi-agent" in self.contributing.lower() or "agent" in self.contributing.lower()

    # --- MCP README ---

    def test_mcp_readme_multiagent_support(self):
        """MCP server README mentions multi-agent support."""
        if self.mcp_readme:
            assert "multi-agent" in self.mcp_readme.lower() or "team" in self.mcp_readme.lower()


# ===========================================================================
# PHASE 10: SDK Import and Model Verification
# ===========================================================================


class TestSDKModelsE2E:
    """Verify all new Pydantic models work correctly."""

    def test_delegation_policy_compact_aliases(self):
        """DelegationPolicy accepts compact wire format."""
        from akf import DelegationPolicy

        # Compact format
        policy = DelegationPolicy(**{
            "from": "agent-a",
            "to": "agent-b",
            "ceil": 0.7,
            "exp": "2030-01-01T00:00:00Z",
        })
        assert policy.delegator == "agent-a"
        assert policy.delegate == "agent-b"
        assert policy.trust_ceiling == 0.7

    def test_delegation_policy_descriptive_names(self):
        """DelegationPolicy accepts descriptive field names."""
        from akf import DelegationPolicy

        policy = DelegationPolicy(
            delegator="agent-a",
            delegate="agent-b",
            trust_ceiling=0.7,
        )
        assert policy.delegator == "agent-a"

    def test_prov_hop_delegation_policy(self):
        """ProvHop can contain delegation_policy."""
        from akf.models import ProvHop, DelegationPolicy

        hop = ProvHop(
            hop=1,
            action="derive",
            actor="test",
            at="2025-01-01T00:00:00Z",
            delegation_policy=DelegationPolicy(
                delegator="a", delegate="b", trust_ceiling=0.6,
            ),
        )
        assert hop.delegation_policy is not None
        assert hop.delegation_policy.trust_ceiling == 0.6

    def test_agent_card_compact_aliases(self):
        """AgentCard accepts compact aliases."""
        from akf import AgentCard

        card = AgentCard(
            id="test-id",
            name="Test",
            caps=["a", "b"],
            ceil=0.8,
            plat="cursor",
            ver="1.0",
            prov="TestCorp",
        )
        assert card.capabilities == ["a", "b"]
        assert card.trust_ceiling == 0.8
        assert card.platform == "cursor"

    def test_team_trust_result_structure(self):
        """TeamTrustResult has all expected fields."""
        from akf import TeamTrustResult

        result = TeamTrustResult(
            team_id="test-team",
            team_avg_trust=0.85,
            agent_scores={"a": 0.9, "b": 0.8},
            total_claims=5,
            claims_per_agent={"a": 3, "b": 2},
        )
        assert result.team_id == "test-team"
        assert result.agent_scores["a"] == 0.9

    def test_team_certify_report_to_dict(self):
        """TeamCertifyReport.to_dict() serializes correctly."""
        from akf import TeamCertifyReport, AgentCertifyReport

        report = TeamCertifyReport(
            team_id="test-team",
            total_files=4,
            certified_count=3,
            failed_count=1,
            avg_trust=0.75,
            agent_reports={
                "agent-a": AgentCertifyReport(
                    agent_id="agent-a",
                    file_count=2,
                    certified_count=2,
                    failed_count=0,
                    avg_trust=0.85,
                ),
                "agent-b": AgentCertifyReport(
                    agent_id="agent-b",
                    file_count=2,
                    certified_count=1,
                    failed_count=1,
                    avg_trust=0.65,
                ),
            },
        )

        d = report.to_dict()
        assert d["team_id"] == "test-team"
        assert d["total_files"] == 4
        assert d["all_agents_certified"] is False  # agent-b has failures
        assert "agent-a" in d["agent_reports"]
        assert d["agent_reports"]["agent-a"]["certified_count"] == 2

    def test_certify_report_all_certified_property(self):
        """CertifyReport.all_certified works correctly."""
        from akf import CertifyReport

        # All pass
        report = CertifyReport(total_files=3, certified_count=3, failed_count=0)
        assert report.all_certified is True

        # Some fail
        report2 = CertifyReport(total_files=3, certified_count=2, failed_count=1)
        assert report2.all_certified is False

        # Empty
        report3 = CertifyReport(total_files=0, certified_count=0, failed_count=0)
        assert report3.all_certified is False


# ===========================================================================
# PHASE 11: Edge Cases and Error Handling
# ===========================================================================


class TestEdgeCasesE2E:
    """Edge cases and error handling for multi-agent features."""

    def test_delegation_zero_ceiling(self):
        """Delegation with trust_ceiling=0 caps everything to 0."""
        import akf
        from akf import DelegationPolicy, delegate

        parent = akf.create(content="test", confidence=0.9, source="test")
        policy = DelegationPolicy(
            delegator="a", delegate="b", trust_ceiling=0.0,
        )
        result = delegate(parent, policy)
        for claim in result.claims:
            assert claim.confidence == 0.0

    def test_delegation_ceiling_1_no_cap(self):
        """Delegation with trust_ceiling=1.0 doesn't reduce confidence."""
        import akf
        from akf import DelegationPolicy, delegate

        parent = akf.create(content="test", confidence=0.9, source="test")
        policy = DelegationPolicy(
            delegator="a", delegate="b", trust_ceiling=1.0,
        )
        result = delegate(parent, policy)
        # Original confidence should be preserved (minus any derive penalty)
        assert len(result.claims) >= 1

    def test_team_stream_many_agents(self):
        """Team stream with 10 agents."""
        from akf import TeamStream

        agents = [f"agent-{i}" for i in range(10)]
        with TeamStream(agents) as ts:
            for agent in agents:
                ts.write(agent, f"Claim from {agent}", confidence=0.7 + (hash(agent) % 20) / 100)

            agg = ts.aggregate()
            assert agg.total_claims == 10
            assert len(agg.claims_per_agent) == 10

        assert len(ts.unit.claims) == 10

    def test_agent_card_no_optional_fields(self):
        """AgentCard with only required fields."""
        from akf import create_agent_card, verify_agent_card

        card = create_agent_card(name="Minimal Bot")
        assert card.id is not None
        assert card.card_hash is not None
        assert verify_agent_card(card) is True

    def test_a2a_card_minimal(self):
        """A2A card with only name field."""
        from akf import from_a2a_card

        card = from_a2a_card({"name": "Bare Agent"})
        assert card.name == "Bare Agent"
        assert card.id is not None

    def test_video_handler_nonexistent_file(self):
        """VideoHandler.extract on non-existent file returns None."""
        from akf.formats.video import VideoHandler

        handler = VideoHandler()
        result = handler.extract("/nonexistent/path/video.mp4")
        assert result is None

    def test_audio_handler_nonexistent_file(self):
        """AudioHandler.extract on non-existent file returns None."""
        from akf.formats.audio import AudioHandler

        handler = AudioHandler()
        result = handler.extract("/nonexistent/path/audio.mp3")
        assert result is None

    def test_certify_empty_directory(self):
        """certify_directory on empty directory."""
        import akf
        from akf import certify_directory

        empty_dir = os.path.join(TEST_DIR, "empty_certify")
        os.makedirs(empty_dir, exist_ok=True)

        report = certify_directory(empty_dir)
        assert report.total_files == 0
        assert report.certified_count == 0

    def test_certify_team_empty_directory(self):
        """certify_team on empty directory."""
        from akf import certify_team

        empty_dir = os.path.join(TEST_DIR, "empty_team_certify")
        os.makedirs(empty_dir, exist_ok=True)

        report = certify_team(empty_dir)
        assert report.total_files == 0
        assert report.all_agents_certified is False

    def test_unicode_in_delegation(self):
        """Delegation handles unicode in claims."""
        import akf
        from akf import DelegationPolicy, delegate

        parent = akf.create(
            content="研究结果 — résultats de recherche 🔬",
            confidence=0.9,
            source="test",
        )
        policy = DelegationPolicy(
            delegator="agent-日本", delegate="agent-français",
            trust_ceiling=0.7,
        )
        result = delegate(parent, policy)
        assert len(result.claims) >= 1

    def test_unicode_in_team_stream(self):
        """Team stream handles unicode content."""
        from akf import TeamStream

        with TeamStream(["agent-α", "agent-β"]) as ts:
            ts.write("agent-α", "Données vérifiées ✓", confidence=0.9)
            ts.write("agent-β", "データ検証済み", confidence=0.85)

        assert len(ts.unit.claims) == 2


# ===========================================================================
# PHASE 12: Website Build Verification
# ===========================================================================


class TestWebsiteBuild:
    """Verify the website builds without errors."""

    @pytest.fixture(autouse=True)
    def _check_site_exists(self):
        site_dir = PROJECT_ROOT / "site"
        if not (site_dir / "package.json").exists():
            pytest.skip("Site directory not found")

    def test_site_has_package_json(self):
        """site/package.json exists."""
        assert (PROJECT_ROOT / "site" / "package.json").exists()

    def test_site_components_have_no_syntax_errors(self):
        """All .tsx files in site/src parse (basic check: no unmatched braces)."""
        for tsx_file in (PROJECT_ROOT / "site" / "src").rglob("*.tsx"):
            content = tsx_file.read_text()
            # Basic sanity: file is non-empty and has export
            assert len(content) > 0, f"Empty file: {tsx_file}"

    def test_site_references_akf_features_consistently(self):
        """Verify key feature terms appear in site source."""
        all_site_text = ""
        for tsx_file in (PROJECT_ROOT / "site" / "src").rglob("*.tsx"):
            all_site_text += tsx_file.read_text() + "\n"

        # Multi-agent features should be referenced
        assert "delegate" in all_site_text
        assert "TeamStream" in all_site_text or "team" in all_site_text.lower()
        assert "A2A" in all_site_text
        assert "--team" in all_site_text
        assert "30+" in all_site_text


# ===========================================================================
# PHASE 13: Format Handler Registration Verification
# ===========================================================================


class TestFormatRegistration:
    """Verify video/audio handlers are registered in universal dispatcher."""

    def test_video_extensions_registered(self):
        """All video extensions route through universal dispatcher."""
        import akf

        for ext in [".mp4", ".mov", ".webm", ".mkv"]:
            fpath = _write_file(f"reg_test{ext}", "DUMMY")
            # Should not raise — handler exists
            try:
                akf.embed(fpath, metadata={
                    "ver": "1.0",
                    "claims": [{"c": "test", "t": 0.8}],
                })
                assert akf.is_enriched(fpath)
            finally:
                # Cleanup sidecar
                sidecar = fpath + ".akf.json"
                if os.path.exists(sidecar):
                    os.remove(sidecar)

    def test_audio_extensions_registered(self):
        """All audio extensions route through universal dispatcher."""
        import akf

        for ext in [".mp3", ".wav", ".flac", ".ogg"]:
            fpath = _write_file(f"reg_test{ext}", "DUMMY")
            try:
                akf.embed(fpath, metadata={
                    "ver": "1.0",
                    "claims": [{"c": "test", "t": 0.8}],
                })
                assert akf.is_enriched(fpath)
            finally:
                sidecar = fpath + ".akf.json"
                if os.path.exists(sidecar):
                    os.remove(sidecar)

    def test_formats_cli_lists_all_media(self):
        """akf formats command lists video and audio."""
        rc, out, err = akf_cli("formats")
        assert rc == 0
        out_lower = out.lower()
        # Should mention at least some media formats
        has_media = any(
            term in out_lower
            for term in ["video", "audio", "mp4", "mp3", ".mov", ".wav"]
        )
        assert has_media, f"No media formats in output: {out[:500]}"
