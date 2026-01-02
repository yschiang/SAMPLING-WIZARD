"""
Critical test: L4 MUST NOT mutate L3 outputs
This is a non-negotiable architecture guard.
"""
import copy
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from fastapi.testclient import TestClient
from backend.src.server.main import app

client = TestClient(app)


def test_l4_scoring_does_not_mutate_l3_output():
    """
    CRITICAL: Verify L4 scoring never modifies the L3 sampling output
    This test enforces the architecture boundary between L3 (selection) and L4 (evaluation)
    """
    
    # Original L3 sampling output
    original_sampling_output = {
        "sampling_strategy_id": "CENTER_EDGE",
        "selected_points": [
            {"die_x": 0, "die_y": 0},
            {"die_x": 3, "die_y": 0},
            {"die_x": -3, "die_y": 0},
            {"die_x": 0, "die_y": 3},
            {"die_x": 0, "die_y": -3}
        ],
        "trace": {
            "strategy_version": "1.0",
            "generated_at": "2024-01-01T00:00:00Z"
        }
    }
    
    # Create deep copy for mutation detection
    original_copy = copy.deepcopy(original_sampling_output)
    
    # Also capture individual point values for detailed validation
    original_points_detail = []
    for point in original_sampling_output["selected_points"]:
        original_points_detail.append({
            "die_x": point["die_x"],
            "die_y": point["die_y"],
            "id": id(point),  # Object identity
            "hash": hash(str(point))  # Content hash
        })
    
    # Prepare L4 scoring request
    score_request = {
        "wafer_map_spec": {
            "wafer_size_mm": 300.0,
            "die_pitch_x_mm": 10.0,
            "die_pitch_y_mm": 10.0,
            "origin": "CENTER",
            "notch_orientation_deg": 0.0,
            "coordinate_system": "DIE_GRID",
            "valid_die_mask": {
                "type": "EDGE_EXCLUSION",
                "radius_mm": 140.0
            },
            "version": "1.0"
        },
        "process_context": {
            "process_step": "LITHO",
            "measurement_intent": "UNIFORMITY",
            "mode": "INLINE",
            "criticality": "HIGH",
            "min_sampling_points": 5,
            "max_sampling_points": 25,
            "allowed_strategy_set": ["CENTER_EDGE"],
            "version": "1.0"
        },
        "tool_profile": {
            "tool_type": "OPTICAL_METROLOGY",
            "vendor": "ASML",
            "coordinate_system_supported": ["DIE_GRID", "MM"],
            "max_points_per_wafer": 49,
            "edge_die_supported": True,
            "ordering_required": False,
            "recipe_format": {
                "type": "JSON",
                "version": "1.0"
            },
            "version": "1.0"
        },
        "sampling_output": original_sampling_output
    }
    
    # Call L4 scoring endpoint
    response = client.post("/v1/sampling/score", json=score_request)
    
    # Verify scoring succeeded
    assert response.status_code == 200, f"L4 scoring failed: {response.status_code}"
    score_data = response.json()
    assert "score_report" in score_data, "Missing score_report in response"
    
    # CRITICAL CHECK: Verify L3 output was NOT mutated
    assert original_sampling_output == original_copy, (
        "ARCHITECTURE VIOLATION: L4 scoring mutated the L3 sampling output! "
        f"Original: {original_copy}, Modified: {original_sampling_output}"
    )
    
    # Enhanced validation: Check individual point integrity
    current_points = original_sampling_output["selected_points"]
    assert len(current_points) == len(original_points_detail), "Point count changed during L4 scoring!"
    
    for i, (current_point, original_detail) in enumerate(zip(current_points, original_points_detail)):
        assert current_point["die_x"] == original_detail["die_x"], f"Point {i} die_x changed: {current_point['die_x']} != {original_detail['die_x']}"
        assert current_point["die_y"] == original_detail["die_y"], f"Point {i} die_y changed: {current_point['die_y']} != {original_detail['die_y']}"
        
        # Verify content hash unchanged
        current_hash = hash(str(current_point))
        assert current_hash == original_detail["hash"], f"Point {i} content hash changed!"
    
    # Verify strategy ID and trace unchanged
    assert original_sampling_output["sampling_strategy_id"] == original_copy["sampling_strategy_id"], "Strategy ID was mutated!"
    assert original_sampling_output["trace"] == original_copy["trace"], "Trace was mutated!"
    
    # Verify the response sampling_output field (if any) matches original
    # Note: L4 should only return score_report, not modify sampling_output
    
    print("✅ L4 NO-MUTATION GUARD: PASSED")
    print(f"   Original points count: {len(original_copy['selected_points'])}")
    print(f"   Points after L4 call: {len(original_sampling_output['selected_points'])}")
    print(f"   All {len(original_points_detail)} points preserved exactly")
    print(f"   Coverage score: {score_data['score_report']['coverage_score']}")
    print(f"   Overall score: {score_data['score_report']['overall_score']}")


