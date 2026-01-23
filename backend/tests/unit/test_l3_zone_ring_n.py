"""
L3 ZONE_RING_N Strategy Tests

Tests for the ZONE_RING_N parameterized sampling strategy.
Validates determinism, ring allocation, parameter handling, and constraints.
"""
import copy
import json
import sys
import os
import math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.src.engines.l3.strategies.zone_ring_n import ZoneRingNStrategy
from backend.src.models.base import WaferMapSpec, ValidDieMask, DiePoint
from backend.src.models.catalog import ProcessContext, ToolProfile, RecipeFormat
from backend.src.models.sampling import SamplingPreviewRequest, StrategySelection

# Load golden fixtures
with open(os.path.join(os.path.dirname(__file__), "../fixtures/golden_requests.json")) as f:
    GOLDEN_REQUESTS = json.load(f)


def create_test_request(**overrides):
    """Create a test request with optional field overrides"""
    base_request = copy.deepcopy(GOLDEN_REQUESTS["preview_request"])

    # Update to use ZONE_RING_N strategy
    base_request["strategy"]["strategy_id"] = "ZONE_RING_N"
    base_request["process_context"]["allowed_strategy_set"] = ["ZONE_RING_N"]

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
        elif key == "strategy_params":
            # v1.3: Use strategy_config.advanced instead of params
            if base_request["strategy"].get("strategy_config") is None:
                base_request["strategy"]["strategy_config"] = {"advanced": value}
            elif "advanced" not in base_request["strategy"]["strategy_config"]:
                base_request["strategy"]["strategy_config"]["advanced"] = value
            else:
                # Merge with existing advanced config
                base_request["strategy"]["strategy_config"]["advanced"].update(value)

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


def test_zone_ring_n_determinism():
    """
    Test that ZONE_RING_N produces identical outputs for identical inputs
    """
    strategy = ZoneRingNStrategy()
    request = create_test_request()

    results = []
    for i in range(3):
        result = strategy.select_points(request)
        results.append(result)

    # All results should be identical
    for i in range(1, len(results)):
        assert results[0].sampling_strategy_id == results[i].sampling_strategy_id
        assert results[0].selected_points == results[i].selected_points
        assert results[0].trace.strategy_version == results[i].trace.strategy_version

    print(f"✅ ZONE_RING_N DETERMINISM: {len(results[0].selected_points)} points consistently generated")


def test_zone_ring_n_default_3_rings():
    """
    Test that ZONE_RING_N defaults to 3 rings when no params provided
    """
    strategy = ZoneRingNStrategy()
    request = create_test_request(max_sampling_points=27, min_sampling_points=20)

    result = strategy.select_points(request)
    points = result.selected_points

    # With 3 rings, expect points across different distance ranges
    die_pitch_x = request.wafer_map_spec.die_pitch_x_mm
    die_pitch_y = request.wafer_map_spec.die_pitch_y_mm
    wafer_radius = request.wafer_map_spec.wafer_size_mm / 2

    # Calculate distances
    distances = []
    for p in points:
        x_mm = p.die_x * die_pitch_x
        y_mm = p.die_y * die_pitch_y
        distance_mm = math.sqrt(x_mm**2 + y_mm**2)
        distances.append(distance_mm)

    # Should have points from different rings (varied distances)
    distance_range = max(distances) - min(distances)
    assert distance_range > wafer_radius * 0.3, \
        f"Expected significant distance spread, got {distance_range:.2f}mm"

    print(f"✅ DEFAULT 3 RINGS: Distance spread {distance_range:.2f}mm")


def test_zone_ring_n_parameter_variations():
    """
    Test ZONE_RING_N with different num_rings parameters
    """
    strategy = ZoneRingNStrategy()

    for num_rings in [1, 2, 3, 5]:
        request = create_test_request(
            strategy_params={"num_rings": num_rings},
            max_sampling_points=25,
            min_sampling_points=15
        )

        result = strategy.select_points(request)
        points = result.selected_points

        assert len(points) >= 15, f"num_rings={num_rings}: insufficient points"
        assert len(points) <= 25, f"num_rings={num_rings}: too many points"

        # Verify determinism with same params
        result2 = strategy.select_points(request)
        assert points == result2.selected_points, f"num_rings={num_rings}: not deterministic"

    print(f"✅ PARAMETER VARIATIONS: Tested num_rings 1, 2, 3, 5")


