"""Signature helpers for the RFA core."""
from __future__ import annotations

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)


def sign_blob(blob: bytes, private_key_pem: bytes) -> bytes:
    """Return a SHA256 signature for ``blob`` using the given private key."""
    key = load_pem_private_key(private_key_pem, password=None)
    return key.sign(blob, padding.PKCS1v15(), hashes.SHA256())


def verify_blob(blob: bytes, signature: bytes, public_key_pem: bytes) -> bool:
    """Validate ``signature`` for ``blob`` against ``public_key_pem``."""
    key = load_pem_public_key(public_key_pem)
    try:
        key.verify(signature, blob, padding.PKCS1v15(), hashes.SHA256())
        return True
    except Exception:
        return False


__all__ = ["sign_blob", "verify_blob"]
