"""
Tests for L5 Recipe Translator - coordinate conversion and tool payload generation.

Validates die coordinate conversion, tool constraint enforcement, and recipe generation.
"""

import pytest
import json
import copy
from pathlib import Path
from src.engine.l5.translator import RecipeTranslator
from src.models.base import WaferMapSpec, ValidDieMask, DiePoint, Warning
from src.models.catalog import ProcessContext, ToolProfile, RecipeFormat
from src.models.sampling import SamplingOutput, SamplingTrace
from src.models.recipes import GenerateRecipeRequest, ToolRecipe

# Load golden requests for test data
fixtures_path = Path(__file__).parent.parent / "fixtures" / "golden_requests.json"
with open(fixtures_path, 'r') as f:
    GOLDEN_REQUESTS = json.load(f)


def create_test_recipe_request(selected_points=None, **overrides):
    """Create a test recipe request with optional overrides"""
    base_request = copy.deepcopy(GOLDEN_REQUESTS["recipe_request_base"])
    
    # Apply overrides
    for key, value in overrides.items():
        if key in ["max_points_per_wafer", "edge_die_supported", "ordering_required"]:
            base_request["tool_profile"][key] = value
        elif key in ["wafer_size_mm", "die_pitch_x_mm", "die_pitch_y_mm"]:
            base_request["wafer_map_spec"][key] = value
    
    # Create models
    wafer_spec = WaferMapSpec(**base_request["wafer_map_spec"])
    tool_profile = ToolProfile(**base_request["tool_profile"])
    
    # Create sampling output with provided points
    if selected_points is None:
        selected_points = [
            DiePoint(die_x=0, die_y=0),     # Center
            DiePoint(die_x=2, die_y=1),     # Inner
            DiePoint(die_x=-1, die_y=3),    # Inner
            DiePoint(die_x=5, die_y=-2),    # Middle
            DiePoint(die_x=-4, die_y=6),    # Outer
        ]
    
    sampling_output = SamplingOutput(
        sampling_strategy_id="CENTER_EDGE",
        selected_points=selected_points,
        trace=SamplingTrace(strategy_version="1.0", generated_at="2024-01-01T12:00:00Z")
    )
    
    return GenerateRecipeRequest(
        wafer_map_spec=wafer_spec,
        tool_profile=tool_profile,
        sampling_output=sampling_output
    )


