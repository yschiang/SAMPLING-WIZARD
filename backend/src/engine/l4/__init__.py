"""
L4 Sampling Score Engine - Read-only evaluation of L3 outputs.

This module provides scoring functionality to evaluate the quality and adequacy 
of sampling points selected by L3 strategies.

Key Principles:
- READ-ONLY: Never modifies L3 outputs (no mutation of selected_points)
- Deterministic: Same inputs produce same scores
- Bounded: All scores are between 0.0 and 1.0
- Comprehensive: Coverage, statistical, risk alignment, and overall scores
"""

from .scorer import SamplingScorer

__all__ = ['SamplingScorer']