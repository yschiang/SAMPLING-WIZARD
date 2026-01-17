from datetime import datetime
from fastapi import APIRouter, HTTPException
from ...models.sampling import (
    SamplingPreviewRequest,
    SamplingPreviewResponse,
    SamplingScoreRequest,
    SamplingScoreResponse,
)
from ...models.errors import SamplingError, ErrorResponse, ValidationError, ErrorCode
from ..utils import get_deterministic_timestamp
from ...engines.l3 import get_strategy  # PR-B: Use registry dispatch
from ...engine.l4 import SamplingScorer

router = APIRouter()


def validate_strategy_allowed(request: SamplingPreviewRequest) -> None:
    """
    Validate that the requested strategy_id is in the process context's allowed set.

    Raises:
        ValidationError: If strategy_id is not in allowed_strategy_set
    """
    strategy_id = request.strategy.strategy_id
    allowed_strategies = request.process_context.allowed_strategy_set

    if strategy_id not in allowed_strategies:
        raise ValidationError(
            ErrorCode.DISALLOWED_STRATEGY,
            f"Strategy '{strategy_id}' is not allowed for this process context. "
            f"Allowed strategies: {allowed_strategies}"
        )


@router.post("/preview", response_model=SamplingPreviewResponse)
async def preview_sampling(request: SamplingPreviewRequest):
    try:
        # PR-A: Route-level strategy allowlist enforcement
        validate_strategy_allowed(request)

        # PR-B: Get strategy from registry by ID (no hardcoded strategy)
        strategy = get_strategy(request.strategy.strategy_id)

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