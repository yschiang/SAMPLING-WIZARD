"""
CENTER_EDGE sampling strategy implementation.

Deterministic ring-based selection around wafer center with edge emphasis.
"""

import math
from typing import List, Set, Tuple, Optional
from ..base import SamplingStrategy
from ....models.base import DiePoint
from ....models.sampling import SamplingOutput, SamplingTrace, SamplingPreviewRequest
from ....models.errors import ValidationError, ConstraintError, ErrorCode, WarningCode
from ....models.strategy_config import CommonStrategyConfig
from ....server.utils import get_deterministic_timestamp
from ..common import apply_edge_exclusion, get_rotation_offset, apply_rotation_to_angle


class CenterEdgeStrategy(SamplingStrategy):
    """
    CENTER_EDGE strategy: Ring-based sampling with center and edge emphasis.

    Algorithm:
    1. Start with wafer center die (0,0)
    2. Generate concentric rings of increasing radius
    3. Select dies from rings with preference for cardinal/diagonal directions
    4. Apply valid_die_mask filtering
    5. Enforce min/max sampling point constraints

    All outputs are deterministic for identical inputs.
    """

    def get_strategy_id(self) -> str:
        return "CENTER_EDGE"

    def get_strategy_version(self) -> str:
        return "1.0"

    def select_points(self, request: SamplingPreviewRequest) -> SamplingOutput:
        """
        Select sampling points using CENTER_EDGE strategy.

        Raises:
            ValidationError: For invalid input parameters
            ConstraintError: When constraints cannot be satisfied
        """
        # Validate strategy is allowed
        self._validate_strategy_allowed(request)

        # Validate input parameters
        self._validate_request_parameters(request)

        # Get common config (v1.3)
        common_config = self._get_common_config(request)

        # Get rotation offset (v1.3)
        rotation_offset = get_rotation_offset(common_config.rotation_seed)

        # Generate candidate points in deterministic ring order (v1.3: with rotation)
        candidates = self._generate_ring_candidates(request.wafer_map_spec, rotation_offset)

        # Apply wafer map valid die mask filtering
        valid_candidates = self._apply_die_mask(candidates, request.wafer_map_spec)

        # Apply additional edge exclusion from common config (v1.3)
        if common_config.edge_exclusion_mm > 0:
            valid_candidates = apply_edge_exclusion(
                valid_candidates,
                request.wafer_map_spec,
                common_config.edge_exclusion_mm
            )

        # Calculate target count (v1.3: use common config if provided)
        if common_config.target_point_count is not None:
            target_count = min(
                common_config.target_point_count,
                request.process_context.max_sampling_points,
                request.tool_profile.max_points_per_wafer
            )
        else:
            target_count = min(
                request.process_context.max_sampling_points,
                request.tool_profile.max_points_per_wafer
            )

        # Apply sampling constraints with error handling
        selected_points = self._apply_sampling_constraints_with_validation(
            valid_candidates,
            request.process_context.min_sampling_points,
            target_count
        )

        # Generate trace
        trace = SamplingTrace(
            strategy_version=self.get_strategy_version(),
            generated_at=get_deterministic_timestamp()
        )

        return SamplingOutput(
            sampling_strategy_id=self.get_strategy_id(),
            selected_points=selected_points,
            trace=trace
        )

    def _get_common_config(self, request: SamplingPreviewRequest) -> CommonStrategyConfig:
        """
        Extract common configuration from strategy_config (v1.3).

        Returns:
            CommonStrategyConfig with defaults for unspecified fields
        """
        if request.strategy.strategy_config and request.strategy.strategy_config.common:
            return request.strategy.strategy_config.common
        # Return default CommonStrategyConfig if not provided
        return CommonStrategyConfig()

    def _generate_ring_candidates(self, wafer_spec, rotation_offset: float = 0.0) -> List[DiePoint]:
        """
        Generate candidate sampling points in deterministic ring order.

        Returns points sorted by:
        1. Ring radius (distance from center)
        2. Angle (for deterministic ordering within ring)
        """
        # Calculate wafer radius in die units
        wafer_radius_mm = wafer_spec.wafer_size_mm / 2
        die_pitch_x = wafer_spec.die_pitch_x_mm
        die_pitch_y = wafer_spec.die_pitch_y_mm

        # Approximate max ring radius in die coordinates
        max_ring_x = int(wafer_radius_mm / die_pitch_x) + 1
        max_ring_y = int(wafer_radius_mm / die_pitch_y) + 1
        max_ring = max(max_ring_x, max_ring_y)

        candidates = []

        # Ring 0: Center point
        candidates.append(DiePoint(die_x=0, die_y=0))

        # Generate rings 1 to max_ring
        for ring in range(1, max_ring + 1):
            ring_points = self._generate_ring_points(ring, rotation_offset)
            candidates.extend(ring_points)

        return candidates

    def _generate_ring_points(self, ring: int, rotation_offset: float = 0.0) -> List[DiePoint]:
        """
        Generate points for a specific ring in deterministic order.

        For each ring, prioritize:
        1. Cardinal directions (N, E, S, W)
        2. Diagonal directions (NE, SE, SW, NW)
        3. Other points sorted by angle
        """
        points = []

        # Cardinal points first (if on ring boundary)
        cardinals = [
            DiePoint(die_x=0, die_y=ring),     # North
            DiePoint(die_x=ring, die_y=0),     # East
            DiePoint(die_x=0, die_y=-ring),    # South
            DiePoint(die_x=-ring, die_y=0),    # West
        ]
        points.extend(cardinals)

        # Diagonal points
        if ring > 1:  # Skip diagonals for ring 1 to avoid duplicates with cardinals
            diagonals = [
                DiePoint(die_x=ring, die_y=ring),     # NE
                DiePoint(die_x=ring, die_y=-ring),    # SE
                DiePoint(die_x=-ring, die_y=-ring),   # SW
                DiePoint(die_x=-ring, die_y=ring),    # NW
            ]
            points.extend(diagonals)

        # Additional ring points (for larger rings)
        if ring > 2:
            additional_points = []

            # Generate points along ring perimeter
            for x in range(-ring, ring + 1):
                for y in range(-ring, ring + 1):
                    # Only include points on ring boundary (not inside)
                    if max(abs(x), abs(y)) == ring:
                        point = DiePoint(die_x=x, die_y=y)

                        # Skip if already added as cardinal/diagonal
                        if point not in points:
                            additional_points.append(point)

            # Sort additional points by angle for deterministic ordering (v1.3: with rotation)
            def angle_key(p: DiePoint) -> tuple:
                angle_rad = math.atan2(p.die_y, p.die_x)
                angle_deg = math.degrees(angle_rad)
                if angle_deg < 0:
                    angle_deg += 360.0
                # Apply rotation offset
                rotated_angle = apply_rotation_to_angle(angle_deg, rotation_offset)
                return (rotated_angle, p.die_x, p.die_y)

            additional_points.sort(key=angle_key)
            points.extend(additional_points)

        return points

    def _apply_die_mask(self, candidates: List[DiePoint], wafer_spec) -> List[DiePoint]:
        """
        Filter candidates based on wafer map valid_die_mask.
        """
        die_mask = wafer_spec.valid_die_mask

        if die_mask.type == "EDGE_EXCLUSION":
            return self._apply_edge_exclusion(candidates, die_mask.radius_mm, wafer_spec)
        elif die_mask.type == "EXPLICIT_LIST":
            return self._apply_explicit_list(candidates, die_mask.valid_die_list)
        else:
            # Unknown mask type - return all candidates (permissive fallback)
            return candidates

    def _apply_edge_exclusion(self, candidates: List[DiePoint],
                             exclusion_radius_mm: float, wafer_spec) -> List[DiePoint]:
        """
        Apply edge exclusion mask - remove points outside the valid radius.
        """
        if exclusion_radius_mm is None:
            return candidates

        valid_points = []
        die_pitch_x = wafer_spec.die_pitch_x_mm
        die_pitch_y = wafer_spec.die_pitch_y_mm

        for point in candidates:
            # Convert die coordinates to mm
            x_mm = point.die_x * die_pitch_x
            y_mm = point.die_y * die_pitch_y

            # Calculate distance from wafer center
            distance_mm = math.sqrt(x_mm**2 + y_mm**2)

            # Include point if within valid radius
            if distance_mm <= exclusion_radius_mm:
                valid_points.append(point)

        return valid_points

    def _apply_explicit_list(self, candidates: List[DiePoint],
                           valid_die_list: List[DiePoint]) -> List[DiePoint]:
        """
        Apply explicit list mask - only include points in the valid list.
        """
        if not valid_die_list:
            return candidates

        # Convert valid list to set for O(1) lookup
        valid_set = {(p.die_x, p.die_y) for p in valid_die_list}

        # Filter candidates to only include valid points
        valid_points = []
        for point in candidates:
            if (point.die_x, point.die_y) in valid_set:
                valid_points.append(point)

        return valid_points

    def _apply_sampling_constraints(self, valid_candidates: List[DiePoint],
                                  min_points: int, max_points: int) -> List[DiePoint]:
        """
        Apply min/max sampling point constraints.

        Returns exactly the number of points needed, respecting limits.
        """
        # Determine target number of points
        available_points = len(valid_candidates)

        if available_points < min_points:
            # Insufficient points available - return all we have
            # This should be logged as a warning in production
            return valid_candidates

        # Take up to max_points, but at least min_points
        target_points = min(max_points, available_points)
        target_points = max(target_points, min_points)

        # Return first N points (already in deterministic ring order)
        return valid_candidates[:target_points]

    def _validate_strategy_allowed(self, request: SamplingPreviewRequest) -> None:
        """
        Validate that CENTER_EDGE strategy is allowed for this process context.

        Raises:
            ValidationError: If strategy is not in allowed_strategy_set
        """
        allowed_strategies = getattr(request.process_context, 'allowed_strategy_set', None)
        if allowed_strategies and self.get_strategy_id() not in allowed_strategies:
            raise ValidationError(
                ErrorCode.DISALLOWED_STRATEGY,
                f"Strategy '{self.get_strategy_id()}' is not allowed for this process context. "
                f"Allowed strategies: {allowed_strategies}"
            )

    def _validate_request_parameters(self, request: SamplingPreviewRequest) -> None:
        """
        Validate input request parameters.

        Raises:
            ValidationError: For invalid parameters
        """
        # Validate wafer spec
        if request.wafer_map_spec.wafer_size_mm <= 0:
            raise ValidationError(
                ErrorCode.INVALID_WAFER_SPEC,
                "wafer_size_mm must be positive"
            )

        if request.wafer_map_spec.die_pitch_x_mm <= 0 or request.wafer_map_spec.die_pitch_y_mm <= 0:
            raise ValidationError(
                ErrorCode.INVALID_WAFER_SPEC,
                "die_pitch_x_mm and die_pitch_y_mm must be positive"
            )

        # Validate constraints
        if request.process_context.min_sampling_points < 0:
            raise ValidationError(
                ErrorCode.INVALID_CONSTRAINTS,
                "min_sampling_points must be non-negative"
            )

        if request.process_context.max_sampling_points < request.process_context.min_sampling_points:
            raise ValidationError(
                ErrorCode.INVALID_CONSTRAINTS,
                "max_sampling_points must be >= min_sampling_points"
            )

        if request.tool_profile.max_points_per_wafer < 1:
            raise ValidationError(
                ErrorCode.INVALID_CONSTRAINTS,
                "tool max_points_per_wafer must be at least 1"
            )

    def _apply_sampling_constraints_with_validation(self, valid_candidates: List[DiePoint],
                                                  min_points: int, max_points: int) -> List[DiePoint]:
        """
        Apply min/max sampling point constraints with proper error handling.

        Raises:
            ConstraintError: When minimum constraints cannot be satisfied
        """
        available_points = len(valid_candidates)

        # Check if we can satisfy minimum constraint
        if available_points < min_points:
            raise ConstraintError(
                ErrorCode.CANNOT_MEET_MIN_POINTS,
                f"Cannot meet min_sampling_points requirement: need {min_points} points, "
                f"but only {available_points} valid dies available after filtering"
            )

        # Take up to max_points, but at least min_points
        target_points = min(max_points, available_points)
        target_points = max(target_points, min_points)

        # Return first N points (already in deterministic ring order)
        return valid_candidates[:target_points]
