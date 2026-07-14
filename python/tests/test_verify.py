"""Tests for replay evidence + akf verify (#128)."""

import json
import os
import time

import pytest
from click.testing import CliRunner

from akf.cli import main
from akf.stamp import stamp_file
from akf.verify import verify_file


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def replayable(tmp_path):
    """A stamped file whose replay probe checks its dep's content."""
    dep = tmp_path / "helper.py"
    dep.write_text("VALUE = 1\n")
    f = tmp_path / "main.py"
    f.write_text("import helper\n")
    stamp_file(
        str(f), agent="claude-code", evidence=["tests pass"],
        replay="python3 -c \"import helper; raise SystemExit(0 if helper.VALUE == 1 else 1)\"",
    )
    return f


class TestReplayRecording:
    def test_recipe_recorded_with_input_hash(self, replayable):
        unit_ev = None
        from akf import universal
        from akf.models import AKF
        unit = AKF(**universal.extract(str(replayable)))
        for ev in unit.claims[0].evidence or []:
            if getattr(ev, "replay", None):
                unit_ev = ev
        assert unit_ev is not None
        assert unit_ev.replay.command.startswith("python3 -c")
        assert unit_ev.replay.expected_exit == 0
        assert unit_ev.replay.input_hash.startswith("sha256:")

    def test_replay_dict_form(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_text("# x\n")
        unit = stamp_file(str(f), agent="a",
                          replay={"command": "true", "expected_exit": 0})
        assert any(getattr(e, "replay", None) for e in unit.claims[0].evidence)


class TestVerify:
    def test_default_is_inspection_not_execution(self, replayable):
        r = verify_file(str(replayable))
        assert r.verdict == "REPLAY_AVAILABLE"
        assert r.executed is False
        assert r.inputs_drifted is False
        assert r.exit_code == 0

    def test_run_confirms(self, replayable):
        r = verify_file(str(replayable), run=True)
        assert r.verdict == "CONFIRMED"
        assert r.exit_code == 0
        assert r.executed

    def test_drifted_inputs_split_the_verdict(self, replayable):
        # Change the dep so its content still satisfies the probe's assertion
        # semantics differently: VALUE stays 1 but file content changes.
        (replayable.parent / "helper.py").write_text("VALUE = 1  # edited\n")
        r = verify_file(str(replayable), run=True)
        assert r.verdict == "CONFIRMED_DRIFTED"
        assert r.exit_code == 1
        assert r.inputs_drifted is True

    def test_refuted_when_probe_fails(self, replayable):
        (replayable.parent / "helper.py").write_text("VALUE = 2\n")
        r = verify_file(str(replayable), run=True)
        assert r.verdict == "REFUTED"
        assert r.exit_code == 2

    def test_unreplayable_without_recipe(self, tmp_path):
        f = tmp_path / "plain.md"
        f.write_text("# p\n")
        stamp_file(str(f), agent="a", evidence=["tests pass"])
        r = verify_file(str(f), run=True)
        assert r.verdict == "UNREPLAYABLE"
        assert r.exit_code == 3


class TestVerifyCli:
    def test_cli_inspection_shows_command(self, runner, replayable):
        result = runner.invoke(main, ["replay", str(replayable)])
        assert result.exit_code == 0
        assert "REPLAY_AVAILABLE" in result.output
        assert "replay=" in result.output

    def test_cli_run_json(self, runner, replayable):
        result = runner.invoke(main, ["replay", str(replayable), "--run", "--json"])
        assert result.exit_code == 0
        assert json.loads(result.output)["verdict"] == "CONFIRMED"

    def test_stamp_cli_replay_flag(self, runner, tmp_path):
        f = tmp_path / "r.md"
        f.write_text("# r\n")
        res = runner.invoke(main, ["stamp", str(f), "--agent", "a", "--replay", "true"])
        assert res.exit_code == 0
        out = runner.invoke(main, ["replay", str(f), "--run"])
        assert "CONFIRMED" in out.output
