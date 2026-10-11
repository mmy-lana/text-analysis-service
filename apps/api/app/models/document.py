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


class PaginatedHistoryModel(BaseSchema):
    items: list[HistoryItemSummaryModel]
    total: int
    page: int
    page_size: int
