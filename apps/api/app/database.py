"""Asynchronous database connector for Turso / LibSQL (sqld) backends.

The official `libsql` Python bindings expose a synchronous Rust-backed client.
All calls are bridged onto the event loop with `asyncio.to_thread` so that the
FastAPI request pipeline never blocks, honoring the fully-async topology
defined in ARCHITECTURE.md.
"""

from __future__ import annotations

import asyncio
from typing import Any

import libsql

from app.config import settings


class Database:
    """Thin asynchronous facade over the `libsql` Rust client."""

    def __init__(self) -> None:
        self._connection: Any | None = None
        self._lock = asyncio.Lock()

    @property
    def is_connected(self) -> bool:
        return self._connection is not None

    def _connect_sync(self) -> Any:
        return libsql.connect(
            url=settings.database_url,
            auth_token=settings.database_auth_token or None,
        )

    async def connect(self) -> None:
        """Open (or re-open) the shared connection; safe to call concurrently."""
        async with self._lock:
            if self._connection is None:
                self._connection = await asyncio.to_thread(self._connect_sync)

    async def disconnect(self) -> None:
        async with self._lock:
            if self._connection is not None:
                try:
                    self._connection.close()
                finally:
                    self._connection = None

    def _execute_sync(self, sql: str, parameters: tuple[Any, ...]) -> Any:
        if self._connection is None:
            raise RuntimeError("Database is not connected")
        if parameters:
            return self._connection.execute(sql, parameters)
        return self._connection.execute(sql)

    async def execute(
        self, sql: str, parameters: tuple[Any, ...] = ()
    ) -> list[dict[str, Any]]:
        """Execute a statement and materialize rows as a list of dictionaries."""
        result = await asyncio.to_thread(self._execute_sync, sql, parameters)
        cursor = getattr(result, "cursor", result)
        columns = [column[0] for column in (getattr(cursor, "description", None) or [])]
        rows = getattr(cursor, "fetchall", lambda: [])()
        return [dict(zip(columns, row)) for row in rows]

    async def execute_write(
        self, sql: str, parameters: tuple[Any, ...] = ()
    ) -> None:
        """Execute a mutating statement inside a committed transaction."""
        if self._connection is None:
            raise RuntimeError("Database is not connected")

        def _run() -> None:
            assert self._connection is not None
            if parameters:
                self._connection.execute(sql, parameters)
            else:
                self._connection.execute(sql)
            self._connection.commit()

        await asyncio.to_thread(_run)

    async def healthcheck(self) -> bool:
        try:
            await self.execute("SELECT 1")
            return True
        except Exception:
            return False


database = Database()
