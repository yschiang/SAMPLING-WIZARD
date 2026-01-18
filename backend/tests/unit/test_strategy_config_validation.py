"""
Unit tests for strategy configuration validation (v1.3).

Tests the strongly-typed configuration system introduced in v1.3:
- CommonStrategyConfig validation
- Per-strategy advanced config validation
- Partial config support (missing fields filled with defaults)
- Unknown field rejection (extra="forbid")
- Range validation (Field constraints)
- Enum validation (Literal types)
- Strong typing enforcement via validate_and_parse_advanced_config()
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

import pytest
from pydantic import ValidationError as PydanticValidationError
from backend.src.models.strategy_config import (
    CommonStrategyConfig,
    CenterEdgeAdvancedConfig,
    GridUniformAdvancedConfig,
    EdgeOnlyAdvancedConfig,
    ZoneRingNAdvancedConfig,
    StrategyConfig,
    validate_and_parse_advanced_config,
    resolve_target_point_count,
    STRATEGY_DEFAULT_TARGET_COUNTS,
)
from backend.src.models.errors import ValidationError, ErrorCode


class TestCommonStrategyConfig:
    """Test CommonStrategyConfig validation."""

    def test_all_defaults(self):
        """Test that all fields are optional and have correct defaults."""
        config = CommonStrategyConfig()

        assert config.target_point_count is None
        assert config.edge_exclusion_mm == 0.0
        assert config.rotation_seed is None
        assert config.deterministic_seed is None

    def test_partial_config_valid(self):
        """Test partial config accepted and defaults filled."""
        config = CommonStrategyConfig(target_point_count=25)

        assert config.target_point_count == 25
        assert config.edge_exclusion_mm == 0.0  # Default
        assert config.rotation_seed is None
        assert config.deterministic_seed is None

    def test_target_point_count_validation(self):
        """Test target_point_count must be >= 1."""
        # Valid
        config = CommonStrategyConfig(target_point_count=1)
        assert config.target_point_count == 1

        config = CommonStrategyConfig(target_point_count=100)
        assert config.target_point_count == 100

        # Invalid: zero
        with pytest.raises(PydanticValidationError) as exc_info:
            CommonStrategyConfig(target_point_count=0)
        assert "greater than or equal to 1" in str(exc_info.value).lower()

        # Invalid: negative
        with pytest.raises(PydanticValidationError) as exc_info:
            CommonStrategyConfig(target_point_count=-5)
        assert "greater than or equal to 1" in str(exc_info.value).lower()

    def test_edge_exclusion_mm_validation(self):
        """Test edge_exclusion_mm must be >= 0.0."""
        # Valid
        config = CommonStrategyConfig(edge_exclusion_mm=0.0)
        assert config.edge_exclusion_mm == 0.0

        config = CommonStrategyConfig(edge_exclusion_mm=5.5)
        assert config.edge_exclusion_mm == 5.5

        # Invalid: negative
        with pytest.raises(PydanticValidationError) as exc_info:
            CommonStrategyConfig(edge_exclusion_mm=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_rotation_seed_validation(self):
        """Test rotation_seed must be in [0, 359]."""
        # Valid
        config = CommonStrategyConfig(rotation_seed=0)
        assert config.rotation_seed == 0

        config = CommonStrategyConfig(rotation_seed=180)
        assert config.rotation_seed == 180

        config = CommonStrategyConfig(rotation_seed=359)
        assert config.rotation_seed == 359

        # Invalid: negative
        with pytest.raises(PydanticValidationError) as exc_info:
            CommonStrategyConfig(rotation_seed=-1)
        assert "greater than or equal to 0" in str(exc_info.value).lower()

        # Invalid: >= 360
        with pytest.raises(PydanticValidationError) as exc_info:
            CommonStrategyConfig(rotation_seed=360)
        assert "less than 360" in str(exc_info.value).lower()

    def test_deterministic_seed_validation(self):
        """Test deterministic_seed must be >= 0."""
        # Valid
        config = CommonStrategyConfig(deterministic_seed=0)
        assert config.deterministic_seed == 0

        config = CommonStrategyConfig(deterministic_seed=42)
        assert config.deterministic_seed == 42

        config = CommonStrategyConfig(deterministic_seed=999999)
        assert config.deterministic_seed == 999999

        # Invalid: negative
        with pytest.raises(PydanticValidationError) as exc_info:
            CommonStrategyConfig(deterministic_seed=-1)
        assert "greater than or equal to 0" in str(exc_info.value).lower()

    def test_unknown_field_rejected(self):
        """Test unknown fields rejected (extra='forbid')."""
        with pytest.raises(PydanticValidationError) as exc_info:
            CommonStrategyConfig(unknown_field=123)
        assert "extra fields not permitted" in str(exc_info.value).lower()


class TestCenterEdgeAdvancedConfig:
    """Test CenterEdgeAdvancedConfig validation."""

    def test_all_defaults(self):
        """Test default values for CENTER_EDGE advanced config."""
        config = CenterEdgeAdvancedConfig()

        assert config.center_weight == 0.2
        assert config.ring_count == 3
        assert config.radial_spacing == "UNIFORM"

    def test_partial_config(self):
        """Test partial config with defaults."""
        config = CenterEdgeAdvancedConfig(ring_count=4)

        assert config.center_weight == 0.2  # Default
        assert config.ring_count == 4
        assert config.radial_spacing == "UNIFORM"  # Default

    def test_center_weight_validation(self):
        """Test center_weight must be in [0.0, 1.0]."""
        # Valid
        config = CenterEdgeAdvancedConfig(center_weight=0.0)
        assert config.center_weight == 0.0

        config = CenterEdgeAdvancedConfig(center_weight=0.5)
        assert config.center_weight == 0.5

        config = CenterEdgeAdvancedConfig(center_weight=1.0)
        assert config.center_weight == 1.0

        # Invalid: < 0
        with pytest.raises(PydanticValidationError) as exc_info:
            CenterEdgeAdvancedConfig(center_weight=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value).lower()

        # Invalid: > 1
        with pytest.raises(PydanticValidationError) as exc_info:
            CenterEdgeAdvancedConfig(center_weight=1.1)
        assert "less than or equal to 1" in str(exc_info.value).lower()

    def test_ring_count_validation(self):
        """Test ring_count must be in [2, 5]."""
        # Valid
        for valid_count in [2, 3, 4, 5]:
            config = CenterEdgeAdvancedConfig(ring_count=valid_count)
            assert config.ring_count == valid_count

        # Invalid: < 2
        with pytest.raises(PydanticValidationError) as exc_info:
            CenterEdgeAdvancedConfig(ring_count=1)
        assert "greater than or equal to 2" in str(exc_info.value).lower()

        # Invalid: > 5
        with pytest.raises(PydanticValidationError) as exc_info:
            CenterEdgeAdvancedConfig(ring_count=6)
        assert "less than or equal to 5" in str(exc_info.value).lower()

    def test_radial_spacing_validation(self):
        """Test radial_spacing must be UNIFORM or EXPONENTIAL."""
        # Valid
        config = CenterEdgeAdvancedConfig(radial_spacing="UNIFORM")
        assert config.radial_spacing == "UNIFORM"

        config = CenterEdgeAdvancedConfig(radial_spacing="EXPONENTIAL")
        assert config.radial_spacing == "EXPONENTIAL"

        # Invalid: unknown option
        with pytest.raises(PydanticValidationError) as exc_info:
            CenterEdgeAdvancedConfig(radial_spacing="INVALID")
        error_msg = str(exc_info.value).lower()
        assert ("uniform" in error_msg and "exponential" in error_msg) or "literal" in error_msg

    def test_unknown_field_rejected(self):
        """Test unknown fields rejected."""
        with pytest.raises(PydanticValidationError) as exc_info:
            CenterEdgeAdvancedConfig(unknown_param=42)
        assert "extra fields not permitted" in str(exc_info.value).lower()


class TestGridUniformAdvancedConfig:
    """Test GridUniformAdvancedConfig validation."""

    def test_all_defaults(self):
        """Test default values for GRID_UNIFORM advanced config."""
        config = GridUniformAdvancedConfig()

        assert config.grid_pitch_mm is None
        assert config.jitter_ratio == 0.0
        assert config.grid_alignment == "CENTER"

    def test_grid_pitch_mm_validation(self):
        """Test grid_pitch_mm must be > 0 if specified."""
        # Valid: None (default)
        config = GridUniformAdvancedConfig(grid_pitch_mm=None)
        assert config.grid_pitch_mm is None

        # Valid: positive
        config = GridUniformAdvancedConfig(grid_pitch_mm=5.0)
        assert config.grid_pitch_mm == 5.0

        # Invalid: zero
        with pytest.raises(PydanticValidationError) as exc_info:
            GridUniformAdvancedConfig(grid_pitch_mm=0.0)
        assert "greater than 0" in str(exc_info.value).lower()

        # Invalid: negative
        with pytest.raises(PydanticValidationError) as exc_info:
            GridUniformAdvancedConfig(grid_pitch_mm=-1.0)
        assert "greater than 0" in str(exc_info.value).lower()

    def test_jitter_ratio_validation(self):
        """Test jitter_ratio must be in [0.0, 0.3]."""
        # Valid
        config = GridUniformAdvancedConfig(jitter_ratio=0.0)
        assert config.jitter_ratio == 0.0

        config = GridUniformAdvancedConfig(jitter_ratio=0.15)
        assert config.jitter_ratio == 0.15

        config = GridUniformAdvancedConfig(jitter_ratio=0.3)
        assert config.jitter_ratio == 0.3

        # Invalid: < 0
        with pytest.raises(PydanticValidationError) as exc_info:
            GridUniformAdvancedConfig(jitter_ratio=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value).lower()

        # Invalid: > 0.3
        with pytest.raises(PydanticValidationError) as exc_info:
            GridUniformAdvancedConfig(jitter_ratio=0.4)
        assert "less than or equal to 0.3" in str(exc_info.value).lower()

    def test_grid_alignment_validation(self):
        """Test grid_alignment must be CENTER or CORNER."""
        # Valid
        config = GridUniformAdvancedConfig(grid_alignment="CENTER")
        assert config.grid_alignment == "CENTER"

        config = GridUniformAdvancedConfig(grid_alignment="CORNER")
        assert config.grid_alignment == "CORNER"

        # Invalid: unknown option
        with pytest.raises(PydanticValidationError) as exc_info:
            GridUniformAdvancedConfig(grid_alignment="EDGE")
        error_msg = str(exc_info.value).lower()
        assert ("center" in error_msg and "corner" in error_msg) or "literal" in error_msg


class TestEdgeOnlyAdvancedConfig:
    """Test EdgeOnlyAdvancedConfig validation."""

    def test_all_defaults(self):
        """Test default values for EDGE_ONLY advanced config."""
        config = EdgeOnlyAdvancedConfig()

        assert config.edge_band_width_mm == 10.0
        assert config.angular_spacing_deg == 45.0
        assert config.prioritize_corners is True

    def test_edge_band_width_mm_validation(self):
        """Test edge_band_width_mm must be in [5.0, 50.0]."""
        # Valid
        config = EdgeOnlyAdvancedConfig(edge_band_width_mm=5.0)
        assert config.edge_band_width_mm == 5.0

        config = EdgeOnlyAdvancedConfig(edge_band_width_mm=25.0)
        assert config.edge_band_width_mm == 25.0

        config = EdgeOnlyAdvancedConfig(edge_band_width_mm=50.0)
        assert config.edge_band_width_mm == 50.0

        # Invalid: < 5.0
        with pytest.raises(PydanticValidationError) as exc_info:
            EdgeOnlyAdvancedConfig(edge_band_width_mm=4.9)
        assert "greater than or equal to 5" in str(exc_info.value).lower()

        # Invalid: > 50.0
        with pytest.raises(PydanticValidationError) as exc_info:
            EdgeOnlyAdvancedConfig(edge_band_width_mm=50.1)
        assert "less than or equal to 50" in str(exc_info.value).lower()

    def test_angular_spacing_deg_validation(self):
        """Test angular_spacing_deg must be in [15.0, 90.0]."""
        # Valid
        config = EdgeOnlyAdvancedConfig(angular_spacing_deg=15.0)
        assert config.angular_spacing_deg == 15.0

        config = EdgeOnlyAdvancedConfig(angular_spacing_deg=45.0)
        assert config.angular_spacing_deg == 45.0

        config = EdgeOnlyAdvancedConfig(angular_spacing_deg=90.0)
        assert config.angular_spacing_deg == 90.0

        # Invalid: < 15.0
        with pytest.raises(PydanticValidationError) as exc_info:
            EdgeOnlyAdvancedConfig(angular_spacing_deg=14.9)
        assert "greater than or equal to 15" in str(exc_info.value).lower()

        # Invalid: > 90.0
        with pytest.raises(PydanticValidationError) as exc_info:
            EdgeOnlyAdvancedConfig(angular_spacing_deg=90.1)
        assert "less than or equal to 90" in str(exc_info.value).lower()

    def test_prioritize_corners_validation(self):
        """Test prioritize_corners is boolean."""
        # Valid
        config = EdgeOnlyAdvancedConfig(prioritize_corners=True)
        assert config.prioritize_corners is True

        config = EdgeOnlyAdvancedConfig(prioritize_corners=False)
        assert config.prioritize_corners is False


class TestZoneRingNAdvancedConfig:
    """Test ZoneRingNAdvancedConfig validation."""

    def test_all_defaults(self):
        """Test default values for ZONE_RING_N advanced config."""
        config = ZoneRingNAdvancedConfig()

        assert config.num_rings == 3
        assert config.allocation_mode == "AREA_PROPORTIONAL"

    def test_num_rings_validation(self):
        """Test num_rings must be in [2, 10]."""
        # Valid
        for valid_rings in [2, 3, 5, 7, 10]:
            config = ZoneRingNAdvancedConfig(num_rings=valid_rings)
            assert config.num_rings == valid_rings

        # Invalid: < 2
        with pytest.raises(PydanticValidationError) as exc_info:
            ZoneRingNAdvancedConfig(num_rings=1)
        assert "greater than or equal to 2" in str(exc_info.value).lower()

        # Invalid: > 10
        with pytest.raises(PydanticValidationError) as exc_info:
            ZoneRingNAdvancedConfig(num_rings=11)
        assert "less than or equal to 10" in str(exc_info.value).lower()

    def test_allocation_mode_validation(self):
        """Test allocation_mode must be AREA_PROPORTIONAL, UNIFORM, or EDGE_HEAVY."""
        # Valid
        for mode in ["AREA_PROPORTIONAL", "UNIFORM", "EDGE_HEAVY"]:
            config = ZoneRingNAdvancedConfig(allocation_mode=mode)
            assert config.allocation_mode == mode

        # Invalid: unknown option
        with pytest.raises(PydanticValidationError) as exc_info:
            ZoneRingNAdvancedConfig(allocation_mode="INVALID")
        error_msg = str(exc_info.value).lower()
        # Check that at least one valid option is mentioned in the error
        assert ("area_proportional" in error_msg or "uniform" in error_msg or "edge_heavy" in error_msg or "literal" in error_msg)


class TestStrategyConfig:
    """Test top-level StrategyConfig model."""

    def test_both_sections_none(self):
        """Test config with both sections as None."""
        config = StrategyConfig()

        assert config.common is None
        assert config.advanced is None

    def test_only_common_section(self):
        """Test config with only common section."""
        config = StrategyConfig(
            common=CommonStrategyConfig(target_point_count=30)
        )

        assert config.common.target_point_count == 30
        assert config.advanced is None

    def test_only_advanced_section(self):
        """Test config with only advanced section (raw dict)."""
        config = StrategyConfig(
            advanced={"center_weight": 0.3}
        )

        assert config.common is None
        assert config.advanced == {"center_weight": 0.3}

    def test_both_sections_present(self):
        """Test config with both sections."""
        config = StrategyConfig(
            common=CommonStrategyConfig(target_point_count=25, edge_exclusion_mm=2.0),
            advanced={"center_weight": 0.3, "ring_count": 4}
        )

        assert config.common.target_point_count == 25
        assert config.common.edge_exclusion_mm == 2.0
        assert config.advanced == {"center_weight": 0.3, "ring_count": 4}

    def test_unknown_top_level_field_rejected(self):
        """Test unknown fields at top level rejected."""
        with pytest.raises(PydanticValidationError) as exc_info:
            StrategyConfig(unknown_section={"foo": "bar"})
        assert "extra fields not permitted" in str(exc_info.value).lower()


class TestValidateAndParseAdvancedConfig:
    """Test validate_and_parse_advanced_config() strong typing enforcement."""

    def test_unknown_strategy_id(self):
        """Test unknown strategy_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_and_parse_advanced_config("UNKNOWN_STRATEGY", None)

        assert exc_info.value.code == ErrorCode.INVALID_STRATEGY_CONFIG
        assert "Unknown strategy_id" in exc_info.value.message
        assert "UNKNOWN_STRATEGY" in exc_info.value.message

    def test_center_edge_all_defaults(self):
        """Test CENTER_EDGE with None returns all defaults."""
        config = validate_and_parse_advanced_config("CENTER_EDGE", None)

        assert isinstance(config, CenterEdgeAdvancedConfig)
        assert config.center_weight == 0.2
        assert config.ring_count == 3
        assert config.radial_spacing == "UNIFORM"

    def test_center_edge_partial_config(self):
        """Test CENTER_EDGE with partial config."""
        config = validate_and_parse_advanced_config("CENTER_EDGE", {"ring_count": 4})

        assert isinstance(config, CenterEdgeAdvancedConfig)
        assert config.center_weight == 0.2  # Default
        assert config.ring_count == 4  # Overridden
        assert config.radial_spacing == "UNIFORM"  # Default

    def test_center_edge_full_config(self):
        """Test CENTER_EDGE with full config."""
        config = validate_and_parse_advanced_config("CENTER_EDGE", {
            "center_weight": 0.3,
            "ring_count": 5,
            "radial_spacing": "EXPONENTIAL"
        })

        assert isinstance(config, CenterEdgeAdvancedConfig)
        assert config.center_weight == 0.3
        assert config.ring_count == 5
        assert config.radial_spacing == "EXPONENTIAL"

    def test_center_edge_invalid_range(self):
        """Test CENTER_EDGE with invalid range raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_and_parse_advanced_config("CENTER_EDGE", {"center_weight": 1.5})

        assert exc_info.value.code == ErrorCode.INVALID_STRATEGY_CONFIG
        assert "Invalid advanced config for CENTER_EDGE" in exc_info.value.message

    def test_center_edge_unknown_field(self):
        """Test CENTER_EDGE with unknown field raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            validate_and_parse_advanced_config("CENTER_EDGE", {"unknown_field": 123})

        assert exc_info.value.code == ErrorCode.INVALID_STRATEGY_CONFIG
        assert "Invalid advanced config for CENTER_EDGE" in exc_info.value.message

    def test_grid_uniform_validation(self):
        """Test GRID_UNIFORM validation."""
        config = validate_and_parse_advanced_config("GRID_UNIFORM", {
            "grid_pitch_mm": 10.0,
            "jitter_ratio": 0.1
        })

        assert isinstance(config, GridUniformAdvancedConfig)
        assert config.grid_pitch_mm == 10.0
        assert config.jitter_ratio == 0.1
        assert config.grid_alignment == "CENTER"  # Default

    def test_edge_only_validation(self):
        """Test EDGE_ONLY validation."""
        config = validate_and_parse_advanced_config("EDGE_ONLY", {
            "edge_band_width_mm": 15.0
        })

        assert isinstance(config, EdgeOnlyAdvancedConfig)
        assert config.edge_band_width_mm == 15.0
        assert config.angular_spacing_deg == 45.0  # Default
        assert config.prioritize_corners is True  # Default

    def test_zone_ring_n_validation(self):
        """Test ZONE_RING_N validation."""
        config = validate_and_parse_advanced_config("ZONE_RING_N", {
            "num_rings": 5,
            "allocation_mode": "EDGE_HEAVY"
        })

        assert isinstance(config, ZoneRingNAdvancedConfig)
        assert config.num_rings == 5
        assert config.allocation_mode == "EDGE_HEAVY"


