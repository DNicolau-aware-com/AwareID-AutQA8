"""Negative tests for encrypted endpoints."""

import pytest


@pytest.mark.stateless
@pytest.mark.face_liveness
@pytest.mark.encrypted
def test_analyze_encrypted_missing_key_field(api_client, face_liveness_base_path):
    """Test analyzeEncrypted with missing key field."""
    payload = {
        "iv": "test_iv",
        "p": "test_p"
    }
    
    response = api_client.http_client.post(
        f"{face_liveness_base_path}/analyzeEncrypted",
        json=payload
    )
    
    assert response.status_code in [400, 500], (
        f"Expected 400 or 500 for missing key, got {response.status_code}"
    )
    
    try:
        error = response.json()
        
        if response.status_code == 400:
            assert "errorCode" in error
            assert error["errorCode"] in ["INPUT_FORMAT_ERROR", "INPUT_VALUES_ERROR"]
            print(f"\n? Proper 400 error returned")
            print(f"  Error Code: {error['errorCode']}")
            print(f"  Error Msg: {error['errorMsg']}")
            
        elif response.status_code == 500:
            assert "errorCode" in error
            assert error["errorCode"] == "INTERNAL_SERVER_ERROR"
            
    except ValueError:
        print(f"\n  Non-JSON error response: {response.text[:200]}")


@pytest.mark.stateless
@pytest.mark.face_liveness
@pytest.mark.encrypted
def test_analyze_encrypted_invalid_encryption_data(api_client, face_liveness_base_path):
    """Test analyzeEncrypted with invalid encryption data."""
    payload = {
        "key": "this_is_not_valid_encrypted_data",
        "iv": "invalid",
        "p": "also_invalid"
    }
    
    response = api_client.http_client.post(
        f"{face_liveness_base_path}/analyzeEncrypted",
        json=payload
    )
    
    assert response.status_code in [400, 500], (
        f"Expected error for invalid encryption data, got {response.status_code}"
    )
    
    try:
        error = response.json()
        assert "errorCode" in error
        assert "errorMsg" in error
        print(f"\n? Proper error returned for invalid encryption")
        print(f"  Error Code: {error['errorCode']}")
        print(f"  Error Msg: {error['errorMsg']}")
    except ValueError:
        print(f"\n  Non-JSON error: {response.text[:200]}")


@pytest.mark.stateless
@pytest.mark.face_liveness
@pytest.mark.encrypted
def test_analyze_encrypted_empty_payload(api_client, face_liveness_base_path):
    """Test analyzeEncrypted with empty payload."""
    response = api_client.http_client.post(
        f"{face_liveness_base_path}/analyzeEncrypted",
        json={}
    )
    
    assert response.status_code in [400, 500], (
        f"Expected error for empty payload, got {response.status_code}"
    )
    
    try:
        error = response.json()
        assert "errorCode" in error
        assert "errorMsg" in error
        assert "status" in error
        assert "timestamp" in error
    except ValueError:
        pass


@pytest.mark.stateless
@pytest.mark.face_liveness
@pytest.mark.encrypted
@pytest.mark.parametrize("missing_field", ["key", "iv", "p"])
def test_encrypted_endpoints_require_all_three_fields(api_client, face_liveness_base_path, missing_field):
    """Test that encrypted endpoints require all three fields: key, iv, and p."""
    full_payload = {"key": "test", "iv": "test", "p": "test"}
    del full_payload[missing_field]
    
    response = api_client.http_client.post(
        f"{face_liveness_base_path}/analyzeEncrypted",
        json=full_payload
    )
    
    assert response.status_code in [400, 500], (
        f"Should reject payload missing '{missing_field}', got {response.status_code}"
    )
    
    try:
        error = response.json()
        assert "errorCode" in error
        print(f"\n? Properly rejected payload missing '{missing_field}'")
        print(f"  Error: {error.get('errorCode')} - {error.get('errorMsg', 'N/A')}")
    except ValueError:
        pass


@pytest.mark.stateless
@pytest.mark.face_liveness
@pytest.mark.encrypted
def test_encrypted_error_codes_match_documentation(api_client, face_liveness_base_path):
    """Test that error responses match documented error code values."""
    response = api_client.http_client.post(
        f"{face_liveness_base_path}/analyzeEncrypted",
        json={"key": "incomplete"}
    )
    
    assert response.status_code in [400, 500]
    
    try:
        error = response.json()
        
        assert "errorCode" in error
        assert "errorMsg" in error
        assert "status" in error
        assert "timestamp" in error
        
        if response.status_code == 400:
            valid_400_codes = ["INPUT_FORMAT_ERROR", "INPUT_VALUES_ERROR"]
            assert error["errorCode"] in valid_400_codes
            print(f"\n? 400 error code validated: {error['errorCode']}")
            
        elif response.status_code == 500:
            assert error["errorCode"] == "INTERNAL_SERVER_ERROR"
            print(f"\n? 500 error code validated: {error['errorCode']}")
        
        print(f"  Full error: {error['errorMsg']}")
        print(f"  Timestamp: {error['timestamp']}")
        
    except ValueError as e:
        pytest.skip(f"Response is not JSON: {response.text[:100]}")


@pytest.mark.stateless
@pytest.mark.face_liveness
@pytest.mark.encrypted
def test_regular_vs_encrypted_payload_formats(api_client, face_liveness_base_path, face_image_base64):
    """Verify that encrypted endpoints reject regular payload format."""
    regular_payload = {
        "video": {
            "meta_data": {"username": "test"},
            "workflow_data": {
                "workflow": "charlie4",
                "frames": [{"image": face_image_base64, "timestamp": 0}]
            }
        }
    }
    
    response = api_client.http_client.post(
        f"{face_liveness_base_path}/analyzeEncrypted",
        json=regular_payload
    )
    
    assert response.status_code in [400, 500], (
        f"Encrypted endpoint must reject regular payload format, got {response.status_code}"
    )
    
    try:
        error = response.json()
        assert "errorCode" in error
        
        if response.status_code == 400:
            assert error["errorCode"] in ["INPUT_FORMAT_ERROR", "INPUT_VALUES_ERROR"]
        
        print(f"\n? Encrypted endpoint properly rejected regular payload format")
        print(f"  Error Code: {error['errorCode']}")
        print(f"  Error Msg: {error.get('errorMsg', 'N/A')}")
        
    except ValueError:
        print(f"\n? Encrypted endpoint rejected regular payload (non-JSON error)")
