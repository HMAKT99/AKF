"""Tests for akf stamp --preset (memory, skill) and decay-aware check."""

import json
import os
import time
from datetime import datetime, timedelta, timezone

import pytest
from click.testing import CliRunner

from akf.check import check_file
from akf.cli import main
from akf.presets import STAMP_PRESETS, get_stamp_preset
from akf import universal


@pytest.fixture
def runner():
    return CliRunner()


class TestPresetDefinitions:
    def test_memory_preset(self):
        p = get_stamp_preset("memory")
        assert p["claim_kwargs"]["decay_half_life"] == 30
        assert p["claim_kwargs"]["kind"] == "memory"
        assert p["classification"] == "internal"

    def test_skill_preset(self):
        p = get_stamp_preset("skill")
        assert p["classification"] == "public"
        assert p["claim_kwargs"]["decay_half_life"] == 365
        assert p["claim_kwargs"]["authority_tier"] == 3

    def test_unknown_preset_raises(self):
        with pytest.raises(KeyError):
            get_stamp_preset("nope")


class TestStampPresetCli:
    def test_memory_preset_sets_decay_and_kind(self, runner, tmp_path):
        path = tmp_path / "facts.md"
        path.write_text("# Facts\n")
        result = runner.invoke(main, ["stamp", str(path), "--preset", "memory",
                                      "--agent", "claude-code"])
        assert result.exit_code == 0
        meta = universal.extract(str(path))
        claim = meta["claims"][0]
        assert claim.get("decay") == 30 or claim.get("decay_half_life") == 30
        assert claim.get("kind") == "memory"
        assert meta.get("classification", meta.get("label")) == "internal"

    def test_skill_preset_sets_public_and_tier(self, runner, tmp_path):
        path = tmp_path / "skill.md"
        path.write_text("# Skill\n")
        result = runner.invoke(main, ["stamp", str(path), "--preset", "skill",
                                      "--agent", "acme"])
        assert result.exit_code == 0
        meta = universal.extract(str(path))
        assert meta.get("classification", meta.get("label")) == "public"
        assert meta["claims"][0].get("tier", meta["claims"][0].get("authority_tier")) == 3

    def test_explicit_label_beats_preset(self, runner, tmp_path):
        path = tmp_path / "skill.md"
        path.write_text("# Skill\n")
        runner.invoke(main, ["stamp", str(path), "--preset", "skill",
                             "--label", "confidential"])
        meta = universal.extract(str(path))
        assert meta.get("classification", meta.get("label")) == "confidential"


class TestMemoryDecayInCheck:
    def _backdate_stamp(self, path, days):
        """Rewrite the stamp's created timestamp to `days` ago and keep the
        file mtime older than that so the stamp isn't STALE."""
        meta = universal.extract(str(path))
        old = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        meta["at"] = old
        meta.pop("created", None)
        universal.embed(str(path), metadata=meta)
        past = time.time() - days * 86400
        os.utime(str(path), (past, past))

    def test_fresh_memory_ok_decayed_memory_low(self, runner, tmp_path):
        path = tmp_path / "mem.md"
        path.write_text("# Mem\n")
        runner.invoke(main, ["stamp", str(path), "--preset", "memory",
                             "--agent", "claude-code", "--confidence", "0.9",
                             "--evidence", "tests pass"])
        fresh = check_file(str(path))
        assert fresh.status == "OK"

        self._backdate_stamp(path, days=90)
        decayed = check_file(str(path))
        assert decayed.status == "LOW"
        assert decayed.trust < fresh.trust / 2  # three half-lives