class TestRecipeTranslator:
    """Test the L5 Recipe Translator implementation."""
    
    def test_translator_basic_functionality(self):
        """Test basic translator functionality with valid inputs."""
        translator = RecipeTranslator()
        request = create_test_recipe_request()
        
        result = translator.translate_recipe(request)
        
        # Validate result structure
        assert "tool_recipe" in result
        assert "warnings" in result
        
        tool_recipe = result["tool_recipe"]
        assert isinstance(tool_recipe, ToolRecipe)
        
        # Validate tool recipe fields
        assert hasattr(tool_recipe, 'recipe_id')
        assert hasattr(tool_recipe, 'tool_type')
        assert hasattr(tool_recipe, 'recipe_payload')
        assert hasattr(tool_recipe, 'translation_notes')
        assert hasattr(tool_recipe, 'recipe_format_version')
        
        # Validate payload structure
        payload = tool_recipe.recipe_payload
        assert "measurement_points" in payload
        assert "point_count" in payload
        assert "coordinate_system" in payload
        assert "tool_type" in payload
        
        # Validate measurement points have proper structure
        points = payload["measurement_points"]
        assert len(points) > 0
        for point in points:
            assert "x_mm" in point
            assert "y_mm" in point
            assert "die_x" in point
            assert "die_y" in point
            assert "point_id" in point
        
        print(f"✅ Basic translation: {len(points)} points converted, "
              f"{len(tool_recipe.translation_notes)} notes")
    
    def test_coordinate_conversion_accuracy(self):
        """Test accuracy of die coordinate → mm coordinate conversion."""
        translator = RecipeTranslator()
        
        # Use known die pitch for precise testing
        test_points = [
            DiePoint(die_x=0, die_y=0),     # Should be (0.0, 0.0)
            DiePoint(die_x=1, die_y=0),     # Should be (10.0, 0.0)
            DiePoint(die_x=0, die_y=1),     # Should be (0.0, 10.0)
            DiePoint(die_x=-2, die_y=3),    # Should be (-20.0, 30.0)
        ]
        
        request = create_test_recipe_request(
            selected_points=test_points,
            die_pitch_x_mm=10.0,
            die_pitch_y_mm=10.0
        )
        
        result = translator.translate_recipe(request)
        payload = result["tool_recipe"].recipe_payload
        converted_points = payload["measurement_points"]
        
        # Validate conversions
        assert len(converted_points) == 4
        
        # Check specific conversions
        expected_conversions = [
            (0, 0.0, 0.0),      # die(0,0) → mm(0.0,0.0)
            (1, 10.0, 0.0),     # die(1,0) → mm(10.0,0.0)
            (2, 0.0, 10.0),     # die(0,1) → mm(0.0,10.0)
            (3, -20.0, 30.0),   # die(-2,3) → mm(-20.0,30.0)
        ]
        
        for point_id, expected_x, expected_y in expected_conversions:
            actual_point = converted_points[point_id]
            assert actual_point["x_mm"] == expected_x, f"Point {point_id} x conversion failed"
            assert actual_point["y_mm"] == expected_y, f"Point {point_id} y conversion failed"
            assert actual_point["die_x"] == test_points[point_id].die_x
            assert actual_point["die_y"] == test_points[point_id].die_y
        
        print(f"✅ Coordinate conversion: all {len(converted_points)} points accurate")
    
    def test_tool_constraint_enforcement(self):
        """Test tool constraint enforcement including max points."""
        translator = RecipeTranslator()
        
        # Create request with many points but low tool limit
        many_points = [DiePoint(die_x=i, die_y=0) for i in range(10)]  # 10 points
        
        request = create_test_recipe_request(
            selected_points=many_points,
            max_points_per_wafer=6  # Limit to 6 points
        )
        
        result = translator.translate_recipe(request)
        tool_recipe = result["tool_recipe"]
        payload = tool_recipe.recipe_payload
        
        # Should be truncated to 6 points
        assert len(payload["measurement_points"]) == 6
        assert payload["point_count"] == 6
        
        # Should have truncation note
        truncation_notes = [note for note in tool_recipe.translation_notes 
                           if "truncated" in note.lower()]
        assert len(truncation_notes) > 0
        
        # Should have warning for significant truncation
        warnings = result["warnings"]
        assert "SIGNIFICANT_POINT_TRUNCATION" in warnings
        
        print(f"✅ Tool constraints: {len(many_points)} → {len(payload['measurement_points'])} points")
    
    def test_wafer_boundary_filtering(self):
        """Test wafer boundary constraint filtering.""" 
        translator = RecipeTranslator()
        
        # Create points including some outside wafer boundary
        test_points = [
            DiePoint(die_x=0, die_y=0),     # Center - should be kept
            DiePoint(die_x=2, die_y=2),     # Inner - should be kept  
            DiePoint(die_x=50, die_y=50),   # Far outside - should be filtered
            DiePoint(die_x=30, die_y=30),   # Outside - should be filtered
        ]
        
        request = create_test_recipe_request(
            selected_points=test_points,
            wafer_size_mm=100.0,  # 50mm radius
            die_pitch_x_mm=2.0,
            die_pitch_y_mm=2.0
        )
        
        result = translator.translate_recipe(request)
        tool_recipe = result["tool_recipe"] 
        payload = tool_recipe.recipe_payload
        
        # Should filter out boundary violations
        assert len(payload["measurement_points"]) < len(test_points)
        
        # Should have boundary filtering note
        boundary_notes = [note for note in tool_recipe.translation_notes 
                         if "boundary" in note.lower()]
        assert len(boundary_notes) > 0
        
        print(f"✅ Boundary filtering: {len(test_points)} → {len(payload['measurement_points'])} points")
    
    def test_translation_notes_completeness(self):
        """Test that translation notes provide comprehensive information."""
        translator = RecipeTranslator()
        
        # Create scenario with multiple translation steps
        test_points = [DiePoint(die_x=i, die_y=0) for i in range(8)]
        
        request = create_test_recipe_request(
            selected_points=test_points,
            max_points_per_wafer=5
        )
        
        result = translator.translate_recipe(request)
        notes = result["tool_recipe"].translation_notes
        
        # Should have multiple types of notes
        assert len(notes) >= 2  # At least coordinate conversion + constraint application
        
        # Should have coordinate conversion note
        conversion_notes = [note for note in notes if "converted" in note.lower()]
        assert len(conversion_notes) > 0
        
        # Should have constraint application note with counts
        constraint_notes = [note for note in notes if "kept_count" in note]
        assert len(constraint_notes) > 0
        
        constraint_note = constraint_notes[0]
        assert "dropped_count" in constraint_note
        
        print(f"✅ Translation notes: {len(notes)} comprehensive notes generated")
    
    def test_deterministic_recipe_generation(self):
        """Test that recipe generation is deterministic."""
        import os
        
        # Set deterministic mode for testing
        original_env = os.getenv("TEST_DETERMINISTIC_TIMESTAMPS")
        os.environ["TEST_DETERMINISTIC_TIMESTAMPS"] = "true"
        
        try:
            translator1 = RecipeTranslator()
            translator2 = RecipeTranslator()
            
            request = create_test_recipe_request()
            
            result1 = translator1.translate_recipe(request)
            result2 = translator2.translate_recipe(request)
            
            # Recipe IDs should be identical
            assert result1["tool_recipe"].recipe_id == result2["tool_recipe"].recipe_id
            
            # Payloads should be identical
            payload1 = result1["tool_recipe"].recipe_payload
            payload2 = result2["tool_recipe"].recipe_payload
            assert payload1 == payload2
            
            # Translation notes should be identical
            assert result1["tool_recipe"].translation_notes == result2["tool_recipe"].translation_notes
            
            print(f"✅ Deterministic generation verified")
        
        finally:
            # Restore original environment
            if original_env is None:
                if "TEST_DETERMINISTIC_TIMESTAMPS" in os.environ:
                    del os.environ["TEST_DETERMINISTIC_TIMESTAMPS"]
            else:
                os.environ["TEST_DETERMINISTIC_TIMESTAMPS"] = original_env
    
    def test_tool_payload_format_compliance(self):
        """Test that generated payloads comply with expected tool format."""
        translator = RecipeTranslator()
        request = create_test_recipe_request()
        
        result = translator.translate_recipe(request)
        payload = result["tool_recipe"].recipe_payload
        
        # Validate required payload fields
        required_fields = [
            "tool_type", "vendor", "coordinate_system", "measurement_points",
            "point_count", "wafer_info", "measurement_order", "format_type", "format_version"
        ]
        
        for field in required_fields:
            assert field in payload, f"Missing required payload field: {field}"
        
        # Validate wafer_info structure
        wafer_info = payload["wafer_info"]
        wafer_required = ["wafer_size_mm", "die_pitch_x_mm", "die_pitch_y_mm", "origin"]
        for field in wafer_required:
            assert field in wafer_info, f"Missing wafer_info field: {field}"
        
        # Validate measurement points structure
        points = payload["measurement_points"]
        if points:
            point = points[0]
            point_required = ["point_id", "x_mm", "y_mm", "die_x", "die_y"]
            for field in point_required:
                assert field in point, f"Missing point field: {field}"
        
        print(f"✅ Tool payload format: all required fields present")
    
    def test_empty_points_handling(self):
        """Test translator behavior with empty points list."""
        translator = RecipeTranslator()
        
        request = create_test_recipe_request(selected_points=[])
        result = translator.translate_recipe(request)
        
        tool_recipe = result["tool_recipe"]
        payload = tool_recipe.recipe_payload
        
        # Should handle empty points gracefully
        assert payload["measurement_points"] == []
        assert payload["point_count"] == 0
        
        # Should still have valid recipe structure
        assert tool_recipe.recipe_id is not None
        assert tool_recipe.tool_type is not None
        
        print(f"✅ Empty points handling: graceful empty recipe generation")