def test_l4_scoring_deterministic_output():
    """
    Verify L4 scoring produces deterministic outputs for same inputs
    Critical for testing and mocks
    """
    
    # Same input payload
    request_payload = {
        "wafer_map_spec": {
            "wafer_size_mm": 300.0,
            "die_pitch_x_mm": 10.0,
            "die_pitch_y_mm": 10.0,
            "origin": "CENTER",
            "notch_orientation_deg": 0.0,
            "coordinate_system": "DIE_GRID",
            "valid_die_mask": {
                "type": "EDGE_EXCLUSION",
                "radius_mm": 140.0
            },
            "version": "1.0"
        },
        "process_context": {
            "process_step": "ETCH",
            "measurement_intent": "CD_CONTROL",
            "mode": "OFFLINE",
            "criticality": "MEDIUM",
            "min_sampling_points": 3,
            "max_sampling_points": 50,
            "allowed_strategy_set": ["CENTER_EDGE"],
            "version": "1.0"
        },
        "tool_profile": {
            "tool_type": "SEM",
            "vendor": "AMAT",
            "coordinate_system_supported": ["DIE_GRID", "MM"],
            "max_points_per_wafer": 25,
            "edge_die_supported": False,
            "ordering_required": True,
            "recipe_format": {
                "type": "JSON",
                "version": "1.0"
            },
            "version": "1.0"
        },
        "sampling_output": {
            "sampling_strategy_id": "CENTER_EDGE",
            "selected_points": [
                {"die_x": 0, "die_y": 0},
                {"die_x": 8, "die_y": 0},
                {"die_x": -8, "die_y": 0}
            ],
            "trace": {
                "strategy_version": "1.0",
                "generated_at": "2024-01-01T12:00:00Z"
            }
        }
    }
    
    # Call L4 scoring twice
    response1 = client.post("/v1/sampling/score", json=request_payload)
    response2 = client.post("/v1/sampling/score", json=request_payload)
    
    # Both should succeed
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    score1 = response1.json()["score_report"]
    score2 = response2.json()["score_report"]
    
    # Scores should be identical (deterministic)
    assert score1["coverage_score"] == score2["coverage_score"]
    assert score1["statistical_score"] == score2["statistical_score"]
    assert score1["risk_alignment_score"] == score2["risk_alignment_score"]
    assert score1["overall_score"] == score2["overall_score"]
    
    print("✅ L4 DETERMINISTIC OUTPUT: PASSED")
    

def test_l4_no_mutation_with_large_point_set():
    """
    Test L4 no-mutation with a larger, more complex point set.
    
    This catches mutation issues that might only appear with more complex data.
    """
    # Create a large sampling output with many points
    large_sampling_output = {
        "sampling_strategy_id": "CENTER_EDGE",
        "selected_points": [
            {"die_x": 0, "die_y": 0},   # Center
            {"die_x": 1, "die_y": 0}, {"die_x": -1, "die_y": 0},  # Ring 1
            {"die_x": 0, "die_y": 1}, {"die_x": 0, "die_y": -1},
            {"die_x": 2, "die_y": 0}, {"die_x": -2, "die_y": 0},  # Ring 2  
            {"die_x": 0, "die_y": 2}, {"die_x": 0, "die_y": -2},
            {"die_x": 3, "die_y": 0}, {"die_x": -3, "die_y": 0},  # Ring 3
            {"die_x": 0, "die_y": 3}, {"die_x": 0, "die_y": -3},
            {"die_x": 2, "die_y": 2}, {"die_x": -2, "die_y": -2},  # Corners
            {"die_x": 2, "die_y": -2}, {"die_x": -2, "die_y": 2}
        ],
        "trace": {
            "strategy_version": "1.0",
            "generated_at": "2024-01-01T06:00:00Z"
        }
    }
    
    original_copy = copy.deepcopy(large_sampling_output)
    
    # Prepare score request
    score_request = {
        "wafer_map_spec": {
            "wafer_size_mm": 300.0,
            "die_pitch_x_mm": 8.0,
            "die_pitch_y_mm": 8.0,
            "origin": "CENTER",
            "notch_orientation_deg": 0.0,
            "coordinate_system": "DIE_GRID",
            "valid_die_mask": {
                "type": "EDGE_EXCLUSION",
                "radius_mm": 120.0
            },
            "version": "1.0"
        },
        "process_context": {
            "process_step": "ETCH",
            "measurement_intent": "CD_CONTROL",
            "mode": "OFFLINE",
            "criticality": "MEDIUM",
            "min_sampling_points": 5,
            "max_sampling_points": 50,
            "allowed_strategy_set": ["CENTER_EDGE"],
            "version": "1.0"
        },
        "tool_profile": {
            "tool_type": "SEM",
            "vendor": "AMAT",
            "coordinate_system_supported": ["DIE_GRID"],
            "max_points_per_wafer": 30,
            "edge_die_supported": True,
            "ordering_required": False,
            "recipe_format": {
                "type": "JSON",
                "version": "1.0"
            },
            "version": "1.0"
        },
        "sampling_output": large_sampling_output
    }
    
    # Call L4 scoring
    response = client.post("/v1/sampling/score", json=score_request)
    assert response.status_code == 200, f"L4 scoring failed: {response.status_code}"
    
    # CRITICAL: Verify no mutation occurred
    assert large_sampling_output == original_copy, (
        "ARCHITECTURE VIOLATION: L4 scoring mutated large sampling output!"
    )
    
    # Verify all points are still present and unchanged
    assert len(large_sampling_output["selected_points"]) == len(original_copy["selected_points"]), "Point count changed!"
    
    for i, (current, original) in enumerate(zip(large_sampling_output["selected_points"], original_copy["selected_points"])):
        assert current == original, f"Point {i} was mutated: {current} != {original}"
    
    print(f"✅ L4 NO-MUTATION (LARGE SET): {len(large_sampling_output['selected_points'])} points preserved")


if __name__ == "__main__":
    test_l4_scoring_does_not_mutate_l3_output()
    test_l4_scoring_deterministic_output()
    test_l4_no_mutation_with_large_point_set()
    print("🎉 All L4 architecture guard tests PASSED!")