"""
L4 Sampling Scorer Implementation.

Evaluates the quality and adequacy of L3 sampling outputs with respect to:
- Spatial coverage across wafer rings
- Statistical sufficiency for measurement intent
- Risk alignment based on process criticality
- Overall composite score

All scoring is read-only and deterministic.
"""

import math
from typing import List, Dict, Any, Set, Tuple
from ...models.base import DiePoint
from ...models.sampling import SamplingOutput, SamplingScoreRequest, SamplingScoreReport
from ...models.catalog import ProcessContext
from ...server.utils import get_deterministic_timestamp


class SamplingScorer:
    """
    L4 Sampling Scorer - evaluates L3 outputs without mutation.
    
    Implements scoring algorithms for:
    - Coverage Score: Spatial distribution across wafer rings
    - Statistical Score: Adequacy for measurement requirements
    - Risk Alignment Score: Alignment with process criticality
    - Overall Score: Weighted composite of all scores
    """
    
    def __init__(self):
        self.version = "1.0"
    
    def score_sampling(self, request: SamplingScoreRequest) -> Dict[str, Any]:
        """
        Score L3 sampling output for quality and adequacy.
        
        Args:
            request: Scoring request with sampling output and context
            
        Returns:
            Score report dict with all scores and warnings
            
        Note: This method is READ-ONLY and never modifies the input sampling_output
        """
        # Extract key data (read-only)
        sampling_output = request.sampling_output
        process_context = request.process_context
        wafer_spec = request.wafer_map_spec
        
        selected_points = sampling_output.selected_points
        
        # Compute individual scores
        coverage_score = self._compute_coverage_score(selected_points, wafer_spec)
        statistical_score = self._compute_statistical_score(selected_points, process_context)
        risk_alignment_score = self._compute_risk_alignment_score(selected_points, process_context, wafer_spec)
        
        # Compute overall score (weighted average)
        overall_score = self._compute_overall_score(
            coverage_score, statistical_score, risk_alignment_score
        )
        
        # Generate warnings for score issues
        warnings = self._generate_score_warnings(
            selected_points, process_context, coverage_score, 
            statistical_score, risk_alignment_score
        )
        
        return {
            "coverage_score": coverage_score,
            "statistical_score": statistical_score,
            "risk_alignment_score": risk_alignment_score,
            "overall_score": overall_score,
            "warnings": warnings,
            "version": self.version
        }
    
    def _compute_coverage_score(self, selected_points: List[DiePoint], wafer_spec) -> float:
        """
        Compute spatial coverage score based on ring distribution.
        
        Algorithm:
        - Identify which rings (0, 1, 2, 3+) have sampling points
        - Score = rings_hit / max_meaningful_rings
        - Ring 0 = center, Ring 1 = inner, Ring 2 = middle, Ring 3+ = outer
        
        Returns:
            Float between 0.0 and 1.0
        """
        if not selected_points:
            return 0.0
        
        # Calculate wafer radius in die units for ring classification
        wafer_radius_mm = wafer_spec.wafer_size_mm / 2
        die_pitch_x = wafer_spec.die_pitch_x_mm
        die_pitch_y = wafer_spec.die_pitch_y_mm
        
        # Classify points into rings based on distance from center
        rings_hit = set()
        
        for point in selected_points:
            # Convert to mm coordinates
            x_mm = point.die_x * die_pitch_x
            y_mm = point.die_y * die_pitch_y
            
            # Calculate distance from center
            distance_mm = math.sqrt(x_mm**2 + y_mm**2)
            
            # Classify into ring (0=center, 1=inner, 2=middle, 3=outer)
            if distance_mm <= die_pitch_x:  # Essentially center
                ring = 0
            elif distance_mm <= wafer_radius_mm * 0.33:  # Inner third
                ring = 1
            elif distance_mm <= wafer_radius_mm * 0.67:  # Middle third  
                ring = 2
            else:  # Outer third
                ring = 3
            
            rings_hit.add(ring)
        
        # Score based on ring diversity (max meaningful rings = 4)
        max_rings = 4
        coverage_score = len(rings_hit) / max_rings
        
        return min(1.0, coverage_score)
    
    def _compute_statistical_score(self, selected_points: List[DiePoint], process_context: ProcessContext) -> float:
        """
        Compute statistical adequacy score based on sampling requirements.
        
        Algorithm:
        - Score based on how well sampling meets min/max requirements
        - Optimal range: min_sampling_points to max_sampling_points
        - Below min: linear penalty
        - Above min but below max: score = 1.0
        - Above max: no penalty (L3 should handle truncation)
        
        Returns:
            Float between 0.0 and 1.0
        """
        num_points = len(selected_points)
        min_points = process_context.min_sampling_points
        max_points = process_context.max_sampling_points
        
        if num_points >= min_points:
            # Meeting or exceeding minimum requirement
            return 1.0
        else:
            # Below minimum - linear penalty
            # Score drops linearly from 1.0 at min_points to 0.0 at 0 points
            if min_points > 0:
                return num_points / min_points
            else:
                return 1.0  # No minimum requirement
    
    def _compute_risk_alignment_score(self, selected_points: List[DiePoint], 
                                     process_context: ProcessContext, wafer_spec) -> float:
        """
        Compute risk alignment score based on process criticality.
        
        Algorithm:
        - HIGH criticality: Requires good edge coverage (outer ring sampling)
        - MEDIUM criticality: Balanced center/edge coverage
        - LOW criticality: Center-heavy sampling is acceptable
        
        Returns:
            Float between 0.0 and 1.0
        """
        if not selected_points:
            return 0.0
        
        criticality = process_context.criticality
        num_points = len(selected_points)
        
        if criticality == "HIGH":
            return self._score_high_criticality_alignment(selected_points, wafer_spec)
        elif criticality == "MEDIUM":
            return self._score_medium_criticality_alignment(selected_points, wafer_spec)
        else:  # LOW
            return self._score_low_criticality_alignment(selected_points, wafer_spec)
    
    def _score_high_criticality_alignment(self, selected_points: List[DiePoint], wafer_spec) -> float:
        """Score HIGH criticality process - requires strong edge coverage."""
        wafer_radius_mm = wafer_spec.wafer_size_mm / 2
        die_pitch_x = wafer_spec.die_pitch_x_mm
        die_pitch_y = wafer_spec.die_pitch_y_mm
        
        edge_points = 0
        total_points = len(selected_points)
        
        # Count points in outer region (beyond 67% of wafer radius)
        outer_threshold = wafer_radius_mm * 0.67
        
        for point in selected_points:
            x_mm = point.die_x * die_pitch_x
            y_mm = point.die_y * die_pitch_y
            distance_mm = math.sqrt(x_mm**2 + y_mm**2)
            
            if distance_mm > outer_threshold:
                edge_points += 1
        
        # HIGH criticality requires at least 30% edge coverage
        required_edge_ratio = 0.3
        actual_edge_ratio = edge_points / total_points if total_points > 0 else 0
        
        # Also penalize if too few total points for HIGH criticality
        min_points_for_high = 8
        point_adequacy = min(1.0, total_points / min_points_for_high)
        
        # Score = combination of edge coverage and total point adequacy
        edge_score = min(1.0, actual_edge_ratio / required_edge_ratio)
        return (edge_score + point_adequacy) / 2.0
    
    def _score_medium_criticality_alignment(self, selected_points: List[DiePoint], wafer_spec) -> float:
        """Score MEDIUM criticality process - requires balanced coverage."""
        wafer_radius_mm = wafer_spec.wafer_size_mm / 2
        die_pitch_x = wafer_spec.die_pitch_x_mm
        die_pitch_y = wafer_spec.die_pitch_y_mm
        
        center_points = 0
        edge_points = 0
        total_points = len(selected_points)
        
        center_threshold = wafer_radius_mm * 0.33
        edge_threshold = wafer_radius_mm * 0.67
        
        for point in selected_points:
            x_mm = point.die_x * die_pitch_x
            y_mm = point.die_y * die_pitch_y
            distance_mm = math.sqrt(x_mm**2 + y_mm**2)
            
            if distance_mm <= center_threshold:
                center_points += 1
            elif distance_mm > edge_threshold:
                edge_points += 1
        
        # MEDIUM criticality wants balanced distribution
        if total_points == 0:
            return 0.0
        
        center_ratio = center_points / total_points
        edge_ratio = edge_points / total_points
        
        # Ideal balance: some center (20-60%), some edge (15-40%)
        center_score = 1.0 if 0.2 <= center_ratio <= 0.6 else max(0.5, 1.0 - abs(center_ratio - 0.4))
        edge_score = 1.0 if 0.15 <= edge_ratio <= 0.4 else max(0.5, 1.0 - abs(edge_ratio - 0.25))
        
        return (center_score + edge_score) / 2.0
    
    def _score_low_criticality_alignment(self, selected_points: List[DiePoint], wafer_spec) -> float:
        """Score LOW criticality process - center-heavy sampling is fine."""
        # LOW criticality is more forgiving - any reasonable distribution scores well
        total_points = len(selected_points)
        
        if total_points == 0:
            return 0.0
        
        # As long as we have some points, LOW criticality should score reasonably well
        # Slight preference for having at least a few points
        min_reasonable = 3
        if total_points >= min_reasonable:
            return 1.0
        else:
            return 0.7 + (total_points / min_reasonable) * 0.3  # 0.7 to 1.0 range
    
    def _compute_overall_score(self, coverage_score: float, statistical_score: float, 
                              risk_alignment_score: float) -> float:
        """
        Compute weighted overall score.
        
        Weights:
        - Coverage: 30% (spatial distribution importance)
        - Statistical: 40% (meeting sampling requirements is critical)
        - Risk Alignment: 30% (process criticality alignment)
        
        Returns:
            Float between 0.0 and 1.0
        """
        weights = {
            'coverage': 0.3,
            'statistical': 0.4, 
            'risk_alignment': 0.3
        }
        
        overall_score = (
            coverage_score * weights['coverage'] +
            statistical_score * weights['statistical'] +
            risk_alignment_score * weights['risk_alignment']
        )
        
        return min(1.0, max(0.0, overall_score))
    
    def _generate_score_warnings(self, selected_points: List[DiePoint], 
                                process_context: ProcessContext,
                                coverage_score: float, statistical_score: float,
                                risk_alignment_score: float) -> List[str]:
        """
        Generate warnings for scoring issues.
        
        Returns:
            List of warning codes for significant scoring issues
        """
        warnings = []
        num_points = len(selected_points)
        
        # Statistical adequacy warnings
        if statistical_score < 0.8:
            if num_points < process_context.min_sampling_points:
                warnings.append("INSUFFICIENT_SAMPLING_POINTS")
        
        # Coverage warnings
        if coverage_score < 0.5:
            warnings.append("POOR_SPATIAL_COVERAGE")
        
        # Risk alignment warnings
        if risk_alignment_score < 0.7:
            if process_context.criticality == "HIGH":
                warnings.append("HIGH_CRITICALITY_INADEQUATE_COVERAGE")
            else:
                warnings.append("SUBOPTIMAL_RISK_ALIGNMENT")
        
        # Overall quality warnings
        overall_score = self._compute_overall_score(coverage_score, statistical_score, risk_alignment_score)
        if overall_score < 0.6:
            warnings.append("OVERALL_SAMPLING_QUALITY_LOW")
        
        return warnings