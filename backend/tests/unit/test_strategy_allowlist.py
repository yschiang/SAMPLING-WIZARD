"""
Tests for PR-A: Route-level strategy allowlist enforcement.

Validates that the route validates strategy_id against allowed_strategy_set
BEFORE invoking the strategy engine.
"""

import pytest
import json
import copy
from pathlib import Path
from fastapi import HTTPException
from src.server.routes.sampling import preview_sampling, validate_strategy_allowed
from src.models.sampling import SamplingPreviewRequest, StrategySelection
from src.models.base import WaferMapSpec, ValidDieMask
from src.models.catalog import ProcessContext, ToolProfile
from src.models.errors import ValidationError, ErrorCode, ErrorType

# Load golden requests for test data
fixtures_path = Path(__file__).parent.parent / "fixtures" / "golden_requests.json"
with open(fixtures_path, 'r') as f:
    GOLDEN_REQUESTS = json.load(f)


def create_test_request(**overrides):
    """Create a test request with optional field overrides"""
    base_request = copy.deepcopy(GOLDEN_REQUESTS["preview_request"])

    # Apply overrides
    for key, value in overrides.items():
        if key == "strategy_id":
            base_request["strategy"]["strategy_id"] = value
        elif key == "allowed_strategy_set":
            base_request["process_context"]["allowed_strategy_set"] = value
        elif key in ["wafer_size_mm", "die_pitch_x_mm", "die_pitch_y_mm"]:
            base_request["wafer_map_spec"][key] = value
        elif key in ["min_sampling_points", "max_sampling_points"]:
            base_request["process_context"][key] = value

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


class TestValidateStrategyAllowed:
    """Unit tests for the validate_strategy_allowed function."""

    def test_allowed_strategy_passes_validation(self):
        """Test that strategy in allowed_strategy_set passes validation."""
        request = create_test_request(
            strategy_id="CENTER_EDGE",
            allowed_strategy_set=["CENTER_EDGE", "EDGE_ONLY"]
        )

        # Should not raise
        validate_strategy_allowed(request)

    def test_disallowed_strategy_raises_validation_error(self):
        """Test that strategy NOT in allowed_strategy_set raises ValidationError."""
        request = create_test_request(
            strategy_id="CENTER_EDGE",
            allowed_strategy_set=["EDGE_ONLY", "GRID_UNIFORM"]  # Excludes CENTER_EDGE
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_strategy_allowed(request)

        error = exc_info.value
        assert error.code == ErrorCode.DISALLOWED_STRATEGY
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.status_code == 400
        assert "CENTER_EDGE" in error.message
        assert "EDGE_ONLY" in error.message or "allowed" in error.message.lower()

    def test_empty_allowlist_rejects_all_strategies(self):
        """Test that empty allowed_strategy_set rejects all strategies."""
        request = create_test_request(
            strategy_id="CENTER_EDGE",
            allowed_strategy_set=[]  # Empty list
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_strategy_allowed(request)

        error = exc_info.value
        assert error.code == ErrorCode.DISALLOWED_STRATEGY

    def test_case_sensitive_matching(self):
        """Test that strategy_id matching is case-sensitive."""
        request = create_test_request(
            strategy_id="CENTER_EDGE",
            allowed_strategy_set=["center_edge"]  # Wrong case
        )

        with pytest.raises(ValidationError) as exc_info:
            validate_strategy_allowed(request)

        error = exc_info.value
        assert error.code == ErrorCode.DISALLOWED_STRATEGY


class TestRouteAllowlistEnforcement:
    """Integration tests for route-level allowlist enforcement."""

    @pytest.mark.asyncio
    async def test_route_rejects_disallowed_strategy_with_400(self):
        """Test that route returns HTTP 400 for disallowed strategy."""
        request = create_test_request(
            strategy_id="CENTER_EDGE",
            allowed_strategy_set=["EDGE_ONLY"]  # Excludes CENTER_EDGE
        )

        with pytest.raises(HTTPException) as exc_info:
            await preview_sampling(request)

        exception = exc_info.value
        assert exception.status_code == 400

        error_detail = exception.detail
        assert error_detail["error"]["code"] == "DISALLOWED_STRATEGY"
        assert error_detail["error"]["type"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_route_accepts_allowed_strategy(self):
        """Test that route accepts strategy in allowed_strategy_set."""
        request = create_test_request(
            strategy_id="CENTER_EDGE",
            allowed_strategy_set=["CENTER_EDGE"]
        )

        # Should not raise
        response = await preview_sampling(request)

        assert response.sampling_output.sampling_strategy_id == "CENTER_EDGE"
        assert len(response.sampling_output.selected_points) > 0

    @pytest.mark.asyncio
    async def test_error_response_structure_matches_schema(self):
        """Test that error response structure matches OpenAPI ErrorResponse schema."""
        request = create_test_request(
            strategy_id="UNKNOWN_STRATEGY",
            allowed_strategy_set=["CENTER_EDGE"]
        )

        with pytest.raises(HTTPException) as exc_info:
            await preview_sampling(request)

        exception = exc_info.value
        error_detail = exception.detail

        # Validate structure matches OpenAPI schema
        assert "error" in error_detail
        assert "code" in error_detail["error"]
        assert "message" in error_detail["error"]
        assert "type" in error_detail["error"]

        assert isinstance(error_detail["error"]["code"], str)
        assert isinstance(error_detail["error"]["message"], str)
        assert isinstance(error_detail["error"]["type"], str)


class TestAllowlistDeterminism:
    """Test that allowlist validation is deterministic."""

    def test_same_input_same_result(self):
        """Test that same input always produces same validation result."""
        request = create_test_request(
            strategy_id="CENTER_EDGE",
            allowed_strategy_set=["EDGE_ONLY"]
        )

        # Run validation 10 times - should always raise same error
        results = []
        for _ in range(10):
            try:
                validate_strategy_allowed(request)
                results.append("pass")
            except ValidationError as e:
                results.append(f"fail:{e.code.value}")

        # All results should be identical
        assert len(set(results)) == 1
        assert results[0] == "fail:DISALLOWED_STRATEGY"
