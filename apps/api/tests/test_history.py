"""Integration tests for the Historical Archive & Persistence Engine.

Runs against a real SQLite database file through the same async LibSQL client
facade used in production, verifying transactions, rollbacks, cascading
removal semantics, and per-identity isolation (verified API keys vs. anonymous
X-Session-ID sessions)."""

from __future__ import annotations

import asyncio
import os
import tempfile

import libsql_client
import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_api_key
from app.database import Database
from app.dependencies import get_database
from app.main import app

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "docker", "sqld", "init.sql"
)

SESSION_A = "aaaaaaaa-1111-2222-3333-444444444444"
SESSION_B = "bbbbbbbb-1111-2222-3333-444444444444"
VALID_KEY = "test-runner-key-0001"


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(scope="module")
def db() -> Database:
    database = Database()
    handle, path = tempfile.mkstemp(suffix=".db")
    os.close(handle)
    _run(database.bind_client(f"file:{path}"))

    with open(os.path.abspath(SCHEMA_PATH), "r", encoding="utf-8") as schema_file:
        statements = [
            stmt.strip()
            for stmt in schema_file.read().split(";")
            if stmt.strip() and not stmt.strip().startswith("PRAGMA")
        ]
    _run(
        database._client.batch([libsql_client.Statement(stmt) for stmt in statements])  # type: ignore[union-attr]
    )
    # Register the verification test key.
    _run(
        database._client.batch(  # type: ignore[union-attr]
            [
                libsql_client.Statement(
                    "INSERT OR IGNORE INTO api_keys (id, key_hash, owner_name) VALUES (?, ?, ?)",
                    args=["key-test-1", hash_api_key(VALID_KEY), "Test Runner"],
                )
            ]
        )
    )
    yield database
    _run(database.disconnect())
    os.unlink(path)


@pytest.fixture(scope="module")
def client(db: Database) -> TestClient:
    app.dependency_overrides[get_database] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _headers(session: str) -> dict[str, str]:
    return {"X-Session-ID": session}


