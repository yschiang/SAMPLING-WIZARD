"""
Common utilities shared across L3 sampling strategies.

All helpers here must be deterministic.

v1.3 additions:
- apply_edge_exclusion(): Filter points near wafer edge
- get_rotation_offset(): Get rotation angle from rotation_seed
- apply_rotation_to_angle(): Apply rotation to angular positions
- get_deterministic_rng_seed(): Get RNG seed for stochastic operations
"""

import math
from datetime import datetime
from typing import List, Optional
from ...models.base import DiePoint, WaferMapSpec


def get_deterministic_timestamp() -> str:
    """
    Get a deterministic timestamp for trace metadata.

    Note: This delegates to server.utils for consistency across the codebase.
    """
    from ...server.utils import get_deterministic_timestamp as _get_timestamp
    return _get_timestamp()


def sort_points_by_distance(points: List[DiePoint], pitch_x: float, pitch_y: float) -> List[DiePoint]:
    """
    Sort points by distance from center (deterministic).

    Args:
        points: List of die points to sort
        pitch_x: Die pitch in X direction (mm)
        pitch_y: Die pitch in Y direction (mm)

    Returns:
        Points sorted by distance from center, with tie-breaking by (die_x, die_y)
    """
    def distance_key(p: DiePoint) -> tuple:
        x_mm = p.die_x * pitch_x
        y_mm = p.die_y * pitch_y
        dist = math.sqrt(x_mm ** 2 + y_mm ** 2)
        return (dist, p.die_x, p.die_y)

    return sorted(points, key=distance_key)


# =============================================================================
# v1.3 Common Configuration Utilities
# =============================================================================

def apply_edge_exclusion(
    points: List[DiePoint],
    wafer_spec: WaferMapSpec,
    edge_exclusion_mm: float
) -> List[DiePoint]:
    """
    Filter out points within edge_exclusion_mm of wafer edge.

    Removes dies whose centers are closer than edge_exclusion_mm to the
    wafer edge. Uses circular distance from wafer center.

    Args:
        points: Candidate die points (die grid coordinates)
        wafer_spec: Wafer dimensions and die pitch
        edge_exclusion_mm: Exclusion zone width (mm from edge)
                          If <= 0, no filtering applied

    Returns:
        Filtered points (deterministic ordering preserved)

    Examples:
        >>> wafer = WaferMapSpec(wafer_size_mm=300, die_pitch_x_mm=10, die_pitch_y_mm=10, ...)
        >>> points = [DiePoint(die_x=0, die_y=0), DiePoint(die_x=14, die_y=0)]
        >>> apply_edge_exclusion(points, wafer, edge_exclusion_mm=10.0)
        [DiePoint(die_x=0, die_y=0)]  # (14,0) is 140mm from center, within 10mm of 150mm edge
    """
    if edge_exclusion_mm <= 0:
        return points

    wafer_radius_mm = wafer_spec.wafer_size_mm / 2.0
    max_distance_mm = wafer_radius_mm - edge_exclusion_mm

    filtered = []
    for point in points:
        # Convert die coordinates to physical position (mm from center)
        x_mm = point.die_x * wafer_spec.die_pitch_x_mm
        y_mm = point.die_y * wafer_spec.die_pitch_y_mm

        # Calculate distance from wafer center
        distance_mm = math.sqrt(x_mm**2 + y_mm**2)

        # Keep point if within allowed radius
        if distance_mm <= max_distance_mm:
            filtered.append(point)

    return filtered


def get_rotation_offset(rotation_seed: Optional[int]) -> float:
    """
    Get rotation offset in degrees from rotation_seed.

    Converts rotation_seed to angular offset for pattern rotation.
    Rotation is applied to angular components of sampling patterns.

    Args:
        rotation_seed: Rotation angle in degrees (0-359)
                      None means no rotation (0 degrees)

    Returns:
        Rotation offset in degrees (0.0-359.0)

    Examples:
        >>> get_rotation_offset(None)
        0.0
        >>> get_rotation_offset(90)
        90.0
        >>> get_rotation_offset(0)
        0.0
    """
    return float(rotation_seed) if rotation_seed is not None else 0.0


def apply_rotation_to_angle(base_angle_deg: float, rotation_offset_deg: float) -> float:
    """
    Apply rotation offset to an angular position.

    Adds rotation offset to base angle and normalizes to [0, 360).

    Args:
        base_angle_deg: Base angular position (degrees)
        rotation_offset_deg: Rotation offset to apply (degrees)

    Returns:
        Rotated angle normalized to [0, 360) range

    Examples:
        >>> apply_rotation_to_angle(0, 90)
        90.0
        >>> apply_rotation_to_angle(270, 180)
        90.0  # (270 + 180) % 360
        >>> apply_rotation_to_angle(45, 0)
        45.0
    """
    rotated = base_angle_deg + rotation_offset_deg
    return rotated % 360.0


def get_deterministic_rng_seed(deterministic_seed: Optional[int]) -> int:
    """
    Get RNG seed for stochastic operations.

    Provides deterministic seed for operations like jitter, random sampling.
    If no seed provided, uses fixed default for reproducibility.

    Args:
        deterministic_seed: User-provided RNG seed (>= 0)
                           None means use default seed

    Returns:
        Integer seed for random.Random() or numpy.random.seed()

    Examples:
        >>> get_deterministic_rng_seed(None)
        42
        >>> get_deterministic_rng_seed(123)
        123
        >>> get_deterministic_rng_seed(0)
        0
    """
    DEFAULT_SEED = 42
    return deterministic_seed if deterministic_seed is not None else DEFAULT_SEED
