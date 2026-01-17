"""
L3 Sampling Engine - Point Selection Layer

BACKWARD COMPATIBILITY FACADE
Real implementation moved to engines/l3/ (PR-B)

This layer is responsible for deterministic sampling point selection.
L3 selects points only - it MUST NOT mutate, reorder, or filter outputs.
"""

# Keep local copies for backward compatibility with test import paths
# that use 'backend.src.engine.l3' instead of 'src.engines.l3'
from .center_edge import CenterEdgeStrategy
from .base import SamplingStrategy

__all__ = ["CenterEdgeStrategy", "SamplingStrategy"]