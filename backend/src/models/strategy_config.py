"""
Strategy configuration models for v1.3.

Defines strongly-typed configuration schemas for all sampling strategies.
Replaces v1.2 untyped `params: Dict[str, Any]` with structured `strategy_config`.
"""

from typing import Union, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from .errors import ValidationError, ErrorCode


# =============================================================================
# Common Configuration (All Strategies)
# =============================================================================

class CommonStrategyConfig(BaseModel):
    """
    Common configuration applicable to all sampling strategies.

    All fields are optional. Backend fills defaults using explicit resolution policy.

    Fields:
        target_point_count: Desired number of points (null = use strategy default)
        edge_exclusion_mm: Exclude points within N mm of wafer edge (0.0 = no exclusion)
        rotation_seed: Deterministic rotation offset in degrees (null = no rotation)
        deterministic_seed: RNG seed for stochastic operations (null = deterministic default)
    """

    target_point_count: Optional[int] = Field(
        default=None,
        ge=1,
        description="Desired number of sampling points (subject to constraints). "
                    "If null, uses strategy-specific default."
    )

    edge_exclusion_mm: float = Field(
        default=0.0,
        ge=0.0,
        description="Exclude points within N mm of wafer edge. Default: 0.0 (no exclusion)"
    )

    rotation_seed: Optional[int] = Field(
        default=None,
        ge=0,
        lt=360,
        description="Deterministic rotation offset in degrees (geometry transform). "
                    "Default: null (no rotation)"
    )

    deterministic_seed: Optional[int] = Field(
        default=None,
        ge=0,
        description="Deterministic RNG seed for stochastic operations (jitter, sampling). "
                    "Default: null (uses strategy-dependent deterministic behavior)"
    )

    class Config:
        extra = "forbid"  # Unknown fields rejected


# =============================================================================
# Advanced Configuration (Per-Strategy)
# =============================================================================

class CenterEdgeAdvancedConfig(BaseModel):
    """
    Advanced configuration for CENTER_EDGE strategy.

    Configures center-edge radial sampling pattern.
    """

    center_weight: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="Fraction of points allocated to center region"
    )

    ring_count: int = Field(
        default=3,
        ge=2,
        le=5,
        description="Number of concentric rings"
    )

    radial_spacing: Literal["UNIFORM", "EXPONENTIAL"] = Field(
        default="UNIFORM",
        description="Ring spacing distribution mode"
    )

    class Config:
        extra = "forbid"


class GridUniformAdvancedConfig(BaseModel):
    """
    Advanced configuration for GRID_UNIFORM strategy.

    Configures uniform grid sampling pattern.
    """

    grid_pitch_mm: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Grid spacing in mm. Default: null (auto-derive from die pitch)"
    )

    jitter_ratio: float = Field(
        default=0.0,
        ge=0.0,
        le=0.3,
        description="Deterministic sub-die randomization factor (requires deterministic_seed if > 0)"
    )

    grid_alignment: Literal["CENTER", "CORNER"] = Field(
        default="CENTER",
        description="Grid alignment mode"
    )

    class Config:
        extra = "forbid"


class EdgeOnlyAdvancedConfig(BaseModel):
    """
    Advanced configuration for EDGE_ONLY strategy.

    Configures edge-focused sampling pattern.
    """

    edge_band_width_mm: float = Field(
        default=10.0,
        ge=5.0,
        le=50.0,
        description="Width of edge sampling zone in mm"
    )

    angular_spacing_deg: float = Field(
        default=45.0,
        ge=15.0,
        le=90.0,
        description="Target angular spacing between points in degrees"
    )

    prioritize_corners: bool = Field(
        default=True,
        description="Prioritize corner regions for edge sampling"
    )

    class Config:
        extra = "forbid"


class ZoneRingNAdvancedConfig(BaseModel):
    """
    Advanced configuration for ZONE_RING_N strategy.

    Configures N-ring zone-based sampling pattern.
    """

    num_rings: int = Field(
        default=3,
        ge=2,
        le=10,
        description="Number of concentric rings (N)"
    )

    allocation_mode: Literal["AREA_PROPORTIONAL", "UNIFORM", "EDGE_HEAVY"] = Field(
        default="AREA_PROPORTIONAL",
        description="Point allocation mode across rings"
    )

    class Config:
        extra = "forbid"


# =============================================================================
# Type Aliases & Registry
# =============================================================================

AdvancedConfigUnion = Union[
    CenterEdgeAdvancedConfig,
    GridUniformAdvancedConfig,
    EdgeOnlyAdvancedConfig,
    ZoneRingNAdvancedConfig
]

