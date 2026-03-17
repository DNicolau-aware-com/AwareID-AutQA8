"""Negative tests for verifyDocumentsAndBiometrics endpoint."""

import pytest


@pytest.mark.stateless
@pytest.mark.document_verification
def test_verify_missing_documents_info(api_client, doc_verification_base_path, face_image_base64):
    """Missing documentsInfo → 400 or 500."""
    payload = {
        "biometricsInfo": {
            "facialImage": {
                "image": face_image_base64
            }
        }
    }
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/verifyDocumentsAndBiometrics",
        json=payload
    )
    assert response.status_code in [400, 500], (
        f"Expected 400 or 500, got {response.status_code}"
    )


@pytest.mark.stateless
@pytest.mark.document_verification
def test_verify_missing_biometrics_info(api_client, doc_verification_base_path, document_image_base64):
    """Missing biometricsInfo → 400 or 500."""
    payload = {
        "documentsInfo": {
            "documentImage": [
                {
                    "lightingScheme": 6,
                    "image": document_image_base64,
                    "format": ".jpeg"
                }
            ]
        }
    }
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/verifyDocumentsAndBiometrics",
        json=payload
    )
    assert response.status_code in [400, 500], (
        f"Expected 400 or 500, got {response.status_code}"
    )


@pytest.mark.stateless
@pytest.mark.document_verification
def test_verify_empty_payload(api_client, doc_verification_base_path):
    """Empty payload → 400 or 500."""
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/verifyDocumentsAndBiometrics",
        json={}
    )
    assert response.status_code in [400, 500], (
        f"Expected 400 or 500, got {response.status_code}"
    )


@pytest.mark.stateless
@pytest.mark.document_verification
def test_verify_invalid_document_image(api_client, doc_verification_base_path, face_image_base64):
    """Invalid base64 document image → 400 or 500."""
    payload = {
        "documentsInfo": {
            "documentImage": [
                {
                    "lightingScheme": 6,
                    "image": "not_valid_base64",
                    "format": ".jpeg"
                }
            ]
        },
        "biometricsInfo": {
            "facialImage": {
                "image": face_image_base64
            }
        }
    }
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/verifyDocumentsAndBiometrics",
        json=payload
    )
    assert response.status_code in [400, 500], (
        f"Expected 400 or 500, got {response.status_code}"
    )


@pytest.mark.stateless
@pytest.mark.document_verification
def test_verify_invalid_face_image(api_client, doc_verification_base_path, document_image_base64):
    """Invalid base64 face image → 400 or 500."""
    payload = {
        "documentsInfo": {
            "documentImage": [
                {
                    "lightingScheme": 6,
                    "image": document_image_base64,
                    "format": ".jpeg"
                }
            ]
        },
        "biometricsInfo": {
            "facialImage": {
                "image": "not_valid_base64"
            }
        }
    }
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/verifyDocumentsAndBiometrics",
        json=payload
    )
    assert response.status_code in [400, 500], (
        f"Expected 400 or 500, got {response.status_code}"
    )


@pytest.mark.stateless
@pytest.mark.document_verification
def test_verify_missing_facial_image_field(api_client, doc_verification_base_path, document_image_base64):
    """biometricsInfo present but facialImage.image missing → 400 or 500."""
    payload = {
        "documentsInfo": {
            "documentImage": [
                {
                    "lightingScheme": 6,
                    "image": document_image_base64,
                    "format": ".jpeg"
                }
            ]
        },
        "biometricsInfo": {
            "facialImage": {}
        }
    }
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/verifyDocumentsAndBiometrics",
        json=payload
    )
    assert response.status_code in [400, 500], (
        f"Expected 400 or 500, got {response.status_code}"
    )
