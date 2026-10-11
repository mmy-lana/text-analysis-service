"""Historical Archive & Persistence Engine.

Asynchronous Turso (LibSQL) repository for persistent report storage with
pagination, keyword search, deletion, and per-identity isolation. Authenticated
callers are isolated by verified API key hash; anonymous callers are isolated
by a salted HMAC digest of their client-generated X-Session-ID header, which
prevents cross-tenant enumeration (SEC-01).
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.algorithms.readability_indexes import analyze_readability
from app.core.algorithms.sentiment_lexicon import analyze_sentiment
from app.database import Database
from app.dependencies import RequestIdentity, get_database, resolve_request_identity
from app.models.common import AnalysisSubmissionPayload, DocumentTextStatisticsModel
from app.models.document import (
    CompleteAnalysisResponseModel,
    HistoryItemSummaryModel,
    PaginatedHistoryModel,
)
from app.models.readability import ReadabilityAnalysisResponse
from app.models.sentiment import EmotionSpectrumModel, SentimentAnalysisResponse

router = APIRouter(prefix="/history", tags=["Historical Archive"])


def _require_identity(identity: RequestIdentity) -> str:
    isolation_value = identity.isolation_value
    if isolation_value is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Archival access requires a verified API key or an X-Session-ID session header."
            ),
        )
    return isolation_value


def _compute_statistics(text: str) -> DocumentTextStatisticsModel:
    paragraphs = [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    words = re.findall(r"\b[a-zA-Z]+(?:'[a-zA-Z]+)?\b", text)
    return DocumentTextStatisticsModel(
        character_count=len(text),
        word_count=len(words),
        sentence_count=len(sentences),
        paragraph_count=len(paragraphs),
    )


def _sentiment_row_values(document_id: str, result: SentimentAnalysisResponse) -> list[Any]:
    return [
        str(uuid.uuid4()),
        document_id,
        result.polarity,
        result.subjectivity,
        result.classification.value,
        result.positivity_score,
        result.negativity_score,
        result.neutrality_score,
        result.compound_score,
        result.emotions.joy,
        result.emotions.sadness,
        result.emotions.anger,
        result.emotions.fear,
        result.emotions.trust,
        result.emotions.surprise,
        result.emotions.disgust,
        result.emotions.anticipation,
    ]


def _readability_row_values(document_id: str, result: ReadabilityAnalysisResponse) -> list[Any]:
    return [
        str(uuid.uuid4()),
        document_id,
        result.flesch_reading_ease,
        result.flesch_kincaid_grade,
        result.gunning_fog_index,
        result.coleman_liau_index,
        result.smog_index,
        result.automated_readability_index,
        result.reading_time_seconds,
        result.speaking_time_seconds,
        result.syllable_count,
        result.complex_word_count,
        result.grade_level_consensus,
        result.cefr_equivalent.value,
    ]


def _isolation_clause(identity: RequestIdentity) -> tuple[str, list[Any]]:
    """Build the per-tenant WHERE fragment for the documents table."""
    if identity.is_authenticated:
        return "d.api_key_id = ?", [identity.api_key_id]
    assert identity.session_id is not None
    return "d.session_id = ?", [identity.session_id]


@router.post(
    "",
    response_model=CompleteAnalysisResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Persist Analyzed Document",
    description=(
        "Runs both engines and stores the document with its sentiment and "
        "readability evaluations, bound to the caller's identity."
    ),
)
async def store_document(
    payload: AnalysisSubmissionPayload,
    identity: RequestIdentity = Depends(resolve_request_identity),
    db: Database = Depends(get_database),
) -> CompleteAnalysisResponseModel:
    _require_identity(identity)
    text = payload.text.strip()
    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Manuscript text is required for archival storage.",
        )

    title = payload.title or (text[:60] + ("..." if len(text) > 60 else ""))
    statistics = _compute_statistics(text)
    sentiment = analyze_sentiment(text)
    readability = analyze_readability(text)

    document_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    statements: list[tuple[str, list[Any]]] = [
        (
            (
                "INSERT INTO documents (id, api_key_id, session_id, title, raw_text, "
                "character_count, word_count, sentence_count, paragraph_count, "
                "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            ),
            [
                document_id,
                identity.api_key_id,
                identity.session_id,
                title,
                text,
                statistics.character_count,
                statistics.word_count,
                statistics.sentence_count,
                statistics.paragraph_count,
                now,
                now,
            ],
        ),
        (
            (
                "INSERT INTO sentiment_evaluations (id, document_id, polarity, "
                "subjectivity, classification, positivity_score, negativity_score, "
                "neutrality_score, compound_score, joy_score, sadness_score, "
                "anger_score, fear_score, trust_score, surprise_score, disgust_score, "
                "anticipation_score) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            ),
            _sentiment_row_values(document_id, sentiment),
        ),
        (
            (
                "INSERT INTO readability_evaluations (id, document_id, "
                "flesch_reading_ease, flesch_kincaid_grade, gunning_fog_index, "
                "coleman_liau_index, smog_index, automated_readability_index, "
                "reading_time_seconds, speaking_time_seconds, syllable_count, "
                "complex_word_count, grade_level_consensus, cefr_equivalent) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            ),
            _readability_row_values(document_id, readability),
        ),
    ]

    # Atomic archival: any failure rolls the whole transaction back, leaving
    # no orphan document row behind.
    await db.execute_batch(statements)

    return CompleteAnalysisResponseModel(
        document_id=document_id,
        title=title,
        statistics=statistics,
        sentiment=sentiment,
        readability=readability,
        processed_at=datetime.now(timezone.utc),
    )


@router.get(
    "",
    response_model=PaginatedHistoryModel,
    summary="List Archived Documents",
    description="Paginated archive listing with keyword search and identity isolation.",
)
async def list_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: Optional[str] = Query(default=None, max_length=255),
    identity: RequestIdentity = Depends(resolve_request_identity),
    db: Database = Depends(get_database),
) -> PaginatedHistoryModel:
    _require_identity(identity)
    where, params = _isolation_clause(identity)
    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where += " AND (d.title LIKE ? ESCAPE '\\' OR d.raw_text LIKE ? ESCAPE '\\')"
        params.extend([f"%{escaped}%", f"%{escaped}%"])

    count_rows = await db.execute(
        f"SELECT COUNT(*) AS total FROM documents d WHERE {where}", tuple(params)
    )
    total = int(count_rows[0]["total"]) if count_rows else 0

    offset = (page - 1) * page_size
    rows = await db.execute(
        (
            "SELECT d.id, d.title, d.word_count, s.classification AS sentiment_classification, "
            "r.cefr_equivalent AS cefr_equivalent, d.created_at "
            "FROM documents d "
            "JOIN sentiment_evaluations s ON s.document_id = d.id "
            "JOIN readability_evaluations r ON r.document_id = d.id "
            f"WHERE {where} "
            "ORDER BY d.created_at DESC LIMIT ? OFFSET ?"
        ),
        (*tuple(params), page_size, offset),
    )

    items = [
        HistoryItemSummaryModel(
            id=row["id"],
            title=row["title"],
            word_count=int(row["word_count"]),
            sentiment_classification=row["sentiment_classification"],
            cefr_equivalent=row["cefr_equivalent"],
            created_at=row["created_at"],
        )
        for row in rows
    ]
    return PaginatedHistoryModel(items=items, total=total, page=page, page_size=page_size)


async def _fetch_document_or_404(
    isolation_value: str, identity: RequestIdentity, document_id: str, db: Database
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if identity.is_authenticated:
        clause, params = "d.api_key_id = ?", [isolation_value]
    else:
        clause, params = "d.session_id = ?", [isolation_value]
    rows = await db.execute(
        f"SELECT d.* FROM documents d WHERE {clause} AND d.id = ?",
        (*params, document_id),
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested archival document could not be located.",
        )
    document = rows[0]

    sentiment_rows = await db.execute(
        "SELECT * FROM sentiment_evaluations WHERE document_id = ?", (document_id,)
    )
    readability_rows = await db.execute(
        "SELECT * FROM readability_evaluations WHERE document_id = ?", (document_id,)
    )
    if not sentiment_rows or not readability_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archival evaluations are missing for this document.",
        )
    return document, sentiment_rows[0], readability_rows[0]


def _sentiment_from_row(row: dict[str, Any]) -> SentimentAnalysisResponse:
    emotions = EmotionSpectrumModel(
        joy=row["joy_score"],
        sadness=row["sadness_score"],
        anger=row["anger_score"],
        fear=row["fear_score"],
        trust=row["trust_score"],
        surprise=row["surprise_score"],
        disgust=row["disgust_score"],
        anticipation=row["anticipation_score"],
    )
    return SentimentAnalysisResponse(
        polarity=row["polarity"],
        subjectivity=row["subjectivity"],
        classification=row["classification"],
        positivity_score=row["positivity_score"],
        negativity_score=row["negativity_score"],
        neutrality_score=row["neutrality_score"],
        compound_score=row["compound_score"],
        emotions=emotions,
        sentence_breakdown=[],
    )


def _readability_from_row(row: dict[str, Any]) -> ReadabilityAnalysisResponse:
    return ReadabilityAnalysisResponse(
        flesch_reading_ease=row["flesch_reading_ease"],
        flesch_kincaid_grade=row["flesch_kincaid_grade"],
        gunning_fog_index=row["gunning_fog_index"],
        coleman_liau_index=row["coleman_liau_index"],
        smog_index=row["smog_index"],
        automated_readability_index=row["automated_readability_index"],
        reading_time_seconds=int(row["reading_time_seconds"]),
        speaking_time_seconds=int(row["speaking_time_seconds"]),
        syllable_count=int(row["syllable_count"]),
        complex_word_count=int(row["complex_word_count"]),
        grade_level_consensus=row["grade_level_consensus"],
        cefr_equivalent=row["cefr_equivalent"],
        sentence_breakdown=[],
    )


@router.get(
    "/{document_id}",
    response_model=CompleteAnalysisResponseModel,
    summary="Fetch Archived Document",
)
async def fetch_document(
    document_id: str,
    identity: RequestIdentity = Depends(resolve_request_identity),
    db: Database = Depends(get_database),
) -> CompleteAnalysisResponseModel:
    isolation_value = _require_identity(identity)
    document, sentiment_row, readability_row = await _fetch_document_or_404(
        isolation_value, identity, document_id, db
    )
    return CompleteAnalysisResponseModel(
        document_id=document["id"],
        title=document["title"],
        statistics=DocumentTextStatisticsModel(
            character_count=int(document["character_count"]),
            word_count=int(document["word_count"]),
            sentence_count=int(document["sentence_count"]),
            paragraph_count=int(document["paragraph_count"]),
        ),
        sentiment=_sentiment_from_row(sentiment_row),
        readability=_readability_from_row(readability_row),
        processed_at=document["updated_at"],
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Archived Document",
)
async def delete_document(
    document_id: str,
    identity: RequestIdentity = Depends(resolve_request_identity),
    db: Database = Depends(get_database),
) -> None:
    isolation_value = _require_identity(identity)
    await _fetch_document_or_404(isolation_value, identity, document_id, db)
    # Explicit child-first removal inside one atomic transaction; foreign key
    # cascades remain enforced server-side on managed Turso deployments.
    await db.execute_batch(
        [
            ("DELETE FROM sentiment_evaluations WHERE document_id = ?", [document_id]),
            ("DELETE FROM readability_evaluations WHERE document_id = ?", [document_id]),
            ("DELETE FROM documents WHERE id = ?", [document_id]),
        ]
    )
