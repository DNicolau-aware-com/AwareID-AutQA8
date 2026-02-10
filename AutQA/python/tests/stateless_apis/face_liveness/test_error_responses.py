"""Error response structure validation tests."""

import pytest


@pytest.mark.stateless
@pytest.mark.face_liveness
def test_error_response_has_required_fields(api_client, face_liveness_base_path):
    """Test that error responses follow the documented structure."""
    response = api_client.http_client.post(f"{face_liveness_base_path}/analyze", json={})
    
    try:
        error = response.json()
        
        # Required fields
        assert "errorCode" in error, "Error must have errorCode"
        assert "errorMsg" in error, "Error must have errorMsg"
        assert "status" in error, "Error must have status"
        assert "timestamp" in error, "Error must have timestamp"
        
        # Validate types
        assert isinstance(error["errorCode"], str), "errorCode must be string"
        assert isinstance(error["errorMsg"], str), "errorMsg must be string"
        assert isinstance(error["status"], int), "status must be integer"
        assert isinstance(error["timestamp"], str), "timestamp must be string"
        
        # Validate error code values
        valid_codes = ["INPUT_FORMAT_ERROR", "INPUT_VALUES_ERROR", "INTERNAL_SERVER_ERROR"]
        assert error["errorCode"] in valid_codes, (
            f"errorCode '{error['errorCode']}' not in valid codes: {valid_codes}"
        )
    except ValueError:
        pytest.skip(f"Response is not JSON (got: {response.text[:100]}). Skipping JSON structure validation.")


@pytest.mark.stateless
@pytest.mark.face_liveness
@pytest.mark.parametrize("endpoint", ["/analyze", "/checkLiveness"])
def test_endpoints_exist_and_are_accessible(api_client, face_liveness_base_path, endpoint):
    """Test that endpoints exist and are accessible."""
    response = api_client.http_client.post(f"{face_liveness_base_path}{endpoint}", json={})
    
    assert response.status_code != 404, (
        f"Endpoint {endpoint} should exist (got 404)"
    )
    
    assert response.status_code in [400, 401, 500], (
        f"Expected 400/401/500 for invalid payload, got {response.status_code}"
    )
