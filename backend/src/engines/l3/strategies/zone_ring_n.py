"""
ZONE_RING_N sampling strategy implementation.

Parameterized zone-based sampling with N concentric rings.
"""

import math
from typing import List, Dict
from ..base import SamplingStrategy
from ....models.base import DiePoint
from ....models.sampling import SamplingOutput, SamplingTrace, SamplingPreviewRequest
from ....models.errors import ValidationError, ConstraintError, ErrorCode
from ....server.utils import get_deterministic_timestamp


class ZoneRingNStrategy(SamplingStrategy):
    """
    ZONE_RING_N strategy: Zone-based sampling with N parameterized rings.

    Algorithm:
    1. Get num_rings from strategy params (default 3)
    2. Generate all candidate dies within wafer bounds
    3. Apply valid_die_mask filtering
    4. Classify dies into N concentric rings by distance
    5. Allocate points per ring proportional to ring area
    6. Select within each ring using canonical ordering + stride
    7. Combine all ring selections
    8. Enforce min/max sampling point constraints

    Ring Division (equal radius increments):
    - For N rings and wafer radius R:
      - Ring 0: 0 to R/N
      - Ring 1: R/N to 2R/N
      - Ring k: kR/N to (k+1)R/N
      - Ring N-1: (N-1)R/N to R

    Point Allocation (proportional to area):
    - Ring k area = π * ((k+1)R/N)² - π * (kR/N)²
    - Allocate points proportionally to area

    Ordering Policy (within each ring):
    - Primary: Distance from center (ascending)
    - Secondary: Angle (atan2) ascending
    - Tertiary: (die_x, die_y) ascending

    All outputs are deterministic for identical inputs.
    """

    DEFAULT_NUM_RINGS = 3

    def get_strategy_id(self) -> str:
        return "ZONE_RING_N"

    def get_strategy_version(self) -> str:
        return "1.0"

    def select_points(self, request: SamplingPreviewRequest) -> SamplingOutput:
        """
        Select sampling points using ZONE_RING_N strategy.

        Raises:
            ValidationError: For invalid input parameters
            ConstraintError: When constraints cannot be satisfied
        """
        # Validate strategy is allowed
        self._validate_strategy_allowed(request)

        # Validate input parameters
        self._validate_request_parameters(request)

        # Get num_rings from strategy params (default 3)
        num_rings = self._get_num_rings(request)

        # Generate candidate points
        candidates = self._generate_candidates(request.wafer_map_spec)

        # Apply wafer map valid die mask filtering
        valid_candidates = self._apply_die_mask(candidates, request.wafer_map_spec)

        # Classify dies into rings
        rings = self._classify_into_rings(
            valid_candidates,
            num_rings,
            request.wafer_map_spec
        )

        # Calculate target count
        target_count = min(
            request.process_context.max_sampling_points,
            request.tool_profile.max_points_per_wafer
        )

        # Allocate points per ring and select
        selected_points = self._allocate_and_select(
            rings,
            num_rings,
            target_count,
            request.wafer_map_spec
        )

        # Apply sampling constraints with error handling
        final_points = self._apply_sampling_constraints_with_validation(
            selected_points,
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
            selected_points=final_points,
            trace=trace
        )

    def _get_num_rings(self, request: SamplingPreviewRequest) -> int:
        """
        Get number of rings from strategy params or use default.

        Args:
            request: Sampling preview request

        Returns:
            Number of rings (default 3)
        """
        if request.strategy.params and 'num_rings' in request.strategy.params:
            num_rings = request.strategy.params['num_rings']

            # Validate num_rings
            if not isinstance(num_rings, int) or num_rings < 1:
                raise ValidationError(
                    ErrorCode.INVALID_CONSTRAINTS,
                    f"num_rings must be a positive integer, got: {num_rings}"
                )
            if num_rings > 10:
                raise ValidationError(
                    ErrorCode.INVALID_CONSTRAINTS,
                    f"num_rings must be <= 10, got: {num_rings}"
                )

            return num_rings

        return self.DEFAULT_NUM_RINGS

    def _generate_candidates(self, wafer_spec) -> List[DiePoint]:
        """
        Generate all candidate die positions within wafer bounds.

        Returns all dies that fall within the wafer radius.
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

        # Generate all candidate points within wafer bounds
        for x in range(-max_ring, max_ring + 1):
            for y in range(-max_ring, max_ring + 1):
                # Convert to mm coordinates
                x_mm = x * die_pitch_x
                y_mm = y * die_pitch_y
                distance_mm = math.sqrt(x_mm**2 + y_mm**2)

                # Only include points within wafer radius
                if distance_mm <= wafer_radius_mm:
                    candidates.append(DiePoint(die_x=x, die_y=y))

        return candidates

    def _classify_into_rings(self, candidates: List[DiePoint],
                            num_rings: int, wafer_spec) -> Dict[int, List[DiePoint]]:
        """
        Classify dies into N concentric rings based on distance from center.

        Args:
            candidates: List of candidate points
            num_rings: Number of rings to divide wafer into
            wafer_spec: Wafer specification

        Returns:
            Dictionary mapping ring_index -> list of DiePoints in that ring
        """
        wafer_radius_mm = wafer_spec.wafer_size_mm / 2
        die_pitch_x = wafer_spec.die_pitch_x_mm
        die_pitch_y = wafer_spec.die_pitch_y_mm

        # Initialize rings
        rings = {i: [] for i in range(num_rings)}

        # Classify each candidate into a ring
        for point in candidates:
            # Calculate distance from center
            x_mm = point.die_x * die_pitch_x
            y_mm = point.die_y * die_pitch_y
            distance_mm = math.sqrt(x_mm**2 + y_mm**2)

            # Determine ring index
            # Ring k: kR/N to (k+1)R/N
            ring_index = int(distance_mm / (wafer_radius_mm / num_rings))

            # Clamp to valid range (handles edge case where distance_mm ≈ wafer_radius_mm)
            if ring_index >= num_rings:
                ring_index = num_rings - 1

            rings[ring_index].append(point)

        return rings

    def _allocate_and_select(self, rings: Dict[int, List[DiePoint]],
                            num_rings: int, target_count: int,
                            wafer_spec) -> List[DiePoint]:
        """
        Allocate points per ring proportional to area and select.

        Args:
            rings: Dictionary of ring_index -> dies in that ring
            num_rings: Total number of rings
            target_count: Total number of points to select
            wafer_spec: Wafer specification

        Returns:
            List of selected points across all rings
        """
        wafer_radius_mm = wafer_spec.wafer_size_mm / 2

        # Calculate ring areas (proportional, no need for π)
        ring_areas = []
        for k in range(num_rings):
            inner_radius = k * wafer_radius_mm / num_rings
            outer_radius = (k + 1) * wafer_radius_mm / num_rings
            area = outer_radius**2 - inner_radius**2
            ring_areas.append(area)

        total_area = sum(ring_areas)

        # Allocate points proportionally to area
        ring_allocations = []
        allocated_total = 0
        for k in range(num_rings):
            proportion = ring_areas[k] / total_area
            allocated = int(target_count * proportion)

            # Ensure at least 1 point if ring has dies and we have budget
            if allocated == 0 and len(rings[k]) > 0 and allocated_total < target_count:
                allocated = 1

            ring_allocations.append(allocated)
            allocated_total += allocated

        # Distribute any remaining points (due to rounding) to larger rings
        remaining = target_count - allocated_total
        if remaining > 0:
            # Add remaining points to rings with largest area (outermost rings)
            for k in range(num_rings - 1, -1, -1):
                if remaining == 0:
                    break
                if len(rings[k]) > ring_allocations[k]:
                    ring_allocations[k] += 1
                    remaining -= 1

        # Select points from each ring
        selected_points = []
        for k in range(num_rings):
            ring_dies = rings[k]
            ring_target = ring_allocations[k]

            if not ring_dies or ring_target == 0:
                continue

            # Sort dies within ring using canonical ordering
            sorted_ring_dies = self._sort_canonical(
                ring_dies,
                wafer_spec.die_pitch_x_mm,
                wafer_spec.die_pitch_y_mm
            )

            # Select with stride
            ring_selected = self._select_with_stride(sorted_ring_dies, ring_target)
            selected_points.extend(ring_selected)

        return selected_points

    def _sort_canonical(self, candidates: List[DiePoint],
                       pitch_x: float, pitch_y: float) -> List[DiePoint]:
        """
        Sort candidates using canonical ordering.

        Canonical ordering:
        1. Distance from center (ascending)
        2. Angle (atan2) ascending
        3. (die_x, die_y) ascending
        """
        def canonical_key(p: DiePoint) -> tuple:
            x_mm = p.die_x * pitch_x
            y_mm = p.die_y * pitch_y
            distance = math.sqrt(x_mm**2 + y_mm**2)
            angle = math.atan2(y_mm, x_mm)
            return (distance, angle, p.die_x, p.die_y)

        return sorted(candidates, key=canonical_key)

    def _select_with_stride(self, candidates: List[DiePoint],
                           target_count: int) -> List[DiePoint]:
        """
        Select points using stride-based sampling.

        Args:
            candidates: Sorted list of candidate points
            target_count: Number of points to select

        Returns:
            List of selected points with uniform spacing
        """
        if not candidates:
            return []

        if target_count >= len(candidates):
            return candidates

        stride = len(candidates) / target_count
        selected = []
        for i in range(target_count):
            index = int(i * stride)
            selected.append(candidates[index])

        return selected

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
            x_mm = point.die_x * die_pitch_x
            y_mm = point.die_y * die_pitch_y
            distance_mm = math.sqrt(x_mm**2 + y_mm**2)

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

        valid_set = {(p.die_x, p.die_y) for p in valid_die_list}

        valid_points = []
        for point in candidates:
            if (point.die_x, point.die_y) in valid_set:
                valid_points.append(point)

        return valid_points

    def _validate_strategy_allowed(self, request: SamplingPreviewRequest) -> None:
        """
        Validate that ZONE_RING_N strategy is allowed for this process context.

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

        # Return first N points (already combined from all rings)
        return valid_candidates[:target_points]
