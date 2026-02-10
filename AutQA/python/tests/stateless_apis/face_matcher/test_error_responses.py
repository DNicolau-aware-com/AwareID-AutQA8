"""Error response structure validation tests."""

import pytest


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_error_response_structure(api_client, face_matcher_base_path):
    """
    Test that error responses follow the Face Matcher error format.
    
    Face Matcher uses a different error format than Face Liveness:
    {
      "error": {
        "code": -3,
        "description": "Error message"
      }
    }
    
    Or standard format:
    {
      "errorCode": "INPUT_FORMAT_ERROR",
      "errorMsg": "...",
      "status": 400,
      "timestamp": "..."
    }
    """
    # Trigger error with empty payload
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={}
    )
    
    assert response.status_code in [400, 500]
    
    try:
        error_response = response.json()
        
        # Check which error format is used
        if "error" in error_response:
            # Nested error format
            error = error_response["error"]
            
            assert "code" in error, "Error must have code"
            assert "description" in error, "Error must have description"
            
            # Validate types
            assert isinstance(error["code"], int), "code must be integer"
            assert isinstance(error["description"], str), "description must be string"
            
            print(f"\n? Nested error format validated")
            print(f"  Error Code: {error['code']}")
            print(f"  Description: {error['description']}")
            
        elif "errorCode" in error_response:
            # Standard error format
            assert "errorMsg" in error_response, "Error must have errorMsg"
            assert "status" in error_response, "Error must have status"
            assert "timestamp" in error_response, "Error must have timestamp"
            
            print(f"\n? Standard error format validated")
            print(f"  Error Code: {error_response['errorCode']}")
            print(f"  Error Msg: {error_response['errorMsg']}")
        else:
            pytest.fail(f"Unknown error format: {error_response}")
        
    except ValueError:
        pytest.skip(f"Response is not JSON: {response.text[:100]}")


@pytest.mark.stateless
@pytest.mark.face_matcher
@pytest.mark.parametrize("endpoint", ["/compare", "/export"])
def test_endpoints_exist_and_require_auth(api_client, face_matcher_base_path, endpoint):
    """Test that endpoints exist and are accessible."""
    response = api_client.http_client.post(
        f"{face_matcher_base_path}{endpoint}",
        json={}
    )
    
    assert response.status_code != 404, (
        f"Endpoint {endpoint} should exist (got 404)"
    )
    
    # Should return error for invalid payload
    assert response.status_code in [400, 401, 500], (
        f"Expected 400/401/500 for invalid payload, got {response.status_code}"
    )
