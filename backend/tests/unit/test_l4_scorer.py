"""
Tests for L4 Sampling Scorer - comprehensive scoring algorithm validation.

Validates coverage, statistical, risk alignment, and overall scoring.
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


def create_test_score_request(selected_points=None, **overrides):
    """Create a test score request with optional overrides"""
    base_request = copy.deepcopy(GOLDEN_REQUESTS["score_request_base"])
    
    # Apply overrides to context
    for key, value in overrides.items():
        if key in ["min_sampling_points", "max_sampling_points", "criticality"]:
            base_request["process_context"][key] = value
        elif key in ["wafer_size_mm", "die_pitch_x_mm", "die_pitch_y_mm"]:
            base_request["wafer_map_spec"][key] = value
    
    # Create models
    wafer_spec = WaferMapSpec(**base_request["wafer_map_spec"])
    process_context = ProcessContext(**base_request["process_context"])
    tool_profile = ToolProfile(**base_request["tool_profile"])
    
    # Create sampling output with provided points
    if selected_points is None:
        selected_points = [
            DiePoint(die_x=0, die_y=0),  # Center
            DiePoint(die_x=1, die_y=0),  # Inner ring
            DiePoint(die_x=0, die_y=1),
            DiePoint(die_x=-1, die_y=0),
            DiePoint(die_x=0, die_y=-1),
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


class TestSamplingScorer:
    """Test the L4 Sampling Scorer implementation."""
    
    def test_scorer_basic_functionality(self):
        """Test basic scorer functionality with valid inputs."""
        scorer = SamplingScorer()
        request = create_test_score_request()
        
        result = scorer.score_sampling(request)
        
        # Validate result structure
        assert "coverage_score" in result
        assert "statistical_score" in result
        assert "risk_alignment_score" in result
        assert "overall_score" in result
        assert "warnings" in result
        assert "version" in result
        
        # Validate score bounds (all scores 0.0 to 1.0)
        assert 0.0 <= result["coverage_score"] <= 1.0
        assert 0.0 <= result["statistical_score"] <= 1.0
        assert 0.0 <= result["risk_alignment_score"] <= 1.0
        assert 0.0 <= result["overall_score"] <= 1.0
        
        # Validate warnings are a list
        assert isinstance(result["warnings"], list)
        
        print(f"✅ Basic scoring: coverage={result['coverage_score']:.2f}, "
              f"statistical={result['statistical_score']:.2f}, "
              f"risk={result['risk_alignment_score']:.2f}, "
              f"overall={result['overall_score']:.2f}")
    
    def test_coverage_score_ring_distribution(self):
        """Test coverage score based on ring distribution."""
        scorer = SamplingScorer()
        
        # Test 1: Only center point - low coverage
        center_only_points = [DiePoint(die_x=0, die_y=0)]
        request = create_test_score_request(selected_points=center_only_points)
        result = scorer._compute_coverage_score(center_only_points, request.wafer_map_spec)
        assert result == 0.25  # 1 ring out of 4 = 0.25
        
        # Test 2: Points in multiple rings - better coverage
        multi_ring_points = [
            DiePoint(die_x=0, die_y=0),   # Ring 0: center
            DiePoint(die_x=2, die_y=0),   # Ring 1: inner
            DiePoint(die_x=8, die_y=0),   # Ring 2: middle  
            DiePoint(die_x=14, die_y=0),  # Ring 3: outer
        ]
        request = create_test_score_request(selected_points=multi_ring_points)
        result = scorer._compute_coverage_score(multi_ring_points, request.wafer_map_spec)
        assert result == 1.0  # 4 rings out of 4 = 1.0
        
        print(f"✅ Coverage scoring: center_only={0.25}, multi_ring={result}")
    
    def test_statistical_score_adequacy(self):
        """Test statistical score based on min/max requirements."""
        scorer = SamplingScorer()
        
        # Test 1: Below minimum points
        few_points = [DiePoint(die_x=0, die_y=0), DiePoint(die_x=1, die_y=0)]
        request = create_test_score_request(
            selected_points=few_points,
            min_sampling_points=5
        )
        result = scorer._compute_statistical_score(few_points, request.process_context)
        assert result == 0.4  # 2/5 = 0.4
        
        # Test 2: Meeting minimum points
        sufficient_points = [DiePoint(die_x=i, die_y=0) for i in range(5)]
        request = create_test_score_request(
            selected_points=sufficient_points,
            min_sampling_points=5
        )
        result = scorer._compute_statistical_score(sufficient_points, request.process_context)
        assert result == 1.0  # Meeting minimum = 1.0
        
        # Test 3: Exceeding minimum points
        excess_points = [DiePoint(die_x=i, die_y=0) for i in range(8)]
        request = create_test_score_request(
            selected_points=excess_points,
            min_sampling_points=5
        )
        result = scorer._compute_statistical_score(excess_points, request.process_context)
        assert result == 1.0  # Exceeding minimum = 1.0
        
        print(f"✅ Statistical scoring: below_min={0.4}, at_min={1.0}, above_min={1.0}")
    
    def test_risk_alignment_criticality_levels(self):
        """Test risk alignment scoring for different criticality levels."""
        scorer = SamplingScorer()
        
        # Common test points - some center, some edge
        test_points = [
            DiePoint(die_x=0, die_y=0),   # Center
            DiePoint(die_x=1, die_y=0),   # Inner
            DiePoint(die_x=10, die_y=0),  # Edge
            DiePoint(die_x=12, die_y=5),  # Edge
            DiePoint(die_x=-10, die_y=8), # Edge
        ]
        
        # Test HIGH criticality (requires good edge coverage)
        high_request = create_test_score_request(
            selected_points=test_points,
            criticality="HIGH"
        )
        high_score = scorer._compute_risk_alignment_score(
            test_points, high_request.process_context, high_request.wafer_map_spec
        )
        
        # Test MEDIUM criticality (balanced coverage)
        medium_request = create_test_score_request(
            selected_points=test_points,
            criticality="MEDIUM"
        )
        medium_score = scorer._compute_risk_alignment_score(
            test_points, medium_request.process_context, medium_request.wafer_map_spec
        )
        
        # Test LOW criticality (forgiving)
        low_request = create_test_score_request(
            selected_points=test_points,
            criticality="LOW"
        )
        low_score = scorer._compute_risk_alignment_score(
            test_points, low_request.process_context, low_request.wafer_map_spec
        )
        
        # Validate scores are reasonable
        assert 0.0 <= high_score <= 1.0
        assert 0.0 <= medium_score <= 1.0
        assert 0.0 <= low_score <= 1.0
        
        # LOW criticality should be most forgiving
        assert low_score >= 0.7  # Should score reasonably well
        
        print(f"✅ Risk alignment: HIGH={high_score:.2f}, MEDIUM={medium_score:.2f}, LOW={low_score:.2f}")
    
    def test_overall_score_weighting(self):
        """Test overall score weighted averaging."""
        scorer = SamplingScorer()
        
        # Test with known individual scores
        coverage = 0.8
        statistical = 0.6 
        risk_alignment = 1.0
        
        overall = scorer._compute_overall_score(coverage, statistical, risk_alignment)
        
        # Expected: 0.8*0.3 + 0.6*0.4 + 1.0*0.3 = 0.24 + 0.24 + 0.30 = 0.78
        expected = 0.78
        assert abs(overall - expected) < 0.01
        
        # Test boundary conditions
        assert scorer._compute_overall_score(0.0, 0.0, 0.0) == 0.0
        assert scorer._compute_overall_score(1.0, 1.0, 1.0) == 1.0
        
        print(f"✅ Overall score weighting: {overall:.2f} (expected {expected:.2f})")
    
    def test_warning_generation(self):
        """Test warning generation for score issues."""
        scorer = SamplingScorer()
        
        # Test case: insufficient points with poor coverage
        insufficient_points = [DiePoint(die_x=0, die_y=0)]  # Only center
        request = create_test_score_request(
            selected_points=insufficient_points,
            min_sampling_points=5,
            criticality="HIGH"
        )
        
        warnings = scorer._generate_score_warnings(
            insufficient_points, request.process_context,
            coverage_score=0.25,  # Poor coverage
            statistical_score=0.2,  # Below min
            risk_alignment_score=0.5  # Poor for HIGH criticality
        )
        
        # Should generate multiple warnings
        assert len(warnings) > 0
        assert any("INSUFFICIENT_SAMPLING_POINTS" in w for w in warnings)
        assert any("POOR_SPATIAL_COVERAGE" in w for w in warnings)
        assert any("HIGH_CRITICALITY_INADEQUATE_COVERAGE" in w for w in warnings)
        
        print(f"✅ Warning generation: {len(warnings)} warnings - {warnings}")
    
    def test_scorer_determinism(self):
        """Test that scorer produces deterministic results."""
        scorer1 = SamplingScorer()
        scorer2 = SamplingScorer()
        
        request = create_test_score_request()
        
        result1 = scorer1.score_sampling(request)
        result2 = scorer2.score_sampling(request)
        
        # All scores should be identical
        assert result1["coverage_score"] == result2["coverage_score"]
        assert result1["statistical_score"] == result2["statistical_score"]
        assert result1["risk_alignment_score"] == result2["risk_alignment_score"]
        assert result1["overall_score"] == result2["overall_score"]
        assert result1["warnings"] == result2["warnings"]
        
        print(f"✅ Deterministic scoring verified")
    
    def test_empty_points_handling(self):
        """Test scorer behavior with empty point list."""
        scorer = SamplingScorer()
        
        request = create_test_score_request(selected_points=[])
        result = scorer.score_sampling(request)
        
        # All scores should be 0.0 for empty points
        assert result["coverage_score"] == 0.0
        assert result["statistical_score"] == 0.0
        assert result["risk_alignment_score"] == 0.0
        assert result["overall_score"] == 0.0
        
        # Should generate warnings
        assert len(result["warnings"]) > 0
        
        print(f"✅ Empty points handling: all scores = 0.0, warnings = {result['warnings']}")


class TestL4NoMutation:
    """Test that L4 scorer never mutates L3 outputs (critical invariant)."""
    
    def test_no_mutation_of_selected_points(self):
        """Test that scoring never modifies the selected_points or individual point values."""
        scorer = SamplingScorer()
        
        # Create request with test points
        request = create_test_score_request(selected_points=[
            DiePoint(die_x=0, die_y=0),
            DiePoint(die_x=5, die_y=3),
            DiePoint(die_x=-2, die_y=7),
        ])
        
        # Store the original points reference and deep copy for comparison
        original_points_ref = request.sampling_output.selected_points
        points_copy_before = copy.deepcopy(request.sampling_output.selected_points)
        sampling_output_copy = copy.deepcopy(request.sampling_output)
        
        # Execute scoring
        result = scorer.score_sampling(request)
        
        # Verify the selected_points list reference didn't change
        assert request.sampling_output.selected_points is original_points_ref
        
        # Verify no mutation occurred in point values
        assert request.sampling_output.selected_points == points_copy_before
        assert request.sampling_output.selected_points == sampling_output_copy.selected_points
        
        # Verify individual point objects weren't modified
        for current_point, before_point in zip(request.sampling_output.selected_points, points_copy_before):
            assert current_point.die_x == before_point.die_x
            assert current_point.die_y == before_point.die_y
        
        # Verify list structure wasn't changed
        assert len(request.sampling_output.selected_points) == len(points_copy_before)
        
        print(f"✅ L4 no-mutation verified: selected_points unchanged")
    
    def test_no_mutation_of_sampling_output_metadata(self):
        """Test that scoring never modifies sampling_output metadata."""
        scorer = SamplingScorer()
        
        request = create_test_score_request()
        
        # Store original values
        original_strategy_id = request.sampling_output.sampling_strategy_id
        original_trace = copy.deepcopy(request.sampling_output.trace)
        
        # Execute scoring
        result = scorer.score_sampling(request)
        
        # Verify metadata unchanged
        assert request.sampling_output.sampling_strategy_id == original_strategy_id
        assert request.sampling_output.trace.strategy_version == original_trace.strategy_version
        assert request.sampling_output.trace.generated_at == original_trace.generated_at
        
        print(f"✅ L4 no-mutation verified: sampling_output metadata unchanged")