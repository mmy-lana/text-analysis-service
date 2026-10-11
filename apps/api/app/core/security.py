"""Cryptographic API key utilities for rate-limit governance and isolation."""

from __future__ import annotations

import hashlib
import hmac
import os

# Rotating salt; in production this is provisioned via the environment.
_SALT_ROTATION = os.environ.get("API_KEY_SALT", "text-analysis-service-v1")


def hash_api_key(raw_key: str) -> str:
    """SHA-256 hash of the raw API key combined with the rotating salt."""
    return hashlib.sha256(f"{_SALT_ROTATION}:{raw_key}".encode()).hexdigest()


def verify_api_key(raw_key: str, key_hash: str) -> bool:
    return hmac.compare_digest(hash_api_key(raw_key), key_hash)
