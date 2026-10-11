"""Tests for the sliding-window rate limiting middleware and key hashing."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from app.core.ratelimit import GLOBAL_WINDOW_STORE, SlidingWindow
from app.core.security import hash_api_key, hash_client_ip, hash_session_id, verify_api_key
from app.main import app


@pytest.fixture()
def local_client() -> TestClient:
    GLOBAL_WINDOW_STORE.reset()
    with TestClient(app) as test_client:
        yield test_client
    GLOBAL_WINDOW_STORE.reset()


class TestSlidingWindowUnit:
    def test_allows_up_to_limit_then_blocks(self) -> None:
        window = SlidingWindow(limit=3, window_seconds=60.0)
        now = time.monotonic()
        assert window.check(now)[0] is True
        assert window.check(now)[0] is True
        allowed, remaining, _ = window.check(now)
        assert allowed is True
        assert remaining == 0
        blocked, _, reset_in = window.check(now)
        assert blocked is False
        assert reset_in > 0

    def test_window_slides_with_time(self) -> None:
        window = SlidingWindow(limit=1, window_seconds=1.0)
        now = time.monotonic()
        assert window.check(now)[0] is True
        assert window.check(now)[0] is False
        allowed, _, _ = window.check(now + 1.5)
        assert allowed is True


class TestMiddlewareBehavior:
    def test_anonymous_quota_is_twenty_per_hour(self, local_client: TestClient) -> None:
        statuses = []
        for _ in range(21):
            response = local_client.post("/api/v1/sentiment/analyze", json={"text": "plain"})
            statuses.append(response.status_code)
        assert statuses[:20] == [200] * 20
        assert statuses[20] == 429

        blocked = local_client.post("/api/v1/sentiment/analyze", json={"text": "plain"})
        assert blocked.status_code == 429
        problem = blocked.json()
        assert problem["title"] == "Rate Limit Exceeded"
        assert "Retry-After" in blocked.headers

    def test_rate_limit_headers_present(self, local_client: TestClient) -> None:
        response = local_client.post("/api/v1/sentiment/analyze", json={"text": "plain"})
        assert response.headers["X-RateLimit-Limit"] == "20"
        assert int(response.headers["X-RateLimit-Remaining"]) >= 0
        assert int(response.headers["X-RateLimit-Reset"]) > 0

    def test_exempt_paths_bypass_limiting(self, local_client: TestClient) -> None:
        for _ in range(25):
            response = local_client.get("/docs")
            assert response.status_code == 200

    def test_authenticated_keys_get_60_per_minute(self, local_client: TestClient) -> None:
        # Rate limit classification keys off X-API-Key presence; route-level
        # verification is covered by the history integration tests.
        GLOBAL_WINDOW_STORE.reset()
        seen = []
        for _ in range(61):
            response = local_client.post(
                "/api/v1/sentiment/analyze",
                json={"text": "plain"},
                headers={"X-API-Key": "some-key"},
            )
            seen.append(response.status_code)
        assert seen[59] == 200
        assert seen[60] == 429
        assert (
            local_client.post("/api/v1/sentiment/analyze", json={"text": "plain"}).status_code
            == 200
        )  # separate anonymous bucket


class TestKeyHashing:
    def test_hmac_digest_is_deterministic_and_bound_to_salt(self) -> None:
        first = hash_api_key("the-key")
        second = hash_api_key("the-key")
        assert first == second
        assert first != hash_api_key("the-other-key")

    def test_verify_api_key_matches(self) -> None:
        digest = hash_api_key("rotate-me")
        assert verify_api_key("rotate-me", digest) is True
        assert verify_api_key("wrong", digest) is False

    def test_session_and_ip_digests_are_domain_separated(self) -> None:
        assert hash_session_id("abc") != hash_api_key("abc")
        assert hash_client_ip("10.0.0.1") != hash_api_key("10.0.0.1")

    def test_digest_is_keyed_not_plain_sha256(self) -> None:
        import hashlib

        raw = "value"
        assert hash_api_key(raw) != hashlib.sha256(raw.encode()).hexdigest()
