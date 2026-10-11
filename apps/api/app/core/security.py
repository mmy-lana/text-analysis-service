"""Cryptographic API key utilities for rate-limit governance and isolation.

Key material is never stored in plaintext: raw API keys and anonymous session
identifiers are reduced to keyed HMAC-SHA-256 digests using the mandatory
API_KEY_SALT provisioned through application settings.
"""

from __future__ import annotations

import hashlib
import hmac

from app.config import settings


def _hmac_digest(value: str) -> str:
    return hmac.new(
        settings.api_key_salt.encode("utf-8"), value.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def hash_api_key(raw_key: str) -> str:
    """Keyed HMAC-SHA-256 digest of a raw API key."""
    return _hmac_digest(raw_key)


def hash_session_id(session_id: str) -> str:
    """Keyed HMAC-SHA-256 digest of a client session identifier."""
    return _hmac_digest(f"session:{session_id}")


def hash_client_ip(client_ip: str) -> str:
    """Keyed HMAC-SHA-256 digest of a client IP for anonymous rate limiting."""
    return _hmac_digest(f"ip:{client_ip}")


def verify_api_key(raw_key: str, key_hash: str) -> bool:
    return hmac.compare_digest(hash_api_key(raw_key), key_hash)
