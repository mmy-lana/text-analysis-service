from fastapi import APIRouter, HTTPException, status

from app.core.algorithms.readability_indexes import analyze_readability
from app.models.common import AnalysisSubmissionPayload
from app.models.readability import ReadabilityAnalysisResponse

router = APIRouter(prefix="/readability", tags=["Readability Engine"])


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
