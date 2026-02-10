"""Negative tests for verifyDocumentsAndBiometrics endpoint."""

import pytest


@pytest.mark.stateless
@pytest.mark.document_verification
def test_verify_missing_documents_info(api_client, doc_verification_base_path, face_image_base64):
    """Test verifyDocumentsAndBiometrics with missing documentsInfo."""
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
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.document_verification
def test_verify_missing_biometrics_info(api_client, doc_verification_base_path, document_image_base64):
    """Test verifyDocumentsAndBiometrics with missing biometricsInfo."""
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
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.document_verification
def test_verify_empty_payload(api_client, doc_verification_base_path):
    """Test verifyDocumentsAndBiometrics with empty payload."""
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/verifyDocumentsAndBiometrics",
        json={}
    )
    
    assert response.status_code in [400, 500]
    
    try:
        error = response.json()
        assert "errorCode" in error
        assert "errorMsg" in error
    except ValueError:
        pass


@pytest.mark.stateless
@pytest.mark.document_verification
def test_verify_invalid_workflow(api_client, doc_verification_base_path, document_image_base64, face_image_base64):
    """Test verifyDocumentsAndBiometrics with invalid workflow."""
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
                "image": face_image_base64
            }
        },
        "processingInstructions": {
            "documentValidationRules": {
                "workflow": "invalid_workflow_999"
            }
        }
    }
    
    response = api_client.http_client.post(
        f"{doc_verification_base_path}/verifyDocumentsAndBiometrics",
        json=payload
    )
    
    assert response.status_code in [400, 500]
