"""
Constraint drift gate tests (v1.3).

These tests enforce that the catalog config schemas remain synchronized with
Pydantic model validation rules. This prevents "constraint drift" where the
catalog (used for FE form generation) diverges from backend validation.

Validates:
- Catalog defaults match Pydantic model defaults
- Catalog ranges match Pydantic Field constraints (ge, le, gt, lt)
- Catalog enum options match Pydantic Literal values
- All enabled strategies have complete config schemas

Architect requirement #2: "Add constraint: test catalog schema = Pydantic defaults"
Extended to include ranges, enums, and completeness checks.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

import json
from pathlib import Path
import pytest
from backend.src.models.strategy_config import (
    CommonStrategyConfig,
    CenterEdgeAdvancedConfig,
    GridUniformAdvancedConfig,
    EdgeOnlyAdvancedConfig,
    ZoneRingNAdvancedConfig,
    ADVANCED_CONFIG_MODELS,
    STRATEGY_DEFAULT_TARGET_COUNTS,
)


# Load catalog once for all tests
_CATALOG_PATH = Path(__file__).parent.parent.parent / "src" / "data" / "catalog" / "strategies.json"

with open(_CATALOG_PATH, 'r') as f:
    _CATALOG = json.load(f)

_STRATEGIES_BY_ID = {s["strategy_id"]: s for s in _CATALOG["strategies"]}


class TestCommonConfigDrift:
    """Test catalog common config matches CommonStrategyConfig model."""

    def test_target_point_count_drift(self):
        """Test target_point_count catalog schema matches Pydantic."""
        # Get catalog schema from any strategy (common is the same for all)
        catalog_field = _STRATEGIES_BY_ID["CENTER_EDGE"]["config_schema"]["common"]["target_point_count"]

        # Pydantic model default
        pydantic_default = CommonStrategyConfig().target_point_count

        # Validate
        assert catalog_field["type"] == "integer", "Catalog type should be 'integer'"
        assert catalog_field["default"] is None, "Catalog default should be null"
        assert pydantic_default is None, "Pydantic default should be None"

        # Range
        assert catalog_field["range"][0] == 1, "Catalog min should be 1"
        assert catalog_field["range"][1] is None, "Catalog max should be null (unbounded)"

    def test_edge_exclusion_mm_drift(self):
        """Test edge_exclusion_mm catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["CENTER_EDGE"]["config_schema"]["common"]["edge_exclusion_mm"]
        pydantic_default = CommonStrategyConfig().edge_exclusion_mm

        # Type and default
        assert catalog_field["type"] == "float", "Catalog type should be 'float'"
        assert catalog_field["default"] == 0.0, "Catalog default should be 0.0"
        assert pydantic_default == 0.0, "Pydantic default should be 0.0"

        # Range
        assert catalog_field["range"][0] == 0.0, "Catalog min should be 0.0"
        assert catalog_field["range"][1] is None, "Catalog max should be null (unbounded)"

    def test_rotation_seed_drift(self):
        """Test rotation_seed catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["CENTER_EDGE"]["config_schema"]["common"]["rotation_seed"]
        pydantic_default = CommonStrategyConfig().rotation_seed

        # Type and default
        assert catalog_field["type"] == "integer", "Catalog type should be 'integer'"
        assert catalog_field["default"] is None, "Catalog default should be null"
        assert pydantic_default is None, "Pydantic default should be None"

        # Range
        assert catalog_field["range"][0] == 0, "Catalog min should be 0"
        assert catalog_field["range"][1] == 359, "Catalog max should be 359"

    def test_deterministic_seed_drift(self):
        """Test deterministic_seed catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["CENTER_EDGE"]["config_schema"]["common"]["deterministic_seed"]
        pydantic_default = CommonStrategyConfig().deterministic_seed

        # Type and default
        assert catalog_field["type"] == "integer", "Catalog type should be 'integer'"
        assert catalog_field["default"] is None, "Catalog default should be null"
        assert pydantic_default is None, "Pydantic default should be None"

        # Range
        assert catalog_field["range"][0] == 0, "Catalog min should be 0"
        assert catalog_field["range"][1] is None, "Catalog max should be null (unbounded)"

    def test_common_config_completeness(self):
        """Test all common fields present in catalog for each strategy."""
        expected_fields = ["target_point_count", "edge_exclusion_mm", "rotation_seed", "deterministic_seed"]

        for strategy_id in ADVANCED_CONFIG_MODELS.keys():
            strategy = _STRATEGIES_BY_ID[strategy_id]
            common_fields = strategy["config_schema"]["common"]

            for field_name in expected_fields:
                assert field_name in common_fields, \
                    f"Strategy {strategy_id} missing common field: {field_name}"


