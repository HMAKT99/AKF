"""Tests for dependency-aware staleness (#124)."""

import os
import time

import pytest

from akf.check import check_file
from akf.deps import resolve_local_deps, changed_deps
from akf.stamp import stamp_file


@pytest.fixture
def pkg(tmp_path):
    """A small package: main.py imports helper.py and pkg/util.py."""
    (tmp_path / "helper.py").write_text("def help(): return 1\n")
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("")
    (tmp_path / "pkg" / "util.py").write_text("def util(): return 2\n")
    main = tmp_path / "main.py"
    main.write_text(
        "import helper\n"
        "from pkg import util\n"
        "import os\n"          # stdlib — must be ignored
        "import requests\n"    # third-party — must be ignored
        "def run(): return helper.help() + util.util()\n"
    )
    return main


class TestResolveLocalDeps:
    def test_finds_local_imports_only(self, pkg):
        deps = resolve_local_deps(str(pkg))
        assert "helper.py" in deps
        assert os.path.join("pkg", "__init__.py") in deps
        assert all("os" not in k and "requests" not in k for k in deps)
        assert all(v.startswith("sha256:") for v in deps.values())

    def test_non_python_file_empty(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# hi\n")
        assert resolve_local_deps(str(f)) == {}

    def test_changed_deps_detects_edit(self, pkg):
        deps = resolve_local_deps(str(pkg))
        assert changed_deps(str(pkg), deps) == []
        (pkg.parent / "helper.py").write_text("def help(): return 999\n")
        assert "helper.py" in changed_deps(str(pkg), deps)

    def test_deleted_dep_counts_as_changed(self, pkg):
        deps = resolve_local_deps(str(pkg))
        (pkg.parent / "helper.py").unlink()
        assert "helper.py" in changed_deps(str(pkg), deps)


class TestDependencyStaleness:
    def _freeze_mtime(self, path):
        """Keep the stamped file's own mtime inside the stamp tolerance."""
        past = time.time() - 1
        os.utime(path, (past, past))

    def test_dep_change_flips_stale(self, pkg):
        stamp_file(str(pkg), agent="claude-code", evidence=["tests pass"])
        assert check_file(str(pkg)).status == "OK"

        # Edit only the dependency — main.py's bytes never move.
        (pkg.parent / "helper.py").write_text("def help(): return 999\n")
        self._freeze_mtime(pkg)
        result = check_file(str(pkg))
        assert result.status == "STALE"
        assert result.reason == "dependency_changed"

    def test_untouched_deps_stay_ok(self, pkg):
        stamp_file(str(pkg), agent="claude-code", evidence=["tests pass"])
        self._freeze_mtime(pkg)
        assert check_file(str(pkg)).status == "OK"

    def test_deps_recorded_in_stamp_meta(self, pkg):
        unit = stamp_file(str(pkg), agent="claude-code")
        assert "helper.py" in unit.meta["deps"]
