"""Shared FastAPI dependencies: database access and request identity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from app.core.security import hash_api_key, hash_session_id
from app.database import Database, database


async def get_database() -> Database:
    """Yield the application-wide database facade for route handlers."""
    if not database.is_connected:
        await database.connect()
    return database


@dataclass(frozen=True)
class RequestIdentity:
    """Resolved tenancy identity for a request.

    `api_key_id` is set when a valid, active API key accompanies the request.
    `session_id` is a salted HMAC digest of the client-supplied X-Session-ID
    used for anonymous multitenancy isolation. Exactly one may be set.
    """

    api_key_id: Optional[str] = None
    session_id: Optional[str] = None

    @property
    def is_authenticated(self) -> bool:
        return self.api_key_id is not None

    @property
    def isolation_value(self) -> Optional[str]:
        return self.api_key_id if self.api_key_id is not None else self.session_id


async def resolve_request_identity(
    request: Request, db: Database = Depends(get_database)
) -> RequestIdentity:
    """Resolve the tenancy identity from API key or session headers.

    A presented X-API-Key must match an active row in `api_keys`; invalid or
    revoked keys are rejected with 401 rather than silently downgraded.
    Anonymous callers must present an X-Session-ID (a client-generated UUID)
    so that their archival writes are isolated from other anonymous users.
    """
    raw_key = request.headers.get("X-API-Key")
    if raw_key:
        key_hash = hash_api_key(raw_key)
        rows = await db.execute(
            "SELECT id FROM api_keys WHERE key_hash = ? AND is_active = 1",
            (key_hash,),
        )
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The presented API key is invalid or has been revoked.",
            )
        return RequestIdentity(api_key_id=key_hash)

    session_header = request.headers.get("X-Session-ID")
    if session_header:
        normalized = session_header.strip()
        if 8 <= len(normalized) <= 128:
            return RequestIdentity(session_id=hash_session_id(normalized))

    return RequestIdentity()
