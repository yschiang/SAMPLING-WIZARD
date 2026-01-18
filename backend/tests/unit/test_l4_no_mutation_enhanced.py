"""
Enhanced L4 No-Mutation Tests - Critical Architecture Guard

These tests ensure L4 scoring never mutates L3 outputs, which is a 
non-negotiable architecture requirement. L4 must be strictly read-only.
"""

import pytest
import json
import copy
from pathlib import Path
from src.engines.l4.scorer import SamplingScorer
from src.models.base import WaferMapSpec, ValidDieMask, DiePoint
from src.models.catalog import ProcessContext, ToolProfile
from src.models.sampling import SamplingScoreRequest, SamplingOutput, SamplingTrace

# Load golden requests for test data
fixtures_path = Path(__file__).parent.parent / "fixtures" / "golden_requests.json"
with open(fixtures_path, 'r') as f:
    GOLDEN_REQUESTS = json.load(f)


def create_enhanced_score_request():
    """Create a comprehensive test score request."""
    base_request = copy.deepcopy(GOLDEN_REQUESTS["score_request_base"])
    
    # Create models
    wafer_spec = WaferMapSpec(**base_request["wafer_map_spec"])
    process_context = ProcessContext(**base_request["process_context"])
    tool_profile = ToolProfile(**base_request["tool_profile"])
    
    # Create diverse sampling points for comprehensive testing
    selected_points = [
        DiePoint(die_x=0, die_y=0),     # Center
        DiePoint(die_x=2, die_y=0),     # Inner ring
        DiePoint(die_x=-1, die_y=1),    # Inner ring
        DiePoint(die_x=5, die_y=-3),    # Middle ring
        DiePoint(die_x=-4, die_y=6),    # Middle ring
        DiePoint(die_x=10, die_y=-2),   # Outer ring
        DiePoint(die_x=-8, die_y=12),   # Outer ring
        DiePoint(die_x=15, die_y=15),   # Far outer
    ]
    
    sampling_output = SamplingOutput(
        sampling_strategy_id="CENTER_EDGE",
        selected_points=selected_points,
        trace=SamplingTrace(strategy_version="1.0", generated_at="2024-01-01T12:00:00Z")
    )
    
    return SamplingScoreRequest(
        wafer_map_spec=wafer_spec,
        process_context=process_context,
        tool_profile=tool_profile,
        sampling_output=sampling_output
    )


