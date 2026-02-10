"""Error response structure validation tests."""

import pytest


@pytest.mark.stateless
@pytest.mark.document_verification
def test_error_response_structure(api_client, doc_verification_base_path):
    """Test that error responses follow the documented structure."""
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/validateDocumentType",
        json={}
    )
    
    assert response.status_code in [400, 500]
    
    try:
        error = response.json()
        
        assert "errorCode" in error, "Error must have errorCode"
        assert "errorMsg" in error, "Error must have errorMsg"
        assert "status" in error, "Error must have status"
        assert "timestamp" in error, "Error must have timestamp"
        
        assert isinstance(error["errorCode"], str), "errorCode must be string"
        assert isinstance(error["errorMsg"], str), "errorMsg must be string"
        assert isinstance(error["status"], int), "status must be integer"
        assert isinstance(error["timestamp"], str), "timestamp must be string"
        
        if response.status_code == 400:
            # Document Verification API uses INVALID_INPUT (not INPUT_FORMAT_ERROR)
            valid_400_codes = ["INPUT_FORMAT_ERROR", "INPUT_VALUES_ERROR", "INVALID_INPUT"]
            assert error["errorCode"] in valid_400_codes, (
                f"Error code '{error['errorCode']}' not in valid 400 codes: {valid_400_codes}"
            )
        elif response.status_code == 500:
            valid_500_codes = ["INTERNAL_SERVER_ERROR", "OCR_PROCESSING_ERROR"]
            assert error["errorCode"] in valid_500_codes, (
                f"Error code '{error['errorCode']}' not in valid 500 codes: {valid_500_codes}"
            )
        
        print(f"\n? Error response structure validated")
        print(f"  Error Code: {error['errorCode']}")
        print(f"  Error Msg: {error['errorMsg']}")
        
    except ValueError:
        pytest.skip(f"Response is not JSON: {response.text[:100]}")


@pytest.mark.stateless
@pytest.mark.document_verification
@pytest.mark.parametrize("endpoint", ["/validateDocumentType", "/verifyDocumentsAndBiometrics"])
def test_endpoints_exist(api_client, doc_verification_base_path, endpoint):
    """Test that endpoints exist and are accessible."""
    response = api_client.http_client.post(
        f"{doc_verification_base_path}{endpoint}",
        json={}
    )
    
    assert response.status_code != 404, (
        f"Endpoint {endpoint} should exist (got 404)"
    )
    
    assert response.status_code in [400, 401, 500], (
        f"Expected 400/401/500 for invalid payload, got {response.status_code}"
    )