class TestResolveTargetPointCount:
    """Test resolve_target_point_count() default resolution policy."""

    def test_explicit_value_within_bounds(self):
        """Test explicit requested value within bounds is used as-is."""
        result = resolve_target_point_count(
            requested=15,
            strategy_id="CENTER_EDGE",
            min_sampling_points=5,
            max_sampling_points=25,
            tool_max=49
        )
        assert result == 15

    def test_explicit_value_clamped_to_min(self):
        """Test explicit value below min is clamped to min."""
        result = resolve_target_point_count(
            requested=3,
            strategy_id="CENTER_EDGE",
            min_sampling_points=5,
            max_sampling_points=25,
            tool_max=49
        )
        assert result == 5  # Clamped to min

    def test_explicit_value_clamped_to_max(self):
        """Test explicit value above max is clamped to max."""
        result = resolve_target_point_count(
            requested=30,
            strategy_id="CENTER_EDGE",
            min_sampling_points=5,
            max_sampling_points=25,
            tool_max=49
        )
        assert result == 25  # Clamped to max_sampling_points

    def test_explicit_value_clamped_to_tool_max(self):
        """Test explicit value above tool_max is clamped to tool_max."""
        result = resolve_target_point_count(
            requested=50,
            strategy_id="CENTER_EDGE",
            min_sampling_points=5,
            max_sampling_points=100,
            tool_max=49
        )
        assert result == 49  # Clamped to tool_max

    def test_strategy_default_used_when_none(self):
        """Test strategy default used when requested is None."""
        result = resolve_target_point_count(
            requested=None,
            strategy_id="CENTER_EDGE",
            min_sampling_points=5,
            max_sampling_points=25,
            tool_max=49
        )
        assert result == 20  # CENTER_EDGE default

    def test_strategy_default_clamped_to_constraints(self):
        """Test strategy default clamped if outside constraints."""
        # Default (20) clamped to max (15)
        result = resolve_target_point_count(
            requested=None,
            strategy_id="CENTER_EDGE",
            min_sampling_points=5,
            max_sampling_points=15,
            tool_max=49
        )
        assert result == 15

    def test_different_strategy_defaults(self):
        """Test different strategies use correct defaults."""
        # CENTER_EDGE: 20
        result = resolve_target_point_count(None, "CENTER_EDGE", 5, 50, 49)
        assert result == 20

        # GRID_UNIFORM: 30
        result = resolve_target_point_count(None, "GRID_UNIFORM", 5, 50, 49)
        assert result == 30

        # EDGE_ONLY: 15
        result = resolve_target_point_count(None, "EDGE_ONLY", 5, 50, 49)
        assert result == 15

        # ZONE_RING_N: 25
        result = resolve_target_point_count(None, "ZONE_RING_N", 5, 50, 49)
        assert result == 25

    def test_unknown_strategy_fallback(self):
        """Test unknown strategy uses fallback default (20)."""
        result = resolve_target_point_count(
            requested=None,
            strategy_id="UNKNOWN_STRATEGY",
            min_sampling_points=5,
            max_sampling_points=50,
            tool_max=49
        )
        assert result == 20  # Fallback default


