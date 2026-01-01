#!/usr/bin/env python3
"""
Quick test script to verify the FastAPI server works
"""
import sys
sys.path.insert(0, '/Users/johnson.chiang/workspace/sampling-wizard')

from backend.src.server.main import app
from fastapi.testclient import TestClient

# Create test client
client = TestClient(app)

def test_endpoints():
    print("🧪 Testing FastAPI server endpoints...")
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200, f"Health check failed: {response.status_code}"
    print("✅ Health endpoint works")
    
    # Test OpenAPI docs
    response = client.get("/openapi.json")
    assert response.status_code == 200, f"OpenAPI failed: {response.status_code}"
    print("✅ OpenAPI spec is generated")
    
    # Test catalog endpoints
    response = client.get("/v1/catalog/techs")
    assert response.status_code == 200, f"Catalog techs failed: {response.status_code}"
    assert "techs" in response.json(), "Techs response missing 'techs' field"
    print("✅ Catalog techs endpoint works")
    
    response = client.get("/v1/catalog/wafer-maps?tech=28nm")
    assert response.status_code == 200, f"Wafer maps failed: {response.status_code}"
    print("✅ Catalog wafer-maps endpoint works")
    
    # Test sampling preview with minimal valid payload
    preview_payload = {
        "wafer_map_spec": {
            "wafer_size_mm": 300,
            "die_pitch_x_mm": 10,
            "die_pitch_y_mm": 10,
            "origin": "CENTER",
            "notch_orientation_deg": 0,
            "coordinate_system": "DIE_GRID",
            "valid_die_mask": {"type": "EDGE_EXCLUSION", "radius_mm": 140},
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
            "recipe_format": {"type": "JSON", "version": "1.0"},
            "version": "1.0"
        },
        "strategy": {
            "strategy_id": "CENTER_EDGE"
        }
    }
    
    response = client.post("/v1/sampling/preview", json=preview_payload)
    assert response.status_code == 200, f"Sampling preview failed: {response.status_code}"
    data = response.json()
    assert "sampling_output" in data, "Preview response missing 'sampling_output'"
    assert "selected_points" in data["sampling_output"], "Missing 'selected_points'"
    print("✅ Sampling preview endpoint works")
    
    print("\n🎉 All endpoints working correctly!")
    print("✅ Backend scaffold is ready!")

if __name__ == "__main__":
    test_endpoints()