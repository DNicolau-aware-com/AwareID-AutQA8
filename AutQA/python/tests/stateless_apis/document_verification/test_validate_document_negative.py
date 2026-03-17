"""Negative tests for validateDocumentType endpoint."""

import pytest


@pytest.mark.stateless
@pytest.mark.document_verification
def test_validate_document_missing_document_image(api_client, doc_verification_base_path):
    """Missing documentImage field → 400 or 500."""
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/validateDocumentType",
        json={}
    )
    assert response.status_code in [400, 500]
    try:
        error = response.json()
        assert "errorCode" in error
        valid_codes = ["INPUT_FORMAT_ERROR", "INPUT_VALUES_ERROR", "INTERNAL_SERVER_ERROR", "INVALID_INPUT"]
        assert error["errorCode"] in valid_codes, (
            f"Unexpected errorCode '{error['errorCode']}'"
        )
        print(f"\nError: {error['errorCode']} - {error['errorMsg']}")
    except (ValueError, pytest.skip.Exception):
        pass


@pytest.mark.stateless
@pytest.mark.document_verification
def test_validate_document_missing_image_field(api_client, doc_verification_base_path):
    """documentImage present but image field missing → 400 or 500."""
    payload = {
        "documentImage": {
            "lightingScheme": 6,
            "format": ".jpeg"
        }
    }
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/validateDocumentType",
        json=payload
    )
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.document_verification
def test_validate_document_invalid_base64(api_client, doc_verification_base_path):
    """Invalid base64 image data → 400 or 500."""
    payload = {
        "documentImage": {
            "lightingScheme": 6,
            "image": "not_valid_base64_image_data",
            "format": ".jpeg"
        }
    }
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/validateDocumentType",
        json=payload
    )
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.document_verification
def test_validate_document_missing_format(api_client, doc_verification_base_path, document_image_base64):
    """Missing format field — server may accept with default or reject."""
    payload = {
        "documentImage": {
            "lightingScheme": 6,
            "image": document_image_base64
        }
    }
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/validateDocumentType",
        json=payload
    )
    assert response.status_code in [200, 400, 500]
