"""AKF Certify — aggregate trust certification for files and directories.

Combines trust scoring, detection, and compliance into a single pass/fail verdict.
"""

from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .models import Evidence


# ---------------------------------------------------------------------------
# Evidence ingestion (stdlib only)
# ---------------------------------------------------------------------------


def parse_junit_xml(path: Union[str, Path]) -> List[Evidence]:
    """Parse a JUnit XML file into a list of Evidence objects.

    Handles both ``<testsuites>`` wrapper and bare ``<testsuite>`` root.
    """
    tree = ET.parse(str(path))
    root = tree.getroot()

    suites: List[ET.Element] = []
    if root.tag == "testsuites":
        suites = list(root.findall("testsuite"))
    elif root.tag == "testsuite":
        suites = [root]
    else:
        return []

    evidences: List[Evidence] = []
    for suite in suites:
        name = suite.get("name", "unknown")
        tests = int(suite.get("tests", "0"))
        failures = int(suite.get("failures", "0"))
        errors = int(suite.get("errors", "0"))
        passed = tests - failures - errors

        if failures == 0 and errors == 0:
            detail = f"{name}: {tests} tests passed"
            etype = "test_pass"
        else:
            detail = f"{name}: {passed}/{tests} passed, {failures} failures, {errors} errors"
            etype = "test_fail"

        evidences.append(Evidence(type=etype, detail=detail))

    return evidences


def parse_evidence_json(path: Union[str, Path]) -> List[Evidence]:
    """Parse an evidence JSON file into a list of Evidence objects.

    Supports three formats:
    - List of ``{"type": ..., "detail": ...}`` objects
    - DeepEval format: ``{"test_results": [...]}``
    - Generic score object: ``{"score": float, "passed": bool}``
    """
    with open(str(path)) as f:
        data = json.load(f)

    evidences: List[Evidence] = []

    if isinstance(data, list):
        for item in data:
            evidences.append(Evidence(
                type=item.get("type", "other"),
                detail=item.get("detail", str(item)),
            ))
    elif isinstance(data, dict):
        if "test_results" in data:
            for result in data["test_results"]:
                passed = result.get("success", result.get("passed", False))
                name = result.get("name", result.get("metric", "test"))
                score = result.get("score", 1.0 if passed else 0.0)
                evidences.append(Evidence(
                    type="test_pass" if passed else "test_fail",
                    detail=f"{name}: score={score}, passed={passed}",
                ))
        elif "score" in data or "passed" in data:
            passed = data.get("passed", data.get("score", 0) >= 0.5)
            score = data.get("score", 1.0 if passed else 0.0)
            evidences.append(Evidence(
                type="test_pass" if passed else "test_fail",
                detail=f"score={score}, passed={passed}",
            ))

    return evidences


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class CertifyResult:
    """Per-file certification result."""

    filepath: str
    certified: bool
    trust_score: float = 0.0
    evidence: List[Evidence] = field(default_factory=list)
    detections: List[Any] = field(default_factory=list)
    compliance_issues: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filepath": self.filepath,
            "certified": self.certified,
            "trust_score": self.trust_score,
            "evidence": [e.to_dict() if hasattr(e, "to_dict") else str(e) for e in self.evidence],
            "detections": [
                {"class": d.detection_class, "severity": d.severity, "findings": d.findings}
                if hasattr(d, "detection_class") else str(d)
                for d in self.detections
            ],
            "compliance_issues": self.compliance_issues,
            "error": self.error,
        }


@dataclass
class CertifyReport:
    """Aggregate certification report."""

    total_files: int = 0
    certified_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    avg_trust: float = 0.0
    results: List[CertifyResult] = field(default_factory=list)

    @property
    def all_certified(self) -> bool:
        return self.failed_count == 0 and self.total_files > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_files": self.total_files,
            "certified_count": self.certified_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "avg_trust": round(self.avg_trust, 4),
            "all_certified": self.all_certified,
            "results": [r.to_dict() for r in self.results],
        }


# ---------------------------------------------------------------------------
# Core certification
# ---------------------------------------------------------------------------


def certify_file(
    filepath: Union[str, Path],
    min_trust: float = 0.7,
    evidence: Optional[List[Evidence]] = None,
) -> CertifyResult:
    """Certify a single file meets trust standards.

    A file is certified when:
    - Average trust score >= *min_trust*
    - Zero critical detections
    """
    from . import universal as akf_u
    from .compliance import _load_unit, audit
    from .detection import run_all_detections
    from .trust import compute_all

    filepath = str(filepath)

    # Check if file has metadata
    meta = akf_u.extract(filepath)
    if meta is None:
        return CertifyResult(filepath=filepath, certified=False, error="no metadata")

    # Load unit
    try:
        unit = _load_unit(filepath)
    except Exception as exc:
        return CertifyResult(filepath=filepath, certified=False, error=str(exc))

    # Attach external evidence
    if evidence:
        for ev in evidence:
            for claim in unit.claims:
                if not hasattr(claim, "evidence") or claim.evidence is None:
                    claim.evidence = []
                claim.evidence.append(ev)

    # Trust
    trust_results = compute_all(unit)
    avg_trust = (
        sum(tr.score for tr in trust_results) / len(trust_results)
        if trust_results
        else 0.0
    )

    # Detections
    try:
        det_report = run_all_detections(unit, trust_threshold=min_trust)
        triggered = [d for d in det_report.results if d.triggered]
        critical_count = det_report.critical_count
    except Exception:
        triggered = []
        critical_count = 0

    # Compliance
    compliance_issues: List[str] = []
    try:
        audit_result = audit(unit)
        for check in audit_result.checks:
            if not check.get("passed", True):
                compliance_issues.append(check.get("name", "unknown"))
    except Exception:
        pass

    certified = avg_trust >= min_trust and critical_count == 0

    all_evidence = list(evidence or [])
    for claim in unit.claims:
        if hasattr(claim, "evidence") and claim.evidence:
            for ev in claim.evidence:
                if ev not in all_evidence:
                    all_evidence.append(ev)

    return CertifyResult(
        filepath=filepath,
        certified=certified,
        trust_score=round(avg_trust, 4),
        evidence=all_evidence,
        detections=triggered,
        compliance_issues=compliance_issues,
    )


def certify_directory(
    dirpath: Union[str, Path],
    min_trust: float = 0.7,
    evidence: Optional[List[Evidence]] = None,
    recursive: bool = True,
) -> CertifyReport:
    """Certify all AKF-enriched files in a directory.

    Files without AKF metadata are skipped (not failed).
    """
    from . import universal as akf_u

    dirpath = Path(dirpath)
    report = CertifyReport()

    if recursive:
        files = sorted(dirpath.rglob("*"))
    else:
        files = sorted(dirpath.iterdir())

    files = [f for f in files if f.is_file()]

    trust_scores: List[float] = []

    for fpath in files:
        report.total_files += 1
        fstr = str(fpath)

        # .akf files are always candidates; for other files check embedded metadata
        if not fstr.endswith(".akf") and not akf_u.is_enriched(fstr):
            report.skipped_count += 1
            continue

        result = certify_file(fstr, min_trust=min_trust, evidence=evidence)
        report.results.append(result)

        if result.error == "no metadata":
            report.skipped_count += 1
        elif result.certified:
            report.certified_count += 1
            trust_scores.append(result.trust_score)
        else:
            report.failed_count += 1
            trust_scores.append(result.trust_score)

    if trust_scores:
        report.avg_trust = round(sum(trust_scores) / len(trust_scores), 4)

    return report
