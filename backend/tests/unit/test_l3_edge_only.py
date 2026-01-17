"""
L3 EDGE_ONLY Strategy Tests

Tests for the EDGE_ONLY sampling strategy implementation.
Validates determinism, mask filtering, constraints, and edge-first ordering.
"""
import copy
import json
import sys
import os
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.src.engines.l3.strategies.edge_only import EdgeOnlyStrategy
from backend.src.models.base import WaferMapSpec, ValidDieMask, DiePoint
from backend.src.models.catalog import ProcessContext, ToolProfile, RecipeFormat
from backend.src.models.sampling import SamplingPreviewRequest, StrategySelection

# Load golden fixtures
with open(os.path.join(os.path.dirname(__file__), "../fixtures/golden_requests.json")) as f:
    GOLDEN_REQUESTS = json.load(f)


def create_test_request(**overrides):
    """Create a test request with optional field overrides"""
    base_request = copy.deepcopy(GOLDEN_REQUESTS["preview_request"])

    # Update to use EDGE_ONLY strategy
    base_request["strategy"]["strategy_id"] = "EDGE_ONLY"
    base_request["process_context"]["allowed_strategy_set"] = ["EDGE_ONLY"]

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


def test_edge_only_determinism():
    """
    Test that EDGE_ONLY strategy produces identical outputs for identical inputs
    """
    strategy = EdgeOnlyStrategy()
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

    print(f"✅ EDGE_ONLY DETERMINISM: {len(results[0].selected_points)} points consistently generated")


def test_edge_only_edge_first_ordering():
    """
    Test that EDGE_ONLY prioritizes edge points (points farthest from center)
    """
    strategy = EdgeOnlyStrategy()
    request = create_test_request(max_sampling_points=50)

    result = strategy.select_points(request)
    points = result.selected_points

    # Calculate distances for all points
    die_pitch_x = request.wafer_map_spec.die_pitch_x_mm
    die_pitch_y = request.wafer_map_spec.die_pitch_y_mm

    distances = []
    for point in points:
        x_mm = point.die_x * die_pitch_x
        y_mm = point.die_y * die_pitch_y
        distance_mm = math.sqrt(x_mm**2 + y_mm**2)
        distances.append(distance_mm)

    # Verify distances are in descending order (edge first)
    # Allow small tolerance for floating point comparison
    for i in range(len(distances) - 1):
        assert distances[i] >= distances[i+1] - 0.01, \
            f"Distance ordering violation at index {i}: {distances[i]:.2f} < {distances[i+1]:.2f}"

    # First point should be at edge (maximum distance)
    max_distance = max(distances)
    first_distance = distances[0]
    assert abs(first_distance - max_distance) < 0.01, \
        f"First point not at edge: {first_distance:.2f}mm vs max {max_distance:.2f}mm"

    print(f"✅ EDGE FIRST ORDERING: Edge points selected first")
    print(f"   Distance range: {min(distances):.2f}mm to {max(distances):.2f}mm")
    print(f"   First 5 distances: {[f'{d:.2f}' for d in distances[:5]]}")


def test_edge_only_no_center_point():
    """
    Test that EDGE_ONLY does not select the center point when edge points are available
    """
    strategy = EdgeOnlyStrategy()
    request = create_test_request(max_sampling_points=25)

    result = strategy.select_points(request)
    points = result.selected_points

    # With edge-first ordering and sufficient valid points,
    # center should not be in the selected points
    center_selected = any(p.die_x == 0 and p.die_y == 0 for p in points)

    # Center might be selected if it's the only point or if we need min points
    # but with normal parameters, edge points should dominate
    die_pitch_x = request.wafer_map_spec.die_pitch_x_mm
    die_pitch_y = request.wafer_map_spec.die_pitch_y_mm

    # Check if center is selected and verify its distance
    if center_selected:
        # Center point should be last or near last (smallest distance)
        center_index = next(i for i, p in enumerate(points) if p.die_x == 0 and p.die_y == 0)
        # Center should be in the latter part of the selection
        assert center_index >= len(points) - 3, \
            f"Center point at index {center_index}, should be near end for EDGE_ONLY"

    print(f"✅ NO CENTER EMPHASIS: Edge points prioritized (center selected: {center_selected})")