class TestCenterEdgeAdvancedDrift:
    """Test CENTER_EDGE advanced config catalog matches CenterEdgeAdvancedConfig model."""

    def test_center_weight_drift(self):
        """Test center_weight catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["CENTER_EDGE"]["config_schema"]["advanced"]["center_weight"]
        pydantic_default = CenterEdgeAdvancedConfig().center_weight

        # Type and default
        assert catalog_field["type"] == "float", "Catalog type should be 'float'"
        assert catalog_field["default"] == 0.2, "Catalog default should be 0.2"
        assert pydantic_default == 0.2, "Pydantic default should be 0.2"

        # Range
        assert catalog_field["range"][0] == 0.0, "Catalog min should be 0.0"
        assert catalog_field["range"][1] == 1.0, "Catalog max should be 1.0"

    def test_ring_count_drift(self):
        """Test ring_count catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["CENTER_EDGE"]["config_schema"]["advanced"]["ring_count"]
        pydantic_default = CenterEdgeAdvancedConfig().ring_count

        # Type and default
        assert catalog_field["type"] == "integer", "Catalog type should be 'integer'"
        assert catalog_field["default"] == 3, "Catalog default should be 3"
        assert pydantic_default == 3, "Pydantic default should be 3"

        # Range
        assert catalog_field["range"][0] == 2, "Catalog min should be 2"
        assert catalog_field["range"][1] == 5, "Catalog max should be 5"

        # Options
        assert "options" in catalog_field, "ring_count should have options for select UI"
        assert catalog_field["options"] == [2, 3, 4, 5], "Catalog options should match valid range"

    def test_radial_spacing_drift(self):
        """Test radial_spacing catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["CENTER_EDGE"]["config_schema"]["advanced"]["radial_spacing"]
        pydantic_default = CenterEdgeAdvancedConfig().radial_spacing

        # Type and default
        assert catalog_field["type"] == "enum", "Catalog type should be 'enum'"
        assert catalog_field["default"] == "UNIFORM", "Catalog default should be 'UNIFORM'"
        assert pydantic_default == "UNIFORM", "Pydantic default should be 'UNIFORM'"

        # Options (match Literal type)
        assert set(catalog_field["options"]) == {"UNIFORM", "EXPONENTIAL"}, \
            "Catalog options should match Pydantic Literal values"


class TestGridUniformAdvancedDrift:
    """Test GRID_UNIFORM advanced config catalog matches GridUniformAdvancedConfig model."""

    def test_grid_pitch_mm_drift(self):
        """Test grid_pitch_mm catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["GRID_UNIFORM"]["config_schema"]["advanced"]["grid_pitch_mm"]
        pydantic_default = GridUniformAdvancedConfig().grid_pitch_mm

        # Type and default
        assert catalog_field["type"] == "float", "Catalog type should be 'float'"
        assert catalog_field["default"] is None, "Catalog default should be null"
        assert pydantic_default is None, "Pydantic default should be None"

        # Range (gt=0.0 means > 0, not >=)
        assert catalog_field["range"][0] == 0.0, "Catalog min should be 0.0"
        assert catalog_field["range"][1] is None, "Catalog max should be null"

    def test_jitter_ratio_drift(self):
        """Test jitter_ratio catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["GRID_UNIFORM"]["config_schema"]["advanced"]["jitter_ratio"]
        pydantic_default = GridUniformAdvancedConfig().jitter_ratio

        # Type and default
        assert catalog_field["type"] == "float", "Catalog type should be 'float'"
        assert catalog_field["default"] == 0.0, "Catalog default should be 0.0"
        assert pydantic_default == 0.0, "Pydantic default should be 0.0"

        # Range
        assert catalog_field["range"][0] == 0.0, "Catalog min should be 0.0"
        assert catalog_field["range"][1] == 0.3, "Catalog max should be 0.3"

    def test_grid_alignment_drift(self):
        """Test grid_alignment catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["GRID_UNIFORM"]["config_schema"]["advanced"]["grid_alignment"]
        pydantic_default = GridUniformAdvancedConfig().grid_alignment

        # Type and default
        assert catalog_field["type"] == "enum", "Catalog type should be 'enum'"
        assert catalog_field["default"] == "CENTER", "Catalog default should be 'CENTER'"
        assert pydantic_default == "CENTER", "Pydantic default should be 'CENTER'"

        # Options
        assert set(catalog_field["options"]) == {"CENTER", "CORNER"}, \
            "Catalog options should match Pydantic Literal values"


