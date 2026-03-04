"""Tests for v1.1 security enhancements: check_access, verify_trust_anchor,
redaction_report, compute_security_hash.
"""

import pytest
from akf.models import AKF, Claim, ProvHop, Origin
from akf.security import (
    check_access, verify_trust_anchor, redaction_report,
    compute_security_hash, security_score,
)


class TestCheckAccess:
    def test_allowed_actor(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="x", confidence=0.5)],
            security={"access_control": {"allowed_actors": ["alice", "bob"]}},
        )
        assert check_access(unit, "alice") is True
        assert check_access(unit, "charlie") is False

    def test_denied_actor(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="x", confidence=0.5)],
            security={"access_control": {"denied_actors": ["eve"]}},
        )
        assert check_access(unit, "eve") is False
        assert check_access(unit, "alice") is True

    def test_no_security_block_fallback(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="x", confidence=0.5)],
            classification="internal",
        )
        # required_level "internal" (rank 1) >= unit rank "internal" (rank 1) -> True
        assert check_access(unit, "anyone", required_level="internal") is True
        # required_level "public" (rank 0) < unit rank "internal" (rank 1) -> False
        assert check_access(unit, "anyone", required_level="public") is False

    def test_public_unit_accessible(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="x", confidence=0.5)],
            classification="public",
        )
        assert check_access(unit, "anyone", required_level="public") is True


class TestVerifyTrustAnchor:
    def test_anchored(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="x", confidence=0.5)],
            prov=[
                ProvHop(hop=0, actor="root@co.com", action="created", timestamp="2024-01-01T00:00:00Z"),
                ProvHop(hop=1, actor="ai-agent", action="enriched", timestamp="2024-01-01T01:00:00Z"),
            ],
        )
        result = verify_trust_anchor(unit, ["root@co.com"])
        assert result["anchored"] is True
        assert result["anchor_actor"] == "root@co.com"
        assert result["chain_length"] == 2

    def test_not_anchored(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="x", confidence=0.5)],
            prov=[ProvHop(hop=0, actor="unknown@co.com", action="created", timestamp="2024-01-01T00:00:00Z")],
        )
        result = verify_trust_anchor(unit, ["trusted@co.com"])
        assert result["anchored"] is False

    def test_no_provenance(self):
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        result = verify_trust_anchor(unit, ["trusted@co.com"])
        assert result["anchored"] is False
        assert result["chain_length"] == 0


class TestRedactionReport:
    def test_high_authority_in_external(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="Secret", confidence=0.9, authority_tier=1)],
            allow_external=True,
        )
        report = redaction_report(unit)
        assert report["total"] >= 1
        assert any("High-authority" in r for r in report["reasons"])

    def test_ai_without_risk_in_classified(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="AI output", confidence=0.7, ai_generated=True)],
            classification="confidential",
        )
        report = redaction_report(unit)
        assert report["total"] >= 1

    def test_clean_unit(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="Public info", confidence=0.9, authority_tier=3)],
            classification="public",
        )
        report = redaction_report(unit)
        assert report["total"] == 0


class TestComputeSecurityHash:
    def test_produces_hash(self):
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        h = compute_security_hash(unit)
        assert h.startswith("sha256:")
        assert len(h) > 10

    def test_deterministic(self):
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        h1 = compute_security_hash(unit)
        h2 = compute_security_hash(unit)
        assert h1 == h2

    def test_different_content_different_hash(self):
        u1 = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        u2 = AKF(version="1.0", claims=[Claim(content="y", confidence=0.5)])
        assert compute_security_hash(u1) != compute_security_hash(u2)


class TestEnhancedSecurityScore:
    def test_new_checks_present(self):
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        result = security_score(unit)
        check_names = [c["check"] for c in result.checks]
        assert "origin_tracking" in check_names
        assert "reviews_present" in check_names
        assert "trust_anchor" in check_names

    def test_score_normalized_to_10(self):
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        result = security_score(unit)
        assert 0 <= result.score <= 10

    def test_full_score_possible(self):
        from akf.models import Review
        unit = AKF(
            version="1.0",
            claims=[Claim(
                content="Full security",
                confidence=0.9,
                source="trusted-src",
                ai_generated=True,
                risk="low risk",
                origin=Origin(type="ai", model="test"),
                reviews=[Review(reviewer="alice@co.com", verdict="approved")],
            )],
            classification="internal",
            inherit_classification=True,
            allow_external=False,
            integrity_hash="sha256:abc",
            prov=[ProvHop(hop=0, actor="admin@co.com", action="created", timestamp="2024-01-01T00:00:00Z")],
            reviews=[Review(reviewer="mgr@co.com", verdict="approved")],
        )
        result = security_score(unit)
        assert result.score >= 8.0
        assert result.grade in ("A", "B")
