"""
Tests for HTTP route error handling.

Validates proper HTTP status codes and error response formats at the API level.
"""

import pytest
import json
import copy
from pathlib import Path
from fastapi import HTTPException
from src.server.routes.sampling import preview_sampling
from src.models.sampling import SamplingPreviewRequest
from src.models.base import WaferMapSpec, ValidDieMask, DiePoint
from src.models.catalog import ProcessContext, ToolProfile, RecipeFormat
from src.models.sampling import SamplingPreviewRequest, StrategySelection

# Load golden requests for test data
fixtures_path = Path(__file__).parent.parent / "fixtures" / "golden_requests.json"
with open(fixtures_path, 'r') as f:
    GOLDEN_REQUESTS = json.load(f)


def create_test_request(**overrides):
    """Create a test request with optional field overrides"""
    base_request = copy.deepcopy(GOLDEN_REQUESTS["preview_request"])
    
    # Apply overrides
    for key, value in overrides.items():
        if key in ["wafer_size_mm", "die_pitch_x_mm", "die_pitch_y_mm"]:
            base_request["wafer_map_spec"][key] = value
        elif key in ["min_sampling_points", "max_sampling_points", "criticality"]:
            base_request["process_context"][key] = value
        elif key in ["max_points_per_wafer", "edge_die_supported"]:
            base_request["tool_profile"][key] = value
        elif key == "valid_die_mask":
            base_request["wafer_map_spec"]["valid_die_mask"] = value
        elif key == "allowed_strategy_set":
            base_request["process_context"]["allowed_strategy_set"] = value
    
    # Convert dict to Pydantic models
    wafer_spec = WaferMapSpec(**base_request["wafer_map_spec"])
    process_context = ProcessContext(**base_request["process_context"]) 
    tool_profile = ToolProfile(**base_request["tool_profile"])
    strategy = StrategySelection(**base_request["strategy"])
    
    return SamplingPreviewRequest(
        wafer_map_spec=wafer_spec,
        process_context=process_context,
        tool_profile=tool_profile,
        strategy=strategy
    )


@pytest.mark.asyncio
async def test_preview_sampling_validation_error_returns_400():
    """Test that validation errors return HTTP 400 with proper error structure."""
    request = create_test_request(
        wafer_size_mm=-100.0  # Force validation error
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await preview_sampling(request)
    
    exception = exc_info.value
    assert exception.status_code == 400
    
    # Validate error response structure matches OpenAPI schema
    error_detail = exception.detail
    assert "error" in error_detail
    assert "code" in error_detail["error"]
    assert "message" in error_detail["error"]
    assert "type" in error_detail["error"]
    
    assert error_detail["error"]["code"] == "INVALID_WAFER_SPEC"
    assert error_detail["error"]["type"] == "VALIDATION_ERROR"
    assert "positive" in error_detail["error"]["message"].lower()


@pytest.mark.asyncio
async def test_preview_sampling_constraint_error_returns_400():
    """Test that constraint errors return HTTP 400 with proper error structure."""
    request = create_test_request(
        valid_die_mask={
            "type": "EXPLICIT_LIST",
            "valid_die_list": [
                {"die_x": 0, "die_y": 0},
                {"die_x": 1, "die_y": 0}
            ]
        },
        min_sampling_points=10  # More than available valid dies
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await preview_sampling(request)
    
    exception = exc_info.value
    assert exception.status_code == 400
    
    # Validate error response structure
    error_detail = exception.detail
    assert error_detail["error"]["code"] == "CANNOT_MEET_MIN_POINTS"
    assert error_detail["error"]["type"] == "CONSTRAINT_ERROR"
    assert "need 10 points" in error_detail["error"]["message"]


@pytest.mark.asyncio
async def test_preview_sampling_strategy_not_allowed_returns_400():
    """Test that disallowed strategy returns HTTP 400 with proper error structure."""
    request = create_test_request(
        allowed_strategy_set=["UNIFORM_GRID", "RANDOM"]  # Excludes CENTER_EDGE
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await preview_sampling(request)
    
    exception = exc_info.value
    assert exception.status_code == 400
    
    # Validate error response structure
    error_detail = exception.detail
    assert error_detail["error"]["code"] == "DISALLOWED_STRATEGY"
    assert error_detail["error"]["type"] == "VALIDATION_ERROR"
    assert "CENTER_EDGE" in error_detail["error"]["message"]


@pytest.mark.asyncio
async def test_preview_sampling_success_returns_200():
    """Test that valid requests return HTTP 200 with proper response structure."""
    request = create_test_request(
        # Use default golden request - should be valid
    )
    
    # Should not raise any exceptions
    response = await preview_sampling(request)
    
    # Validate response structure
    assert hasattr(response, 'sampling_output')
    assert hasattr(response, 'warnings')
    assert response.sampling_output.sampling_strategy_id == "CENTER_EDGE"
    assert len(response.sampling_output.selected_points) >= 5
    assert len(response.sampling_output.selected_points) <= 25
    assert isinstance(response.warnings, list)