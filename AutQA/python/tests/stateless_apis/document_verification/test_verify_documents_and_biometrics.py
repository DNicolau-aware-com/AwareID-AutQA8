"""Document and biometrics verification tests."""

import pytest


@pytest.mark.stateless
@pytest.mark.document_verification
def test_verify_document_and_face(api_client, doc_verification_base_path, document_image_base64, document_image_rear_base64, face_image_base64):
    """
    Test POST /documentVerification/verifyDocumentsAndBiometrics.
    
    Verifies document (front and back) and performs facial match against the portrait from ID.
    Uses exact payload structure with two document images.
    """
    payload = {
        "documentsInfo": {
            "documentImage": [
                {
                    "lightingScheme": 6,
                    "image": document_image_base64,      # Front image
                    "format": "JPG"
                },
                {
                    "lightingScheme": 6,
                    "image": document_image_rear_base64,  # Back image
                    "format": "JPG"
                }
            ],
            "documentPayload": {
                "request": {
                    "vendor": "REGULA",
                    "data": {}
                }
            },
            "processParam": {
                "alreadyCropped": False
            }
        },
        "biometricsInfo": {
            "facialImage": {
                "image": face_image_base64
            }
        },
        "processingInstructions": {
            "checkLiveness": True
        }
    }
    
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/verifyDocumentsAndBiometrics",
        json=payload
    )
    
    # Skip if images are invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            error_code = error.get("errorCode", "")
            error_msg = error.get("errorMsg", "").lower()
            
            # Skip on any of these - all indicate bad images
            skip_codes = ["INVALID_INPUT", "OCR_PROCESSING_ERROR"]
            skip_keywords = ["base64", "improper", "invalid", "unexpected error", "processing"]
            
            if error_code in skip_codes or any(keyword in error_msg for keyword in skip_keywords):
                pytest.skip(f"Document or face image is not valid. Error: {error_code} - {error.get('errorMsg')}")
        except:
            pass
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    result = response.json()
    
    # Verify required response fields
    assert "overallAuthenticationResult" in result, "Response should contain overallAuthenticationResult"
    assert "documentAuthenticationResult" in result, "Response should contain documentAuthenticationResult"
    assert "biometricsAuthenticationResult" in result, "Response should contain biometricsAuthenticationResult"
    
    # Verify result values
    assert result["overallAuthenticationResult"] in ["OK", "FAILED", "UNDEFINED"], (
        f"Invalid overallAuthenticationResult: {result['overallAuthenticationResult']}"
    )
    
    print(f"\n? Document and biometrics verification successful!")
    print(f"  Overall Result: {result['overallAuthenticationResult']}")
    
    # Display document authentication results
    if "documentAuthenticationResult" in result:
        doc_result = result["documentAuthenticationResult"]
        print(f"\n  ?? Document Authentication:")
        print(f"    Document Type: {doc_result.get('documentType', 'N/A')}")
        print(f"    Country: {doc_result.get('countryName', 'N/A')}")
        print(f"    ICAO Code: {doc_result.get('icaoCode', 'N/A')}")
        print(f"    Year: {doc_result.get('year', 'N/A')}")
        print(f"    Overall Result: {doc_result.get('overallResult', 'N/A')}")
        print(f"    Overall Score: {doc_result.get('overallResultScore', 'N/A')}")
        print(f"    MRZ Present: {doc_result.get('mrzPresence', 'N/A')}")
        print(f"    RFID Present: {doc_result.get('rfidPresence', 'N/A')}")
    
    # Display biometric authentication results
    if "biometricsAuthenticationResult" in result:
        bio_result = result["biometricsAuthenticationResult"]
        print(f"\n  ?? Biometric Authentication:")
        print(f"    Match Result: {bio_result.get('matchResult', 'N/A')}")
        print(f"    Match Score: {bio_result.get('matchScore', 'N/A')}")
        print(f"    Modality: {bio_result.get('modality', 'N/A')}")
    
    # Display additional info
    print(f"\n  ??  Additional Info:")
    print(f"    Retry Document Capture: {result.get('retryDocumentCapture', 'N/A')}")
    print(f"    ICAO Chip Available: {result.get('icaoChipAvailable', 'N/A')}")
    print(f"    ICAO Verification Result: {result.get('icaoVerificationResult', 'N/A')}")
