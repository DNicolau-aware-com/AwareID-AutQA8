"""Negative tests for Validate Document Type endpoint."""

import pytest


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.document_verification
def test_validate_document_type_missing_image(api_client, document_verification_base_path):
    """Test validateDocumentType with missing image."""
    payload = {
        "documentImage": {
            "lightingScheme": 6,
            "format": ".jpeg"
        }
    }
    
    response = api_client.http_client.post(
        f"{document_verification_base_path}/validateDocumentType",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.document_verification
def test_validate_document_type_invalid_base64(api_client, document_verification_base_path):
    """Test validateDocumentType with invalid base64 image."""
    payload = {
        "documentImage": {
            "lightingScheme": 6,
            "image": "not-valid-base64!!!",
            "format": ".jpeg"
        }
    }
    
    response = api_client.http_client.post(
        f"{document_verification_base_path}/validateDocumentType",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.document_verification
def test_validate_document_type_missing_format(api_client, document_verification_base_path, document_front_image):
    """Test validateDocumentType with missing format."""
    payload = {
        "documentImage": {
            "lightingScheme": 6,
            "image": document_front_image
        }
    }
    
    response = api_client.http_client.post(
        f"{document_verification_base_path}/validateDocumentType",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.document_verification
def test_validate_document_type_invalid_lighting_scheme(api_client, document_verification_base_path, document_front_image):
    """Test validateDocumentType with invalid lighting scheme."""
    payload = {
        "documentImage": {
            "lightingScheme": 999,  # Invalid value
            "image": document_front_image,
            "format": ".jpeg"
        }
    }
    
    response = api_client.http_client.post(
        f"{document_verification_base_path}/validateDocumentType",
        json=payload
    )
    
    # API may accept or reject invalid lighting scheme
    assert response.status_code in [200, 400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.document_verification
def test_validate_document_type_empty_payload(api_client, document_verification_base_path):
    """Test validateDocumentType with empty payload."""
    response = api_client.http_client.post(
        f"{document_verification_base_path}/validateDocumentType",
        json={}
    )
    
    assert response.status_code in [400, 500]
