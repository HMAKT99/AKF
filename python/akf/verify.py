"""Replay verification — turn claimed evidence into checked evidence (#128).

``akf check`` reads what a stamp *claims*; ``akf verify`` re-runs the probe
the stamp carries. Verdicts:

    CONFIRMED          replay succeeded AND inputs match the issuance fingerprint
    CONFIRMED_DRIFTED  replay succeeded, but against inputs that diverged since
                       issuance — provably reproducible, possibly reproducibly
                       wrong (credit: Mike Czerwinski)
    REFUTED            replay ran and did not produce the claimed result
    UNREPLAYABLE       no replay recipe recorded (or execution not requested)

Running a recipe executes a command recorded inside the file's stamp. By
default ``verify_file`` only inspects (fingerprint drift + recipe display);
execution requires ``run=True`` — never replay stamps from untrusted files
without reading the command first.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

from .models import AKF
from .deps import input_fingerprint

_REPLAY_TIMEOUT_S = 300


@dataclass
class VerifyResult:
    file: str
    verdict: str  # CONFIRMED | CONFIRMED_DRIFTED | REFUTED | UNREPLAYABLE | REPLAY_AVAILABLE
    exit_code: int
    command: Optional[str] = None
    inputs_drifted: Optional[bool] = None
    detail: Optional[str] = None
    executed: bool = False

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "verdict": self.verdict,
            "exit_code": self.exit_code,
            "command": self.command,
            "inputs_drifted": self.inputs_drifted,
            "detail": self.detail,
            "executed": self.executed,
        }

    def summary_line(self) -> str:
        parts = [self.verdict]
        if self.inputs_drifted is not None:
            parts.append("inputs=" + ("drifted" if self.inputs_drifted else "intact"))
        if self.command:
            parts.append(f'replay="{self.command}"')
        if self.detail:
            parts.append(self.detail)
        return " ".join(parts)


def _current_fingerprint(filepath: str, unit: AKF) -> str:
    from .deps import hash_source

    base_dir = os.path.dirname(os.path.abspath(filepath))
    recorded = (unit.meta or {}).get("deps") or {}
    current_deps = {}
    for rel in recorded:
        dep_path = os.path.join(base_dir, rel)
        try:
            with open(dep_path, "rb") as f:
                current_deps[rel] = "sha256:" + hashlib.sha256(f.read()).hexdigest()[:16]
        except OSError:
            current_deps[rel] = "missing"
    current_srcs = [hash_source(c.source, base_dir) or "missing"
                    for c in unit.claims if getattr(c, "src_hash", None)]
    return input_fingerprint(current_deps, current_srcs)


def _find_replay(unit: AKF):
    for claim in unit.claims:
        for ev in claim.evidence or []:
            replay = getattr(ev, "replay", None)
            if replay and getattr(replay, "command", None):
                return replay
    return None


def verify_file(filepath: str, run: bool = False) -> VerifyResult:
    """Verify a file's stamped claims against their replay recipe.

    Without ``run``, reports drift + the recipe (safe inspection). With
    ``run``, executes the recorded command in the file's directory and
    returns CONFIRMED / CONFIRMED_DRIFTED / REFUTED.
    """
    from . import universal
    from .core import load

    meta = universal.extract(filepath)
    if meta is not None:
        unit = AKF(**meta)
    elif filepath.endswith(".akf"):
        try:
            unit = load(filepath)
        except Exception:
            unit = None
    else:
        unit = None

    if unit is None:
        return VerifyResult(file=filepath, verdict="UNREPLAYABLE", exit_code=3,
                            detail="no_metadata")

    replay = _find_replay(unit)
    if replay is None:
        return VerifyResult(file=filepath, verdict="UNREPLAYABLE", exit_code=3,
                            detail="no_replay_recipe")

    drifted: Optional[bool] = None
    if replay.input_hash:
        drifted = _current_fingerprint(filepath, unit) != replay.input_hash

    if not run:
        return VerifyResult(
            file=filepath,
            verdict="REPLAY_AVAILABLE",
            exit_code=1 if drifted else 0,
            command=replay.command,
            inputs_drifted=drifted,
            detail="pass run=True (--run) to execute",
        )

    base_dir = os.path.dirname(os.path.abspath(filepath))
    cwd = os.path.join(base_dir, replay.cwd) if replay.cwd else base_dir
    try:
        proc = subprocess.run(
            replay.command, shell=True, cwd=cwd,
            capture_output=True, text=True, timeout=_REPLAY_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return VerifyResult(file=filepath, verdict="REFUTED", exit_code=2,
                            command=replay.command, inputs_drifted=drifted,
                            detail=f"timeout>{_REPLAY_TIMEOUT_S}s", executed=True)

    exit_ok = proc.returncode == replay.expected_exit
    output_ok = True
    if replay.output_digest:
        digest = "sha256:" + hashlib.sha256(proc.stdout.encode()).hexdigest()[:16]
        output_ok = digest == replay.output_digest

    if exit_ok and output_ok:
        if drifted:
            return VerifyResult(file=filepath, verdict="CONFIRMED_DRIFTED", exit_code=1,
                                command=replay.command, inputs_drifted=True,
                                detail="replay succeeded against diverged inputs", executed=True)
        return VerifyResult(file=filepath, verdict="CONFIRMED", exit_code=0,
                            command=replay.command, inputs_drifted=drifted, executed=True)

    detail = f"exit={proc.returncode} expected={replay.expected_exit}" if not exit_ok \
        else "output digest mismatch"
    return VerifyResult(file=filepath, verdict="REFUTED", exit_code=2,
                        command=replay.command, inputs_drifted=drifted,
                        detail=detail, executed=True)
