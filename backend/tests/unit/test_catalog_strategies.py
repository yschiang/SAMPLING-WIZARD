"""
Tests for catalog strategy filtering.

Validates that only enabled strategies are returned from the catalog endpoint.
"""
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from fastapi.testclient import TestClient
from backend.src.server.main import app

client = TestClient(app)


class TestStrategyFiltering:
    """Test that catalog endpoint returns only enabled strategies."""

    def test_process_context_returns_only_enabled_strategies(self):
        """Test that process-context endpoint returns only enabled strategies from catalog."""
        response = client.get(
            "/v1/catalog/process-context",
            params={
                "tech": "28nm",
                "step": "LITHO",
                "intent": "UNIFORMITY",
                "mode": "INLINE"
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "process_context" in data
        assert "allowed_strategy_set" in data["process_context"]

        allowed_strategies = data["process_context"]["allowed_strategy_set"]

        # Based on strategies.json, all 4 strategies are enabled
        assert "CENTER_EDGE" in allowed_strategies, "CENTER_EDGE should be enabled"
        assert "GRID_UNIFORM" in allowed_strategies, "GRID_UNIFORM should be enabled"
        assert "EDGE_ONLY" in allowed_strategies, "EDGE_ONLY should be enabled"
        assert "ZONE_RING_N" in allowed_strategies, "ZONE_RING_N should be enabled"

        # Verify we got exactly 4 strategies
        assert len(allowed_strategies) == 4, f"Expected 4 enabled strategies, got {len(allowed_strategies)}"

    def test_all_enabled_strategies_in_response(self):
        """Test that all enabled strategies are returned in response."""
        response = client.get(
            "/v1/catalog/process-context",
            params={
                "tech": "14nm",
                "step": "ETCH",
                "intent": "CD_CONTROL",
                "mode": "OFFLINE"
            }
        )

        assert response.status_code == 200
        allowed_strategies = response.json()["process_context"]["allowed_strategy_set"]

        # All 4 strategies are currently enabled
        expected_strategies = ["CENTER_EDGE", "GRID_UNIFORM", "EDGE_ONLY", "ZONE_RING_N"]
        for strategy in expected_strategies:
            assert strategy in allowed_strategies, \
                f"Enabled strategy {strategy} should be in allowed_strategy_set"

    def test_strategy_list_consistency_across_calls(self):
        """Test that strategy filtering is consistent across different process contexts."""
        # Make multiple calls with different parameters
        params_list = [
            {"tech": "28nm", "step": "LITHO", "intent": "UNIFORMITY", "mode": "INLINE"},
            {"tech": "14nm", "step": "ETCH", "intent": "CD_CONTROL", "mode": "OFFLINE"},
            {"tech": "7nm", "step": "LITHO", "intent": "THICKNESS", "mode": "MONITOR"}
        ]

        all_strategy_sets = []
        for params in params_list:
            response = client.get("/v1/catalog/process-context", params=params)
            assert response.status_code == 200
            strategies = response.json()["process_context"]["allowed_strategy_set"]
            all_strategy_sets.append(set(strategies))

        # All calls should return the same set of enabled strategies
        first_set = all_strategy_sets[0]
        for strategy_set in all_strategy_sets[1:]:
            assert strategy_set == first_set, \
                "Enabled strategy set should be consistent across different process contexts"

        # Verify it's the expected set (all 4 strategies enabled)
        assert first_set == {"CENTER_EDGE", "GRID_UNIFORM", "EDGE_ONLY", "ZONE_RING_N"}, \
            f"Expected all 4 strategies, got {first_set}"


class TestCatalogDataIntegrity:
    """Test catalog data loading and error handling."""

    def test_catalog_loads_successfully(self):
        """Test that the strategies catalog file loads without errors."""
        from backend.src.server.routes.catalog import get_enabled_strategies

        strategies = get_enabled_strategies()

        # Should return a list
        assert isinstance(strategies, list), "get_enabled_strategies should return a list"

        # Should not be empty
        assert len(strategies) > 0, "Should have at least one enabled strategy"

        # All items should be strings
        for strategy_id in strategies:
            assert isinstance(strategy_id, str), f"Strategy ID should be string, got {type(strategy_id)}"

    def test_enabled_strategies_match_catalog_data(self):
        """Test that enabled strategies match what's defined in strategies.json."""
        import json
        from pathlib import Path

        # Load the catalog file directly
        catalog_path = Path(__file__).parent.parent.parent / "src" / "data" / "catalog" / "strategies.json"
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)

        # Get enabled strategies from catalog
        expected_enabled = [s["strategy_id"] for s in catalog["strategies"] if s.get("enabled", False)]

        # Get enabled strategies from the function
        from backend.src.server.routes.catalog import get_enabled_strategies
        actual_enabled = get_enabled_strategies()

        # They should match
        assert set(actual_enabled) == set(expected_enabled), \
            f"Enabled strategies mismatch. Expected: {expected_enabled}, Got: {actual_enabled}"