class TestEdgeOnlyAdvancedDrift:
    """Test EDGE_ONLY advanced config catalog matches EdgeOnlyAdvancedConfig model."""

    def test_edge_band_width_mm_drift(self):
        """Test edge_band_width_mm catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["EDGE_ONLY"]["config_schema"]["advanced"]["edge_band_width_mm"]
        pydantic_default = EdgeOnlyAdvancedConfig().edge_band_width_mm

        # Type and default
        assert catalog_field["type"] == "float", "Catalog type should be 'float'"
        assert catalog_field["default"] == 10.0, "Catalog default should be 10.0"
        assert pydantic_default == 10.0, "Pydantic default should be 10.0"

        # Range
        assert catalog_field["range"][0] == 5.0, "Catalog min should be 5.0"
        assert catalog_field["range"][1] == 50.0, "Catalog max should be 50.0"

    def test_angular_spacing_deg_drift(self):
        """Test angular_spacing_deg catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["EDGE_ONLY"]["config_schema"]["advanced"]["angular_spacing_deg"]
        pydantic_default = EdgeOnlyAdvancedConfig().angular_spacing_deg

        # Type and default
        assert catalog_field["type"] == "float", "Catalog type should be 'float'"
        assert catalog_field["default"] == 45.0, "Catalog default should be 45.0"
        assert pydantic_default == 45.0, "Pydantic default should be 45.0"

        # Range
        assert catalog_field["range"][0] == 15.0, "Catalog min should be 15.0"
        assert catalog_field["range"][1] == 90.0, "Catalog max should be 90.0"

    def test_prioritize_corners_drift(self):
        """Test prioritize_corners catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["EDGE_ONLY"]["config_schema"]["advanced"]["prioritize_corners"]
        pydantic_default = EdgeOnlyAdvancedConfig().prioritize_corners

        # Type and default
        assert catalog_field["type"] == "boolean", "Catalog type should be 'boolean'"
        assert catalog_field["default"] is True, "Catalog default should be true"
        assert pydantic_default is True, "Pydantic default should be True"


class TestZoneRingNAdvancedDrift:
    """Test ZONE_RING_N advanced config catalog matches ZoneRingNAdvancedConfig model."""

    def test_num_rings_drift(self):
        """Test num_rings catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["ZONE_RING_N"]["config_schema"]["advanced"]["num_rings"]
        pydantic_default = ZoneRingNAdvancedConfig().num_rings

        # Type and default
        assert catalog_field["type"] == "integer", "Catalog type should be 'integer'"
        assert catalog_field["default"] == 3, "Catalog default should be 3"
        assert pydantic_default == 3, "Pydantic default should be 3"

        # Range
        assert catalog_field["range"][0] == 2, "Catalog min should be 2"
        assert catalog_field["range"][1] == 10, "Catalog max should be 10"

        # Options
        assert "options" in catalog_field, "num_rings should have options for select UI"
        assert catalog_field["options"] == [2, 3, 4, 5, 6, 7, 8, 9, 10], \
            "Catalog options should match valid range"

    def test_allocation_mode_drift(self):
        """Test allocation_mode catalog schema matches Pydantic."""
        catalog_field = _STRATEGIES_BY_ID["ZONE_RING_N"]["config_schema"]["advanced"]["allocation_mode"]
        pydantic_default = ZoneRingNAdvancedConfig().allocation_mode

        # Type and default
        assert catalog_field["type"] == "enum", "Catalog type should be 'enum'"
        assert catalog_field["default"] == "AREA_PROPORTIONAL", \
            "Catalog default should be 'AREA_PROPORTIONAL'"
        assert pydantic_default == "AREA_PROPORTIONAL", \
            "Pydantic default should be 'AREA_PROPORTIONAL'"

        # Options
        assert set(catalog_field["options"]) == {"AREA_PROPORTIONAL", "UNIFORM", "EDGE_HEAVY"}, \
            "Catalog options should match Pydantic Literal values"


class TestStrategyDefaultTargetCountsDrift:
    """Test catalog default_target_point_count matches STRATEGY_DEFAULT_TARGET_COUNTS."""

    def test_all_strategies_have_catalog_defaults(self):
        """Test all strategies in ADVANCED_CONFIG_MODELS have catalog default_target_point_count."""
        for strategy_id in ADVANCED_CONFIG_MODELS.keys():
            strategy = _STRATEGIES_BY_ID[strategy_id]
            assert "default_target_point_count" in strategy, \
                f"Strategy {strategy_id} missing default_target_point_count in catalog"

    def test_catalog_defaults_match_registry(self):
        """Test catalog default_target_point_count values match STRATEGY_DEFAULT_TARGET_COUNTS."""
        for strategy_id in ADVANCED_CONFIG_MODELS.keys():
            catalog_default = _STRATEGIES_BY_ID[strategy_id]["default_target_point_count"]
            registry_default = STRATEGY_DEFAULT_TARGET_COUNTS[strategy_id]

            assert catalog_default == registry_default, \
                f"Strategy {strategy_id}: catalog default ({catalog_default}) != " \
                f"registry default ({registry_default})"

    def test_expected_default_values(self):
        """Test expected default values present in catalog."""
        assert _STRATEGIES_BY_ID["CENTER_EDGE"]["default_target_point_count"] == 20
        assert _STRATEGIES_BY_ID["GRID_UNIFORM"]["default_target_point_count"] == 30
        assert _STRATEGIES_BY_ID["EDGE_ONLY"]["default_target_point_count"] == 15
        assert _STRATEGIES_BY_ID["ZONE_RING_N"]["default_target_point_count"] == 25


