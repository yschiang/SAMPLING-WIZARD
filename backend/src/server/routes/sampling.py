from datetime import datetime
from fastapi import APIRouter
from ...models.sampling import (
    SamplingPreviewRequest,
    SamplingPreviewResponse,
    SamplingScoreRequest,
    SamplingScoreResponse,
)

router = APIRouter()

@router.post("/preview", response_model=SamplingPreviewResponse)
async def preview_sampling(request: SamplingPreviewRequest):
    # L3 CENTER_EDGE strategy implementation (deterministic placeholder)
    candidates = [
        {"die_x": 0, "die_y": 0},   # center
        {"die_x": 3, "die_y": 0}, {"die_x": -3, "die_y": 0},  # inner ring
        {"die_x": 0, "die_y": 3}, {"die_x": 0, "die_y": -3},
        {"die_x": 8, "die_y": 0}, {"die_x": -8, "die_y": 0},  # outer ring
        {"die_x": 0, "die_y": 8}, {"die_x": 0, "die_y": -8},
        {"die_x": 6, "die_y": 6}, {"die_x": -6, "die_y": -6}  # corners
    ]

    # Apply constraints (simplified for v0)
    max_points = min(
        request.process_context.max_sampling_points,
        request.tool_profile.max_points_per_wafer
    )
    selected_points = candidates[:max_points]

    return SamplingPreviewResponse(
        sampling_output={
            "sampling_strategy_id": "CENTER_EDGE",
            "selected_points": selected_points,
            "trace": {
                "strategy_version": "1.0",
                "generated_at": datetime.utcnow().isoformat() + "Z"
            }
        },
        warnings=[]
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