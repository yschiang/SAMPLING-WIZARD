"""
L3 GRID_UNIFORM Strategy Tests

Tests for the GRID_UNIFORM sampling strategy implementation.
Validates determinism, uniform distribution, mask filtering, and constraints.
"""
import copy
import json
import sys
import os
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.src.engines.l3.strategies.grid_uniform import GridUniformStrategy
from backend.src.models.base import WaferMapSpec, ValidDieMask, DiePoint
from backend.src.models.catalog import ProcessContext, ToolProfile, RecipeFormat
from backend.src.models.sampling import SamplingPreviewRequest, StrategySelection

# Load golden fixtures
with open(os.path.join(os.path.dirname(__file__), "../fixtures/golden_requests.json")) as f:
    GOLDEN_REQUESTS = json.load(f)


def create_test_request(**overrides):
    """Create a test request with optional field overrides"""
    base_request = copy.deepcopy(GOLDEN_REQUESTS["preview_request"])

    # Update to use GRID_UNIFORM strategy
    base_request["strategy"]["strategy_id"] = "GRID_UNIFORM"
    base_request["process_context"]["allowed_strategy_set"] = ["GRID_UNIFORM"]

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


def test_grid_uniform_determinism():
    """
    Test that GRID_UNIFORM strategy produces identical outputs for identical inputs
    """
    strategy = GridUniformStrategy()
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

    print(f"✅ GRID_UNIFORM DETERMINISM: {len(results[0].selected_points)} points consistently generated")


