"""
L3 CENTER_EDGE Strategy Tests

Tests for the real CENTER_EDGE sampling strategy implementation.
Validates determinism, mask filtering, constraints, and wafer geometry handling.
"""
import copy
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.src.engine.l3 import CenterEdgeStrategy
from backend.src.models.base import WaferMapSpec, ValidDieMask, DiePoint
from backend.src.models.catalog import ProcessContext, ToolProfile, RecipeFormat
from backend.src.models.sampling import SamplingPreviewRequest, StrategySelection

# Load golden fixtures
with open(os.path.join(os.path.dirname(__file__), "../fixtures/golden_requests.json")) as f:
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
    
    # Convert dict to Pydantic models
    from backend.src.models.base import WaferMapSpec
    from backend.src.models.catalog import ProcessContext, ToolProfile, RecipeFormat  
    from backend.src.models.sampling import SamplingPreviewRequest, StrategySelection
    
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


def test_center_edge_determinism():
    """
    Test that CENTER_EDGE strategy produces identical outputs for identical inputs
    """
    strategy = CenterEdgeStrategy()
    request = create_test_request()
    
    # Run multiple times
    results = []
    for i in range(3):
        result = strategy.select_points(request)
        results.append(result)
    
    # All results should be identical (excluding timestamps)
    for i in range(1, len(results)):
        assert results[0].sampling_strategy_id == results[i].sampling_strategy_id
        assert results[0].selected_points == results[i].selected_points
        assert results[0].trace.strategy_version == results[i].trace.strategy_version
    
    # Should always start with center point
    assert results[0].selected_points[0].die_x == 0
    assert results[0].selected_points[0].die_y == 0
    
    print(f"✅ CENTER_EDGE DETERMINISM: {len(results[0].selected_points)} points consistently generated")


def test_center_edge_ring_structure():
    """
    Test that CENTER_EDGE follows proper ring structure
    """
    strategy = CenterEdgeStrategy()
    request = create_test_request(max_sampling_points=50)  # Get many points to see rings
    
    result = strategy.select_points(request)
    points = result.selected_points
    
    # Should start with center
    assert points[0].die_x == 0 and points[0].die_y == 0
    
    # Should have ring 1 points early (cardinals)
    ring1_cardinals = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    found_ring1 = []
    for point in points[1:8]:  # Check first few points after center
        if (point.die_x, point.die_y) in ring1_cardinals:
            found_ring1.append((point.die_x, point.die_y))
    
    assert len(found_ring1) >= 2, f"Should find ring 1 cardinals early, found {found_ring1}"
    
    print(f"✅ RING STRUCTURE: Center + ring structure verified")
    print(f"   First 8 points: {[(p.die_x, p.die_y) for p in points[:8]]}")


def test_center_edge_edge_exclusion_mask():
    """
    Test edge exclusion mask filtering
    """
    strategy = CenterEdgeStrategy()
    
    # Test with restrictive edge exclusion
    mask = {
        "type": "EDGE_EXCLUSION", 
        "radius_mm": 50.0  # Only points within 50mm
    }
    request = create_test_request(valid_die_mask=mask, max_sampling_points=100)
    
    result = strategy.select_points(request)
    points = result.selected_points
    
    # Verify all points are within radius
    die_pitch_x = request.wafer_map_spec.die_pitch_x_mm
    die_pitch_y = request.wafer_map_spec.die_pitch_y_mm
    
    for point in points:
        x_mm = point.die_x * die_pitch_x
        y_mm = point.die_y * die_pitch_y
        distance_mm = (x_mm**2 + y_mm**2)**0.5
        
        assert distance_mm <= 50.0, f"Point ({point.die_x}, {point.die_y}) at {distance_mm:.1f}mm exceeds 50mm limit"
    
    # Should include center
    assert points[0].die_x == 0 and points[0].die_y == 0
    
    print(f"✅ EDGE EXCLUSION: All {len(points)} points within 50mm radius")


def test_center_edge_explicit_list_mask():
    """
    Test explicit list mask filtering
    """
    strategy = CenterEdgeStrategy()
    
    # Define explicit valid die list
    valid_list = [
        {"die_x": 0, "die_y": 0},  # center
        {"die_x": 1, "die_y": 0},  # east
        {"die_x": 0, "die_y": 1},  # north
        {"die_x": 2, "die_y": 0},  # farther east
        {"die_x": 0, "die_y": 2},  # farther north
    ]
    
    mask = {
        "type": "EXPLICIT_LIST",
        "valid_die_list": valid_list
    }
    
    request = create_test_request(valid_die_mask=mask, max_sampling_points=50)
    
    result = strategy.select_points(request)
    points = result.selected_points
    
    # All points must be from valid list
    valid_coords = {(p["die_x"], p["die_y"]) for p in valid_list}
    for point in points:
        assert (point.die_x, point.die_y) in valid_coords, \
            f"Point ({point.die_x}, {point.die_y}) not in explicit valid list"
    
    # Should include center (highest priority)
    assert points[0].die_x == 0 and points[0].die_y == 0
    
    print(f"✅ EXPLICIT LIST: All {len(points)} points from valid list")
    print(f"   Selected: {[(p.die_x, p.die_y) for p in points]}")


