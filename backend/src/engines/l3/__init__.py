"""
L3 Sampling Engine - Point Selection Layer

This layer is responsible for deterministic sampling point selection.
L3 selects points only - it MUST NOT mutate, reorder, or filter outputs.

Usage:
    from engines.l3 import get_strategy, SamplingStrategy

    strategy = get_strategy("CENTER_EDGE")
    output = strategy.select_points(request)
"""

from .registry import get_strategy, list_strategies
from .base import SamplingStrategy

__all__ = ["get_strategy", "list_strategies", "SamplingStrategy"]
