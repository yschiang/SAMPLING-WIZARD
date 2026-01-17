"""
Base interfaces and types for L3 sampling strategies.
"""

from abc import ABC, abstractmethod
from typing import List
from ...models.base import DiePoint
from ...models.sampling import SamplingOutput, SamplingPreviewRequest


class SamplingStrategy(ABC):
    """
    Base class for all L3 sampling strategies.

    CRITICAL INVARIANT: L3 only selects points - no mutation, reordering, or filtering
    of outputs is allowed at this layer.
    """

    @abstractmethod
    def select_points(self, request: SamplingPreviewRequest) -> SamplingOutput:
        """
        Select sampling points deterministically based on strategy.

        Args:
            request: Complete sampling preview request with all context

        Returns:
            SamplingOutput with selected points, strategy ID, and trace

        REQUIREMENTS:
        - Must be deterministic: same inputs -> same outputs
        - Must apply wafer map valid_die_mask filtering
        - Must enforce process_context min/max sampling points
        - Must respect tool_profile max_points_per_wafer
        - Must NOT reorder, dedupe, or mutate selected points after selection
        """
        pass

    @abstractmethod
    def get_strategy_id(self) -> str:
        """Return unique strategy identifier."""
        pass

    @abstractmethod
    def get_strategy_version(self) -> str:
        """Return strategy version for trace."""
        pass