class TestL5NoMutation:
    """Test that L5 translator never mutates L3 outputs (critical invariant)."""
    
    def test_no_mutation_of_sampling_output(self):
        """Test that translation never modifies the sampling_output."""
        translator = RecipeTranslator()
        
        # Create request with test points
        request = create_test_recipe_request(selected_points=[
            DiePoint(die_x=0, die_y=0),
            DiePoint(die_x=3, die_y=-2),
            DiePoint(die_x=-5, die_y=7),
        ])
        
        # Store original references and deep copies
        original_sampling_output_ref = request.sampling_output
        original_points_ref = request.sampling_output.selected_points
        sampling_output_copy = copy.deepcopy(request.sampling_output)
        points_copy = copy.deepcopy(request.sampling_output.selected_points)
        
        # Execute translation
        result = translator.translate_recipe(request)
        
        # Verify no mutation of object references
        assert request.sampling_output is original_sampling_output_ref
        assert request.sampling_output.selected_points is original_points_ref
        
        # Verify no mutation of values
        assert request.sampling_output == sampling_output_copy
        assert request.sampling_output.selected_points == points_copy
        
        # Verify individual point values unchanged
        for current_point, original_point in zip(request.sampling_output.selected_points, points_copy):
            assert current_point.die_x == original_point.die_x
            assert current_point.die_y == original_point.die_y
        
        print(f"✅ L5 no-mutation verified: sampling_output unchanged")
    
    def test_no_mutation_concurrent_translations(self):
        """Test that concurrent translations don't cause mutations."""
        import os
        
        # Set deterministic mode for testing
        original_env = os.getenv("TEST_DETERMINISTIC_TIMESTAMPS")
        os.environ["TEST_DETERMINISTIC_TIMESTAMPS"] = "true"
        
        try:
            translator = RecipeTranslator()
            request = create_test_recipe_request()
            
            # Store initial state
            initial_state = copy.deepcopy(request.sampling_output)
            
            # Run multiple translations
            results = []
            for i in range(3):
                result = translator.translate_recipe(request)
                results.append(result)
                
                # Verify state unchanged after each operation
                assert request.sampling_output == initial_state
            
            # Verify all results are identical (deterministic)
            for i in range(1, len(results)):
                assert results[i]["tool_recipe"].recipe_id == results[0]["tool_recipe"].recipe_id
                assert results[i]["tool_recipe"].recipe_payload == results[0]["tool_recipe"].recipe_payload
            
            print(f"✅ Concurrent translation no-mutation verified: {len(results)} operations")
        
        finally:
            # Restore original environment
            if original_env is None:
                if "TEST_DETERMINISTIC_TIMESTAMPS" in os.environ:
                    del os.environ["TEST_DETERMINISTIC_TIMESTAMPS"]
            else:
                os.environ["TEST_DETERMINISTIC_TIMESTAMPS"] = original_env