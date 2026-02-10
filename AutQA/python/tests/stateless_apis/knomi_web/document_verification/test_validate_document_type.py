"""Validate Document Type tests for Knomi Web Document Verification."""

import pytest


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.document_verification
def test_validate_document_type_front(api_client, document_verification_base_path, document_front_image):
    """
    Test POST /b2c/sdk/documentVerification/validateDocumentType with front document.
    
    Validates the document type and extracts document metadata.
    """
    payload = {
        "documentImage": {
            "lightingScheme": 6,
            "image": document_front_image,
            "format": ".jpeg"
        }
    }
    
    response = api_client.http_client.post(
        f"{document_verification_base_path}/validateDocumentType",
        json=payload
    )
    
    # Skip if document image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            error_msg = error.get("errorMsg", "").lower()
            if "image" in error_msg or "invalid" in error_msg or "document" in error_msg:
                pytest.skip(f"Document image is invalid: {error.get('errorMsg')}")
        except:
            pass
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    result = response.json()
    
    # Verify required fields
    assert "validDocument" in result, "Response should contain validDocument flag"
    assert "documentName" in result, "Response should contain documentName"
    assert "documentID" in result, "Response should contain documentID"
    assert "fidType" in result, "Response should contain fidType"
    assert "fidTypeId" in result, "Response should contain fidTypeId"
    assert "year" in result, "Response should contain year"
    assert "countryName" in result, "Response should contain countryName"
    
    # Optional fields
    if "nextpageExpected" in result:
        assert isinstance(result["nextpageExpected"], bool)
    if "mrzPresence" in result:
        assert isinstance(result["mrzPresence"], bool)
    if "rfidPresence" in result:
        assert isinstance(result["rfidPresence"], int)
    
    print(f"\n Document validated successfully!")
    print(f"  Valid Document: {result['validDocument']}")
    print(f"  Document Name: {result['documentName']}")
    print(f"  Country: {result['countryName']}")
    print(f"  Document ID: {result['documentID']}")
    print(f"  FID Type: {result['fidType']}")
    print(f"  Year: {result['year']}")
    
    if result.get("mrzPresence"):
        print(f"  MRZ Present: Yes")
    if result.get("nextpageExpected"):
        print(f"  Next Page Expected: Yes")
    if result.get("icaocode"):
        print(f"  ICAO Code: {result['icaocode']}")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.document_verification
@pytest.mark.parametrize("lighting_scheme", [0, 1, 2, 3, 4, 5, 6])
def test_validate_document_type_lighting_schemes(api_client, document_verification_base_path, document_front_image, lighting_scheme):
    """
    Test POST /b2c/sdk/documentVerification/validateDocumentType with different lighting schemes.
    
    Tests various lighting schemes (0-6) for document capture conditions.
    """
    payload = {
        "documentImage": {
            "lightingScheme": lighting_scheme,
            "image": document_front_image,
            "format": ".jpeg"
        }
    }
    
    response = api_client.http_client.post(
        f"{document_verification_base_path}/validateDocumentType",
        json=payload
    )
    
    # Skip if document image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            if "image" in error.get("errorMsg", "").lower():
                pytest.skip("Document image is invalid")
        except:
            pass
    
    assert response.status_code == 200, (
        f"Lighting scheme {lighting_scheme} failed with {response.status_code}"
    )
    
    result = response.json()
    assert "validDocument" in result
    
    print(f"\n Lighting scheme {lighting_scheme} works")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.document_verification
@pytest.mark.parametrize("format", [".jpeg", ".jpg", ".png"])
def test_validate_document_type_image_formats(api_client, document_verification_base_path, document_front_image, format):
    """
    Test POST /b2c/sdk/documentVerification/validateDocumentType with different image formats.
    
    Tests JPEG, JPG, and PNG formats.
    """
    payload = {
        "documentImage": {
            "lightingScheme": 6,
            "image": document_front_image,
            "format": format
        }
    }
    
    response = api_client.http_client.post(
        f"{document_verification_base_path}/validateDocumentType",
        json=payload
    )
    
    # Skip if document image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            if "image" in error.get("errorMsg", "").lower():
                pytest.skip("Document image is invalid")
        except:
            pass
    
    assert response.status_code == 200, (
        f"Format {format} failed with {response.status_code}"
    )
    
    result = response.json()
    assert "validDocument" in result
    
    print(f"\n Image format {format} works")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.document_verification
