"""
Tests for L4 integration with sampling routes.

Validates that the real L4 scorer integrates properly with HTTP endpoints.
"""

import pytest
import json
import copy
from pathlib import Path
from src.server.routes.sampling import score_sampling
from src.models.base import WaferMapSpec, ValidDieMask, DiePoint
from src.models.catalog import ProcessContext, ToolProfile
from src.models.sampling import SamplingScoreRequest, SamplingOutput, SamplingTrace

# Load golden requests for test data
fixtures_path = Path(__file__).parent.parent / "fixtures" / "golden_requests.json"
with open(fixtures_path, 'r') as f:
    GOLDEN_REQUESTS = json.load(f)


def create_integration_score_request(selected_points=None, **overrides):
    """Create a test score request for integration testing"""
    base_request = copy.deepcopy(GOLDEN_REQUESTS["score_request_base"])
    
    # Apply overrides
    for key, value in overrides.items():
        if key in ["min_sampling_points", "max_sampling_points", "criticality"]:
            base_request["process_context"][key] = value
        elif key in ["wafer_size_mm", "die_pitch_x_mm", "die_pitch_y_mm"]:
            base_request["wafer_map_spec"][key] = value
    
    # Create models
    wafer_spec = WaferMapSpec(**base_request["wafer_map_spec"])
    process_context = ProcessContext(**base_request["process_context"])
    tool_profile = ToolProfile(**base_request["tool_profile"])
    
    # Create sampling output with provided points
    if selected_points is None:
        selected_points = [
            DiePoint(die_x=0, die_y=0),   # Center
            DiePoint(die_x=3, die_y=0),   # Inner
            DiePoint(die_x=0, die_y=3),
            DiePoint(die_x=6, die_y=-2),  # Middle
            DiePoint(die_x=-4, die_y=5),
            DiePoint(die_x=12, die_y=8),  # Outer
        ]
    
    sampling_output = SamplingOutput(
        sampling_strategy_id="CENTER_EDGE",
        selected_points=selected_points,
        trace=SamplingTrace(strategy_version="1.0", generated_at="2024-01-01T12:00:00Z")
    )
    
    return SamplingScoreRequest(
        wafer_map_spec=wafer_spec,
        process_context=process_context,
        tool_profile=tool_profile,
        sampling_output=sampling_output
    )


@pytest.mark.asyncio
async def test_l4_route_integration():
    """Test L4 scorer integration with HTTP route."""
    request = create_integration_score_request()
    
    # Execute scoring via route
    response = await score_sampling(request)
    
    # Validate response structure
    assert hasattr(response, 'score_report')
    score_report = response.score_report
    
    # Validate all required score fields present
    required_fields = ["coverage_score", "statistical_score", "risk_alignment_score", 
                      "overall_score", "warnings", "version"]
    for field in required_fields:
        assert hasattr(score_report, field), f"Missing required field: {field}"
    
    # Validate score bounds
    assert 0.0 <= score_report.coverage_score <= 1.0
    assert 0.0 <= score_report.statistical_score <= 1.0
    assert 0.0 <= score_report.risk_alignment_score <= 1.0
    assert 0.0 <= score_report.overall_score <= 1.0
    
    # Validate warnings is a list
    assert isinstance(score_report.warnings, list)
    
    # Validate version
    assert score_report.version == "1.0"
    
    print(f"✅ L4 route integration: coverage={score_report.coverage_score:.2f}, "
          f"statistical={score_report.statistical_score:.2f}, "
          f"risk={score_report.risk_alignment_score:.2f}, "
          f"overall={score_report.overall_score:.2f}")


