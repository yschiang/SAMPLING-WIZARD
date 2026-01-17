"""
Minimal L3 Strategy Registry.

Maps strategy_id to strategy implementation.
No framework, no DI, no dynamic loading - just a simple dict.
"""

from typing import Dict, Type, List
from .base import SamplingStrategy
from .strategies.center_edge import CenterEdgeStrategy


# Strategy registry: strategy_id -> strategy class
_REGISTRY: Dict[str, Type[SamplingStrategy]] = {
    "CENTER_EDGE": CenterEdgeStrategy,
}


def get_strategy(strategy_id: str) -> SamplingStrategy:
    """
    Get a strategy instance by ID.

    Args:
        strategy_id: The strategy identifier (e.g., "CENTER_EDGE")

    Returns:
        An instance of the requested strategy

    Raises:
        KeyError: If strategy_id is not registered
    """
    strategy_class = _REGISTRY.get(strategy_id)
    if strategy_class is None:
        registered = list(_REGISTRY.keys())
        raise KeyError(
            f"Unknown strategy: '{strategy_id}'. "
            f"Registered strategies: {registered}"
        )
    return strategy_class()


def list_strategies() -> List[str]:
    """
    Return list of registered strategy IDs.

    Returns:
        List of strategy identifiers
    """
    return list(_REGISTRY.keys())


def is_registered(strategy_id: str) -> bool:
    """
    Check if a strategy is registered.

    Args:
        strategy_id: The strategy identifier to check

    Returns:
        True if registered, False otherwise
    """
    return strategy_id in _REGISTRY
