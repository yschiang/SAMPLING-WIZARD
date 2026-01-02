"""
Determinism Tests - Critical Infrastructure

Ensures all endpoints produce identical outputs for identical inputs.
This is essential for reproducible behavior and reliable testing.
"""
import copy
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from fastapi.testclient import TestClient
from backend.src.server.main import app

client = TestClient(app)

# Load golden fixtures
with open(os.path.join(os.path.dirname(__file__), "../fixtures/golden_requests.json")) as f:
    GOLDEN_REQUESTS = json.load(f)


def normalize_for_determinism_check(response_data):
    """
    Normalize response data for determinism comparison.
    
    Excludes timestamp fields that may vary between calls while preserving
    all other data for strict comparison.
    """
    data = copy.deepcopy(response_data)
    
    # Remove generated_at timestamps from sampling output traces
    if isinstance(data, dict):
        if "sampling_output" in data and "trace" in data["sampling_output"]:
            if "generated_at" in data["sampling_output"]["trace"]:
                del data["sampling_output"]["trace"]["generated_at"]
        
        # Recursively normalize nested objects
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = normalize_for_determinism_check(value)
            elif isinstance(value, list):
                data[key] = [normalize_for_determinism_check(item) if isinstance(item, dict) else item for item in value]
    
    return data


def test_preview_endpoint_determinism():
    """
    Test that /v1/sampling/preview produces identical outputs for identical inputs.
    
    This is critical for reproducible sampling behavior.
    """
    request_payload = GOLDEN_REQUESTS["preview_request"]
    
    # Make multiple calls with identical input
    responses = []
    for i in range(3):
        response = client.post("/v1/sampling/preview", json=request_payload)
        assert response.status_code == 200, f"Preview call {i} failed: {response.status_code}"
        responses.append(response.json())
    
    # Normalize responses for comparison (exclude timestamps)
    normalized_responses = [normalize_for_determinism_check(resp) for resp in responses]
    
    # All normalized responses should be identical
    for i in range(1, len(normalized_responses)):
        assert normalized_responses[0] == normalized_responses[i], (
            f"DETERMINISM FAILURE: Preview call {i} produced different output\n"
            f"First call: {normalized_responses[0]}\n"
            f"Call {i}: {normalized_responses[i]}"
        )
    
    # Verify we got valid sampling output
    assert "sampling_output" in responses[0], "Missing sampling_output in response"
    assert "selected_points" in responses[0]["sampling_output"], "Missing selected_points"
    assert len(responses[0]["sampling_output"]["selected_points"]) > 0, "No points selected"
    
    print(f"✅ PREVIEW DETERMINISM: {len(responses)} identical calls produced same {len(responses[0]['sampling_output']['selected_points'])} points")


def test_score_endpoint_determinism():
    """
    Test that /v1/sampling/score produces identical outputs for identical inputs.
    
    This ensures scoring behavior is reproducible.
    """
    # First get sampling output from preview
    preview_response = client.post("/v1/sampling/preview", json=GOLDEN_REQUESTS["preview_request"])
    assert preview_response.status_code == 200
    sampling_output = preview_response.json()["sampling_output"]
    
    # Build score request
    score_request = copy.deepcopy(GOLDEN_REQUESTS["score_request_base"])
    score_request["sampling_output"] = sampling_output
    
    # Make multiple calls with identical input
    responses = []
    for i in range(3):
        response = client.post("/v1/sampling/score", json=score_request)
        assert response.status_code == 200, f"Score call {i} failed: {response.status_code}"
        responses.append(response.json())
    
    # All responses should be identical (no timestamps to normalize)
    for i in range(1, len(responses)):
        assert responses[0] == responses[i], (
            f"DETERMINISM FAILURE: Score call {i} produced different output\n"
            f"First call: {responses[0]}\n"
            f"Call {i}: {responses[i]}"
        )
    
    # Verify we got valid score report
    assert "score_report" in responses[0], "Missing score_report in response"
    score_report = responses[0]["score_report"]
    
    # Verify score structure and ranges
    required_scores = ["coverage_score", "statistical_score", "risk_alignment_score", "overall_score"]
    for score_field in required_scores:
        assert score_field in score_report, f"Missing {score_field} in score report"
        score_value = score_report[score_field]
        assert 0.0 <= score_value <= 1.0, f"{score_field} should be between 0 and 1, got {score_value}"
    
    print(f"✅ SCORE DETERMINISM: {len(responses)} identical calls produced same scores")


