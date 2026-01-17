"""
Tests for PR-B: L3 Strategy Registry.

Validates registry dispatch, unknown strategy handling, and strategy listing.
"""

import pytest
from src.engines.l3 import get_strategy, list_strategies, SamplingStrategy
from src.engines.l3.registry import is_registered
from src.engines.l3.strategies.center_edge import CenterEdgeStrategy


class TestRegistryDispatch:
    """Test registry dispatch functionality."""

    def test_get_strategy_returns_center_edge(self):
        """Test that get_strategy('CENTER_EDGE') returns CenterEdgeStrategy instance."""
        strategy = get_strategy("CENTER_EDGE")

        assert isinstance(strategy, SamplingStrategy)
        assert isinstance(strategy, CenterEdgeStrategy)
        assert strategy.get_strategy_id() == "CENTER_EDGE"

    def test_get_strategy_unknown_raises_key_error(self):
        """Test that get_strategy with unknown ID raises KeyError."""
        with pytest.raises(KeyError) as exc_info:
            get_strategy("UNKNOWN_STRATEGY")

        assert "Unknown strategy" in str(exc_info.value)
        assert "UNKNOWN_STRATEGY" in str(exc_info.value)

    def test_get_strategy_returns_new_instance_each_call(self):
        """Test that get_strategy returns a new instance each time."""
        strategy1 = get_strategy("CENTER_EDGE")
        strategy2 = get_strategy("CENTER_EDGE")

        assert strategy1 is not strategy2
        assert type(strategy1) == type(strategy2)


class TestRegistryListing:
    """Test registry listing functionality."""

    def test_list_strategies_includes_center_edge(self):
        """Test that list_strategies includes CENTER_EDGE."""
        strategies = list_strategies()

        assert "CENTER_EDGE" in strategies

    def test_list_strategies_returns_list(self):
        """Test that list_strategies returns a list."""
        strategies = list_strategies()

        assert isinstance(strategies, list)
        assert len(strategies) >= 1

    def test_is_registered_true_for_center_edge(self):
        """Test is_registered returns True for CENTER_EDGE."""
        assert is_registered("CENTER_EDGE") is True

    def test_is_registered_false_for_unknown(self):
        """Test is_registered returns False for unknown strategy."""
        assert is_registered("UNKNOWN") is False


class TestBackwardCompatibility:
    """Test backward compatibility with old import paths."""

    def test_old_import_path_works(self):
        """Test that importing from engine.l3 still works and produces equivalent behavior."""
        from src.engine.l3 import CenterEdgeStrategy as OldCenterEdge
        from src.engine.l3 import SamplingStrategy as OldSamplingStrategy

        # Old imports should still work (classes exist and are usable)
        assert OldCenterEdge is not None
        assert OldSamplingStrategy is not None

        # Verify they have the same interface
        assert hasattr(OldCenterEdge, 'select_points')
        assert hasattr(OldCenterEdge, 'get_strategy_id')
        assert hasattr(OldCenterEdge, 'get_strategy_version')

    def test_old_import_instance_works(self):
        """Test that instances from old import work correctly."""
        from src.engine.l3 import CenterEdgeStrategy as OldCenterEdge

        strategy = OldCenterEdge()
        assert strategy.get_strategy_id() == "CENTER_EDGE"
        assert strategy.get_strategy_version() == "1.0"

    def test_old_and_new_produce_same_output(self):
        """Test that old and new imports produce identical outputs."""
        import json
        import copy
        from pathlib import Path
        from src.engine.l3 import CenterEdgeStrategy as OldCenterEdge
        from src.engines.l3.strategies.center_edge import CenterEdgeStrategy as NewCenterEdge
        from src.models.sampling import SamplingPreviewRequest, StrategySelection
        from src.models.base import WaferMapSpec
        from src.models.catalog import ProcessContext, ToolProfile

        # Load golden fixture
        fixtures_path = Path(__file__).parent.parent / "fixtures" / "golden_requests.json"
        with open(fixtures_path, 'r') as f:
            golden = json.load(f)

        base_request = copy.deepcopy(golden["preview_request"])
        request = SamplingPreviewRequest(
            wafer_map_spec=WaferMapSpec(**base_request["wafer_map_spec"]),
            process_context=ProcessContext(**base_request["process_context"]),
            tool_profile=ToolProfile(**base_request["tool_profile"]),
            strategy=StrategySelection(**base_request["strategy"])
        )

        # Execute both
        old_output = OldCenterEdge().select_points(request)
        new_output = NewCenterEdge().select_points(request)

        # Verify identical outputs
        assert old_output.sampling_strategy_id == new_output.sampling_strategy_id
        assert len(old_output.selected_points) == len(new_output.selected_points)
        for old_p, new_p in zip(old_output.selected_points, new_output.selected_points):
            assert old_p.die_x == new_p.die_x
            assert old_p.die_y == new_p.die_y
