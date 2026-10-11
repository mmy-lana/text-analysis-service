from typing import Annotated, List

from pydantic import Field

from app.models.common import BaseSchema, CEFREquivalentEnum


class SentenceComplexityModel(BaseSchema):
    index: int = Field(ge=0, description="Zero-based sentence index within document")
    text: str = Field(description="Raw sentence text body")
    word_count: int = Field(ge=0, description="Word count in sentence")
    syllable_count: int = Field(ge=0, description="Total syllables in sentence")
    character_count: int = Field(ge=0, description="Total character count excluding spaces")
    complex_word_count: int = Field(ge=0, description="Count of words with 3 or more syllables")
    reading_ease: float = Field(
        ge=-20.0, le=120.0, description="Sentence-level Flesch Reading Ease score"
    )
    is_extremely_long: bool = Field(description="True if word count is 30 or greater")


class ReadabilityAnalysisResponse(BaseSchema):
    flesch_reading_ease: float = Field(ge=-20.0, le=120.0)
    flesch_kincaid_grade: float = Field(ge=0.0)
    gunning_fog_index: float = Field(ge=0.0)
    coleman_liau_index: float = Field(ge=0.0)
    smog_index: float = Field(ge=0.0)
    automated_readability_index: float = Field(ge=0.0)
    reading_time_seconds: int = Field(ge=0)
    speaking_time_seconds: int = Field(ge=0)
    syllable_count: int = Field(ge=0)
    complex_word_count: int = Field(ge=0)
    grade_level_consensus: str
    cefr_equivalent: CEFREquivalentEnum
    sentence_breakdown: list[SentenceComplexityModel]


class ReadabilityBatchRequest(BaseSchema):
    texts: List[Annotated[str, Field(min_length=1, max_length=100000)]] = Field(
        min_length=1, max_length=50
    )


class ReadabilityBatchResponse(BaseSchema):
    results: List[ReadabilityAnalysisResponse]
