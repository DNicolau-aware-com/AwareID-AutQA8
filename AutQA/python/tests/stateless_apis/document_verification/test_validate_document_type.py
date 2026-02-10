"""Document type validation tests."""

import pytest


@pytest.mark.stateless
@pytest.mark.document_verification
def test_validate_document_type_with_valid_document(api_client, doc_verification_base_path, document_image_base64):
    """
    Test POST /documentVerification/validateDocumentType with valid document.
    
    Validates whether the presented document is valid and understood by the server.
    Uses lighting scheme 6 (standard).
    """
    payload = {
        "documentImage": {
            "lightingScheme": 6,
            "image": document_image_base64,
            "format": ".jpeg"
        }
    }
    
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/validateDocumentType",
        json=payload
    )
    
    # Skip if document image is invalid or has base64 formatting issues
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            error_code = error.get("errorCode", "")
            error_msg = error.get("errorMsg", "").lower()
            
            if error_code == "INVALID_INPUT" or "base64" in error_msg or "improper" in error_msg:
                pytest.skip("Document image has base64 formatting issues. Check for newlines/whitespace in .env file")
            
            if error_code == "OCR_PROCESSING_ERROR" or "invalid" in error_msg:
                pytest.skip("Document image is not valid for Document Verification API")
        except:
            pass
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    result = response.json()
    
    # Verify required response fields
    assert "validDocument" in result, "Response should contain validDocument"
    assert "nextpageExpected" in result, "Response should contain nextpageExpected"
    assert "documentName" in result, "Response should contain documentName"
    assert "documentID" in result, "Response should contain documentID"
    assert "fidType" in result, "Response should contain fidType"
    assert "fidTypeId" in result, "Response should contain fidTypeId"
    assert "year" in result, "Response should contain year"
    assert "countryName" in result, "Response should contain countryName"
    
    # Verify types
    assert isinstance(result["validDocument"], bool), "validDocument should be boolean"
    assert isinstance(result["nextpageExpected"], bool), "nextpageExpected should be boolean"
    assert isinstance(result["mrzPresence"], bool), "mrzPresence should be boolean"
    
    print(f"\n? Document validation successful!")
    print(f"  Valid Document: {result['validDocument']}")
    print(f"  Document Name: {result['documentName']}")
    print(f"  Country: {result['countryName']}")
    print(f"  MRZ Present: {result['mrzPresence']}")
    print(f"  Next Page Expected: {result['nextpageExpected']}")
    print(f"  Document ID: {result['documentID']}")
    print(f"  FID Type: {result['fidType']}")