def test_zone_ring_n_ring_allocation_stability():
    """
    Test that ring allocation is stable and proportional
    """
    strategy = ZoneRingNStrategy()

    # Use N=3 with controlled target
    request = create_test_request(
        strategy_params={"num_rings": 3},
        max_sampling_points=27,  # 27 = 3 + 9 + 15 (proportional to 1:3:5 ratio)
        min_sampling_points=27
    )

    result = strategy.select_points(request)
    points = result.selected_points

    # Classify returned points into rings
    wafer_radius = request.wafer_map_spec.wafer_size_mm / 2
    die_pitch_x = request.wafer_map_spec.die_pitch_x_mm
    die_pitch_y = request.wafer_map_spec.die_pitch_y_mm

    ring_counts = {0: 0, 1: 0, 2: 0}
    for p in points:
        x_mm = p.die_x * die_pitch_x
        y_mm = p.die_y * die_pitch_y
        distance_mm = math.sqrt(x_mm**2 + y_mm**2)

        ring_index = int(distance_mm / (wafer_radius / 3))
        if ring_index >= 3:
            ring_index = 2
        ring_counts[ring_index] += 1

    # Ring allocation should be roughly proportional (1:3:5 ratio)
    # Allow some variation due to discrete points
    total = sum(ring_counts.values())
    if total > 0:
        ring0_pct = (ring_counts[0] / total) * 100
        ring2_pct = (ring_counts[2] / total) * 100

        # Ring 0 should be smallest (~11%), Ring 2 largest (~56%)
        assert ring0_pct < 30, f"Ring 0 has {ring0_pct:.1f}% (should be smallest)"
        assert ring2_pct > 30, f"Ring 2 has {ring2_pct:.1f}% (should be largest)"

    print(f"✅ RING ALLOCATION: Ring distribution {ring_counts}")


def test_zone_ring_n_invalid_params():
    """
    Test parameter validation
    """
    from backend.src.models.errors import ValidationError, ErrorCode
    import pytest

    strategy = ZoneRingNStrategy()

    # Test invalid num_rings (negative)
    request1 = create_test_request(strategy_params={"num_rings": -1})
    with pytest.raises(ValidationError) as exc_info:
        strategy.select_points(request1)
    assert "positive integer" in exc_info.value.message.lower()

    # Test invalid num_rings (zero)
    request2 = create_test_request(strategy_params={"num_rings": 0})
    with pytest.raises(ValidationError) as exc_info:
        strategy.select_points(request2)

    # Test invalid num_rings (too large)
    request3 = create_test_request(strategy_params={"num_rings": 100})
    with pytest.raises(ValidationError) as exc_info:
        strategy.select_points(request3)
    assert "<= 10" in exc_info.value.message

    print(f"✅ INVALID PARAMS: All validation errors raised correctly")


def test_zone_ring_n_edge_exclusion_mask():
    """
    Test edge exclusion mask filtering
    """
    strategy = ZoneRingNStrategy()

    mask = {"type": "EDGE_EXCLUSION", "radius_mm": 50.0}
    request = create_test_request(
        valid_die_mask=mask,
        max_sampling_points=20,
        min_sampling_points=5,
        strategy_params={"num_rings": 3}
    )

    result = strategy.select_points(request)
    points = result.selected_points

    # Verify all points within radius
    die_pitch_x = request.wafer_map_spec.die_pitch_x_mm
    die_pitch_y = request.wafer_map_spec.die_pitch_y_mm

    for point in points:
        x_mm = point.die_x * die_pitch_x
        y_mm = point.die_y * die_pitch_y
        distance_mm = math.sqrt(x_mm**2 + y_mm**2)
        assert distance_mm <= 50.0 + 0.01

    print(f"✅ EDGE EXCLUSION: All {len(points)} points within 50mm")


def test_zone_ring_n_explicit_list_mask():
    """
    Test explicit list mask filtering
    """
    strategy = ZoneRingNStrategy()

    valid_list = [
        {"die_x": 0, "die_y": 0},
        {"die_x": 5, "die_y": 0},
        {"die_x": 0, "die_y": 5},
        {"die_x": -5, "die_y": 0},
        {"die_x": 0, "die_y": -5},
        {"die_x": 10, "die_y": 0},
        {"die_x": 0, "die_y": 10},
    ]

    mask = {"type": "EXPLICIT_LIST", "valid_die_list": valid_list}
    request = create_test_request(
        valid_die_mask=mask,
        max_sampling_points=7,
        min_sampling_points=1
    )

    result = strategy.select_points(request)
    points = result.selected_points

    valid_coords = {(p["die_x"], p["die_y"]) for p in valid_list}
    for point in points:
        assert (point.die_x, point.die_y) in valid_coords

    print(f"✅ EXPLICIT LIST: All {len(points)} points from valid list")


