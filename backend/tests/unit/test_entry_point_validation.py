"""
Entry-point validation tests for v1.3 strategy config.

Proves that unknown fields and invalid configurations are rejected
at the API entry point with proper 400 errors.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

import json
import copy
from fastapi.testclient import TestClient
from backend.src.server.main import app

client = TestClient(app)

# Load golden fixtures
with open(os.path.join(os.path.dirname(__file__), "../fixtures/golden_requests.json")) as f:
    GOLDEN_REQUESTS = json.load(f)


class TestStrategyConfigEntryPointValidation:
    """Test that strategy_config validation happens at API entry point."""

    def test_valid_config_accepted(self):
        """Test that valid strategy_config is accepted."""
        request = copy.deepcopy(GOLDEN_REQUESTS["preview_request_with_full_config"])
        response = client.post("/v1/sampling/preview", json=request)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"

    def test_missing_strategy_config_accepted(self):
        """Test that missing strategy_config (null) is accepted with defaults."""
        request = copy.deepcopy(GOLDEN_REQUESTS["preview_request"])
        response = client.post("/v1/sampling/preview", json=request)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"

    def test_partial_common_config_accepted(self):
        """Test that partial common config is accepted."""
        request = copy.deepcopy(GOLDEN_REQUESTS["preview_request_with_common_config"])
        response = client.post("/v1/sampling/preview", json=request)

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"

    def test_unknown_common_field_rejected(self):
        """Test that unknown fields in common section are rejected by Pydantic."""
        request = copy.deepcopy(GOLDEN_REQUESTS["preview_request"])
        request["strategy"]["strategy_config"] = {
            "common": {
                "target_point_count": 20,
                "unknown_field": "invalid"  # Unknown field
            }
        }

        response = client.post("/v1/sampling/preview", json=request)

        # Pydantic should reject with 422 Unprocessable Entity for unknown fields
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.json()}"
        error_detail = response.json()
        assert "detail" in error_detail, "Expected validation error detail"

    def test_invalid_range_in_common_rejected(self):
        """Test that invalid range in common config is rejected."""
        request = copy.deepcopy(GOLDEN_REQUESTS["preview_request"])
        request["strategy"]["strategy_config"] = {
            "common": {
                "target_point_count": 0  # Invalid: must be >= 1
            }
        }

        response = client.post("/v1/sampling/preview", json=request)

        # Pydantic should reject with 422
        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.json()}"
        error_detail = response.json()
        assert "detail" in error_detail

    def test_invalid_rotation_seed_rejected(self):
        """Test that rotation_seed out of range [0, 359] is rejected."""
        request = copy.deepcopy(GOLDEN_REQUESTS["preview_request"])
        request["strategy"]["strategy_config"] = {
            "common": {
                "rotation_seed": 360  # Invalid: must be < 360
            }
        }

        response = client.post("/v1/sampling/preview", json=request)

        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.json()}"

    def test_negative_edge_exclusion_rejected(self):
        """Test that negative edge_exclusion_mm is rejected."""
        request = copy.deepcopy(GOLDEN_REQUESTS["preview_request"])
        request["strategy"]["strategy_config"] = {
            "common": {
                "edge_exclusion_mm": -1.0  # Invalid: must be >= 0
            }
        }

        response = client.post("/v1/sampling/preview", json=request)

        assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.json()}"


class TestAdvancedConfigValidationNote:
    """
    NOTE: Advanced config validation currently happens via raw Dict[str, Any] in StrategyConfig model.

    Full validation with INVALID_STRATEGY_CONFIG error code requires:
    - Calling validate_and_parse_advanced_config() in route or strategy
    - Converting advanced dict to typed model before strategy execution

    This is tracked as follow-up work in PR-D2 or later.

    Current behavior:
    - Unknown fields in advanced dict are NOT rejected by Pydantic (Dict[str, Any] accepts anything)
    - Validation happens when strategy accesses advanced config (if implemented)
    - ZoneRingNStrategy already validates num_rings via updated v1.3 accessor
    """

    def test_advanced_config_passes_through_pydantic(self):
        """Test that advanced config passes Pydantic validation (Dict[str, Any])."""
        request = copy.deepcopy(GOLDEN_REQUESTS["preview_request"])
        request["strategy"]["strategy_config"] = {
            "advanced": {
                "center_weight": 0.3,
                "ring_count": 4
            }
        }

        response = client.post("/v1/sampling/preview", json=request)

        # Should pass Pydantic (Dict[str, Any] accepts anything)
        # Strategy-level validation would happen in select_points()
        assert response.status_code == 200, f"Got {response.status_code}: {response.json()}"
