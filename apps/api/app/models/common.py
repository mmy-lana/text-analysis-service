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
    pass