def test_recipe_endpoint_determinism():
    """
    Test that /v1/recipes/generate produces identical outputs for identical inputs.
    
    This ensures recipe generation behavior is reproducible.
    """
    # First get sampling output from preview
    preview_response = client.post("/v1/sampling/preview", json=GOLDEN_REQUESTS["preview_request"])
    assert preview_response.status_code == 200
    sampling_output = preview_response.json()["sampling_output"]
    
    # Build recipe request
    recipe_request = copy.deepcopy(GOLDEN_REQUESTS["recipe_request_base"])
    recipe_request["sampling_output"] = sampling_output
    
    # Make multiple calls with identical input
    responses = []
    for i in range(3):
        response = client.post("/v1/recipes/generate", json=recipe_request)
        assert response.status_code == 200, f"Recipe call {i} failed: {response.status_code}"
        responses.append(response.json())
    
    # All responses should be identical
    for i in range(1, len(responses)):
        assert responses[0] == responses[i], (
            f"DETERMINISM FAILURE: Recipe call {i} produced different output\n"
            f"First call: {responses[0]}\n"
            f"Call {i}: {responses[i]}"
        )
    
    # Verify we got valid tool recipe
    assert "tool_recipe" in responses[0], "Missing tool_recipe in response"
    tool_recipe = responses[0]["tool_recipe"]
    
    required_fields = ["recipe_id", "tool_type", "recipe_payload", "translation_notes", "recipe_format_version"]
    for field in required_fields:
        assert field in tool_recipe, f"Missing {field} in tool recipe"
    
    print(f"✅ RECIPE DETERMINISM: {len(responses)} identical calls produced same recipe")


def test_cross_call_consistency():
    """
    Test that the outputs remain consistent across the full pipeline.
    
    This ensures that preview → score → recipe maintains data consistency.
    """
    request_payload = GOLDEN_REQUESTS["preview_request"]
    
    # Run full pipeline multiple times
    pipeline_results = []
    for i in range(2):
        # Preview
        preview_response = client.post("/v1/sampling/preview", json=request_payload)
        assert preview_response.status_code == 200
        sampling_output = preview_response.json()["sampling_output"]
        
        # Score  
        score_request = copy.deepcopy(GOLDEN_REQUESTS["score_request_base"])
        score_request["sampling_output"] = sampling_output
        score_response = client.post("/v1/sampling/score", json=score_request)
        assert score_response.status_code == 200
        score_report = score_response.json()["score_report"]
        
        # Recipe
        recipe_request = copy.deepcopy(GOLDEN_REQUESTS["recipe_request_base"])
        recipe_request["sampling_output"] = sampling_output
        recipe_response = client.post("/v1/recipes/generate", json=recipe_request)
        assert recipe_response.status_code == 200
        tool_recipe = recipe_response.json()["tool_recipe"]
        
        pipeline_results.append({
            "sampling_output": normalize_for_determinism_check({"sampling_output": sampling_output})["sampling_output"],
            "score_report": score_report,
            "tool_recipe": tool_recipe
        })
    
    # Compare pipeline results
    result1, result2 = pipeline_results
    assert result1["sampling_output"] == result2["sampling_output"], "Sampling outputs differ between pipeline runs"
    assert result1["score_report"] == result2["score_report"], "Score reports differ between pipeline runs"  
    assert result1["tool_recipe"] == result2["tool_recipe"], "Tool recipes differ between pipeline runs"
    
    print("✅ PIPELINE CONSISTENCY: Full preview→score→recipe pipeline is deterministic")


def test_determinism_with_different_inputs():
    """
    Test that different inputs produce different outputs (sanity check).
    
    This ensures our determinism isn't due to static outputs.
    """
    base_request = GOLDEN_REQUESTS["preview_request"]
    
    # Create two different requests
    request1 = copy.deepcopy(base_request)
    request2 = copy.deepcopy(base_request)
    request2["process_context"]["max_sampling_points"] = 8  # Different constraint
    
    # Get responses
    response1 = client.post("/v1/sampling/preview", json=request1)
    response2 = client.post("/v1/sampling/preview", json=request2)
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Normalize responses
    norm_resp1 = normalize_for_determinism_check(response1.json())
    norm_resp2 = normalize_for_determinism_check(response2.json())
    
    # Different inputs should produce different outputs
    assert norm_resp1 != norm_resp2, "Different inputs produced identical outputs (possible static response)"
    
    # But each input should be deterministic when called multiple times
    response1_repeat = client.post("/v1/sampling/preview", json=request1)
    norm_resp1_repeat = normalize_for_determinism_check(response1_repeat.json())
    assert norm_resp1 == norm_resp1_repeat, "Same input produced different outputs on repeat"
    
    print("✅ DETERMINISM SANITY: Different inputs produce different outputs, same inputs produce same outputs")


if __name__ == "__main__":
    test_preview_endpoint_determinism()
    test_score_endpoint_determinism()  
    test_recipe_endpoint_determinism()
    test_cross_call_consistency()
    test_determinism_with_different_inputs()
    print("🎉 All determinism tests PASSED!")