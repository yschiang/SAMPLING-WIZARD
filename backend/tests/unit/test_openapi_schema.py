"""
OpenAPI schema validation for v1.3.

Verifies that FastAPI auto-generates correct OpenAPI schema from Pydantic models.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.src.server.main import app


def test_strategy_selection_schema_v13():
    """Test that StrategySelection schema reflects v1.3 structure."""
    openapi_schema = app.openapi()
    schemas = openapi_schema["components"]["schemas"]

    strategy_selection = schemas["StrategySelection"]

    # v1.3: Should have strategy_id and strategy_config
    assert "strategy_id" in strategy_selection["properties"]
    assert "strategy_config" in strategy_selection["properties"]

    # v1.3: Should NOT have params (removed)
    assert "params" not in strategy_selection["properties"], \
        "params field should be removed in v1.3"

    # strategy_config should reference StrategyConfig schema
    strategy_config_ref = strategy_selection["properties"]["strategy_config"]
    assert "$ref" in strategy_config_ref or "anyOf" in strategy_config_ref, \
        "strategy_config should reference StrategyConfig schema"

    print("✅ StrategySelection schema:")
    print(f"  - strategy_id: present")
    print(f"  - strategy_config: present")
    print(f"  - params: {'REMOVED' if 'params' not in strategy_selection['properties'] else 'PRESENT (ERROR)'}")


def test_strategy_config_schema_structure():
    """Test that StrategyConfig schema has common and advanced sections."""
    openapi_schema = app.openapi()
    schemas = openapi_schema["components"]["schemas"]

    # StrategyConfig should exist
    assert "StrategyConfig" in schemas, "StrategyConfig schema should exist"

    strategy_config = schemas["StrategyConfig"]

    # Should have common and advanced properties
    assert "properties" in strategy_config
    properties = strategy_config["properties"]

    assert "common" in properties, "StrategyConfig should have 'common' property"
    assert "advanced" in properties, "StrategyConfig should have 'advanced' property"

    print("✅ StrategyConfig schema:")
    print(f"  - common: present (references CommonStrategyConfig)")
    print(f"  - advanced: present (Dict[str, Any])")


def test_common_strategy_config_fields():
    """Test that CommonStrategyConfig has all required fields."""
    openapi_schema = app.openapi()
    schemas = openapi_schema["components"]["schemas"]

    assert "CommonStrategyConfig" in schemas, "CommonStrategyConfig schema should exist"

    common_config = schemas["CommonStrategyConfig"]
    properties = common_config["properties"]

    expected_fields = ["target_point_count", "edge_exclusion_mm", "rotation_seed", "deterministic_seed"]

    for field in expected_fields:
        assert field in properties, f"CommonStrategyConfig should have '{field}' field"

    print("✅ CommonStrategyConfig fields:")
    for field in expected_fields:
        print(f"  - {field}: present")


if __name__ == "__main__":
    test_strategy_selection_schema_v13()
    test_strategy_config_schema_structure()
    test_common_strategy_config_fields()
    print("\n✅ All OpenAPI schema validations passed!")