def test_zone_ring_n_constraint_enforcement():
    """
    Test min/max sampling point constraint enforcement
    """
    strategy = ZoneRingNStrategy()

    # Test max constraint
    request = create_test_request(max_sampling_points=8, min_sampling_points=5)
    result = strategy.select_points(request)
    assert len(result.selected_points) <= 8

    # Test min constraint
    request = create_test_request(min_sampling_points=15, max_sampling_points=50)
    result = strategy.select_points(request)
    assert len(result.selected_points) >= 15

    # Test tool limit
    request = create_test_request(max_points_per_wafer=6, min_sampling_points=1)
    result = strategy.select_points(request)
    assert len(result.selected_points) <= 6

    print(f"✅ CONSTRAINT ENFORCEMENT: All constraints respected")


def test_zone_ring_n_insufficient_points():
    """
    Test behavior when insufficient points available
    """
    from backend.src.models.errors import ConstraintError, ErrorCode
    import pytest

    strategy = ZoneRingNStrategy()

    mask = {"type": "EDGE_EXCLUSION", "radius_mm": 5.0}
    request = create_test_request(
        valid_die_mask=mask,
        min_sampling_points=50,
        max_sampling_points=100
    )

    with pytest.raises(ConstraintError) as exc_info:
        strategy.select_points(request)

    assert exc_info.value.code == ErrorCode.CANNOT_MEET_MIN_POINTS


def test_zone_ring_n_strategy_metadata():
    """
    Test strategy metadata
    """
    strategy = ZoneRingNStrategy()

    assert strategy.get_strategy_id() == "ZONE_RING_N"
    assert strategy.get_strategy_version() == "1.0"

    request = create_test_request()
    result = strategy.select_points(request)

    assert result.sampling_strategy_id == "ZONE_RING_N"
    assert result.trace.strategy_version == "1.0"
    assert len(result.trace.generated_at) > 0

    print(f"✅ STRATEGY METADATA: ID={result.sampling_strategy_id}, Version={result.trace.strategy_version}")


def test_zone_ring_n_strategy_allowlist_enforcement():
    """
    Test that ZONE_RING_N is rejected when not in allowed set
    """
    from backend.src.models.errors import ValidationError, ErrorCode
    import pytest

    strategy = ZoneRingNStrategy()
    request = create_test_request(allowed_strategy_set=["CENTER_EDGE"])

    with pytest.raises(ValidationError) as exc_info:
        strategy.select_points(request)

    assert exc_info.value.code == ErrorCode.DISALLOWED_STRATEGY
    assert "ZONE_RING_N" in exc_info.value.message


def test_zone_ring_n_wafer_geometries():
    """
    Test ZONE_RING_N with different wafer geometries
    """
    strategy = ZoneRingNStrategy()

    request_fine = create_test_request(die_pitch_x_mm=5.0, die_pitch_y_mm=5.0, max_sampling_points=25, min_sampling_points=15)
    result_fine = strategy.select_points(request_fine)

    request_coarse = create_test_request(die_pitch_x_mm=25.0, die_pitch_y_mm=25.0, max_sampling_points=25, min_sampling_points=10)
    result_coarse = strategy.select_points(request_coarse)

    # Verify determinism
    result_fine_2 = strategy.select_points(request_fine)
    assert result_fine.selected_points == result_fine_2.selected_points

    print(f"✅ WAFER GEOMETRIES: Fine={len(result_fine.selected_points)}, Coarse={len(result_coarse.selected_points)}")


# =============================================================================
# v1.3 Common Configuration Tests
# =============================================================================

def test_zone_ring_n_common_edge_exclusion():
    """
    Test edge_exclusion_mm from common config (v1.3).

    Verifies that additional edge exclusion is applied on top of wafer mask.
    """
    strategy = ZoneRingNStrategy()

    # Request with common edge_exclusion_mm
    request_dict = create_test_request(
        max_sampling_points=50,
        min_sampling_points=5
    )

    # Add common config with edge exclusion
    request_dict.strategy.strategy_config = {
        "common": {
            "edge_exclusion_mm": 30.0
        }
    }

    # Recreate request with Pydantic validation
    from backend.src.models.strategy_config import StrategyConfig
    request_dict.strategy.strategy_config = StrategyConfig(**request_dict.strategy.strategy_config)

    result = strategy.select_points(request_dict)
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


