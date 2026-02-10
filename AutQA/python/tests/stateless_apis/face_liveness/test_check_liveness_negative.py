"""Negative tests for checkLiveness endpoint."""

import pytest


@pytest.mark.stateless
@pytest.mark.face_liveness
def test_check_liveness_missing_payload(api_client, face_liveness_base_path):
    """Test checkLiveness endpoint with empty payload."""
    response = api_client.http_client.post(f"{face_liveness_base_path}/checkLiveness", json={})
    
    assert response.status_code in [400, 500], (
        f"Expected error for empty payload, got {response.status_code}"
    )
    
    try:
        error = response.json()
        assert "errorCode" in error
        assert "errorMsg" in error
    except ValueError:
        assert response.text, "Response should contain error message"


@pytest.mark.stateless
@pytest.mark.face_liveness
def test_check_liveness_invalid_workflow(api_client, face_liveness_base_path):
    """Test checkLiveness endpoint with invalid workflow."""
    payload = {
        "video": {
            "meta_data": {},
            "workflow_data": {
                "workflow": "nonexistent_workflow",
                "frames": []
            }
        }
    }
    
    response = api_client.http_client.post(f"{face_liveness_base_path}/checkLiveness", json=payload)
    
    assert response.status_code in [400, 500]
