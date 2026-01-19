"""
Route-level validation tests (Phase 6).

Tests type-safe advanced config validation and business rule validation at API boundary.
Ensures that invalid configurations are rejected early, before strategy execution.
"""

import pytest
from src.server.utils import validate_strategy_config_at_boundary
from src.models.strategy_config import StrategyConfig, CommonStrategyConfig
from src.models.errors import ValidationError, ErrorCode


# =============================================================================
# Advanced Config Validation Tests (Type Safety)
# =============================================================================

def test_valid_center_edge_advanced_config_passes():
    """Valid CENTER_EDGE advanced config passes validation."""
    config = StrategyConfig(
        advanced={
            "center_weight": 0.3,
            "ring_count": 4,
            "radial_spacing": "EXPONENTIAL"
        }
    )

    # Should not raise
    validate_strategy_config_at_boundary("CENTER_EDGE", config, 300.0)


def test_valid_grid_uniform_advanced_config_passes():
    """Valid GRID_UNIFORM advanced config passes validation."""
    config = StrategyConfig(
        advanced={
            "grid_pitch_mm": 10.0,
            "jitter_ratio": 0.1,
            "grid_alignment": "CORNER"
        }
    )

    # Should not raise
    validate_strategy_config_at_boundary("GRID_UNIFORM", config, 300.0)


def test_wrong_strategy_advanced_config_rejected():
    """Advanced config for wrong strategy rejected."""
    config = StrategyConfig(
        advanced={
            "num_rings": 5,  # This is for ZONE_RING_N
            "allocation_mode": "UNIFORM"
        }
    )

    # CENTER_EDGE doesn't have these fields - should fail
    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config_at_boundary("CENTER_EDGE", config, 300.0)

    assert exc_info.value.code == ErrorCode.INVALID_STRATEGY_CONFIG
    assert "CENTER_EDGE" in str(exc_info.value)


def test_invalid_type_advanced_config_rejected():
    """Advanced config with invalid field type rejected."""
    config = StrategyConfig(
        advanced={
            "center_weight": "high"  # Should be float 0-1
        }
    )

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config_at_boundary("CENTER_EDGE", config, 300.0)

    assert exc_info.value.code == ErrorCode.INVALID_STRATEGY_CONFIG


def test_out_of_range_advanced_config_rejected():
    """Advanced config with out-of-range value rejected."""
    config = StrategyConfig(
        advanced={
            "center_weight": 1.5,  # Must be 0-1
            "ring_count": 3
        }
    )

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config_at_boundary("CENTER_EDGE", config, 300.0)

    assert exc_info.value.code == ErrorCode.INVALID_STRATEGY_CONFIG


def test_unknown_field_advanced_config_rejected():
    """Advanced config with unknown field rejected."""
    config = StrategyConfig(
        advanced={
            "center_weight": 0.5,
            "unknown_field": 123  # Not a valid field
        }
    )

    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config_at_boundary("CENTER_EDGE", config, 300.0)

    assert exc_info.value.code == ErrorCode.INVALID_STRATEGY_CONFIG


def test_no_advanced_config_passes():
    """No advanced config (None) passes validation."""
    config = StrategyConfig(
        common=CommonStrategyConfig(edge_exclusion_mm=10.0)
    )

    # Should not raise
    validate_strategy_config_at_boundary("CENTER_EDGE", config, 300.0)


# =============================================================================
# Business Rule Validation Tests (Edge Exclusion)
# =============================================================================

def test_edge_exclusion_exceeds_radius_rejected():
    """edge_exclusion_mm > wafer_radius rejected."""
    config = StrategyConfig(
        common=CommonStrategyConfig(edge_exclusion_mm=160.0)
    )

    # Wafer radius = 300mm / 2 = 150mm
    # edge_exclusion (160mm) > radius (150mm) → should fail
    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config_at_boundary("CENTER_EDGE", config, 300.0)

    assert exc_info.value.code == ErrorCode.INVALID_STRATEGY_CONFIG
    assert "160.0mm" in str(exc_info.value)
    assert "150.0mm" in str(exc_info.value)


def test_edge_exclusion_equals_radius_rejected():
    """edge_exclusion_mm == wafer_radius rejected."""
    config = StrategyConfig(
        common=CommonStrategyConfig(edge_exclusion_mm=150.0)
    )

    # Wafer radius = 300mm / 2 = 150mm
    # edge_exclusion (150mm) == radius (150mm) → should fail (excludes entire wafer)
    with pytest.raises(ValidationError) as exc_info:
        validate_strategy_config_at_boundary("CENTER_EDGE", config, 300.0)

    assert exc_info.value.code == ErrorCode.INVALID_STRATEGY_CONFIG
    assert "150.0mm" in str(exc_info.value)


def test_edge_exclusion_valid_passes():
    """edge_exclusion_mm < wafer_radius passes."""
    config = StrategyConfig(
        common=CommonStrategyConfig(edge_exclusion_mm=50.0)
    )

    # Wafer radius = 300mm / 2 = 150mm
    # edge_exclusion (50mm) < radius (150mm) → valid
    validate_strategy_config_at_boundary("CENTER_EDGE", config, 300.0)


def test_zero_edge_exclusion_passes():
    """edge_exclusion_mm = 0 passes (no exclusion)."""
    config = StrategyConfig(
        common=CommonStrategyConfig(edge_exclusion_mm=0.0)
    )

    # No edge exclusion - should pass
    validate_strategy_config_at_boundary("CENTER_EDGE", config, 300.0)


def test_no_common_config_passes():
    """No common config (None) passes validation."""
    config = StrategyConfig(
        advanced={"center_weight": 0.5}
    )

    # Should not raise
    validate_strategy_config_at_boundary("CENTER_EDGE", config, 300.0)


def test_none_strategy_config_passes():
    """None strategy_config passes validation."""
    # Should not raise - no config to validate
    validate_strategy_config_at_boundary("CENTER_EDGE", None, 300.0)
