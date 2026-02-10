"""Negative tests for Analyze Image endpoint."""

import pytest


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_analyze_image_missing_image_data(api_client, preface_base_path, preface_profile_xml):
    """Test analyzeImage with missing imageData."""
    payload = {
        "images": [
            {
                "id": "test",
                "input": {
                    "faceSensitivity": 0.7
                },
                "output": [
                    {
                        "id": "output_1",
                        "profileXml": preface_profile_xml
                    }
                ]
            }
        ]
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/analyzeImage",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_analyze_image_invalid_base64(api_client, preface_base_path, preface_profile_xml):
    """Test analyzeImage with invalid base64 image data."""
    payload = {
        "images": [
            {
                "id": "test",
                "input": {
                    "imageData": "not-valid-base64!!!",
                    "faceSensitivity": 0.7
                },
                "output": [
                    {
                        "id": "output_1",
                        "profileXml": preface_profile_xml
                    }
                ]
            }
        ]
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/analyzeImage",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_analyze_image_empty_images_array(api_client, preface_base_path):
    """Test analyzeImage with empty images array."""
    payload = {
        "images": []
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/analyzeImage",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_analyze_image_invalid_detection_mode(api_client, preface_base_path, face_image_base64, preface_profile_xml):
    """Test analyzeImage with invalid faceDetectionMode."""
    payload = {
        "images": [
            {
                "id": "test",
                "input": {
                    "imageData": face_image_base64,
                    "faceDetectionMode": "INVALID_MODE"
                },
                "output": [
                    {
                        "id": "output_1",
                        "profileXml": preface_profile_xml
                    }
                ]
            }
        ]
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/analyzeImage",
        json=payload
    )
    
    assert response.status_code in [400, 500]