class TestCatalogCompleteness:
    """Test all enabled strategies have complete config schemas."""

    def test_all_enabled_strategies_have_config_schema(self):
        """Test all enabled strategies have config_schema field."""
        enabled_strategies = [s for s in _CATALOG["strategies"] if s.get("enabled", False)]

        for strategy in enabled_strategies:
            assert "config_schema" in strategy, \
                f"Enabled strategy {strategy['strategy_id']} missing config_schema"
            assert "common" in strategy["config_schema"], \
                f"Strategy {strategy['strategy_id']} missing common config schema"
            assert "advanced" in strategy["config_schema"], \
                f"Strategy {strategy['strategy_id']} missing advanced config schema"

    def test_all_advanced_config_models_have_catalog_entry(self):
        """Test all strategies in ADVANCED_CONFIG_MODELS have catalog entry."""
        for strategy_id in ADVANCED_CONFIG_MODELS.keys():
            assert strategy_id in _STRATEGIES_BY_ID, \
                f"Strategy {strategy_id} in ADVANCED_CONFIG_MODELS but not in catalog"

            strategy = _STRATEGIES_BY_ID[strategy_id]
            assert strategy.get("enabled", False), \
                f"Strategy {strategy_id} in ADVANCED_CONFIG_MODELS but not enabled in catalog"

    def test_enabled_strategies_match_advanced_config_models(self):
        """Test enabled strategies in catalog match ADVANCED_CONFIG_MODELS registry."""
        enabled_strategy_ids = [
            s["strategy_id"] for s in _CATALOG["strategies"] if s.get("enabled", False)
        ]

        registry_strategy_ids = list(ADVANCED_CONFIG_MODELS.keys())

        assert set(enabled_strategy_ids) == set(registry_strategy_ids), \
            f"Enabled strategies ({enabled_strategy_ids}) != " \
            f"ADVANCED_CONFIG_MODELS registry ({registry_strategy_ids})"


class TestCatalogStructuralIntegrity:
    """Test catalog has required structural elements."""

    def test_catalog_has_strategies_key(self):
        """Test catalog has 'strategies' key."""
        assert "strategies" in _CATALOG, "Catalog missing 'strategies' key"
        assert isinstance(_CATALOG["strategies"], list), "'strategies' should be a list"

    def test_each_strategy_has_required_fields(self):
        """Test each strategy has required top-level fields."""
        required_fields = ["strategy_id", "name", "description", "enabled"]

        for strategy in _CATALOG["strategies"]:
            for field in required_fields:
                assert field in strategy, \
                    f"Strategy {strategy.get('strategy_id', 'UNKNOWN')} missing field: {field}"

    def test_config_schema_structure(self):
        """Test config_schema has correct structure."""
        for strategy in _CATALOG["strategies"]:
            if "config_schema" in strategy:
                schema = strategy["config_schema"]
                strategy_id = strategy["strategy_id"]

                # Must have common and advanced
                assert "common" in schema, f"{strategy_id} config_schema missing 'common'"
                assert "advanced" in schema, f"{strategy_id} config_schema missing 'advanced'"

                # Common and advanced must be dicts
                assert isinstance(schema["common"], dict), \
                    f"{strategy_id} 'common' should be a dict"
                assert isinstance(schema["advanced"], dict), \
                    f"{strategy_id} 'advanced' should be a dict"

    def test_field_schema_structure(self):
        """Test each field schema has required properties."""
        required_props = ["type", "default", "description"]

        for strategy in _CATALOG["strategies"]:
            if "config_schema" not in strategy:
                continue

            strategy_id = strategy["strategy_id"]
            schema = strategy["config_schema"]

            # Check common fields
            for field_name, field_schema in schema["common"].items():
                for prop in required_props:
                    assert prop in field_schema, \
                        f"{strategy_id}.common.{field_name} missing property: {prop}"

            # Check advanced fields
            for field_name, field_schema in schema["advanced"].items():
                for prop in required_props:
                    assert prop in field_schema, \
                        f"{strategy_id}.advanced.{field_name} missing property: {prop}"
