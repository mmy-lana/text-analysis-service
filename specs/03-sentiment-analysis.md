### Domain Models & Schema Contracts

The sentiment analysis engine processes unstructured text, generating polarity, subjectivity, and Plutchik's discrete eight-vector emotional profile without external cloud API dependencies.

#### Pydantic API Models (`apps/api/app/models/sentiment.py`)

```python
from typing import Annotated, List, Optional
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
```

### Pure Algorithmic Engine Specification (`apps/api/app/core/algorithms/sentiment_lexicon.py`)

```python
import math
import re
from typing import Dict, List, Tuple
from app.models.common import SentimentClassificationEnum
from app.models.sentiment import (
    EmotionSpectrumModel,
    SentenceSentimentItem,
    SentimentAnalysisResponse,
)

LEXICON_POLARITY: Dict[str, float] = {
    "brilliant": 0.8,
    "excellent": 0.75,
    "superb": 0.8,
    "good": 0.5,
    "great": 0.6,
    "masterpiece": 0.9,
    "delight": 0.65,
    "clean": 0.3,
    "clarity": 0.4,
    "coherent": 0.45,
    "terrible": -0.8,
    "abysmal": -0.85,
    "poor": -0.5,
    "horrific": -0.9,
    "flawed": -0.4,
    "disaster": -0.8,
    "catastrophic": -0.85,
    "dull": -0.4,
    "broken": -0.6,
    "ugly": -0.55,
}

EMOTION_LEXICON: Dict[str, Dict[str, float]] = {
    "joy": {"delight": 0.8, "brilliant": 0.7, "victory": 0.9, "triumph": 0.85, "peace": 0.6, "celebrate": 0.75},
    "sadness": {"mourn": 0.9, "grief": 0.95, "abysmal": 0.6, "loss": 0.7, "tragedy": 0.85, "alone": 0.5},
    "anger": {"fury": 0.95, "rage": 0.9, "wrath": 0.85, "hate": 0.8, "bitter": 0.6, "infuriating": 0.75},
    "fear": {"terror": 0.95, "panic": 0.9, "horrific": 0.85, "threat": 0.7, "dread": 0.8, "danger": 0.65},
    "trust": {"faith": 0.8, "reliable": 0.7, "integrity": 0.85, "truth": 0.75, "honest": 0.7, "secure": 0.6},
    "surprise": {"astonish": 0.85, "sudden": 0.5, "shock": 0.8, "unbelievable": 0.75, "wonder": 0.7},
    "disgust": {"revolt": 0.85, "nauseating": 0.9, "vile": 0.8, "rotten": 0.75, "ugly": 0.6},
    "anticipation": {"await": 0.5, "prepare": 0.4, "horizon": 0.4, "longing": 0.6, "approaching": 0.5},
}

INTENSIFIERS: Dict[str, float] = {
    "very": 1.3,
    "extremely": 1.5,
    "immensely": 1.6,
    "remarkably": 1.4,
    "slightly": 0.7,
    "hardly": 0.5,
}

NEGATORS = {"not", "never", "no", "without", "hardly", "neither", "scarcely"}


def split_into_sentences(text: str) -> List[str]:
    raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw_sentences if s.strip()]


def tokenize(sentence: str) -> List[str]:
    return re.findall(r'\b[a-zA-Z]+\b', sentence.lower())


def evaluate_sentiment_vector(tokens: List[str]) -> Tuple[float, float, float, float, float]:
    if not tokens:
        return 0.0, 0.0, 0.0, 1.0, 0.0

    pos_accum = 0.0
    neg_accum = 0.0
    subjectivity_hits = 0

    for i, token in enumerate(tokens):
        if token in LEXICON_POLARITY:
            score = LEXICON_POLARITY[token]
            subjectivity_hits += 1

            multiplier = 1.0
            if i > 0 and tokens[i - 1] in INTENSIFIERS:
                multiplier = INTENSIFIERS[tokens[i - 1]]

            negated = False
            for lookback in range(max(0, i - 3), i):
                if tokens[lookback] in NEGATORS:
                    negated = True
                    break

            final_val = score * multiplier
            if negated:
                final_val = -final_val * 0.75

            if final_val > 0:
                pos_accum += final_val
            else:
                neg_accum += abs(final_val)

    total_tokens = len(tokens)
    total_val = pos_accum + neg_accum
    subjectivity = min(1.0, (subjectivity_hits * 1.5) / max(total_tokens, 1))

    if total_val == 0.0:
        return 0.0, subjectivity, 0.0, 1.0, 0.0

    pos_ratio = pos_accum / total_val
    neg_ratio = neg_accum / total_val
    neu_ratio = 0.0

    diff = pos_accum - neg_accum
    compound = diff / math.sqrt((diff * diff) + 15.0)
    polarity = max(-1.0, min(1.0, compound))

    return polarity, subjectivity, pos_ratio, neu_ratio, neg_ratio


def evaluate_emotions(text: str) -> EmotionSpectrumModel:
    tokens = tokenize(text)
    total_tokens = max(len(tokens), 1)
    scores: Dict[str, float] = {e: 0.0 for e in EMOTION_LEXICON}

    for token in tokens:
        for emotion, lexicon in EMOTION_LEXICON.items():
            if token in lexicon:
                scores[emotion] += lexicon[token]

    normalized: Dict[str, float] = {}
    for emotion, raw in scores.items():
        scaled = raw / (total_tokens * 0.15 + 1.0)
        normalized[emotion] = round(max(0.0, min(1.0, scaled)), 4)

    return EmotionSpectrumModel(**normalized)


def classify_polarity(polarity: float) -> SentimentClassificationEnum:
    if polarity >= 0.45:
        return SentimentClassificationEnum.STRONGLY_POSITIVE
    elif polarity >= 0.1:
        return SentimentClassificationEnum.POSITIVE
    elif polarity <= -0.45:
        return SentimentClassificationEnum.STRONGLY_NEGATIVE
    elif polarity <= -0.1:
        return SentimentClassificationEnum.NEGATIVE
    return SentimentClassificationEnum.NEUTRAL


def analyze_sentiment(text: str) -> SentimentAnalysisResponse:
    sentences = split_into_sentences(text)
    sentence_items: List[SentenceSentimentItem] = []

    all_tokens = tokenize(text)
    polarity, subjectivity, pos_score, neu_score, neg_score = evaluate_sentiment_vector(all_tokens)

    for idx, s_text in enumerate(sentences):
        s_tokens = tokenize(s_text)
        s_pol, s_subj, _, _, _ = evaluate_sentiment_vector(s_tokens)
        sentence_items.append(
            SentenceSentimentItem(
                index=idx,
                text=s_text,
                polarity=round(s_pol, 4),
                subjectivity=round(s_subj, 4),
                classification=classify_polarity(s_pol),
            )
        )

    emotions = evaluate_emotions(text)

    return SentimentAnalysisResponse(
        polarity=round(polarity, 4),
        subjectivity=round(subjectivity, 4),
        classification=classify_polarity(polarity),
        positivity_score=round(pos_score, 4),
        negativity_score=round(neg_score, 4),
        neutrality_score=round(neu_score, 4),
        compound_score=round(polarity, 4),
        emotions=emotions,
        sentence_breakdown=sentence_items,
    )
```

