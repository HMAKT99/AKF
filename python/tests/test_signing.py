"""Tests for AKF Ed25519 signing and verification."""

import pytest

cryptography = pytest.importorskip("cryptography")

from akf.core import create
from akf.signing import keygen, sign, verify


@pytest.fixture
def key_pair(tmp_path):
    """Generate a fresh keypair in tmp_path."""
    priv, pub = keygen(key_dir=str(tmp_path), name="test")
    return priv, pub


@pytest.fixture
def sample_unit():
    return create("Revenue $4.2B", confidence=0.98, source="SEC 10-Q")


class TestKeygen:
    def test_creates_files(self, tmp_path):
        priv, pub = keygen(key_dir=str(tmp_path))
        assert (tmp_path / "default.pem").exists()
        assert (tmp_path / "default.pub.pem").exists()

    def test_pem_format(self, tmp_path):
        priv, pub = keygen(key_dir=str(tmp_path))
        priv_content = open(priv, "rb").read()
        pub_content = open(pub, "rb").read()
        assert b"BEGIN PRIVATE KEY" in priv_content
        assert b"END PRIVATE KEY" in priv_content
        assert b"BEGIN PUBLIC KEY" in pub_content
        assert b"END PUBLIC KEY" in pub_content

    def test_custom_name(self, tmp_path):
        priv, pub = keygen(key_dir=str(tmp_path), name="mykey")
        assert priv.endswith("mykey.pem")
        assert pub.endswith("mykey.pub.pem")
        assert (tmp_path / "mykey.pem").exists()
        assert (tmp_path / "mykey.pub.pem").exists()


class TestSignVerify:
    def test_sign_adds_fields(self, key_pair, sample_unit):
        priv, pub = key_pair
        signed = sign(sample_unit, priv, signer="test@example.com")
        assert signed.signature is not None
        assert signed.signature_algorithm == "ed25519"
        assert signed.public_key_id is not None
        assert signed.signed_at is not None
        assert signed.signed_by == "test@example.com"

    def test_roundtrip(self, key_pair, sample_unit):
        priv, pub = key_pair
        signed = sign(sample_unit, priv)
        assert verify(signed, pub) is True

    def test_tampered_rejects(self, key_pair, sample_unit):
        priv, pub = key_pair
        signed = sign(sample_unit, priv)
        # Tamper with the signed unit
        tampered = signed.model_copy(update={
            "claims": [signed.claims[0].model_copy(update={"content": "TAMPERED"})]
        })
        with pytest.raises(ValueError, match="tampered"):
            verify(tampered, pub)

    def test_unsigned_raises(self, key_pair, sample_unit):
        _, pub = key_pair
        with pytest.raises(ValueError, match="no signature"):
            verify(sample_unit, pub)

    def test_different_keys_fail(self, tmp_path, sample_unit):
        priv_a, _ = keygen(key_dir=str(tmp_path / "a"), name="a")
        _, pub_b = keygen(key_dir=str(tmp_path / "b"), name="b")
        signed = sign(sample_unit, priv_a)
        with pytest.raises(ValueError):
            verify(signed, pub_b)
