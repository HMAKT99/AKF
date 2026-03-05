"""Tests for Delta 5: SecurityReport / full_report."""

import akf
from akf.models import AKF, Claim, Origin, Review, Evidence, ProvHop
from akf.security import full_report


def _unit_with_full_metadata():
    """A well-formed unit with all security features."""
    return AKF(
        version="1.0",
        classification="internal",
        integrity_hash="sha256:abc123def456",
        claims=[
            Claim(
                content="Q3 revenue projected at $42.1B",
                confidence=0.82,
                ai_generated=True,
                origin=Origin(type="ai", model="gpt-4o"),
                risk="Projection based on estimates",
                reviews=[Review(reviewer="jane@corp.com", verdict="approved")],
                evidence=[Evidence(type="test_pass", detail="back-tested")],
            ),
        ],
        prov=[
            ProvHop(hop=0, actor="finance-agent@corp.ai", action="created",
                    timestamp="2026-03-01T00:00:00Z"),
        ],
    )


def _minimal_unit():
    return akf.create("test claim", confidence=0.5)


class TestFullReport:
    def test_well_formed_scores_high(self):
        report = full_report(_unit_with_full_metadata())
        assert report.score >= 7.0
        assert report.has_classification
        assert report.has_provenance

    def test_minimal_scores_low(self):
        report = full_report(_minimal_unit())
        assert report.score < 6.0

    def test_confidential_blocks_sharing(self):
        unit = AKF(
            version="1.0",
            classification="confidential",
            claims=[Claim(content="secret", confidence=0.9)],
        )
        report = full_report(unit)
        assert report.can_share_external is False

    def test_public_allows_sharing(self):
        unit = AKF(
            version="1.0",
            classification="public",
            claims=[Claim(content="public info", confidence=0.9)],
        )
        report = full_report(unit)
        assert report.can_share_external is True

    def test_redaction_for_unreviewed_ai(self):
        unit = AKF(
            version="1.0",
            classification="confidential",
            claims=[
                Claim(content="AI claim without review", confidence=0.8, ai_generated=True),
            ],
        )
        report = full_report(unit)
        assert report.redaction_needed
        assert len(report.redaction_items) > 0

    def test_grade_property(self):
        report = full_report(_unit_with_full_metadata())
        assert report.grade in ("A+", "A", "A-", "B+", "B", "B-", "C", "D", "F")

    def test_to_dict(self):
        report = full_report(_unit_with_full_metadata())
        d = report.to_dict()
        assert "score" in d
        assert "grade" in d
        assert "classification" in d