### API Endpoint Specification (`apps/api/app/api/v1/sentiment.py`)

```python
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.core.algorithms.sentiment_lexicon import analyze_sentiment
from app.models.common import AnalysisSubmissionPayload
from app.models.sentiment import (
    SentimentAnalysisResponse,
    SentimentBatchRequest,
    SentimentBatchResponse,
)

router = APIRouter(prefix="/sentiment", tags=["Sentiment Analysis"])


async def get_batch_semaphore(request: Request) -> asyncio.Semaphore:
    return request.app.state.batch_semaphore


async def run_bounded_sentiment_analysis(
    text: str, semaphore: asyncio.Semaphore
) -> SentimentAnalysisResponse:
    async with semaphore:
        return await asyncio.to_thread(analyze_sentiment, text)


@router.post(
    "/analyze",
    response_model=SentimentAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute Text Sentiment",
    description="Asynchronously parses text payload and returns polarity, subjectivity, and discrete emotions.",
)
async def analyze_single_sentiment(payload: AnalysisSubmissionPayload) -> SentimentAnalysisResponse:
    cleaned = payload.text.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Supplied manuscript payload is devoid of textual content.",
        )
    return analyze_sentiment(cleaned)


@router.post(
    "/batch",
    response_model=SentimentBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute Batch Sentiments",
    description="Processes up to 50 individual text segments concurrently with bounded thread execution.",
)
async def analyze_batch_sentiment(
    payload: SentimentBatchRequest,
    semaphore: asyncio.Semaphore = Depends(get_batch_semaphore),
) -> SentimentBatchResponse:
    results = list(
        await asyncio.gather(
            *(run_bounded_sentiment_analysis(text, semaphore) for text in payload.texts)
        )
    )
    return SentimentBatchResponse(results=results)
```

### Edge Conditions & Validation Rules

1. Zero-Length / Whitespace Text: Returns HTTP 422 with an RFC 7807 detail string.
2. Large String Payloads: Strings exceeding 100,000 characters trigger an automatic rejection at the Pydantic boundary with HTTP 422.
3. Special Symbols & HTML: Injected tags are stripped during tokenization, preventing regex back-tracking overflows.
4. Non-English Text: Characters lacking ASCII alphabetic mappings are omitted from lexical computation; results default to Neutral classification (`polarity: 0.0`, `subjectivity: 0.0`).
