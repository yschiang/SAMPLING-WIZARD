"""
Tests for PR-B: L3 CENTER_EDGE Regression Tests.

Validates that CENTER_EDGE output is IDENTICAL after moving to registry.
"""

import pytest
import json
import copy
from pathlib import Path
from src.engines.l3 import get_strategy
from src.engines.l3.strategies.center_edge import CenterEdgeStrategy
from src.models.sampling import SamplingPreviewRequest, StrategySelection
from src.models.base import WaferMapSpec
from src.models.catalog import ProcessContext, ToolProfile

# Load golden requests for test data
fixtures_path = Path(__file__).parent.parent / "fixtures" / "golden_requests.json"
with open(fixtures_path, 'r') as f:
    GOLDEN_REQUESTS = json.load(f)


def create_golden_request() -> SamplingPreviewRequest:
    """Create request from golden fixture."""
    base_request = copy.deepcopy(GOLDEN_REQUESTS["preview_request"])

    wafer_spec = WaferMapSpec(**base_request["wafer_map_spec"])
    process_context = ProcessContext(**base_request["process_context"])
    tool_profile = ToolProfile(**base_request["tool_profile"])
    strategy = StrategySelection(**base_request["strategy"])

    return SamplingPreviewRequest(
        wafer_map_spec=wafer_spec,
        process_context=process_context,
        tool_profile=tool_profile,
        strategy=strategy
    )


class TestCenterEdgeRegression:
    """Regression tests to ensure CENTER_EDGE behavior is unchanged."""

    def test_golden_output_structure(self):
        """Test that output structure matches expected schema."""
        request = create_golden_request()
        strategy = get_strategy("CENTER_EDGE")

        output = strategy.select_points(request)

        # Validate structure
        assert output.sampling_strategy_id == "CENTER_EDGE"
        assert hasattr(output, 'selected_points')
        assert hasattr(output, 'trace')
        assert output.trace.strategy_version == "1.0"

    def test_golden_output_point_count(self):
        """Test that point count matches expected range from golden fixture."""
        request = create_golden_request()
        strategy = get_strategy("CENTER_EDGE")

        output = strategy.select_points(request)

        # Golden fixture: min=5, max=25
        assert len(output.selected_points) >= 5
        assert len(output.selected_points) <= 25

    def test_golden_output_center_point_first(self):
        """Test that center point (0,0) is always first."""
        request = create_golden_request()
        strategy = get_strategy("CENTER_EDGE")

        output = strategy.select_points(request)

        # Center point should always be first
        first_point = output.selected_points[0]
        assert first_point.die_x == 0
        assert first_point.die_y == 0

    def test_golden_output_determinism(self):
        """Test that same input produces identical output (10 runs)."""
        request = create_golden_request()

        outputs = []
        for _ in range(10):
            strategy = get_strategy("CENTER_EDGE")
            output = strategy.select_points(request)
            outputs.append(output)

        # All outputs should be identical
        first_output = outputs[0]
        for i, output in enumerate(outputs[1:], 1):
            assert output.sampling_strategy_id == first_output.sampling_strategy_id, \
                f"Run {i}: strategy_id differs"
            assert len(output.selected_points) == len(first_output.selected_points), \
                f"Run {i}: point count differs"

            for j, (p1, p2) in enumerate(zip(first_output.selected_points, output.selected_points)):
                assert p1.die_x == p2.die_x, f"Run {i}, point {j}: die_x differs"
                assert p1.die_y == p2.die_y, f"Run {i}, point {j}: die_y differs"

    def test_registry_vs_direct_instantiation(self):
        """Test that registry dispatch produces same output as direct instantiation."""
        request = create_golden_request()

        # Via registry
        registry_strategy = get_strategy("CENTER_EDGE")
        registry_output = registry_strategy.select_points(request)

        # Direct instantiation
        direct_strategy = CenterEdgeStrategy()
        direct_output = direct_strategy.select_points(request)

        # Should be identical
        assert registry_output.sampling_strategy_id == direct_output.sampling_strategy_id
        assert len(registry_output.selected_points) == len(direct_output.selected_points)

        for p1, p2 in zip(registry_output.selected_points, direct_output.selected_points):
            assert p1.die_x == p2.die_x
            assert p1.die_y == p2.die_y


class TestCenterEdgeEdgeCases:
    """Test CENTER_EDGE with various edge cases."""

    def test_small_wafer(self):
        """Test with smaller wafer size."""
        request = create_golden_request()
        request.wafer_map_spec.wafer_size_mm = 100.0
        request.wafer_map_spec.valid_die_mask.radius_mm = 45.0
        request.process_context.min_sampling_points = 3
        request.process_context.max_sampling_points = 10

        strategy = get_strategy("CENTER_EDGE")
        output = strategy.select_points(request)

        assert len(output.selected_points) >= 3
        assert output.selected_points[0].die_x == 0
        assert output.selected_points[0].die_y == 0

    def test_large_max_points(self):
        """Test with large max_points (should still be deterministic)."""
        request = create_golden_request()
        request.process_context.max_sampling_points = 100
        request.tool_profile.max_points_per_wafer = 100

        strategy = get_strategy("CENTER_EDGE")
        output1 = strategy.select_points(request)

        strategy2 = get_strategy("CENTER_EDGE")
        output2 = strategy2.select_points(request)

        assert len(output1.selected_points) == len(output2.selected_points)
        for p1, p2 in zip(output1.selected_points, output2.selected_points):
            assert p1.die_x == p2.die_x
            assert p1.die_y == p2.die_y
