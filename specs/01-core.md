### Turso SQLite Database DDL

The database engine is Turso (LibSQL). The following schema must be executed within `docker/sqld/init.sql` and mirrored in cloud provisioning migrations.

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS api_keys (
    id TEXT PRIMARY KEY,
    key_hash TEXT NOT NULL UNIQUE,
    owner_name TEXT NOT NULL,
    rate_limit_per_minute INTEGER NOT NULL DEFAULT 60,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    revoked_at TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    api_key_id TEXT,
    title TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    character_count INTEGER NOT NULL,
    word_count INTEGER NOT NULL,
    sentence_count INTEGER NOT NULL,
    paragraph_count INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sentiment_evaluations (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL UNIQUE,
    polarity REAL NOT NULL,
    subjectivity REAL NOT NULL,
    classification TEXT NOT NULL CHECK (classification IN ('strongly_negative', 'negative', 'neutral', 'positive', 'strongly_positive')),
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
);

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
    cefr_equivalent TEXT NOT NULL CHECK (cefr_equivalent IN ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc')),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_api_key_id ON documents(api_key_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_evaluations_document_id ON sentiment_evaluations(document_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_classification ON sentiment_evaluations(classification);
CREATE INDEX IF NOT EXISTS idx_readability_evaluations_document_id ON readability_evaluations(document_id);
CREATE INDEX IF NOT EXISTS idx_readability_cefr ON readability_evaluations(cefr_equivalent);
```

### TypeScript Data Transfer Objects (`packages/shared-types/src/index.ts`)

```typescript
export type SentimentCategory =
  | 'strongly_negative'
  | 'negative'
  | 'neutral'
  | 'positive'
  | 'strongly_positive';

export type CEFRLevel = 'A1' | 'A2' | 'B1' | 'B2' | 'C1' | 'C2';

export interface ApiErrorDetail {
  loc: (string | number)[];
  msg: string;
  type: string;
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  errors?: ApiErrorDetail[];
}

export interface EmotionSpectrum {
  joy: number;
  sadness: number;
  anger: number;
  fear: number;
  trust: number;
  surprise: number;
  disgust: number;
  anticipation: number;
}

export interface SentimentAnalysisResult {
  polarity: number;
  subjectivity: number;
  classification: SentimentCategory;
  positivityScore: number;
  negativityScore: number;
  neutralityScore: number;
  compoundScore: number;
  emotions: EmotionSpectrum;
}

export interface SentenceComplexity {
  index: number;
  text: string;
  wordCount: number;
  syllableCount: number;
  characterCount: number;
  complexWordCount: number;
  readingEase: number;
  isExtremelyLong: boolean;
}

export interface ReadabilityAnalysisResult {
  fleschReadingEase: number;
  fleschKincaidGrade: number;
  gunningFogIndex: number;
  colemanLiauIndex: number;
  smogIndex: number;
  automatedReadabilityIndex: number;
  readingTimeSeconds: number;
  speakingTimeSeconds: number;
  syllableCount: number;
  complexWordCount: number;
  gradeLevelConsensus: string;
  cefrEquivalent: CEFRLevel;
  sentenceBreakdown: SentenceComplexity[];
}

export interface DocumentTextStatistics {
  characterCount: number;
  wordCount: number;
  sentenceCount: number;
  paragraphCount: number;
}

export interface CompleteAnalysisRequest {
  title?: string;
  text: string;
  storeResult?: boolean;
}

export interface CompleteAnalysisResponse {
  documentId?: string;
  title: string;
  statistics: DocumentTextStatistics;
  sentiment: SentimentAnalysisResult;
  readability: ReadabilityAnalysisResult;
  processedAt: string;
}

export interface HistoryItemSummary {
  id: string;
  title: string;
  wordCount: number;
  sentimentClassification: SentimentCategory;
  cefrEquivalent: CEFRLevel;
  createdAt: string;
}

export interface PaginatedHistoryResponse {
  items: HistoryItemSummary[];
  total: number;
  page: number;
  pageSize: number;
}
```

### Application Configuration (`apps/api/app/config.py`)

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "http://127.0.0.1:8080"
    database_auth_token: str = ""
    environment: str = "development"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:4173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
```

### Application Entrypoint (`apps/api/app/main.py`)

```python
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.batch_semaphore = asyncio.Semaphore(10)
    yield


app = FastAPI(
    title="Text Sentiment & Readability API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
)

app.include_router(api_v1_router, prefix="/api/v1")
```

### Base Models (`apps/api/app/models/common.py`)

```python
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class SentimentClassificationEnum(str, Enum):
    STRONGLY_NEGATIVE = "strongly_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    STRONGLY_POSITIVE = "strongly_positive"


class CEFREquivalentEnum(str, Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
        str_strip_whitespace=True,
    )


class ProblemDetailsModel(BaseSchema):
    type: str = Field(default="about:blank")
    title: str
    status: int
    detail: str
    instance: Optional[str] = None
    errors: Optional[List[dict[str, Any]]] = None


class DocumentTextStatisticsModel(BaseSchema):
    character_count: int = Field(ge=0)
    word_count: int = Field(ge=0)
    sentence_count: int = Field(ge=0)
    paragraph_count: int = Field(ge=0)


class AnalysisSubmissionPayload(BaseSchema):
    title: Optional[str] = Field(default=None, max_length=255)
    text: str = Field(min_length=1, max_length=100000)
    store_result: bool = Field(default=False)


class CompleteAnalysisRequestModel(AnalysisSubmissionPayload):
    """Distinct schema component for combined document analysis requests."""
    pass
```

### Document Models (`apps/api/app/models/document.py`)

```python
from datetime import datetime
from typing import Optional
from app.models.common import (
    BaseSchema,
    CEFREquivalentEnum,
    DocumentTextStatisticsModel,
    SentimentClassificationEnum,
)
from app.models.readability import ReadabilityAnalysisResponse
from app.models.sentiment import SentimentAnalysisResponse


class CompleteAnalysisResponseModel(BaseSchema):
    document_id: Optional[str] = None
    title: str
    statistics: DocumentTextStatisticsModel
    sentiment: SentimentAnalysisResponse
    readability: ReadabilityAnalysisResponse
    processed_at: datetime


class HistoryItemSummaryModel(BaseSchema):
    id: str
    title: str
    word_count: int
    sentiment_classification: SentimentClassificationEnum
    cefr_equivalent: CEFREquivalentEnum
    created_at: datetime

    # Database projection mapping:
    # Raw table column `s.classification` aliased AS Pydantic field `sentiment_classification`
    # Raw table column `r.cefr_equivalent` maps directly to Pydantic field `cefr_equivalent`
    # Query:
    # SELECT d.id, d.title, d.word_count,
    #        s.classification AS sentiment_classification,
    #        r.cefr_equivalent AS cefr_equivalent,
    #        d.created_at
    # FROM documents d
    # JOIN sentiment_evaluations s ON s.document_id = d.id
    # JOIN readability_evaluations r ON r.document_id = d.id
```