class TestL4NoMutationEnhanced:
    """Enhanced tests for L4 no-mutation invariant with deep validation."""
    
    def test_deep_no_mutation_verification(self):
        """
        Comprehensive deep mutation test with all aspects of sampling output.
        """
        scorer = SamplingScorer()
        request = create_enhanced_score_request()
        
        # Create deep copies for comparison (before scoring)
        wafer_spec_before = copy.deepcopy(request.wafer_map_spec)
        process_context_before = copy.deepcopy(request.process_context) 
        tool_profile_before = copy.deepcopy(request.tool_profile)
        sampling_output_before = copy.deepcopy(request.sampling_output)
        
        # Store object references
        original_selected_points_ref = request.sampling_output.selected_points
        original_sampling_output_ref = request.sampling_output
        
        # Execute scoring multiple times to ensure consistent no-mutation
        result1 = scorer.score_sampling(request)
        result2 = scorer.score_sampling(request)
        result3 = scorer.score_sampling(request)
        
        # Verify object references unchanged
        assert request.sampling_output is original_sampling_output_ref
        assert request.sampling_output.selected_points is original_selected_points_ref
        
        # Verify deep equality after scoring (no field mutations)
        assert request.wafer_map_spec == wafer_spec_before
        assert request.process_context == process_context_before
        assert request.tool_profile == tool_profile_before
        assert request.sampling_output == sampling_output_before
        
        # Verify individual point values unchanged
        for i, (current_point, before_point) in enumerate(zip(
            request.sampling_output.selected_points, 
            sampling_output_before.selected_points
        )):
            assert current_point.die_x == before_point.die_x, f"Point {i} die_x mutated"
            assert current_point.die_y == before_point.die_y, f"Point {i} die_y mutated"
        
        # Verify trace metadata unchanged
        assert request.sampling_output.trace == sampling_output_before.trace
        assert request.sampling_output.sampling_strategy_id == sampling_output_before.sampling_strategy_id
        
        # Verify multiple scoring calls produce identical results
        assert result1 == result2 == result3
        
        print(f"✅ Enhanced L4 no-mutation verified: all objects and values unchanged")
    
    def test_stress_test_no_mutation_with_extreme_inputs(self):
        """
        Stress test with extreme inputs to ensure no edge-case mutations.
        """
        scorer = SamplingScorer()
        
        # Test with extreme point coordinates
        extreme_points = [
            DiePoint(die_x=-1000, die_y=-1000),  # Far negative
            DiePoint(die_x=0, die_y=0),          # Center
            DiePoint(die_x=1000, die_y=1000),    # Far positive
            DiePoint(die_x=999999, die_y=-999999),  # Very extreme
        ]
        
        request = create_enhanced_score_request()
        request.sampling_output.selected_points = extreme_points
        
        # Deep copy for comparison
        extreme_points_before = copy.deepcopy(extreme_points)
        sampling_output_before = copy.deepcopy(request.sampling_output)
        
        # Execute scoring with extreme inputs
        result = scorer.score_sampling(request)
        
        # Verify no mutations occurred even with extreme coordinates
        assert request.sampling_output.selected_points == extreme_points_before
        assert request.sampling_output == sampling_output_before
        
        # Verify individual extreme coordinates unchanged
        for current_point, before_point in zip(request.sampling_output.selected_points, extreme_points_before):
            assert current_point.die_x == before_point.die_x
            assert current_point.die_y == before_point.die_y
        
        print(f"✅ Extreme input no-mutation verified: coordinates preserved")
    
    def test_concurrent_scoring_no_mutation(self):
        """
        Test that concurrent/repeated scoring operations don't cause mutations.
        """
        scorer = SamplingScorer()
        request = create_enhanced_score_request()
        
        # Store initial state
        initial_state = copy.deepcopy(request.sampling_output)
        
        # Run multiple scoring operations
        results = []
        for i in range(5):
            result = scorer.score_sampling(request)
            results.append(result)
            
            # Verify state unchanged after each operation
            assert request.sampling_output == initial_state
        
        # Verify all results are identical (deterministic)
        for i in range(1, len(results)):
            assert results[i] == results[0], f"Result {i} differs from result 0"
        
        print(f"✅ Concurrent scoring no-mutation verified: {len(results)} operations")
    
    def test_no_mutation_with_empty_points(self):
        """
        Test no-mutation behavior with edge case of empty points list.
        """
        scorer = SamplingScorer()
        request = create_enhanced_score_request()
        
        # Set empty points list
        request.sampling_output.selected_points = []
        original_empty_list_ref = request.sampling_output.selected_points
        
        # Store state
        sampling_output_before = copy.deepcopy(request.sampling_output)
        
        # Score with empty points
        result = scorer.score_sampling(request)
        
        # Verify empty list wasn't replaced or mutated
        assert request.sampling_output.selected_points is original_empty_list_ref
        assert request.sampling_output.selected_points == []
        assert request.sampling_output == sampling_output_before
        
        # Verify scoring still works with empty input
        assert result["coverage_score"] == 0.0
        assert result["statistical_score"] == 0.0
        assert result["risk_alignment_score"] == 0.0
        assert result["overall_score"] == 0.0
        assert len(result["warnings"]) > 0
        
        print(f"✅ Empty points no-mutation verified: list reference preserved")
    
    def test_point_object_identity_preservation(self):
        """
        Test that individual DiePoint object identities are preserved.
        """
        scorer = SamplingScorer()
        request = create_enhanced_score_request()
        
        # Store object IDs of individual points
        point_ids_before = [id(point) for point in request.sampling_output.selected_points]
        
        # Execute scoring
        result = scorer.score_sampling(request)
        
        # Verify object IDs are preserved (no new point objects created)
        point_ids_after = [id(point) for point in request.sampling_output.selected_points]
        assert point_ids_before == point_ids_after
        
        # Verify same objects at same indices
        for i, (before_id, after_id) in enumerate(zip(point_ids_before, point_ids_after)):
            assert before_id == after_id, f"Point {i} object identity changed"
        
        print(f"✅ Point object identity preservation verified: {len(point_ids_before)} objects")


def test_l4_architecture_boundary_enforcement():
    """
    Test that enforces the L3/L4 architecture boundary.
    
    L3: Selection (modifies, creates points)
    L4: Evaluation (read-only, never modifies)
    """
    scorer = SamplingScorer()
    request = create_enhanced_score_request()
    
    # Verify L4 has no methods that could mutate L3 outputs
    l4_methods = [method for method in dir(scorer) if not method.startswith('_')]
    mutation_keywords = ['add', 'remove', 'modify', 'update', 'set', 'delete', 'append', 'pop']
    
    for method in l4_methods:
        for keyword in mutation_keywords:
            assert keyword not in method.lower(), f"L4 method '{method}' suggests mutation capability"
    
    # Verify L4 only has scoring-related public methods
    expected_methods = ['score_sampling', 'version']  # Expected public methods/attributes
    actual_public_methods = [m for m in l4_methods if not m.startswith('_')]
    
    for method in actual_public_methods:
        assert method in expected_methods or 'score' in method.lower(), \
               f"Unexpected L4 public method: {method}"
    
    print(f"✅ L3/L4 architecture boundary enforced: L4 is read-only")