def _store(client: TestClient, payload: dict, headers: dict[str, str]) -> dict:
    response = client.post("/api/v1/history", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


STORED_PAYLOADS = [
    {"title": "Joyful Reflections", "text": "A brilliant masterpiece of delight and peace."},
    {"title": "Dark Warnings", "text": "A horrific catastrophic disaster of grief and dread."},
]


class TestIdentityEnforcement:
    def test_unidentified_callers_are_refused(self, client: TestClient) -> None:
        response = client.get("/api/v1/history")
        assert response.status_code == 401
        assert "X-Session-ID" in response.json()["detail"]

        store_response = client.post("/api/v1/history", json=STORED_PAYLOADS[0])
        assert store_response.status_code == 401

    def test_invalid_api_key_is_rejected(self, client: TestClient) -> None:
        response = client.get("/api/v1/history", headers={"X-API-Key": "bogus-key-not-registered"})
        assert response.status_code == 401
        assert "revoked" in response.json()["detail"]

    def test_valid_api_key_is_accepted(self, client: TestClient) -> None:
        response = client.get("/api/v1/history", headers={"X-API-Key": VALID_KEY})
        assert response.status_code == 200

    def test_short_session_ids_are_treated_as_unidentified(self, client: TestClient) -> None:
        response = client.get("/api/v1/history", headers={"X-Session-ID": "abc"})
        assert response.status_code == 401


class TestPersistence:
    def test_store_and_fetch_document_with_session(self, client: TestClient) -> None:
        stored = _store(client, STORED_PAYLOADS[0], _headers(SESSION_A))
        assert stored["documentId"] is not None
        assert stored["statistics"]["wordCount"] > 0

        fetched = client.get(f"/api/v1/history/{stored['documentId']}", headers=_headers(SESSION_A))
        assert fetched.status_code == 200
        body = fetched.json()
        assert body["title"] == "Joyful Reflections"
        assert body["sentiment"]["classification"] == stored["sentiment"]["classification"]
        assert body["readability"]["cefrEquivalent"] == stored["readability"]["cefrEquivalent"]

    def test_pagination_and_search(self, client: TestClient) -> None:
        for payload in STORED_PAYLOADS:
            _store(client, payload, _headers(SESSION_A))

        listing = client.get(
            "/api/v1/history", params={"page": 1, "page_size": 1}, headers=_headers(SESSION_A)
        )
        assert listing.status_code == 200
        body = listing.json()
        assert body["pageSize"] == 1
        assert body["total"] >= 2
        assert len(body["items"]) == 1

        searched = client.get(
            "/api/v1/history", params={"search": "Dark Warnings"}, headers=_headers(SESSION_A)
        )
        assert searched.status_code == 200
        assert all("Dark Warnings" == item["title"] for item in searched.json()["items"])

        searched_fragment = client.get(
            "/api/v1/history", params={"search": "brilliant"}, headers=_headers(SESSION_A)
        )
        assert searched_fragment.status_code == 200
        assert searched_fragment.json()["total"] >= 1

        no_hits = client.get(
            "/api/v1/history", params={"search": "zzznotfoundzzz"}, headers=_headers(SESSION_A)
        )
        assert no_hits.json()["total"] == 0

    def test_delete_unknown_document_returns_problem_details(self, client: TestClient) -> None:
        response = client.delete("/api/v1/history/does-not-exist", headers=_headers(SESSION_A))
        assert response.status_code == 404
        assert response.json()["title"] == "Request Failed"


class TestTenantIsolation:
    def test_sessions_cannot_enumerate_each_other(self, client: TestClient) -> None:
        stored = _store(client, STORED_PAYLOADS[0], _headers(SESSION_A))
        document_id = stored["documentId"]

        other_session_list = client.get("/api/v1/history", headers=_headers(SESSION_B))
        assert all(item["id"] != document_id for item in other_session_list.json()["items"])

        other_session_fetch = client.get(
            f"/api/v1/history/{document_id}", headers=_headers(SESSION_B)
        )
        assert other_session_fetch.status_code == 404

        other_session_delete = client.delete(
            f"/api/v1/history/{document_id}", headers=_headers(SESSION_B)
        )
        assert other_session_delete.status_code == 404

    def test_anonymous_documents_are_invisible_without_session(self, client: TestClient) -> None:
        stored = _store(client, STORED_PAYLOADS[1], _headers(SESSION_A))
        # Without any session header the caller is refused outright.
        bare_fetch = client.get(f"/api/v1/history/{stored['documentId']}")
        assert bare_fetch.status_code == 401

        bare_list = client.get("/api/v1/history")
        assert bare_list.status_code == 401

    def test_keyed_tenancy_is_separate_from_sessions(self, client: TestClient) -> None:
        keyed_store = client.post(
            "/api/v1/history",
            json={"title": "Keyed Document", "text": "Simple plain words."},
            headers={"X-API-Key": VALID_KEY},
        )
        assert keyed_store.status_code == 201
        document_id = keyed_store.json()["documentId"]

        session_list = client.get("/api/v1/history", headers=_headers(SESSION_A))
        assert all(item["id"] != document_id for item in session_list.json()["items"])

        keyed_fetch = client.get(f"/api/v1/history/{document_id}", headers={"X-API-Key": VALID_KEY})
        assert keyed_fetch.status_code == 200

        keyed_delete = client.delete(
            f"/api/v1/history/{document_id}", headers={"X-API-Key": VALID_KEY}
        )
        assert keyed_delete.status_code == 204


class TestTransactionsAndRollback:
    def test_rollback_on_evaluation_failure(self, client: TestClient, db: Database) -> None:
        # Force the second statement to violate the CEFR CHECK constraint so
        # the whole archival batch rolls back, leaving no orphan document.
        statements = [
            libsql_client.Statement(
                "INSERT INTO documents (id, api_key_id, session_id, title, raw_text, "
                "character_count, word_count, sentence_count, paragraph_count) "
                "VALUES (?, NULL, NULL, ?, ?, 10, 2, 1, 1)",
                args=["rollback-doc-id", "Orphan Probe", "probe text"],
            ),
            libsql_client.Statement(
                "INSERT INTO readability_evaluations (id, document_id, flesch_reading_ease, "
                "flesch_kincaid_grade, gunning_fog_index, coleman_liau_index, smog_index, "
                "automated_readability_index, reading_time_seconds, speaking_time_seconds, "
                "syllable_count, complex_word_count, grade_level_consensus, cefr_equivalent) "
                "VALUES ('rb-eval', 'rollback-doc-id', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, "
                "'Grade 1', 'Z9')",
            ),
        ]
        with pytest.raises(libsql_client.LibsqlError):
            _run(db.execute_batch([(s.sql, list(s.args or [])) for s in statements]))  # type: ignore[union-attr]

        response = client.get("/api/v1/history/rollback-doc-id", headers=_headers(SESSION_A))
        assert response.status_code == 404  # document insert was rolled back

    def test_foreign_key_cascading_removal(self, client: TestClient, db: Database) -> None:
        stored = _store(client, STORED_PAYLOADS[1], _headers(SESSION_A))
        document_id = stored["documentId"]

        rows = _run(
            db.execute(
                "SELECT COUNT(*) AS n FROM sentiment_evaluations WHERE document_id = ?",
                (document_id,),
            )
        )
        assert rows[0]["n"] == 1

        delete_response = client.delete(
            f"/api/v1/history/{document_id}", headers=_headers(SESSION_A)
        )
        assert delete_response.status_code == 204

        remaining_docs = _run(
            db.execute("SELECT COUNT(*) AS n FROM documents WHERE id = ?", (document_id,))
        )
        remaining_sentiment = _run(
            db.execute(
                "SELECT COUNT(*) AS n FROM sentiment_evaluations WHERE document_id = ?",
                (document_id,),
            )
        )
        remaining_readability = _run(
            db.execute(
                "SELECT COUNT(*) AS n FROM readability_evaluations WHERE document_id = ?",
                (document_id,),
            )
        )
        assert remaining_docs[0]["n"] == 0
        assert remaining_sentiment[0]["n"] == 0
        assert remaining_readability[0]["n"] == 0
