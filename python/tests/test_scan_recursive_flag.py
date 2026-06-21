"""Regression tests for the ``akf scan`` recursion flag.

``--recursive`` / ``-r`` was defined as ``is_flag=True, default=True`` which made
passing the flag *disable* recursion — the opposite of its name. These tests pin the
correct behaviour: recursive forms walk the whole tree, non-recursive forms stay at
the top level.
"""

import re

from click.testing import CliRunner

from akf.cli import main


def _stamp(runner: CliRunner, path) -> None:
    res = runner.invoke(
        main, ["stamp", str(path), "--agent", "claude-code", "--evidence", "t"]
    )
    assert res.exit_code == 0, res.output


def _scanned_count(output: str) -> int:
    m = re.search(r"(\d+) scanned", output)
    assert m, "no scan count found in output:\n" + output
    return int(m.group(1))


def _build_tree(tmp_path) -> tuple:
    """Two stamped files at the top level, three nested deeper."""
    (tmp_path / "sub" / "deep").mkdir(parents=True)
    top = [tmp_path / "a.txt", tmp_path / "b.txt"]
    nested = [
        tmp_path / "sub" / "c.txt",
        tmp_path / "sub" / "deep" / "d.txt",
        tmp_path / "sub" / "deep" / "e.txt",
    ]
    runner = CliRunner()
    for p in top + nested:
        p.write_text("x", encoding="utf-8")
        _stamp(runner, p)
    return len(top), len(top) + len(nested)


def test_recursive_forms_walk_whole_tree(tmp_path) -> None:
    n_top, total = _build_tree(tmp_path)
    runner = CliRunner()

    # Default is recursive.
    assert _scanned_count(runner.invoke(main, ["scan", str(tmp_path)]).output) == total

    # -r / --recursive must also recurse (regression: these used to scan top-level only).
    for flag in ("-r", "--recursive"):
        out = runner.invoke(main, ["scan", str(tmp_path), flag]).output
        assert _scanned_count(out) == total, "{} should recurse".format(flag)


def test_non_recursive_forms_stay_top_level(tmp_path) -> None:
    n_top, total = _build_tree(tmp_path)
    runner = CliRunner()

    for flag in ("--no-recursive", "-R"):
        out = runner.invoke(main, ["scan", str(tmp_path), flag]).output
        assert _scanned_count(out) == n_top, "{} should scan top-level only".format(flag)