class TestStrategyDefaultTargetCounts:
    """Test STRATEGY_DEFAULT_TARGET_COUNTS registry."""

    def test_all_strategies_have_defaults(self):
        """Test all enabled strategies have default target counts."""
        expected_strategies = ["CENTER_EDGE", "GRID_UNIFORM", "EDGE_ONLY", "ZONE_RING_N"]

        for strategy_id in expected_strategies:
            assert strategy_id in STRATEGY_DEFAULT_TARGET_COUNTS, \
                f"Strategy {strategy_id} missing from STRATEGY_DEFAULT_TARGET_COUNTS"

    def test_default_values_are_positive_integers(self):
        """Test all defaults are positive integers."""
        for strategy_id, default_count in STRATEGY_DEFAULT_TARGET_COUNTS.items():
            assert isinstance(default_count, int), \
                f"{strategy_id} default is not an integer: {default_count}"
            assert default_count > 0, \
                f"{strategy_id} default is not positive: {default_count}"

    def test_expected_default_values(self):
        """Test expected default values match specification."""
        assert STRATEGY_DEFAULT_TARGET_COUNTS["CENTER_EDGE"] == 20
        assert STRATEGY_DEFAULT_TARGET_COUNTS["GRID_UNIFORM"] == 30
        assert STRATEGY_DEFAULT_TARGET_COUNTS["EDGE_ONLY"] == 15
        assert STRATEGY_DEFAULT_TARGET_COUNTS["ZONE_RING_N"] == 25
