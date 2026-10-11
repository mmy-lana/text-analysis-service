"""Asynchronous database connector for Turso / LibSQL (sqld) backends.

Uses the official pure-Python async `libsql-client` package, which speaks the
native Hrana-over-HTTP protocol exposed by both the containerized `sqld`
emulator and managed Turso clusters. The client is fully asynchronous, so the
FastAPI request pipeline never blocks.
"""

from __future__ import annotations

from typing import Any

import libsql_client

from app.config import settings


class Database:
    """Thin asynchronous facade over the `libsql-client` HTTP client."""

    def __init__(self) -> None:
        self._client: libsql_client.Client | None = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    async def connect(self) -> None:
        """Create (or re-create) the shared HTTP client; idempotent."""
        if self._client is None:
            self._client = libsql_client.create_client(
                url=settings.database_url,
                auth_token=settings.database_auth_token or None,
            )

    async def disconnect(self) -> None:
        if self._client is not None:
            try:
                await self._client.close()
            finally:
                self._client = None

    async def execute(
        self, sql: str, parameters: tuple[Any, ...] | list[Any] = ()
    ) -> list[dict[str, Any]]:
        """Execute a statement and materialize rows as a list of dictionaries."""
        if self._client is None:
            raise RuntimeError("Database is not connected")
        args = list(parameters)
        result_set = await self._client.execute(sql, args=args)
        return [row.asdict() for row in result_set.rows]

    async def execute_batch(self, statements: list[str]) -> list[list[dict[str, Any]]]:
        """Execute multiple statements transactionally; rows materialized per statement."""
        if self._client is None:
            raise RuntimeError("Database is not connected")
        result_sets = await self._client.batch(
            [libsql_client.Statement(sql) for sql in statements],
            transaction=True,
        )
        return [
            [row.asdict() for row in result_set.rows] for result_set in result_sets
        ]

    async def execute_write(
        self, sql: str, parameters: tuple[Any, ...] | list[Any] = ()
    ) -> None:
        """Execute a mutating statement (auto-committed by the Hrana pipeline)."""
        await self.execute(sql, parameters)

    async def healthcheck(self) -> bool:
        try:
            await self.execute("SELECT 1")
            return True
        except Exception:
            return False


database = Database()
