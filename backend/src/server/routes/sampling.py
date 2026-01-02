from datetime import datetime
from fastapi import APIRouter
from ...models.sampling import (
    SamplingPreviewRequest,
    SamplingPreviewResponse,
    SamplingScoreRequest,
    SamplingScoreResponse,
)
from ..utils import get_deterministic_timestamp
from ...engine.l3 import CenterEdgeStrategy

router = APIRouter()

@router.post("/preview", response_model=SamplingPreviewResponse)
async def preview_sampling(request: SamplingPreviewRequest):
    # Use real L3 CENTER_EDGE strategy implementation
    strategy = CenterEdgeStrategy()
    
    # Execute L3 sampling point selection
    sampling_output = strategy.select_points(request)
    
    # Return schema-correct response (no contract changes)
    return SamplingPreviewResponse(
        sampling_output=sampling_output,
        warnings=[]  # Real warnings implementation will be added in PR-2
    )

@router.post("/score", response_model=SamplingScoreResponse)
async def score_sampling(request: SamplingScoreRequest):
    # L4 deterministic scoring (no mutation of points)
    num_points = len(request.sampling_output.selected_points)

    # Simple v0 scoring
    coverage_score = min(1.0, num_points / 15.0)  # rings approximation
    statistical_score = min(1.0, num_points / request.process_context.min_sampling_points)

    # Risk alignment: penalize if HIGH criticality and < 8 points
    risk_alignment_score = 1.0
    if request.process_context.criticality == "HIGH" and num_points < 8:
        risk_alignment_score = 0.6

    overall_score = (coverage_score + statistical_score + risk_alignment_score) / 3.0

    warnings = []
    if risk_alignment_score < 1.0:
        warnings.append("HIGH_CRITICALITY_LOW_COVERAGE")

    return SamplingScoreResponse(score_report={
        "coverage_score": coverage_score,
        "statistical_score": statistical_score,
        "risk_alignment_score": risk_alignment_score,
        "overall_score": overall_score,
        "warnings": warnings,
        "version": "1.0"
    })