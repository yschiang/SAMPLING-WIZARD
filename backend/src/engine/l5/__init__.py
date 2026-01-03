"""
L5 Recipe Translation Engine - Converts L3 outputs to tool-executable recipes.

This module provides coordinate conversion and tool payload generation functionality
to translate sampling points into format-specific recipes that tools can execute.

Key Principles:
- READ-ONLY: Never modifies L3 outputs (coordinate conversion only)
- Deterministic: Same inputs produce same recipe outputs
- Tool-Aware: Enforces tool constraints and capabilities
- Traceable: Provides detailed translation notes for transparency
"""

from .translator import RecipeTranslator

__all__ = ['RecipeTranslator']