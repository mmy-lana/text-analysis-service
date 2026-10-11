"""Shared FastAPI dependencies."""

from __future__ import annotations

from app.database import Database, database


async def get_database() -> Database:
    """Yield the application-wide database facade for route handlers."""
    if not database.is_connected:
        await database.connect()
    return database
