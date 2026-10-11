import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.algorithms.readability_indexes import analyze_readability
from app.models.common import AnalysisSubmissionPayload
from app.models.readability import (
    ReadabilityAnalysisResponse,
    ReadabilityBatchRequest,
    ReadabilityBatchResponse,
)

router = APIRouter(prefix="/readability", tags=["Readability Engine"])


async def get_batch_semaphore(request: Request) -> asyncio.Semaphore:
    return request.app.state.batch_semaphore


async def run_bounded_readability_analysis(
    text: str, semaphore: asyncio.Semaphore
) -> ReadabilityAnalysisResponse:
    async with semaphore:
        return await asyncio.to_thread(analyze_readability, text)


@router.post(
    "/analyze",
    response_model=ReadabilityAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute Manuscript Readability Metrics",
    description=(
        "Parses textual manuscript and extracts Flesch-Kincaid, Gunning Fog, "
        "and reading friction diagnostics."
    ),
)
async def analyze_text_readability(
    payload: AnalysisSubmissionPayload,
) -> ReadabilityAnalysisResponse:
    cleaned = payload.text.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Manuscript text is required for linguistic grading.",
        )
    return analyze_readability(cleaned)


@router.post(
    "/batch",
    response_model=ReadabilityBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute Batch Readability Metrics",
    description=(
        "Processes up to 50 individual text segments concurrently with bounded thread execution."
    ),
)
async def analyze_batch_readability(
    payload: ReadabilityBatchRequest,
    semaphore: asyncio.Semaphore = Depends(get_batch_semaphore),
) -> ReadabilityBatchResponse:
    results = list(
        await asyncio.gather(
            *(run_bounded_readability_analysis(text, semaphore) for text in payload.texts)
        )
    )
    return ReadabilityBatchResponse(results=results)
