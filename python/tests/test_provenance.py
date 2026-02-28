"""Tests for AKF provenance."""

from akf.models import AKF, Claim, ProvHop
from akf.provenance import (
    add_hop,
    compute_hop_hash,
    compute_integrity_hash,
    format_tree,
    validate_chain,
)
from akf.core import create


class TestHopHash:
    def test_deterministic(self):
        hop = {"hop": 0, "by": "user", "do": "created", "at": "2025-01-01T00:00:00Z"}
        h1 = compute_hop_hash(None, hop)
        h2 = compute_hop_hash(None, hop)
        assert h1 == h2
        assert h1.startswith("sha256:")

    def test_chaining(self):
        hop = {"hop": 0, "by": "user", "do": "created", "at": "2025-01-01T00:00:00Z"}
        h1 = compute_hop_hash(None, hop)
        h2 = compute_hop_hash(h1, {"hop": 1, "by": "agent", "do": "enriched", "at": "2025-01-01T01:00:00Z"})
        assert h1 != h2
        assert h2.startswith("sha256:")

    def test_different_data_different_hash(self):
        h1 = compute_hop_hash(None, {"hop": 0, "by": "a", "do": "created", "at": "2025-01-01T00:00:00Z"})
        h2 = compute_hop_hash(None, {"hop": 0, "by": "b", "do": "created", "at": "2025-01-01T00:00:00Z"})
        assert h1 != h2


class TestIntegrityHash:
    def test_basic(self):
        unit = create("test", t=0.5)
        h = compute_integrity_hash(unit)
        assert h.startswith("sha256:")

    def test_detects_tampering(self):
        unit = create("test", t=0.5)
        h1 = compute_integrity_hash(unit)
        tampered = unit.model_copy(update={"claims": [Claim(c="tampered", t=0.1)]})
        h2 = compute_integrity_hash(tampered)
        assert h1 != h2

    def test_excludes_hash_field(self):
        unit = create("test", t=0.5)
        h1 = compute_integrity_hash(unit)
        unit_with_hash = unit.model_copy(update={"hash": "sha256:old"})
        h2 = compute_integrity_hash(unit_with_hash)
        assert h1 == h2


class TestValidateChain:
    def test_valid_chain(self):
        prov = [
            ProvHop(hop=0, by="a", **{"do": "created"}, at="2025-01-01T00:00:00Z"),
            ProvHop(hop=1, by="b", **{"do": "enriched"}, at="2025-01-01T01:00:00Z"),
        ]
        assert validate_chain(prov) is True

    def test_invalid_chain(self):
        prov = [
            ProvHop(hop=0, by="a", **{"do": "created"}, at="2025-01-01T00:00:00Z"),
            ProvHop(hop=5, by="b", **{"do": "enriched"}, at="2025-01-01T01:00:00Z"),
        ]
        assert validate_chain(prov) is False


class TestAddHop:
    def test_add_first_hop(self):
        unit = create("test", t=0.5)
        updated = add_hop(unit, by="agent", action="enriched", adds=["c1"])
        assert updated.prov is not None
        assert len(updated.prov) == 1
        assert updated.prov[0].hop == 0
        assert updated.hash is not None

    def test_add_second_hop(self):
        unit = create("test", t=0.5)
        unit = add_hop(unit, by="user", action="created")
        unit = add_hop(unit, by="agent", action="enriched", adds=["c2"])
        assert len(unit.prov) == 2
        assert unit.prov[1].hop == 1

    def test_hop_with_penalty(self):
        unit = create("test", t=0.5)
        unit = add_hop(unit, by="agent", action="consumed", penalty=-0.03)
        assert unit.prov[0].pen == -0.03

    def test_hop_with_drops(self):
        unit = create("test", t=0.5)
        unit = add_hop(unit, by="reviewer", action="reviewed", drops=["c1", "c2"])
        assert unit.prov[0].drops == ["c1", "c2"]


class TestFormatTree:
    def test_no_provenance(self):
        unit = create("test", t=0.5)
        assert format_tree(unit) == "(no provenance)"

    def test_single_hop(self):
        unit = create("test", t=0.5)
        unit = add_hop(unit, by="sarah@test.com", action="created", adds=["c1"])
        tree = format_tree(unit)
        assert "sarah@test.com" in tree
        assert "created" in tree

    def test_multi_hop(self):
        unit = create("test", t=0.5)
        unit = add_hop(unit, by="sarah@test.com", action="created", adds=["c1"])
        unit = add_hop(unit, by="copilot", action="enriched", adds=["c2"])
        unit = add_hop(unit, by="agent", action="consumed", drops=["c1"])
        tree = format_tree(unit)
        assert "sarah@test.com" in tree
        assert "copilot" in tree
        assert "agent" in tree
