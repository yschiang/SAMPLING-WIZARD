"""
Tests for L3 common utilities (v1.3).

Tests common configuration parameter utilities:
- apply_edge_exclusion()
- get_rotation_offset()
- apply_rotation_to_angle()
- get_deterministic_rng_seed()
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

import pytest
from backend.src.engines.l3.common import (
    apply_edge_exclusion,
    get_rotation_offset,
    apply_rotation_to_angle,
    get_deterministic_rng_seed,
)
from backend.src.models.base import DiePoint, WaferMapSpec, ValidDieMask


def create_test_wafer_spec(wafer_size_mm=300.0, die_pitch=10.0) -> WaferMapSpec:
    """Helper to create test wafer spec."""
    return WaferMapSpec(
        wafer_size_mm=wafer_size_mm,
        die_pitch_x_mm=die_pitch,
        die_pitch_y_mm=die_pitch,
        origin="CENTER",
        notch_orientation_deg=0.0,
        coordinate_system="DIE_GRID",
        valid_die_mask=ValidDieMask(type="EDGE_EXCLUSION", radius_mm=wafer_size_mm/2),
        version="1.0"
    )


class TestApplyEdgeExclusion:
    """Test apply_edge_exclusion() function."""

    def test_zero_exclusion_returns_all_points(self):
        """Test that zero exclusion returns all points unchanged."""
        wafer = create_test_wafer_spec()
        points = [
            DiePoint(die_x=0, die_y=0),
            DiePoint(die_x=10, die_y=0),
            DiePoint(die_x=14, die_y=0),
        ]

        result = apply_edge_exclusion(points, wafer, edge_exclusion_mm=0.0)

        assert len(result) == 3
        assert result == points

    def test_negative_exclusion_returns_all_points(self):
        """Test that negative exclusion is treated as no exclusion."""
        wafer = create_test_wafer_spec()
        points = [DiePoint(die_x=0, die_y=0), DiePoint(die_x=14, die_y=0)]

        result = apply_edge_exclusion(points, wafer, edge_exclusion_mm=-5.0)

        assert len(result) == 2
        assert result == points

    def test_small_exclusion_filters_edge_points(self):
        """Test that small exclusion (5mm) filters edge points."""
        wafer = create_test_wafer_spec(wafer_size_mm=300.0, die_pitch=10.0)
        # 300mm wafer, radius = 150mm
        # 5mm exclusion = max distance 145mm
        points = [
            DiePoint(die_x=0, die_y=0),    # 0mm - KEEP
            DiePoint(die_x=10, die_y=0),   # 100mm - KEEP
            DiePoint(die_x=14, die_y=0),   # 140mm - KEEP
            DiePoint(die_x=15, die_y=0),   # 150mm - REMOVE (at edge)
        ]

        result = apply_edge_exclusion(points, wafer, edge_exclusion_mm=5.0)

        assert len(result) == 3
        assert DiePoint(die_x=0, die_y=0) in result
        assert DiePoint(die_x=10, die_y=0) in result
        assert DiePoint(die_x=14, die_y=0) in result
        assert DiePoint(die_x=15, die_y=0) not in result

    def test_large_exclusion_filters_many_points(self):
        """Test that large exclusion (50mm) filters many edge points."""
        wafer = create_test_wafer_spec(wafer_size_mm=300.0, die_pitch=10.0)
        # 50mm exclusion = max distance 100mm
        points = [
            DiePoint(die_x=0, die_y=0),    # 0mm - KEEP
            DiePoint(die_x=5, die_y=0),    # 50mm - KEEP
            DiePoint(die_x=10, die_y=0),   # 100mm - KEEP (exactly at limit)
            DiePoint(die_x=11, die_y=0),   # 110mm - REMOVE
            DiePoint(die_x=14, die_y=0),   # 140mm - REMOVE
        ]

        result = apply_edge_exclusion(points, wafer, edge_exclusion_mm=50.0)

        assert len(result) == 3
        assert DiePoint(die_x=0, die_y=0) in result
        assert DiePoint(die_x=5, die_y=0) in result
        assert DiePoint(die_x=10, die_y=0) in result

    def test_exclusion_removes_all_points(self):
        """Test exclusion larger than wafer removes all points."""
        wafer = create_test_wafer_spec(wafer_size_mm=300.0)
        points = [
            DiePoint(die_x=0, die_y=0),
            DiePoint(die_x=5, die_y=0),
            DiePoint(die_x=10, die_y=0),
        ]

        # 200mm exclusion on 150mm radius wafer = max distance -50mm (impossible)
        result = apply_edge_exclusion(points, wafer, edge_exclusion_mm=200.0)

        assert len(result) == 0

    def test_preserves_ordering(self):
        """Test that filtering preserves original point ordering."""
        wafer = create_test_wafer_spec()
        points = [
            DiePoint(die_x=0, die_y=0),
            DiePoint(die_x=1, die_y=0),
            DiePoint(die_x=2, die_y=0),
            DiePoint(die_x=14, die_y=0),  # Will be filtered
            DiePoint(die_x=3, die_y=0),
        ]

        result = apply_edge_exclusion(points, wafer, edge_exclusion_mm=20.0)

        # Should maintain order of kept points
        assert result[0] == DiePoint(die_x=0, die_y=0)
        assert result[1] == DiePoint(die_x=1, die_y=0)
        assert result[2] == DiePoint(die_x=2, die_y=0)
        assert result[3] == DiePoint(die_x=3, die_y=0)

    def test_works_with_different_wafer_sizes(self):
        """Test exclusion logic with different wafer sizes."""
        # 200mm wafer
        wafer_200 = create_test_wafer_spec(wafer_size_mm=200.0, die_pitch=10.0)
        points = [DiePoint(die_x=0, die_y=0), DiePoint(die_x=9, die_y=0)]

        result = apply_edge_exclusion(points, wafer_200, edge_exclusion_mm=10.0)
        # 200mm wafer, radius=100mm, exclusion=10mm, max=90mm
        # (9,0) = 90mm - should be kept (at limit)
        assert len(result) == 2

        # 450mm wafer
        wafer_450 = create_test_wafer_spec(wafer_size_mm=450.0, die_pitch=10.0)
        result = apply_edge_exclusion(points, wafer_450, edge_exclusion_mm=10.0)
        # 450mm wafer, radius=225mm, exclusion=10mm, max=215mm
        # Both points well within limit
        assert len(result) == 2

    def test_circular_distance_calculation(self):
        """Test that distance calculation is circular (not rectangular)."""
        wafer = create_test_wafer_spec(wafer_size_mm=300.0, die_pitch=10.0)
        points = [
            DiePoint(die_x=10, die_y=10),  # Distance = sqrt(100^2 + 100^2) = 141.4mm
            DiePoint(die_x=14, die_y=0),   # Distance = 140mm
        ]

        result = apply_edge_exclusion(points, wafer, edge_exclusion_mm=15.0)
        # Max distance = 150 - 15 = 135mm
        # Both points should be removed (> 135mm)
        assert len(result) == 0


class TestGetRotationOffset:
    """Test get_rotation_offset() function."""

    def test_none_returns_zero(self):
        """Test that None rotation_seed returns 0.0."""
        assert get_rotation_offset(None) == 0.0

    def test_zero_returns_zero(self):
        """Test that 0 rotation_seed returns 0.0."""
        assert get_rotation_offset(0) == 0.0

    def test_positive_values(self):
        """Test that positive rotation seeds are returned as floats."""
        assert get_rotation_offset(90) == 90.0
        assert get_rotation_offset(180) == 180.0
        assert get_rotation_offset(359) == 359.0

    def test_returns_float_type(self):
        """Test that return type is always float."""
        result = get_rotation_offset(45)
        assert isinstance(result, float)

        result = get_rotation_offset(None)
        assert isinstance(result, float)


class TestApplyRotationToAngle:
    """Test apply_rotation_to_angle() function."""

    def test_zero_rotation_unchanged(self):
        """Test that zero rotation leaves angle unchanged."""
        assert apply_rotation_to_angle(0, 0) == 0.0
        assert apply_rotation_to_angle(45, 0) == 45.0
        assert apply_rotation_to_angle(270, 0) == 270.0

    def test_90_degree_rotation(self):
        """Test 90 degree rotation."""
        assert apply_rotation_to_angle(0, 90) == 90.0
        assert apply_rotation_to_angle(45, 90) == 135.0
        assert apply_rotation_to_angle(270, 90) == 0.0  # (270 + 90) % 360

    def test_180_degree_rotation(self):
        """Test 180 degree rotation."""
        assert apply_rotation_to_angle(0, 180) == 180.0
        assert apply_rotation_to_angle(90, 180) == 270.0
        assert apply_rotation_to_angle(270, 180) == 90.0

    def test_wraparound_normalization(self):
        """Test that angles wrap around to [0, 360)."""
        assert apply_rotation_to_angle(270, 180) == 90.0  # (270 + 180) % 360
        assert apply_rotation_to_angle(359, 10) == 9.0     # (359 + 10) % 360
        assert apply_rotation_to_angle(180, 180) == 0.0    # (180 + 180) % 360

    def test_full_rotation_returns_original(self):
        """Test that 360 degree rotation returns original angle."""
        assert apply_rotation_to_angle(45, 360) == 45.0
        assert apply_rotation_to_angle(270, 360) == 270.0

    def test_multiple_full_rotations(self):
        """Test that multiple full rotations normalize correctly."""
        assert apply_rotation_to_angle(45, 720) == 45.0  # 2 full rotations
        assert apply_rotation_to_angle(0, 1080) == 0.0   # 3 full rotations


class TestGetDeterministicRngSeed:
    """Test get_deterministic_rng_seed() function."""

    def test_none_returns_default(self):
        """Test that None returns default seed (42)."""
        assert get_deterministic_rng_seed(None) == 42

    def test_zero_returns_zero(self):
        """Test that 0 is returned as-is (valid seed)."""
        assert get_deterministic_rng_seed(0) == 0

    def test_positive_values(self):
        """Test that positive values are returned as-is."""
        assert get_deterministic_rng_seed(123) == 123
        assert get_deterministic_rng_seed(999999) == 999999

    def test_returns_int_type(self):
        """Test that return type is always int."""
        result = get_deterministic_rng_seed(None)
        assert isinstance(result, int)

        result = get_deterministic_rng_seed(42)
        assert isinstance(result, int)


class TestDeterminism:
    """Test that common utilities are deterministic."""

    def test_edge_exclusion_determinism(self):
        """Test that edge exclusion produces same results for same input."""
        wafer = create_test_wafer_spec()
        points = [
            DiePoint(die_x=0, die_y=0),
            DiePoint(die_x=5, die_y=0),
            DiePoint(die_x=10, die_y=0),
            DiePoint(die_x=14, die_y=0),
        ]

        result1 = apply_edge_exclusion(points, wafer, edge_exclusion_mm=20.0)
        result2 = apply_edge_exclusion(points, wafer, edge_exclusion_mm=20.0)
        result3 = apply_edge_exclusion(points, wafer, edge_exclusion_mm=20.0)

        assert result1 == result2 == result3

    def test_rotation_helpers_determinism(self):
        """Test that rotation helpers are deterministic."""
        # get_rotation_offset
        offset1 = get_rotation_offset(90)
        offset2 = get_rotation_offset(90)
        assert offset1 == offset2

        # apply_rotation_to_angle
        angle1 = apply_rotation_to_angle(45, 90)
        angle2 = apply_rotation_to_angle(45, 90)
        assert angle1 == angle2

    def test_rng_seed_determinism(self):
        """Test that RNG seed helper is deterministic."""
        seed1 = get_deterministic_rng_seed(None)
        seed2 = get_deterministic_rng_seed(None)
        seed3 = get_deterministic_rng_seed(123)
        seed4 = get_deterministic_rng_seed(123)

        assert seed1 == seed2 == 42
        assert seed3 == seed4 == 123
