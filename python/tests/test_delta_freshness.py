"""Tests for Delta 6: Claim freshness — expires_at, depends_on, is_expired, freshness_status."""

from datetime import datetime, timedelta, timezone

from akf.models import Claim
from akf.trust import is_expired, freshness_status


class TestClaimFreshnessFields:
    def test_expires_at(self):
        c = Claim(content="test", confidence=0.9, expires_at="2026-09-30T23:59:59Z")
        assert c.expires_at == "2026-09-30T23:59:59Z"

    def test_verified_at(self):
        c = Claim(content="test", confidence=0.9, verified_at="2026-03-01T00:00:00Z")
        assert c.verified_at == "2026-03-01T00:00:00Z"

    def test_depends_on(self):
        c = Claim(
            content="derived fact", confidence=0.8,
            depends_on=["c001", "c002"], relationship="inferred_from",
        )
        assert len(c.depends_on) == 2
        assert c.relationship == "inferred_from"

    def test_fields_default_none(self):
        c = Claim(content="test", confidence=0.9)
        assert c.expires_at is None
        assert c.verified_at is None
        assert c.depends_on is None
        assert c.relationship is None


class TestIsExpired:
    def test_no_expiry_not_expired(self):
        c = Claim(content="test", confidence=0.9)
        assert is_expired(c) is False

    def test_future_expiry_not_expired(self):
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        c = Claim(content="test", confidence=0.9, expires_at=future)
        assert is_expired(c) is False

    def test_past_expiry_is_expired(self):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        c = Claim(content="test", confidence=0.9, expires_at=past)
        assert is_expired(c) is True


class TestFreshnessStatus:
    def test_no_expiry(self):
        c = Claim(content="test", confidence=0.9)
        assert freshness_status(c) == "no_expiry"

    def test_expired(self):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        c = Claim(content="test", confidence=0.9, expires_at=past)
        assert freshness_status(c) == "expired"

    def test_stale_no_verification(self):
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        c = Claim(content="test", confidence=0.9, expires_at=future)
        assert freshness_status(c) == "stale"

    def test_fresh_with_verification(self):
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        now = datetime.now(timezone.utc).isoformat()
        c = Claim(content="test", confidence=0.9, expires_at=future, verified_at=now)
        assert freshness_status(c) == "fresh"
