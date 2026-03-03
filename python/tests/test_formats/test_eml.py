"""Tests for AKF Email (.eml) format handler.

Named ``test_eml.py`` (not ``test_email.py``) to avoid shadowing the
stdlib ``email`` package.
"""

import base64
import json
import os
import tempfile
from typing import Dict

import pytest

from akf.formats.email import (
    EmailHandler,
    embed,
    extract,
    has_ai_content,
    is_enriched,
    scan,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def create_test_eml(path: str) -> None:
    """Create a minimal valid .eml file."""
    content = (
        "From: sender@example.com\r\n"
        "To: recipient@example.com\r\n"
        "Subject: Test Email\r\n"
        "Date: Tue, 3 Mar 2026 10:00:00 +0000\r\n"
        "Message-ID: <test-001@example.com>\r\n"
        "MIME-Version: 1.0\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "\r\n"
        "This is a test email body.\r\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def create_multipart_eml(path: str) -> None:
    """Create a multipart .eml for testing content preservation."""
    content = (
        "From: sender@example.com\r\n"
        "To: recipient@example.com\r\n"
        "Subject: Multipart Test\r\n"
        "Date: Tue, 3 Mar 2026 10:00:00 +0000\r\n"
        "Message-ID: <test-002@example.com>\r\n"
        "MIME-Version: 1.0\r\n"
        'Content-Type: multipart/mixed; boundary="BOUNDARY"\r\n'
        "\r\n"
        "--BOUNDARY\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "\r\n"
        "Plain text body.\r\n"
        "--BOUNDARY\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n"
        "<p>HTML body.</p>\r\n"
        "--BOUNDARY--\r\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


SAMPLE_METADATA = {
    "akf": "1.0",
    "classification": "confidential",
    "overall_trust": 0.75,
    "ai_contribution": 0.6,
    "claims": [
        {"c": "Meeting notes summarized", "t": 0.8, "ai": True, "ver": False},
        {"c": "Action items extracted", "t": 0.85, "ai": True, "ver": True},
        {"c": "Original text preserved", "t": 1.0, "ai": False, "ver": True},
    ],
    "provenance": [
        {"actor": "gpt-4", "action": "summarized", "at": "2026-03-01T12:00:00Z"}
    ],
}


# ------------------------------------------------------------------
# Handler attributes
# ------------------------------------------------------------------

class TestEmailHandlerAttributes:
    def test_format_name(self) -> None:
        h = EmailHandler()
        assert h.FORMAT_NAME == "Email"

    def test_extensions(self) -> None:
        h = EmailHandler()
        assert ".eml" in h.EXTENSIONS

    def test_mode(self) -> None:
        h = EmailHandler()
        assert h.MODE == "embedded"

    def test_mechanism(self) -> None:
        h = EmailHandler()
        assert h.MECHANISM == "X-AKF custom header"

    def test_no_dependencies(self) -> None:
        h = EmailHandler()
        assert h.DEPENDENCIES == []


# ------------------------------------------------------------------
# Embed / extract round-trip
# ------------------------------------------------------------------

class TestEmailEmbedExtract:
    def test_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "test.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            handler.embed(eml_path, SAMPLE_METADATA)

            result = handler.extract(eml_path)
            assert result is not None
            assert result["akf"] == "1.0"
            assert result["classification"] == "confidential"
            assert result["overall_trust"] == 0.75
            assert len(result["claims"]) == 3

    def test_extract_unenriched_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "plain.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            result = handler.extract(eml_path)
            assert result is None

    def test_overwrite_existing_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "overwrite.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            handler.embed(eml_path, SAMPLE_METADATA)

            updated = dict(SAMPLE_METADATA)
            updated["classification"] = "public"
            handler.embed(eml_path, updated)

            result = handler.extract(eml_path)
            assert result is not None
            assert result["classification"] == "public"


# ------------------------------------------------------------------
# Classification header
# ------------------------------------------------------------------

class TestEmailClassification:
    def test_classification_header_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "classified.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            handler.embed(eml_path, SAMPLE_METADATA)

            cls = handler.get_classification(eml_path)
            assert cls == "confidential"

    def test_no_classification_header_when_absent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "noclassify.eml")
            create_test_eml(eml_path)

            meta_no_class = dict(SAMPLE_METADATA)
            del meta_no_class["classification"]

            handler = EmailHandler()
            handler.embed(eml_path, meta_no_class)

            cls = handler.get_classification(eml_path)
            assert cls is None

    def test_classification_updated_on_re_embed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "reclassify.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            handler.embed(eml_path, SAMPLE_METADATA)
            assert handler.get_classification(eml_path) == "confidential"

            updated = dict(SAMPLE_METADATA)
            updated["classification"] = "internal"
            handler.embed(eml_path, updated)
            assert handler.get_classification(eml_path) == "internal"


# ------------------------------------------------------------------
# is_enriched
# ------------------------------------------------------------------

class TestEmailIsEnriched:
    def test_false_before_embed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "check.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            assert handler.is_enriched(eml_path) is False

    def test_true_after_embed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "check.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            handler.embed(eml_path, SAMPLE_METADATA)
            assert handler.is_enriched(eml_path) is True


# ------------------------------------------------------------------
# has_ai_content
# ------------------------------------------------------------------

class TestEmailHasAIContent:
    def test_has_ai_content_true(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "ai.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            handler.embed(eml_path, SAMPLE_METADATA)

            assert handler.has_ai_content(eml_path) is True

    def test_has_ai_content_false_no_ai_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "human.eml")
            create_test_eml(eml_path)

            meta_no_ai = {
                "akf": "1.0",
                "claims": [
                    {"c": "Human written", "t": 1.0, "ai": False, "ver": True},
                ],
            }

            handler = EmailHandler()
            handler.embed(eml_path, meta_no_ai)

            assert handler.has_ai_content(eml_path) is False

    def test_has_ai_content_false_unenriched(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "plain.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            assert handler.has_ai_content(eml_path) is False


# ------------------------------------------------------------------
# Content preservation
# ------------------------------------------------------------------

class TestEmailContentPreservation:
    def test_original_headers_preserved(self) -> None:
        import email as email_mod
        import email.policy

        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "preserve.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            handler.embed(eml_path, SAMPLE_METADATA)

            with open(eml_path, "rb") as fh:
                msg = email_mod.message_from_bytes(
                    fh.read(), policy=email.policy.default
                )

            assert msg["From"] == "sender@example.com"
            assert msg["To"] == "recipient@example.com"
            assert msg["Subject"] == "Test Email"
            assert msg["Message-ID"] == "<test-001@example.com>"

    def test_body_preserved(self) -> None:
        import email as email_mod
        import email.policy

        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "body.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            handler.embed(eml_path, SAMPLE_METADATA)

            with open(eml_path, "rb") as fh:
                msg = email_mod.message_from_bytes(
                    fh.read(), policy=email.policy.default
                )

            body = msg.get_body(preferencelist=("plain",))
            assert body is not None
            content = body.get_content()
            assert "test email body" in content.lower()

    def test_multipart_preserved(self) -> None:
        import email as email_mod
        import email.policy

        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "multi.eml")
            create_multipart_eml(eml_path)

            handler = EmailHandler()
            handler.embed(eml_path, SAMPLE_METADATA)

            with open(eml_path, "rb") as fh:
                msg = email_mod.message_from_bytes(
                    fh.read(), policy=email.policy.default
                )

            assert msg["Subject"] == "Multipart Test"
            # Should still have multipart content
            assert msg.is_multipart()


# ------------------------------------------------------------------
# Scan
# ------------------------------------------------------------------

class TestEmailScan:
    def test_scan_unenriched(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "scan.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            report = handler.scan(eml_path)
            assert report.enriched is False
            assert report.format == "Email"

    def test_scan_enriched(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "scan.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            handler.embed(eml_path, SAMPLE_METADATA)

            report = handler.scan(eml_path)
            assert report.enriched is True
            assert report.classification == "confidential"
            assert report.claim_count == 3
            assert report.ai_claim_count == 2
            assert report.verified_claim_count == 2


# ------------------------------------------------------------------
# Auto-enrich
# ------------------------------------------------------------------

class TestEmailAutoEnrich:
    def test_auto_enrich_creates_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "auto.eml")
            create_test_eml(eml_path)

            handler = EmailHandler()
            handler.auto_enrich(eml_path, "gpt-4", classification="internal")

            result = handler.extract(eml_path)
            assert result is not None
            assert result["akf"] == "1.0"
            assert result["classification"] == "internal"
            assert result["ai_contribution"] == 1.0


# ------------------------------------------------------------------
# Module-level convenience functions
# ------------------------------------------------------------------

class TestModuleFunctions:
    def test_module_embed_extract(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "modtest.eml")
            create_test_eml(eml_path)

            embed(eml_path, SAMPLE_METADATA)
            result = extract(eml_path)
            assert result is not None
            assert result.get("classification") == "confidential"
            assert is_enriched(eml_path) is True

    def test_module_scan(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "modtest.eml")
            create_test_eml(eml_path)

            report = scan(eml_path)
            assert report.enriched is False

    def test_module_has_ai_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            eml_path = os.path.join(tmpdir, "modtest.eml")
            create_test_eml(eml_path)

            embed(eml_path, SAMPLE_METADATA)
            assert has_ai_content(eml_path) is True
