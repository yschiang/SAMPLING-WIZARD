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