# Mapping for runtime validation
ADVANCED_CONFIG_MODELS = {
    "CENTER_EDGE": CenterEdgeAdvancedConfig,
    "GRID_UNIFORM": GridUniformAdvancedConfig,
    "EDGE_ONLY": EdgeOnlyAdvancedConfig,
    "ZONE_RING_N": ZoneRingNAdvancedConfig,
}

# Strategy-specific default target point counts
STRATEGY_DEFAULT_TARGET_COUNTS = {
    "CENTER_EDGE": 20,
    "GRID_UNIFORM": 30,
    "EDGE_ONLY": 15,
    "ZONE_RING_N": 25,
}


# =============================================================================
# Top-Level Configuration
# =============================================================================

class StrategyConfig(BaseModel):
    """
    Complete strategy configuration with common and advanced sections.

    Both sections are optional. Backend fills defaults for missing fields.
    Advanced config is validated based on strategy_id at selection time.
    """

    common: Optional[CommonStrategyConfig] = None
    advanced: Optional[Dict[str, Any]] = None  # Validated per-strategy via validate_and_parse_advanced_config

    class Config:
        extra = "forbid"  # Unknown fields at this level rejected


# =============================================================================
# Validation Utilities
# =============================================================================

def validate_and_parse_advanced_config(
    strategy_id: str,
    advanced_dict: Optional[Dict[str, Any]]
) -> AdvancedConfigUnion:
    """
    Validate and parse advanced config based on strategy_id.

    Provides strong typing and validation for strategy-specific configuration.
    Unknown fields, invalid ranges, and type mismatches are rejected.

    Args:
        strategy_id: Strategy identifier (e.g., "CENTER_EDGE")
        advanced_dict: Raw advanced config dict (may be None or partial)

    Returns:
        Typed advanced config model with defaults filled

    Raises:
        ValidationError: If strategy unknown or advanced config invalid

    Examples:
        >>> validate_and_parse_advanced_config("CENTER_EDGE", None)
        CenterEdgeAdvancedConfig(center_weight=0.2, ring_count=3, radial_spacing="UNIFORM")

        >>> validate_and_parse_advanced_config("CENTER_EDGE", {"ring_count": 4})
        CenterEdgeAdvancedConfig(center_weight=0.2, ring_count=4, radial_spacing="UNIFORM")

        >>> validate_and_parse_advanced_config("CENTER_EDGE", {"invalid_field": 1})
        ValidationError: Unknown field 'invalid_field' in CENTER_EDGE advanced config
    """
    if strategy_id not in ADVANCED_CONFIG_MODELS:
        raise ValidationError(
            ErrorCode.INVALID_STRATEGY_CONFIG,
            f"Unknown strategy_id: '{strategy_id}'. "
            f"Valid strategies: {list(ADVANCED_CONFIG_MODELS.keys())}"
        )

    model_class = ADVANCED_CONFIG_MODELS[strategy_id]

    try:
        if advanced_dict is None:
            # All defaults
            return model_class()
        else:
            # Partial or full config - Pydantic fills missing defaults
            return model_class(**advanced_dict)
    except Exception as e:
        # Re-raise with clear strategy context
        raise ValidationError(
            ErrorCode.INVALID_STRATEGY_CONFIG,
            f"Invalid advanced config for {strategy_id}: {str(e)}"
        )


def resolve_target_point_count(
    requested: Optional[int],
    strategy_id: str,
    min_sampling_points: int,
    max_sampling_points: int,
    tool_max: int
) -> int:
    """
    Resolve target_point_count using deterministic default policy.

    Explicit Default Resolution Policy:
    1. Use requested value if provided
    2. Otherwise use strategy-specific default
    3. Clamp to [min_sampling_points, min(max_sampling_points, tool_max)]

    This is NOT "magic inference" - all defaults are explicit and documented.

    Args:
        requested: User-provided target (None if not specified)
        strategy_id: Strategy identifier for default lookup
        min_sampling_points: From process_context
        max_sampling_points: From process_context
        tool_max: tool_profile.max_points_per_wafer

    Returns:
        Resolved target point count

    Examples:
        >>> resolve_target_point_count(None, "CENTER_EDGE", 5, 25, 49)
        20  # Strategy default fits within constraints

        >>> resolve_target_point_count(50, "CENTER_EDGE", 5, 25, 49)
        25  # Clamped to max_sampling_points

        >>> resolve_target_point_count(3, "CENTER_EDGE", 5, 25, 49)
        5   # Clamped to min_sampling_points
    """
    # Step 1: Determine base target
    if requested is not None:
        base_target = requested
    else:
        # Use strategy-specific default
        base_target = STRATEGY_DEFAULT_TARGET_COUNTS.get(strategy_id, 20)

    # Step 2: Determine upper bound
    upper_bound = min(max_sampling_points, tool_max)

    # Step 3: Clamp to constraints
    resolved = max(min_sampling_points, min(base_target, upper_bound))

    return resolved