def test_grid_uniform_quadrant_distribution():
    """
    Test that GRID_UNIFORM distributes points across quadrants (not clustered)
    """
    strategy = GridUniformStrategy()
    request = create_test_request(max_sampling_points=25, min_sampling_points=20)

    result = strategy.select_points(request)
    points = result.selected_points

    # Count points per quadrant
    quadrants = {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
    for p in points:
        if p.die_x >= 0 and p.die_y >= 0:
            quadrants['Q1'] += 1
        elif p.die_x < 0 and p.die_y >= 0:
            quadrants['Q2'] += 1
        elif p.die_x < 0 and p.die_y < 0:
            quadrants['Q3'] += 1
        else:  # p.die_x >= 0 and p.die_y < 0
            quadrants['Q4'] += 1

    # Should have points in at least 3 quadrants (reasonable distribution)
    occupied_quadrants = sum(1 for count in quadrants.values() if count > 0)
    assert occupied_quadrants >= 3, \
        f"Expected points in at least 3 quadrants, found {occupied_quadrants}: {quadrants}"

    # No quadrant should have more than 70% of points (not heavily clustered)
    total_points = len(points)
    for quad, count in quadrants.items():
        percentage = (count / total_points) * 100
        assert percentage <= 70, \
            f"Quadrant {quad} has {percentage:.1f}% of points (too clustered)"

    print(f"✅ QUADRANT DISTRIBUTION: Points across {occupied_quadrants} quadrants")
    print(f"   Quadrant distribution: {quadrants}")


def test_grid_uniform_distance_spread():
    """
    Test that GRID_UNIFORM has good distance spread (center to edge coverage)
    """
    strategy = GridUniformStrategy()
    request = create_test_request(max_sampling_points=25)

    result = strategy.select_points(request)
    points = result.selected_points

    # Calculate distances
    die_pitch_x = request.wafer_map_spec.die_pitch_x_mm
    die_pitch_y = request.wafer_map_spec.die_pitch_y_mm
    wafer_radius = request.wafer_map_spec.wafer_size_mm / 2

    distances = []
    for p in points:
        x_mm = p.die_x * die_pitch_x
        y_mm = p.die_y * die_pitch_y
        distance_mm = math.sqrt(x_mm**2 + y_mm**2)
        distances.append(distance_mm)

    # Check distance spread
    distance_range = max(distances) - min(distances)

    # Valid die mask might limit the range
    valid_radius = request.wafer_map_spec.valid_die_mask.radius_mm
    if valid_radius:
        expected_min_range = valid_radius * 0.5
    else:
        expected_min_range = wafer_radius * 0.5

    assert distance_range >= expected_min_range, \
        f"Distance spread {distance_range:.2f}mm too small, expected >={expected_min_range:.2f}mm"

    print(f"✅ DISTANCE SPREAD: {distance_range:.2f}mm range")
    print(f"   Min: {min(distances):.2f}mm, Max: {max(distances):.2f}mm")


def test_grid_uniform_spatial_variance():
    """
    Test that points have spatial variance (not all in same region)
    """
    strategy = GridUniformStrategy()
    request = create_test_request(max_sampling_points=25)

    result = strategy.select_points(request)
    points = result.selected_points

    # Calculate variance in X and Y directions
    x_coords = [p.die_x for p in points]
    y_coords = [p.die_y for p in points]

    x_mean = sum(x_coords) / len(x_coords)
    y_mean = sum(y_coords) / len(y_coords)

    x_variance = sum((x - x_mean)**2 for x in x_coords) / len(x_coords)
    y_variance = sum((y - y_mean)**2 for y in y_coords) / len(y_coords)

    # Should have reasonable variance (not all clustered at one point)
    assert x_variance > 1.0, f"X variance too low: {x_variance:.2f}"
    assert y_variance > 1.0, f"Y variance too low: {y_variance:.2f}"

    print(f"✅ SPATIAL VARIANCE: X={x_variance:.2f}, Y={y_variance:.2f}")


def test_grid_uniform_stride_edge_cases():
    """
    Test stride calculation edge cases
    """
    strategy = GridUniformStrategy()

    # Edge case 1: target_count = 1 (select first point only)
    request1 = create_test_request(max_sampling_points=1, min_sampling_points=1)
    result1 = strategy.select_points(request1)
    assert len(result1.selected_points) == 1

    # Edge case 2: target_count = available (select all)
    # Create restrictive mask to limit points
    mask = {"type": "EDGE_EXCLUSION", "radius_mm": 30.0}
    request2 = create_test_request(valid_die_mask=mask, max_sampling_points=100, min_sampling_points=1)
    result2 = strategy.select_points(request2)
    assert len(result2.selected_points) > 0

    # Edge case 3: Various stride values
    for target in [5, 10, 15]:
        request = create_test_request(max_sampling_points=target, min_sampling_points=target)
        result = strategy.select_points(request)
        assert len(result.selected_points) == target, \
            f"Expected {target} points, got {len(result.selected_points)}"

    print(f"✅ STRIDE EDGE CASES: All edge cases handled correctly")


def test_grid_uniform_edge_exclusion_mask():
    """
    Test edge exclusion mask filtering with uniform distribution
    """
    strategy = GridUniformStrategy()

    # Test with restrictive edge exclusion
    mask = {
        "type": "EDGE_EXCLUSION",
        "radius_mm": 50.0  # Only points within 50mm
    }
    request = create_test_request(valid_die_mask=mask, max_sampling_points=20)

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

    # Should still have reasonable distribution within the valid region
    # Check that we have points at different distances
    distances = []
    for p in points:
        x_mm = p.die_x * die_pitch_x
        y_mm = p.die_y * die_pitch_y
        distances.append(math.sqrt(x_mm**2 + y_mm**2))

    distance_range = max(distances) - min(distances)
    assert distance_range > 10.0, \
        f"Even with mask, should have distance spread, got {distance_range:.2f}mm"

    print(f"✅ EDGE EXCLUSION: All {len(points)} points within 50mm radius")
    print(f"   Distance spread within mask: {distance_range:.2f}mm")


def test_grid_uniform_explicit_list_mask():
    """
    Test explicit list mask filtering with stride-based selection
    """
    strategy = GridUniformStrategy()

    # Define explicit valid die list spanning different regions
    valid_list = [
        {"die_x": 0, "die_y": 0},    # center
        {"die_x": 5, "die_y": 0},    # east
        {"die_x": 0, "die_y": 5},    # north
        {"die_x": -5, "die_y": 0},   # west
        {"die_x": 0, "die_y": -5},   # south
        {"die_x": 10, "die_y": 0},   # far east
        {"die_x": 0, "die_y": 10},   # far north
        {"die_x": -10, "die_y": 0},  # far west
        {"die_x": 0, "die_y": -10},  # far south
        {"die_x": 7, "die_y": 7},    # NE
        {"die_x": -7, "die_y": 7},   # NW
        {"die_x": -7, "die_y": -7},  # SW
        {"die_x": 7, "die_y": -7},   # SE
    ]

    mask = {
        "type": "EXPLICIT_LIST",
        "valid_die_list": valid_list
    }

    request = create_test_request(valid_die_mask=mask, max_sampling_points=10)

    result = strategy.select_points(request)
    points = result.selected_points

    # All points must be from valid list
    valid_coords = {(p["die_x"], p["die_y"]) for p in valid_list}
    for point in points:
        assert (point.die_x, point.die_y) in valid_coords, \
            f"Point ({point.die_x}, {point.die_y}) not in explicit valid list"

    print(f"✅ EXPLICIT LIST: All {len(points)} points from valid list")
    print(f"   Selected: {[(p.die_x, p.die_y) for p in points]}")


def test_grid_uniform_constraint_enforcement():
    """
    Test min/max sampling point constraint enforcement
    """
    strategy = GridUniformStrategy()

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


def test_grid_uniform_insufficient_points():
    """
    Test GRID_UNIFORM behavior when insufficient points available (should raise ConstraintError)
    """
    from backend.src.models.errors import ConstraintError, ErrorCode
    import pytest

    strategy = GridUniformStrategy()

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


def test_grid_uniform_strategy_metadata():
    """
    Test strategy metadata (ID, version, etc.)
    """
    strategy = GridUniformStrategy()

    assert strategy.get_strategy_id() == "GRID_UNIFORM"
    assert strategy.get_strategy_version() == "1.0"

    request = create_test_request()
    result = strategy.select_points(request)

    assert result.sampling_strategy_id == "GRID_UNIFORM"
    assert result.trace.strategy_version == "1.0"
    assert len(result.trace.generated_at) > 0

    print(f"✅ STRATEGY METADATA: ID={result.sampling_strategy_id}, Version={result.trace.strategy_version}")


def test_grid_uniform_strategy_allowlist_enforcement():
    """
    Test that GRID_UNIFORM is rejected when not in allowed_strategy_set
    """
    from backend.src.models.errors import ValidationError, ErrorCode
    import pytest

    strategy = GridUniformStrategy()

    # Request with GRID_UNIFORM not in allowed set
    request = create_test_request(allowed_strategy_set=["CENTER_EDGE"])

    with pytest.raises(ValidationError) as exc_info:
        strategy.select_points(request)

    error = exc_info.value
    assert error.code == ErrorCode.DISALLOWED_STRATEGY
    assert "GRID_UNIFORM" in error.message
    assert "not allowed" in error.message


def test_grid_uniform_wafer_geometries():
    """
    Test GRID_UNIFORM with different wafer geometries
    """
    strategy = GridUniformStrategy()

    # Test fine pitch (small dies)
    request_fine = create_test_request(die_pitch_x_mm=5.0, die_pitch_y_mm=5.0, max_sampling_points=25)
    result_fine = strategy.select_points(request_fine)

    # Test coarse pitch (large dies)
    request_coarse = create_test_request(die_pitch_x_mm=25.0, die_pitch_y_mm=25.0, max_sampling_points=25)
    result_coarse = strategy.select_points(request_coarse)

    # Test rectangular dies
    request_rect = create_test_request(die_pitch_x_mm=15.0, die_pitch_y_mm=5.0, max_sampling_points=25)
    result_rect = strategy.select_points(request_rect)

    # All should be deterministic
    result_fine_2 = strategy.select_points(request_fine)
    assert result_fine.selected_points == result_fine_2.selected_points

    # All should have uniform distribution
    for result in [result_fine, result_coarse, result_rect]:
        points = result.selected_points

        # Check quadrant distribution
        quadrants = {'Q1': 0, 'Q2': 0, 'Q3': 0, 'Q4': 0}
        for p in points:
            if p.die_x >= 0 and p.die_y >= 0: quadrants['Q1'] += 1
            elif p.die_x < 0 and p.die_y >= 0: quadrants['Q2'] += 1
            elif p.die_x < 0 and p.die_y < 0: quadrants['Q3'] += 1
            else: quadrants['Q4'] += 1

        occupied = sum(1 for c in quadrants.values() if c > 0)
        assert occupied >= 3, f"Poor distribution: only {occupied} quadrants"

    print(f"✅ WAFER GEOMETRIES:")
    print(f"   Fine pitch (5x5mm): {len(result_fine.selected_points)} points")
    print(f"   Coarse pitch (25x25mm): {len(result_coarse.selected_points)} points")
    print(f"   Rectangular (15x5mm): {len(result_rect.selected_points)} points")


if __name__ == "__main__":
    test_grid_uniform_determinism()
    test_grid_uniform_quadrant_distribution()
    test_grid_uniform_distance_spread()
    test_grid_uniform_spatial_variance()
    test_grid_uniform_stride_edge_cases()
    test_grid_uniform_edge_exclusion_mask()
    test_grid_uniform_explicit_list_mask()
    test_grid_uniform_constraint_enforcement()
    test_grid_uniform_insufficient_points()
    test_grid_uniform_strategy_metadata()
    test_grid_uniform_strategy_allowlist_enforcement()
    test_grid_uniform_wafer_geometries()
    print("🎉 All L3 GRID_UNIFORM tests PASSED!")
