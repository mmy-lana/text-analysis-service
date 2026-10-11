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