@pytest.mark.asyncio
async def test_l4_route_different_criticality_levels():
    """Test L4 scorer with different criticality levels via route."""
    base_points = [
        DiePoint(die_x=0, die_y=0),     # Center
        DiePoint(die_x=2, die_y=0),     # Inner
        DiePoint(die_x=8, die_y=5),     # Edge
        DiePoint(die_x=-10, die_y=-8),  # Edge
    ]
    
    # Test HIGH criticality
    high_request = create_integration_score_request(
        selected_points=base_points,
        criticality="HIGH"
    )
    high_response = await score_sampling(high_request)
    high_scores = high_response.score_report
    
    # Test MEDIUM criticality
    medium_request = create_integration_score_request(
        selected_points=base_points,
        criticality="MEDIUM"
    )
    medium_response = await score_sampling(medium_request)
    medium_scores = medium_response.score_report
    
    # Test LOW criticality
    low_request = create_integration_score_request(
        selected_points=base_points,
        criticality="LOW"
    )
    low_response = await score_sampling(low_request)
    low_scores = low_response.score_report
    
    # Validate all responses have proper structure
    for scores in [high_scores, medium_scores, low_scores]:
        assert 0.0 <= scores.coverage_score <= 1.0
        assert 0.0 <= scores.statistical_score <= 1.0
        assert 0.0 <= scores.risk_alignment_score <= 1.0
        assert 0.0 <= scores.overall_score <= 1.0
        assert isinstance(scores.warnings, list)
    
    # LOW criticality should generally be most forgiving
    assert low_scores.risk_alignment_score >= 0.7
    
    print(f"✅ L4 criticality scoring: HIGH={high_scores.risk_alignment_score:.2f}, "
          f"MEDIUM={medium_scores.risk_alignment_score:.2f}, "
          f"LOW={low_scores.risk_alignment_score:.2f}")


@pytest.mark.asyncio
async def test_l4_route_edge_cases():
    """Test L4 scorer edge cases via route."""
    
    # Test 1: Empty points
    empty_request = create_integration_score_request(selected_points=[])
    empty_response = await score_sampling(empty_request)
    empty_scores = empty_response.score_report
    
    assert empty_scores.coverage_score == 0.0
    assert empty_scores.statistical_score == 0.0
    assert empty_scores.risk_alignment_score == 0.0
    assert empty_scores.overall_score == 0.0
    assert len(empty_scores.warnings) > 0
    
    # Test 2: Single point (minimal)
    single_request = create_integration_score_request(
        selected_points=[DiePoint(die_x=0, die_y=0)]
    )
    single_response = await score_sampling(single_request)
    single_scores = single_response.score_report
    
    assert single_scores.coverage_score == 0.25  # 1 ring out of 4
    assert 0.0 < single_scores.statistical_score <= 1.0
    assert single_scores.overall_score > 0.0
    
    # Test 3: Many points (comprehensive coverage)
    many_points = [
        DiePoint(die_x=0, die_y=0),     # Center ring
        DiePoint(die_x=2, die_y=0),     # Inner ring
        DiePoint(die_x=5, die_y=3),     # Middle ring
        DiePoint(die_x=12, die_y=-8),   # Outer ring
        DiePoint(die_x=-10, die_y=10),  # Outer ring
        DiePoint(die_x=15, die_y=15),   # Far outer
    ]
    many_request = create_integration_score_request(selected_points=many_points)
    many_response = await score_sampling(many_request)
    many_scores = many_response.score_report
    
    assert many_scores.coverage_score == 1.0  # All rings covered
    assert many_scores.statistical_score == 1.0  # Exceeds minimum
    assert many_scores.overall_score > single_scores.overall_score
    
    print(f"✅ L4 edge cases: empty=0.0, single={single_scores.overall_score:.2f}, "
          f"comprehensive={many_scores.overall_score:.2f}")


@pytest.mark.asyncio
async def test_l4_route_determinism():
    """Test that L4 route produces deterministic results."""
    request = create_integration_score_request()
    
    # Execute scoring multiple times
    responses = []
    for i in range(3):
        response = await score_sampling(request)
        responses.append(response.score_report)
    
    # All responses should be identical
    for i in range(1, len(responses)):
        assert responses[i] == responses[0], f"Response {i} differs from response 0"
    
    print(f"✅ L4 route determinism verified: {len(responses)} identical responses")