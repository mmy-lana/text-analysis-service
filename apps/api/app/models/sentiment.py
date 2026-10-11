from typing import Annotated, List
from pydantic import Field
from app.models.common import BaseSchema, SentimentClassificationEnum


class EmotionSpectrumModel(BaseSchema):
    joy: float = Field(ge=0.0, le=1.0)
    sadness: float = Field(ge=0.0, le=1.0)
    anger: float = Field(ge=0.0, le=1.0)
    fear: float = Field(ge=0.0, le=1.0)
    trust: float = Field(ge=0.0, le=1.0)
    surprise: float = Field(ge=0.0, le=1.0)
    disgust: float = Field(ge=0.0, le=1.0)
    anticipation: float = Field(ge=0.0, le=1.0)


class SentenceSentimentItem(BaseSchema):
    index: int
    text: str
    polarity: float = Field(ge=-1.0, le=1.0)
    subjectivity: float = Field(ge=0.0, le=1.0)
    classification: SentimentClassificationEnum


class SentimentAnalysisResponse(BaseSchema):
    polarity: float = Field(ge=-1.0, le=1.0)
    subjectivity: float = Field(ge=0.0, le=1.0)
    classification: SentimentClassificationEnum
    positivity_score: float = Field(ge=0.0, le=1.0)
    negativity_score: float = Field(ge=0.0, le=1.0)
    neutrality_score: float = Field(ge=0.0, le=1.0)
    compound_score: float = Field(ge=-1.0, le=1.0)
    emotions: EmotionSpectrumModel
    sentence_breakdown: List[SentenceSentimentItem]


class SentimentBatchRequest(BaseSchema):
    texts: List[Annotated[str, Field(min_length=1, max_length=100000)]] = Field(
        min_length=1, max_length=50
    )


class SentimentBatchResponse(BaseSchema):
    results: List[SentimentAnalysisResponse]