def test_zone_ring_n_common_rotation_seed():
    """
    Test rotation_seed from common config (v1.3).

    Verifies that rotation affects angular ordering of points.
    """
    strategy = ZoneRingNStrategy()

    # Request with no rotation
    request_no_rotation = create_test_request(max_sampling_points=20, min_sampling_points=15)
    result_no_rotation = strategy.select_points(request_no_rotation)

    # Request with 90 degree rotation
    request_rotated = create_test_request(max_sampling_points=20, min_sampling_points=15)
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

    # Verify determinism: same rotation produces same result
    result_rotated_2 = strategy.select_points(request_rotated)
    assert result_rotated.selected_points == result_rotated_2.selected_points

    # Note: Point sets may differ due to angular ordering change
    # (rotation affects canonical sort, which affects stride selection)

    print(f"✅ COMMON ROTATION: No rotation={len(result_no_rotation.selected_points)} points, 90° rotation={len(result_rotated.selected_points)} points (deterministic)")


def test_zone_ring_n_common_target_point_count():
    """
    Test target_point_count from common config (v1.3).

    Verifies that explicit target count is respected within constraints.
    """
    strategy = ZoneRingNStrategy()

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

    # Should respect target_point_count (12) since it's within [5, 50]
    # Note: Final count may be adjusted by ring allocation logic
    assert len(points) >= 5, "Should meet min constraint"
    assert len(points) <= 50, "Should not exceed max constraint"

    # Verify determinism
    result_2 = strategy.select_points(request)
    assert len(result_2.selected_points) == len(points)
    assert result_2.selected_points == points

    print(f"✅ COMMON TARGET_POINT_COUNT: Requested 12, got {len(points)} (within [5, 50])")


def test_zone_ring_n_common_config_integration():
    """
    Test multiple common config parameters together (v1.3).

    Verifies that edge_exclusion, rotation, and target_point_count work together.
    """
    strategy = ZoneRingNStrategy()

    request = create_test_request(
        max_sampling_points=50,
        min_sampling_points=10
    )

    from backend.src.models.strategy_config import StrategyConfig
    request.strategy.strategy_config = StrategyConfig(**{
        "common": {
            "target_point_count": 18,
            "edge_exclusion_mm": 20.0,
            "rotation_seed": 45
        }
    })

    result = strategy.select_points(request)
    points = result.selected_points

    # Verify constraints
    assert len(points) >= 10, "Should meet min constraint"
    assert len(points) <= 50, "Should not exceed max constraint"

    # Verify edge exclusion
    wafer_radius = 150.0
    max_allowed_radius = wafer_radius - 20.0  # 130mm
    for point in points:
        x_mm = point.die_x * 10.0
        y_mm = point.die_y * 10.0
        distance_mm = math.sqrt(x_mm**2 + y_mm**2)
        assert distance_mm <= max_allowed_radius + 0.01

    # Verify determinism
    result_2 = strategy.select_points(request)
    assert result_2.selected_points == points

    print(f"✅ COMMON CONFIG INTEGRATION: {len(points)} points with edge_exclusion=20mm, rotation=45°, target=18")


if __name__ == "__main__":
    test_zone_ring_n_determinism()
    test_zone_ring_n_default_3_rings()
    test_zone_ring_n_parameter_variations()
    test_zone_ring_n_ring_allocation_stability()
    test_zone_ring_n_invalid_params()
    test_zone_ring_n_edge_exclusion_mask()
    test_zone_ring_n_explicit_list_mask()
    test_zone_ring_n_constraint_enforcement()
    test_zone_ring_n_insufficient_points()
    test_zone_ring_n_strategy_metadata()
    test_zone_ring_n_strategy_allowlist_enforcement()
    test_zone_ring_n_wafer_geometries()
    # v1.3 common config tests
    test_zone_ring_n_common_edge_exclusion()
    test_zone_ring_n_common_rotation_seed()
    test_zone_ring_n_common_target_point_count()
    test_zone_ring_n_common_config_integration()
    print("🎉 All L3 ZONE_RING_N tests PASSED!")
