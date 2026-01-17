"""
Common utilities shared across L3 sampling strategies.

All helpers here must be deterministic.
"""

from datetime import datetime
from typing import List
from ...models.base import DiePoint


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
    import math

    def distance_key(p: DiePoint) -> tuple:
        x_mm = p.die_x * pitch_x
        y_mm = p.die_y * pitch_y
        dist = math.sqrt(x_mm ** 2 + y_mm ** 2)
        return (dist, p.die_x, p.die_y)

    return sorted(points, key=distance_key)
