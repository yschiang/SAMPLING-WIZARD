"""
L3 Sampling Engine - Point Selection Layer

This layer is responsible for deterministic sampling point selection.
L3 selects points only - it MUST NOT mutate, reorder, or filter outputs.
"""

from .center_edge import CenterEdgeStrategy
from .base import SamplingStrategy

__all__ = ["CenterEdgeStrategy", "SamplingStrategy"]