def test_center_edge_constraint_enforcement():
    """
    Test min/max sampling point constraint enforcement
    """
    strategy = CenterEdgeStrategy()
    
    # Test max constraint
    request = create_test_request(max_sampling_points=8)
    result = strategy.select_points(request)
    assert len(result.selected_points) <= 8, f"Exceeded max constraint: {len(result.selected_points)} > 8"
    
    # Test tool constraint
    request = create_test_request(max_points_per_wafer=5)
    result = strategy.select_points(request)
    assert len(result.selected_points) <= 5, f"Exceeded tool constraint: {len(result.selected_points)} > 5"
    
    # Test min constraint (with sufficient available points)
    request = create_test_request(min_sampling_points=15, max_sampling_points=50)
    result = strategy.select_points(request)
    assert len(result.selected_points) >= 15, f"Below min constraint: {len(result.selected_points)} < 15"
    
    # Test tool limit vs process limit (tool should win if lower)
    request = create_test_request(max_sampling_points=20, max_points_per_wafer=6)
    result = strategy.select_points(request)
    assert len(result.selected_points) <= 6, f"Should respect tool limit: {len(result.selected_points)} > 6"
    
    print(f"✅ CONSTRAINT ENFORCEMENT: All min/max constraints respected")


def test_center_edge_wafer_geometries():
    """
    Test CENTER_EDGE with different wafer geometries
    """
    strategy = CenterEdgeStrategy()
    
    # Test fine pitch (small dies)
    request_fine = create_test_request(die_pitch_x_mm=5.0, die_pitch_y_mm=5.0, max_sampling_points=50)
    result_fine = strategy.select_points(request_fine)
    
    # Test coarse pitch (large dies)  
    request_coarse = create_test_request(die_pitch_x_mm=25.0, die_pitch_y_mm=25.0, max_sampling_points=50)
    result_coarse = strategy.select_points(request_coarse)
    
    # Test rectangular dies
    request_rect = create_test_request(die_pitch_x_mm=15.0, die_pitch_y_mm=5.0, max_sampling_points=50)
    result_rect = strategy.select_points(request_rect)
    
    # Fine pitch should allow more points within same radius
    # (though this depends on the edge exclusion radius)
    
    # All should start with center
    for result in [result_fine, result_coarse, result_rect]:
        assert result.selected_points[0].die_x == 0
        assert result.selected_points[0].die_y == 0
    
    # All should be deterministic
    result_fine_2 = strategy.select_points(request_fine)
    assert result_fine.selected_points == result_fine_2.selected_points
    
    print(f"✅ WAFER GEOMETRIES:")
    print(f"   Fine pitch (5x5mm): {len(result_fine.selected_points)} points")
    print(f"   Coarse pitch (25x25mm): {len(result_coarse.selected_points)} points") 
    print(f"   Rectangular (15x5mm): {len(result_rect.selected_points)} points")


def test_center_edge_insufficient_points():
    """
    Test CENTER_EDGE behavior when insufficient points available (should now raise ConstraintError)
    """
    from backend.src.models.errors import ConstraintError, ErrorCode
    import pytest
    
    strategy = CenterEdgeStrategy()
    
    # Very restrictive mask with high min requirement
    mask = {
        "type": "EDGE_EXCLUSION",
        "radius_mm": 1.0  # Only center die should be valid
    }
    
    request = create_test_request(
        valid_die_mask=mask,
        min_sampling_points=10,  # Want 10 but only ~1 available
        max_sampling_points=50
    )
    
    # Should now raise ConstraintError instead of returning insufficient points
    with pytest.raises(ConstraintError) as exc_info:
        strategy.select_points(request)
    
    error = exc_info.value
    assert error.code == ErrorCode.CANNOT_MEET_MIN_POINTS
    assert "need 10 points" in error.message
    assert "only 1 valid dies" in error.message


def test_center_edge_strategy_metadata():
    """
    Test strategy metadata (ID, version, etc.)
    """
    strategy = CenterEdgeStrategy()
    
    assert strategy.get_strategy_id() == "CENTER_EDGE"
    assert strategy.get_strategy_version() == "1.0"
    
    request = create_test_request()
    result = strategy.select_points(request)
    
    assert result.sampling_strategy_id == "CENTER_EDGE"
    assert result.trace.strategy_version == "1.0"
    assert len(result.trace.generated_at) > 0
    
    print(f"✅ STRATEGY METADATA: ID={result.sampling_strategy_id}, Version={result.trace.strategy_version}")


if __name__ == "__main__":
    test_center_edge_determinism()
    test_center_edge_ring_structure()
    test_center_edge_edge_exclusion_mask()
    test_center_edge_explicit_list_mask()
    test_center_edge_constraint_enforcement()
    test_center_edge_wafer_geometries()
    test_center_edge_insufficient_points()
    test_center_edge_strategy_metadata()
    print("🎉 All L3 CENTER_EDGE tests PASSED!")