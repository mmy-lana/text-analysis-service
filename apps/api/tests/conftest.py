"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from app.core.ratelimit import GLOBAL_WINDOW_STORE


@pytest.fixture(autouse=True)
def _reset_rate_limit_windows():
    """Isolate sliding-window state between tests."""
    GLOBAL_WINDOW_STORE.reset()
    yield
    GLOBAL_WINDOW_STORE.reset()