def test_edge_only_edge_exclusion_mask():
    """
    Test edge exclusion mask filtering
    """
    strategy = EdgeOnlyStrategy()

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
        distance_mm = math.sqrt(x_mm**2 + y_mm**2)

        assert distance_mm <= 50.0 + 0.01, \
            f"Point ({point.die_x}, {point.die_y}) at {distance_mm:.1f}mm exceeds 50mm limit"

    # First point should be at or near the 50mm boundary (edge of valid region)
    first_point = points[0]
    x_mm = first_point.die_x * die_pitch_x
    y_mm = first_point.die_y * die_pitch_y
    first_distance = math.sqrt(x_mm**2 + y_mm**2)

    # Should be close to the exclusion boundary
    assert first_distance >= 40.0, \
        f"First point should be near edge boundary, but is at {first_distance:.2f}mm"

    print(f"✅ EDGE EXCLUSION: All {len(points)} points within 50mm radius")
    print(f"   First point at {first_distance:.2f}mm (near boundary)")


def test_edge_only_explicit_list_mask():
    """
    Test explicit list mask filtering
    """
    strategy = EdgeOnlyStrategy()

    # Define explicit valid die list with some edge points
    valid_list = [
        {"die_x": 0, "die_y": 0},    # center
        {"die_x": 10, "die_y": 0},   # far east (edge)
        {"die_x": 0, "die_y": 10},   # far north (edge)
        {"die_x": -10, "die_y": 0},  # far west (edge)
        {"die_x": 0, "die_y": -10},  # far south (edge)
        {"die_x": 1, "die_y": 0},    # near center
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

    # Edge points (±10, 0) and (0, ±10) should be selected first
    die_pitch_x = request.wafer_map_spec.die_pitch_x_mm
    die_pitch_y = request.wafer_map_spec.die_pitch_y_mm

    # First points should be the far edge points
    first_coords = [(p.die_x, p.die_y) for p in points[:4]]
    edge_coords = [(10, 0), (0, 10), (-10, 0), (0, -10)]

    # All edge coords should be in the first few selections
    for edge_coord in edge_coords:
        assert edge_coord in first_coords, \
            f"Edge point {edge_coord} should be in first selections, got {first_coords}"

    print(f"✅ EXPLICIT LIST: All {len(points)} points from valid list")
    print(f"   Selected order: {[(p.die_x, p.die_y) for p in points]}")


def test_edge_only_constraint_enforcement():
    """
    Test min/max sampling point constraint enforcement
    """
    strategy = EdgeOnlyStrategy()

    # Test max constraint
    request = create_test_request(max_sampling_points=8)
    result = strategy.select_points(request)
    assert len(result.selected_points) <= 8, \
        f"Exceeded max constraint: {len(result.selected_points)} > 8"

    # Test tool constraint
    request = create_test_request(max_points_per_wafer=5)
    result = strategy.select_points(request)
    assert len(result.selected_points) <= 5, \
        f"Exceeded tool constraint: {len(result.selected_points)} > 5"

    # Test min constraint (with sufficient available points)
    request = create_test_request(min_sampling_points=15, max_sampling_points=50)
    result = strategy.select_points(request)
    assert len(result.selected_points) >= 15, \
        f"Below min constraint: {len(result.selected_points)} < 15"

    # Test tool limit vs process limit (tool should win if lower)
    request = create_test_request(max_sampling_points=20, max_points_per_wafer=6)
    result = strategy.select_points(request)
    assert len(result.selected_points) <= 6, \
        f"Should respect tool limit: {len(result.selected_points)} > 6"

    print(f"✅ CONSTRAINT ENFORCEMENT: All min/max constraints respected")


def test_edge_only_insufficient_points():
    """
    Test EDGE_ONLY behavior when insufficient points available (should raise ConstraintError)
    """
    from backend.src.models.errors import ConstraintError, ErrorCode
    import pytest

    strategy = EdgeOnlyStrategy()

    # Very restrictive mask with high min requirement
    mask = {
        "type": "EDGE_EXCLUSION",
        "radius_mm": 5.0  # Very few points available
    }

    request = create_test_request(
        valid_die_mask=mask,
        min_sampling_points=50,  # Want 50 but only a few available
        max_sampling_points=100
    )

    # Should raise ConstraintError
    with pytest.raises(ConstraintError) as exc_info:
        strategy.select_points(request)

    error = exc_info.value
    assert error.code == ErrorCode.CANNOT_MEET_MIN_POINTS
    assert "need 50 points" in error.message


def test_edge_only_strategy_metadata():
    """
    Test strategy metadata (ID, version, etc.)
    """
    strategy = EdgeOnlyStrategy()

    assert strategy.get_strategy_id() == "EDGE_ONLY"
    assert strategy.get_strategy_version() == "1.0"

    request = create_test_request()
    result = strategy.select_points(request)

    assert result.sampling_strategy_id == "EDGE_ONLY"
    assert result.trace.strategy_version == "1.0"
    assert len(result.trace.generated_at) > 0

    print(f"✅ STRATEGY METADATA: ID={result.sampling_strategy_id}, Version={result.trace.strategy_version}")


def test_edge_only_strategy_allowlist_enforcement():
    """
    Test that EDGE_ONLY is rejected when not in allowed_strategy_set
    """
    from backend.src.models.errors import ValidationError, ErrorCode
    import pytest

    strategy = EdgeOnlyStrategy()

    # Request with EDGE_ONLY not in allowed set
    request = create_test_request(allowed_strategy_set=["CENTER_EDGE"])

    with pytest.raises(ValidationError) as exc_info:
        strategy.select_points(request)

    error = exc_info.value
    assert error.code == ErrorCode.DISALLOWED_STRATEGY
    assert "EDGE_ONLY" in error.message
    assert "not allowed" in error.message


def test_edge_only_wafer_geometries():
    """
    Test EDGE_ONLY with different wafer geometries
    """
    strategy = EdgeOnlyStrategy()

    # Test fine pitch (small dies)
    request_fine = create_test_request(die_pitch_x_mm=5.0, die_pitch_y_mm=5.0, max_sampling_points=50)
    result_fine = strategy.select_points(request_fine)

    # Test coarse pitch (large dies)
    request_coarse = create_test_request(die_pitch_x_mm=25.0, die_pitch_y_mm=25.0, max_sampling_points=50)
    result_coarse = strategy.select_points(request_coarse)

    # Test rectangular dies
    request_rect = create_test_request(die_pitch_x_mm=15.0, die_pitch_y_mm=5.0, max_sampling_points=50)
    result_rect = strategy.select_points(request_rect)

    # All should be deterministic
    result_fine_2 = strategy.select_points(request_fine)
    assert result_fine.selected_points == result_fine_2.selected_points

    # All should prioritize edge points
    for result, pitch_x, pitch_y in [
        (result_fine, 5.0, 5.0),
        (result_coarse, 25.0, 25.0),
        (result_rect, 15.0, 5.0)
    ]:
        points = result.selected_points
        # Calculate distances
        distances = []
        for p in points:
            dist = math.sqrt((p.die_x * pitch_x)**2 + (p.die_y * pitch_y)**2)
            distances.append(dist)

        # Verify descending order (edge first)
        for i in range(len(distances) - 1):
            assert distances[i] >= distances[i+1] - 0.01

    print(f"✅ WAFER GEOMETRIES:")
    print(f"   Fine pitch (5x5mm): {len(result_fine.selected_points)} points")
    print(f"   Coarse pitch (25x25mm): {len(result_coarse.selected_points)} points")
    print(f"   Rectangular (15x5mm): {len(result_rect.selected_points)} points")


if __name__ == "__main__":
    test_edge_only_determinism()
    test_edge_only_edge_first_ordering()
    test_edge_only_no_center_point()
    test_edge_only_edge_exclusion_mask()
    test_edge_only_explicit_list_mask()
    test_edge_only_constraint_enforcement()
    test_edge_only_insufficient_points()
    test_edge_only_strategy_metadata()
    test_edge_only_strategy_allowlist_enforcement()
    test_edge_only_wafer_geometries()
    print("🎉 All L3 EDGE_ONLY tests PASSED!")
