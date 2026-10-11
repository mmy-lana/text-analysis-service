"""Integration tests for the Historical Archive & Persistence Engine.

Runs against a real SQLite database file through the same async LibSQL client
facade used in production, verifying transactions, rollbacks, and cascading
removal semantics."""

from __future__ import annotations

import asyncio
import os
import tempfile

import libsql_client
import pytest
from fastapi.testclient import TestClient

from app.database import Database
from app.dependencies import get_database
from app.main import app

SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "docker", "sqld", "init.sql"
)


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(scope="module")
def db() -> Database:
    database = Database()
    handle, path = tempfile.mkstemp(suffix=".db")
    os.close(handle)
    database._client = libsql_client.create_client(url=f"file:{path}")

    with open(os.path.abspath(SCHEMA_PATH), "r", encoding="utf-8") as schema_file:
        statements = [
            stmt.strip()
            for stmt in schema_file.read().split(";")
            if stmt.strip() and not stmt.strip().startswith("PRAGMA")
        ]
    _run(database._client.batch([libsql_client.Statement(stmt) for stmt in statements]))  # type: ignore[union-attr]
    yield database
    _run(database.disconnect())
    os.unlink(path)


@pytest.fixture(scope="module")
def client(db: Database) -> TestClient:
    app.dependency_overrides[get_database] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


STORED_PAYLOADS = [
    {"title": "Joyful Reflections", "text": "A brilliant masterpiece of delight and peace."},
    {"title": "Dark Warnings", "text": "A horrific catastrophic disaster of grief and dread."},
]


def _store(client: TestClient, payload: dict) -> dict:
    response = client.post("/api/v1/history", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


class TestPersistence:
    def test_store_and_fetch_document(self, client: TestClient) -> None:
        stored = _store(client, STORED_PAYLOADS[0])
        assert stored["documentId"] is not None
        assert stored["statistics"]["wordCount"] > 0

        fetched = client.get(f"/api/v1/history/{stored['documentId']}")
        assert fetched.status_code == 200
        body = fetched.json()
        assert body["title"] == "Joyful Reflections"
        assert body["sentiment"]["classification"] == stored["sentiment"]["classification"]
        assert body["readability"]["cefrEquivalent"] == stored["readability"]["cefrEquivalent"]

    def test_pagination_and_search(self, client: TestClient) -> None:
        for payload in STORED_PAYLOADS:
            _store(client, payload)

        listing = client.get("/api/v1/history?page=1&page_size=1")
        assert listing.status_code == 200
        body = listing.json()
        assert body["pageSize"] == 1
        assert body["total"] >= 2
        assert len(body["items"]) == 1

        searched = client.get("/api/v1/history", params={"search": "Dark Warnings"})
        assert searched.status_code == 200
        assert all("Dark Warnings" == item["title"] for item in searched.json()["items"])

        searched_fragment = client.get("/api/v1/history", params={"search": "brilliant"})
        assert searched_fragment.status_code == 200
        assert searched_fragment.json()["total"] >= 1

        no_hits = client.get("/api/v1/history", params={"search": "zzznotfoundzzz"})
        assert no_hits.json()["total"] == 0

    def test_delete_is_idempotent_not_found(self, client: TestClient) -> None:
        response = client.delete("/api/v1/history/does-not-exist")
        assert response.status_code == 404
        problem = response.json()
        assert problem["title"] == "Request Failed"


class TestTransactionsAndRollback:
    def test_rollback_on_evaluation_failure(self, client: TestClient, db: Database) -> None:

        # Force the second statement to violate the CEFR CHECK constraint so
        # the whole archival batch rolls back, leaving no orphan document.
        statements = [
            libsql_client.Statement(
                "INSERT INTO documents (id, api_key_id, title, raw_text, character_count, "
                "word_count, sentence_count, paragraph_count) VALUES (?, NULL, ?, ?, 10, 2, 1, 1)",
                args=["rollback-doc-id", "Orphan Probe", "probe text"],
            ),
            libsql_client.Statement(
                "INSERT INTO readability_evaluations (id, document_id, flesch_reading_ease, "
                "flesch_kincaid_grade, gunning_fog_index, coleman_liau_index, smog_index, "
                "automated_readability_index, reading_time_seconds, speaking_time_seconds, "
                "syllable_count, complex_word_count, grade_level_consensus, cefr_equivalent) "
                "VALUES ('rb-eval', 'rollback-doc-id', 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 'Grade 1', 'Z9')",
            ),
        ]
        with pytest.raises(libsql_client.LibsqlError):
            _run(db._client.batch(statements))  # type: ignore[union-attr]

        response = client.get("/api/v1/history/rollback-doc-id")
        assert response.status_code == 404  # document insert was rolled back

    def test_foreign_key_cascading_removal(self, client: TestClient, db: Database) -> None:

        stored = _store(client, STORED_PAYLOADS[1])
        document_id = stored["documentId"]

        rows = _run(
            db.execute(
                "SELECT COUNT(*) AS n FROM sentiment_evaluations WHERE document_id = ?",
                (document_id,),
            )
        )
        assert rows[0]["n"] == 1

        delete_response = client.delete(f"/api/v1/history/{document_id}")
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


class TestApiKeyIsolation:
    def test_documents_are_isolated_by_api_key(self, client: TestClient) -> None:
        keyed_store = client.post(
            "/api/v1/history",
            json={"title": "Keyed Document", "text": "Simple plain words."},
            headers={"X-API-Key": "secret-key-123"},
        )
        assert keyed_store.status_code == 201
        document_id = keyed_store.json()["documentId"]

        anon_list = client.get("/api/v1/history")
        assert all(item["title"] != "Keyed Document" for item in anon_list.json()["items"])

        keyed_list = client.get(
            "/api/v1/history", headers={"X-API-Key": "secret-key-123"}
        )
        assert any(
            item["title"] == "Keyed Document" for item in keyed_list.json()["items"]
        )

        other_key = client.get(
            "/api/v1/history", headers={"X-API-Key": "different-key"}
        )
        assert all(item["title"] != "Keyed Document" for item in other_key.json()["items"])

        anon_fetch = client.get(f"/api/v1/history/{document_id}")
        assert anon_fetch.status_code == 404

        keyed_fetch = client.get(
            f"/api/v1/history/{document_id}", headers={"X-API-Key": "secret-key-123"}
        )
        assert keyed_fetch.status_code == 200

        keyed_delete = client.delete(
            f"/api/v1/history/{document_id}", headers={"X-API-Key": "secret-key-123"}
        )
        assert keyed_delete.status_code == 204
