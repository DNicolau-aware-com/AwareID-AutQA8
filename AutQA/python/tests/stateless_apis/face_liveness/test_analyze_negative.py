"""Negative tests for analyze endpoint."""

import pytest


@pytest.mark.stateless
@pytest.mark.face_liveness
def test_analyze_missing_payload(api_client, face_liveness_base_path):
    """Test analyze endpoint with empty payload."""
    response = api_client.http_client.post(f"{face_liveness_base_path}/analyze", json={})
    
    assert response.status_code in [400, 500], (
        f"Expected 400 or 500 for empty payload, got {response.status_code}"
    )
    
    try:
        error = response.json()
        assert "errorCode" in error
        assert "errorMsg" in error
        assert "status" in error
        assert "timestamp" in error
    except ValueError:
        assert response.text, "Response should contain error message"
        print(f"Non-JSON error response: {response.text}")


@pytest.mark.stateless
@pytest.mark.face_liveness
def test_analyze_missing_video_field(api_client, face_liveness_base_path):
    """Test analyze endpoint without video field."""
    payload = {"invalid_field": "test"}
    
    response = api_client.http_client.post(f"{face_liveness_base_path}/analyze", json=payload)
    
    assert response.status_code in [400, 500], (
        f"Expected error for missing video field, got {response.status_code}"
    )
    
    try:
        error = response.json()
        assert error["errorCode"] in ["INPUT_FORMAT_ERROR", "INPUT_VALUES_ERROR", "INTERNAL_SERVER_ERROR"]
    except ValueError:
        assert response.text, "Response should contain error message"


@pytest.mark.stateless
@pytest.mark.face_liveness
def test_analyze_missing_workflow_data(api_client, face_liveness_base_path):
    """Test analyze endpoint with missing workflow_data."""
    payload = {
        "video": {
            "meta_data": {}
        }
    }
    
    response = api_client.http_client.post(f"{face_liveness_base_path}/analyze", json=payload)
    
    assert response.status_code in [400, 500], (
        f"Expected error for missing workflow_data, got {response.status_code}"
    )


@pytest.mark.stateless
@pytest.mark.face_liveness
def test_analyze_invalid_workflow_name(api_client, face_liveness_base_path):
    """Test analyze endpoint with invalid workflow name."""
    payload = {
        "video": {
            "meta_data": {},
            "workflow_data": {
                "workflow": "invalid_workflow_999",
                "frames": []
            }
        }
    }
    
    response = api_client.http_client.post(f"{face_liveness_base_path}/analyze", json=payload)
    
    assert response.status_code in [400, 500], (
        f"Expected error for invalid workflow, got {response.status_code}"
    )


@pytest.mark.stateless
@pytest.mark.face_liveness
def test_analyze_empty_frames(api_client, face_liveness_base_path):
    """Test analyze endpoint with empty frames array."""
    payload = {
        "video": {
            "meta_data": {},
            "workflow_data": {
                "workflow": "charlie4",
                "frames": []
            }
        }
    }
    
    response = api_client.http_client.post(f"{face_liveness_base_path}/analyze", json=payload)
    
    assert response.status_code in [400, 500], (
        f"Expected error for empty frames, got {response.status_code}"
    )