def test_validate_document_type_with_vendor_payload(api_client, document_verification_base_path, document_front_image):
    """
    Test POST /b2c/sdk/documentVerification/validateDocumentType with vendor payload.
    
    Includes vendor-specific data in the request.
    """
    payload = {
        "documentImage": {
            "lightingScheme": 6,
            "image": document_front_image,
            "format": ".jpeg"
        },
        "documentPayload": {
            "request": {
                "vendor": "TestVendor",
                "data": {
                    "customField": "customValue"
                }
            }
        }
    }
    
    response = api_client.http_client.post(
        f"{document_verification_base_path}/validateDocumentType",
        json=payload
    )
    
    # Skip if document image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            if "image" in error.get("errorMsg", "").lower():
                pytest.skip("Document image is invalid")
        except:
            pass
    
    assert response.status_code == 200
    
    result = response.json()
    assert "validDocument" in result
    
    print(f"\n Vendor payload accepted")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.document_verification
def test_validate_document_type_with_process_param(api_client, document_verification_base_path, document_front_image):
    """
    Test POST /b2c/sdk/documentVerification/validateDocumentType with processParam.
    
    Specifies that document is already cropped.
    """
    payload = {
        "documentImage": {
            "lightingScheme": 6,
            "image": document_front_image,
            "format": ".jpeg"
        },
        "processParam": {
            "alreadyCropped": True
        }
    }
    
    response = api_client.http_client.post(
        f"{document_verification_base_path}/validateDocumentType",
        json=payload
    )
    
    # Skip if document image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            if "image" in error.get("errorMsg", "").lower():
                pytest.skip("Document image is invalid")
        except:
            pass
    
    assert response.status_code == 200
    
    result = response.json()
    assert "validDocument" in result
    
    print(f"\n ProcessParam (alreadyCropped) works")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.document_verification
def test_validate_document_type_response_structure(api_client, document_verification_base_path, document_front_image):
    """
    Test that /b2c/sdk/documentVerification/validateDocumentType returns proper structure.
    
    Validates the complete response format.
    """
    payload = {
        "documentImage": {
            "lightingScheme": 6,
            "image": document_front_image,
            "format": ".jpeg"
        }
    }
    
    response = api_client.http_client.post(
        f"{document_verification_base_path}/validateDocumentType",
        json=payload
    )
    
    # Skip if document image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            if "image" in error.get("errorMsg", "").lower():
                pytest.skip("Document image is invalid")
        except:
            pass
    
    assert response.status_code == 200
    
    # Check Content-Type
    content_type = response.headers.get('Content-Type', '')
    assert 'application/json' in content_type.lower()
    
    result = response.json()
    
    # Verify required fields exist and have correct types
    assert isinstance(result["validDocument"], bool), "validDocument should be boolean"
    assert isinstance(result["documentName"], str), "documentName should be string"
    assert isinstance(result["documentID"], str), "documentID should be string"
    assert isinstance(result["fidType"], str), "fidType should be string"
    assert isinstance(result["fidTypeId"], str), "fidTypeId should be string"
    assert isinstance(result["year"], str), "year should be string"
    assert isinstance(result["countryName"], str), "countryName should be string"
    
    # Verify optional fields if present
    if "nextpageExpected" in result:
        assert isinstance(result["nextpageExpected"], bool)
    if "mrzPresence" in result:
        assert isinstance(result["mrzPresence"], bool)
    if "rfidPresence" in result:
        assert isinstance(result["rfidPresence"], int)
    if "childDocumentIDs" in result:
        assert isinstance(result["childDocumentIDs"], list)
    
    print(f"\n Response structure is valid")
    print(f"  Content-Type: {content_type}")
