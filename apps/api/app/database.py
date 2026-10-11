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

# Idempotent DDL mirroring docker/sqld/init.sql. Applied automatically on
# first connection because the libsql-server container does not execute
# docker-entrypoint-initdb.d scripts.
SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS api_keys (
        id TEXT PRIMARY KEY,
        key_hash TEXT NOT NULL UNIQUE,
        owner_name TEXT NOT NULL,
        rate_limit_per_minute INTEGER NOT NULL DEFAULT 60,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
        revoked_at TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        api_key_id TEXT,
        session_id TEXT,
        title TEXT NOT NULL,
        raw_text TEXT NOT NULL,
        character_count INTEGER NOT NULL,
        word_count INTEGER NOT NULL,
        sentence_count INTEGER NOT NULL,
        paragraph_count INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
        FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE SET NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS sentiment_evaluations (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL UNIQUE,
        polarity REAL NOT NULL,
        subjectivity REAL NOT NULL,
        classification TEXT NOT NULL CHECK (
            classification IN (
                'strongly_negative', 'negative', 'neutral', 'positive', 'strongly_positive'
            )
        ),
        positivity_score REAL NOT NULL,
        negativity_score REAL NOT NULL,
        neutrality_score REAL NOT NULL,
        compound_score REAL NOT NULL,
        joy_score REAL NOT NULL,
        sadness_score REAL NOT NULL,
        anger_score REAL NOT NULL,
        fear_score REAL NOT NULL,
        trust_score REAL NOT NULL,
        surprise_score REAL NOT NULL,
        disgust_score REAL NOT NULL,
        anticipation_score REAL NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS readability_evaluations (
        id TEXT PRIMARY KEY,
        document_id TEXT NOT NULL UNIQUE,
        flesch_reading_ease REAL NOT NULL,
        flesch_kincaid_grade REAL NOT NULL,
        gunning_fog_index REAL NOT NULL,
        coleman_liau_index REAL NOT NULL,
        smog_index REAL NOT NULL,
        automated_readability_index REAL NOT NULL,
        reading_time_seconds INTEGER NOT NULL,
        speaking_time_seconds INTEGER NOT NULL,
        syllable_count INTEGER NOT NULL,
        complex_word_count INTEGER NOT NULL,
        grade_level_consensus TEXT NOT NULL,
        cefr_equivalent TEXT NOT NULL CHECK (
            cefr_equivalent IN ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')
        ),
        created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash)",
    "CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_documents_api_key_id ON documents(api_key_id)",
    "CREATE INDEX IF NOT EXISTS idx_documents_session_id ON documents(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_sentiment_evaluations_document_id ON sentiment_evaluations(document_id)",  # noqa: E501
    "CREATE INDEX IF NOT EXISTS idx_sentiment_classification ON sentiment_evaluations(classification)",  # noqa: E501
    "CREATE INDEX IF NOT EXISTS idx_readability_evaluations_document_id ON readability_evaluations(document_id)",  # noqa: E501
    "CREATE INDEX IF NOT EXISTS idx_readability_cefr ON readability_evaluations(cefr_equivalent)",
)


class Database:
    """Thin asynchronous facade over the `libsql-client` HTTP client."""

    def __init__(self) -> None:
        self._client: libsql_client.Client | None = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    async def bind_client(self, url: str) -> None:
        """Bind an explicit client URL (test harness / alternate backends)."""
        await self.disconnect()
        self._client = libsql_client.create_client(url=url)
        try:
            await self._client.execute("PRAGMA foreign_keys = ON")
        except libsql_client.LibsqlError:
            pass
        await self.ensure_schema()

    async def connect(self, url: str | None = None) -> None:
        """Create (or re-create) the shared HTTP client; idempotent.

        `url` overrides `settings.database_url` (used by tests to bind a
        local SQLite file through the same Hrana facade). Referential
        integrity is enforced by issuing `PRAGMA foreign_keys = ON` on the
        connection; backends that reject the pragma are tolerated so that
        managed Turso deployments remain compatible.
        """
        if self._client is None:
            self._client = libsql_client.create_client(
                url=url or settings.database_url,
                auth_token=settings.database_auth_token or None,
            )
            try:
                await self._client.execute("PRAGMA foreign_keys = ON")
            except libsql_client.LibsqlError:
                # Managed Turso instances enforce foreign keys server-side.
                pass
            await self.ensure_schema()

    async def ensure_schema(self) -> None:
        """Apply the idempotent DDL when the domain tables are absent."""
        if self._client is None:
            raise RuntimeError("Database is not connected")
        rows = await self.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'documents'"
        )
        if not rows:
            await self._client.batch([libsql_client.Statement(stmt) for stmt in SCHEMA_STATEMENTS])

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

    async def execute_batch(
        self, statements: list[tuple[str, list[Any]]]
    ) -> list[list[dict[str, Any]]]:
        """Execute (sql, args) pairs atomically; rows materialized per statement.

        The batch is wrapped in an explicit BEGIN/COMMIT transaction. Any
        failure mid-batch aborts the commit and rolls every statement back,
        leaving the database in its pre-batch state.
        """
        if self._client is None:
            raise RuntimeError("Database is not connected")
        result_sets = await self._client.batch(
            [libsql_client.Statement(sql, args=args) for sql, args in statements]
        )
        return [[row.asdict() for row in result_set.rows] for result_set in result_sets]

    async def execute_transaction(
        self, statements: list[tuple[str, list[Any]]]
    ) -> list[list[dict[str, Any]]]:
        """Alias of `execute_batch` retained for call-site readability."""
        return await self.execute_batch(statements)

    async def execute_write(self, sql: str, parameters: tuple[Any, ...] | list[Any] = ()) -> None:
        """Execute a mutating statement (auto-committed by the Hrana pipeline)."""
        await self.execute(sql, parameters)

    async def healthcheck(self) -> bool:
        try:
            await self.execute("SELECT 1")
            return True
        except Exception:
            return False


database = Database()
