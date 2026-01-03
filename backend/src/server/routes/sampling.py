from datetime import datetime
from fastapi import APIRouter, HTTPException
from ...models.sampling import (
    SamplingPreviewRequest,
    SamplingPreviewResponse,
    SamplingScoreRequest,
    SamplingScoreResponse,
)
from ...models.errors import SamplingError, ErrorResponse
from ..utils import get_deterministic_timestamp
from ...engine.l3 import CenterEdgeStrategy
from ...engine.l4 import SamplingScorer

router = APIRouter()

@router.post("/preview", response_model=SamplingPreviewResponse)
async def preview_sampling(request: SamplingPreviewRequest):
    try:
        # Use real L3 CENTER_EDGE strategy implementation
        strategy = CenterEdgeStrategy()
        
        # Execute L3 sampling point selection with error handling
        sampling_output = strategy.select_points(request)
        
        # Return schema-correct response (no contract changes)
        return SamplingPreviewResponse(
            sampling_output=sampling_output,
            warnings=[]  # Warnings will be added for non-blocking issues
        )
        
    except SamplingError as e:
        # Convert to HTTP error with proper status code and error format
        error_response = e.to_error_response()
        raise HTTPException(
            status_code=e.status_code,
            detail=error_response.dict()
        )

@router.post("/score", response_model=SamplingScoreResponse)
async def score_sampling(request: SamplingScoreRequest):
    # Use real L4 scoring engine (read-only evaluation)
    scorer = SamplingScorer()
    
    # Generate comprehensive score report
    score_report = scorer.score_sampling(request)
    
    # Return schema-correct response (no contract changes)
    return SamplingScoreResponse(score_report=score_report)