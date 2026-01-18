"""
Tests for L3 error handling and validation.

Validates proper HTTP status codes, error response formats, and warning codes.
"""

import pytest
import json
import copy
from pathlib import Path
from src.engines.l3.strategies.center_edge import CenterEdgeStrategy
from src.models.base import WaferMapSpec, ValidDieMask, DiePoint
from src.models.catalog import ProcessContext, ToolProfile, RecipeFormat
from src.models.sampling import SamplingPreviewRequest, StrategySelection
from src.models.errors import (
    ValidationError, ConstraintError, ErrorCode, ErrorType
)

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


class TestL3ValidationErrors:
    """Test validation error conditions that should return 4xx status codes."""
    
    def test_disallowed_strategy_error(self):
        """Test strategy not in allowed_strategy_set raises DISALLOWED_STRATEGY error."""
        strategy = CenterEdgeStrategy()
        
        # Create request with allowed_strategy_set that excludes CENTER_EDGE
        request = create_test_request(
            allowed_strategy_set=["UNIFORM_GRID", "RANDOM"]  # Excludes CENTER_EDGE
        )
        
        with pytest.raises(ValidationError) as exc_info:
            strategy.select_points(request)
        
        error = exc_info.value
        assert error.code == ErrorCode.DISALLOWED_STRATEGY
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.status_code == 400
        assert "CENTER_EDGE" in error.message
        assert "UNIFORM_GRID" in error.message
    
    def test_invalid_wafer_spec_negative_size(self):
        """Test negative wafer_size_mm raises INVALID_WAFER_SPEC error."""
        strategy = CenterEdgeStrategy()
        
        request = create_test_request(
            wafer_size_mm=-100.0  # Invalid negative size
        )
        
        with pytest.raises(ValidationError) as exc_info:
            strategy.select_points(request)
        
        error = exc_info.value
        assert error.code == ErrorCode.INVALID_WAFER_SPEC
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.status_code == 400
        assert "positive" in error.message.lower()
    
    def test_invalid_die_pitch(self):
        """Test invalid die pitch raises INVALID_WAFER_SPEC error."""
        strategy = CenterEdgeStrategy()
        
        request = create_test_request(
            die_pitch_x_mm=0.0,  # Invalid zero pitch
            die_pitch_y_mm=-1.0  # Invalid negative pitch
        )
        
        with pytest.raises(ValidationError) as exc_info:
            strategy.select_points(request)
        
        error = exc_info.value
        assert error.code == ErrorCode.INVALID_WAFER_SPEC
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.status_code == 400
    
    def test_invalid_constraints_negative_min(self):
        """Test negative min_sampling_points raises INVALID_CONSTRAINTS error."""
        strategy = CenterEdgeStrategy()
        
        request = create_test_request(
            min_sampling_points=-1  # Invalid negative minimum
        )
        
        with pytest.raises(ValidationError) as exc_info:
            strategy.select_points(request)
        
        error = exc_info.value
        assert error.code == ErrorCode.INVALID_CONSTRAINTS
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.status_code == 400
        assert "non-negative" in error.message
    
    def test_invalid_constraints_max_less_than_min(self):
        """Test max < min sampling points raises INVALID_CONSTRAINTS error."""
        strategy = CenterEdgeStrategy()
        
        request = create_test_request(
            min_sampling_points=20,
            max_sampling_points=10  # Invalid: max < min
        )
        
        with pytest.raises(ValidationError) as exc_info:
            strategy.select_points(request)
        
        error = exc_info.value
        assert error.code == ErrorCode.INVALID_CONSTRAINTS
        assert error.error_type == ErrorType.VALIDATION_ERROR
        assert error.status_code == 400
        assert ">=" in error.message


class TestL3ConstraintErrors:
    """Test constraint error conditions that should return 4xx status codes."""
    
    def test_insufficient_valid_dies_constraint_error(self):
        """Test insufficient valid dies to meet min_sampling_points raises CONSTRAINT_ERROR."""
        strategy = CenterEdgeStrategy()
        
        # Use explicit list with only 2 dies, but require 5 minimum points
        request = create_test_request(
            valid_die_mask={
                "type": "EXPLICIT_LIST",
                "valid_die_list": [
                    {"die_x": 0, "die_y": 0},
                    {"die_x": 1, "die_y": 0}
                ]
            },
            min_sampling_points=5  # Require more than available
        )
        
        with pytest.raises(ConstraintError) as exc_info:
            strategy.select_points(request)
        
        error = exc_info.value
        assert error.code == ErrorCode.CANNOT_MEET_MIN_POINTS
        assert error.error_type == ErrorType.CONSTRAINT_ERROR
        assert error.status_code == 400
        assert "need 5 points" in error.message
        assert "only 2 valid dies" in error.message


class TestL3ErrorResponseFormat:
    """Test that error responses match the OpenAPI schema format."""
    
    def test_error_response_structure(self):
        """Test that SamplingError produces correct ErrorResponse structure."""
        strategy = CenterEdgeStrategy()
        
        request = create_test_request(
            wafer_size_mm=-1.0  # Force validation error
        )
        
        with pytest.raises(ValidationError) as exc_info:
            strategy.select_points(request)
        
        error = exc_info.value
        error_response = error.to_error_response()
        
        # Validate structure matches OpenAPI ErrorResponse schema
        assert hasattr(error_response, 'error')
        assert hasattr(error_response.error, 'code')
        assert hasattr(error_response.error, 'message')
        assert hasattr(error_response.error, 'type')
        
        assert isinstance(error_response.error.code, str)
        assert isinstance(error_response.error.message, str)
        assert isinstance(error_response.error.type, str)
        
        assert error_response.error.code == ErrorCode.INVALID_WAFER_SPEC.value
        assert error_response.error.type == ErrorType.VALIDATION_ERROR.value


class TestL3SuccessfulValidation:
    """Test that valid requests pass validation and execute successfully."""
    
    def test_valid_request_passes_validation(self):
        """Test that a valid request passes all validation and executes."""
        strategy = CenterEdgeStrategy()
        
        request = create_test_request(
            # Use default golden request - should be valid
        )
        
        # Should not raise any exceptions
        result = strategy.select_points(request)
        
        # Validate result structure
        assert result.sampling_strategy_id == "CENTER_EDGE"
        assert len(result.selected_points) >= 5  # At least minimum from golden request
        assert len(result.selected_points) <= 25  # At most maximum from golden request
        assert result.trace.strategy_version == "1.0"