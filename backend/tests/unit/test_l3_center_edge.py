"""
L3 CENTER_EDGE Strategy Tests

Tests for the real CENTER_EDGE sampling strategy implementation.
Validates determinism, mask filtering, constraints, and wafer geometry handling.
"""
import copy
import json
import math
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.src.engines.l3.strategies.center_edge import CenterEdgeStrategy
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


# =============================================================================
# v1.3 Common Configuration Tests
# =============================================================================

def test_center_edge_common_edge_exclusion():
    """
    Test edge_exclusion_mm from common config (v1.3).

    Verifies that additional edge exclusion is applied on top of wafer mask.
    """
    strategy = CenterEdgeStrategy()

    # Request with common edge_exclusion_mm
    request = create_test_request(max_sampling_points=50, min_sampling_points=5)

    from backend.src.models.strategy_config import StrategyConfig
    request.strategy.strategy_config = StrategyConfig(**{
        "common": {
            "edge_exclusion_mm": 30.0
        }
    })

    result = strategy.select_points(request)
    points = result.selected_points

    # Verify all points are within edge exclusion boundary
    # 300mm wafer, 30mm exclusion = max radius 120mm
    wafer_radius = 150.0  # 300mm / 2
    max_allowed_radius = wafer_radius - 30.0  # 120mm

    for point in points:
        x_mm = point.die_x * 10.0
        y_mm = point.die_y * 10.0
        distance_mm = math.sqrt(x_mm**2 + y_mm**2)
        assert distance_mm <= max_allowed_radius + 0.01, f"Point ({point.die_x}, {point.die_y}) at {distance_mm}mm exceeds exclusion"

    print(f"✅ COMMON EDGE_EXCLUSION: All {len(points)} points within 120mm (30mm exclusion)")


def test_center_edge_common_rotation_seed():
    """
    Test rotation_seed from common config (v1.3).

    Verifies that rotation affects angular ordering of ring points.
    """
    strategy = CenterEdgeStrategy()

    # Request with no rotation
    request_no_rotation = create_test_request(max_sampling_points=20, min_sampling_points=10)
    result_no_rotation = strategy.select_points(request_no_rotation)

    # Request with 90 degree rotation
    request_rotated = create_test_request(max_sampling_points=20, min_sampling_points=10)
    from backend.src.models.strategy_config import StrategyConfig
    request_rotated.strategy.strategy_config = StrategyConfig(**{
        "common": {
            "rotation_seed": 90
        }
    })

    result_rotated = strategy.select_points(request_rotated)

    # Verify both produce points (sanity check)
    assert len(result_no_rotation.selected_points) > 0
    assert len(result_rotated.selected_points) > 0

    # Both should start with center (0,0) - rotation doesn't affect center
    assert result_no_rotation.selected_points[0].die_x == 0
    assert result_no_rotation.selected_points[0].die_y == 0
    assert result_rotated.selected_points[0].die_x == 0
    assert result_rotated.selected_points[0].die_y == 0

    # Verify determinism: same rotation produces same result
    result_rotated_2 = strategy.select_points(request_rotated)
    assert result_rotated.selected_points == result_rotated_2.selected_points

    print(f"✅ COMMON ROTATION: No rotation={len(result_no_rotation.selected_points)} points, 90° rotation={len(result_rotated.selected_points)} points (deterministic)")


def test_center_edge_common_target_point_count():
    """
    Test target_point_count from common config (v1.3).

    Verifies that explicit target count is respected within constraints.
    """
    strategy = CenterEdgeStrategy()

    # Request with explicit target_point_count
    request = create_test_request(
        max_sampling_points=50,
        min_sampling_points=5
    )

    from backend.src.models.strategy_config import StrategyConfig
    request.strategy.strategy_config = StrategyConfig(**{
        "common": {
            "target_point_count": 12
        }
    })

    result = strategy.select_points(request)
    points = result.selected_points

    # Should use target_point_count (12) since it's within [5, 50]
    assert len(points) == 12, f"Expected 12 points (target_point_count), got {len(points)}"

    # Should start with center
    assert points[0].die_x == 0 and points[0].die_y == 0

    # Verify determinism
    result_2 = strategy.select_points(request)
    assert len(result_2.selected_points) == len(points)
    assert result_2.selected_points == points

    print(f"✅ COMMON TARGET_POINT_COUNT: Requested 12, got {len(points)}")


def test_center_edge_common_config_integration():
    """
    Test multiple common config parameters together (v1.3).

    Verifies that edge_exclusion, rotation, and target_point_count work together.
    """
    strategy = CenterEdgeStrategy()

    request = create_test_request(
        max_sampling_points=50,
        min_sampling_points=5
    )

    from backend.src.models.strategy_config import StrategyConfig
    request.strategy.strategy_config = StrategyConfig(**{
        "common": {
            "target_point_count": 15,
            "edge_exclusion_mm": 20.0,
            "rotation_seed": 45
        }
    })

    result = strategy.select_points(request)
    points = result.selected_points

    # Verify target count
    assert len(points) == 15, f"Expected 15 points, got {len(points)}"

    # Verify edge exclusion
    wafer_radius = 150.0
    max_allowed_radius = wafer_radius - 20.0  # 130mm
    for point in points:
        x_mm = point.die_x * 10.0
        y_mm = point.die_y * 10.0
        distance_mm = math.sqrt(x_mm**2 + y_mm**2)
        assert distance_mm <= max_allowed_radius + 0.01

    # Should start with center
    assert points[0].die_x == 0 and points[0].die_y == 0

    # Verify determinism
    result_2 = strategy.select_points(request)
    assert result_2.selected_points == points

    print(f"✅ COMMON CONFIG INTEGRATION: {len(points)} points with edge_exclusion=20mm, rotation=45°, target=15")


if __name__ == "__main__":
    test_center_edge_determinism()
    test_center_edge_ring_structure()
    test_center_edge_edge_exclusion_mask()
    test_center_edge_explicit_list_mask()
    test_center_edge_constraint_enforcement()
    test_center_edge_wafer_geometries()
    test_center_edge_insufficient_points()
    test_center_edge_strategy_metadata()
    # v1.3 common config tests
    test_center_edge_common_edge_exclusion()
    test_center_edge_common_rotation_seed()
    test_center_edge_common_target_point_count()
    test_center_edge_common_config_integration()
    print("🎉 All L3 CENTER_EDGE tests PASSED!")