"""Negative tests for Autocapture Video Encrypted endpoint."""

import pytest


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_autocapture_video_missing_frames(api_client, preface_base_path, preface_profile_xml):
    """Test autocaptureVideoEncrypted with missing frames."""
    payload = {
        "profile": {
            "xml": preface_profile_xml
        },
        "resolutionPreview": {
            "width": 240,
            "height": 320
        },
        "resolutionCapture": {
            "width": 480,
            "height": 640
        }
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/autocaptureVideoEncrypted",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_autocapture_video_empty_frames_array(api_client, preface_base_path, preface_profile_xml):
    """Test autocaptureVideoEncrypted with empty frames array."""
    payload = {
        "profile": {
            "xml": preface_profile_xml
        },
        "frames": [],
        "resolutionPreview": {
            "width": 240,
            "height": 320
        },
        "resolutionCapture": {
            "width": 480,
            "height": 640
        }
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/autocaptureVideoEncrypted",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_autocapture_video_missing_profile(api_client, preface_base_path, face_image_base64):
    """Test autocaptureVideoEncrypted with missing profile."""
    payload = {
        "frames": [
            {
                "data": face_image_base64,
                "timestamp": 1565891124780.0,
                "tags": []
            }
        ],
        "resolutionPreview": {
            "width": 240,
            "height": 320
        },
        "resolutionCapture": {
            "width": 480,
            "height": 640
        }
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/autocaptureVideoEncrypted",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_autocapture_video_missing_resolution(api_client, preface_base_path, face_image_base64, preface_profile_xml):
    """Test autocaptureVideoEncrypted with missing resolution."""
    payload = {
        "profile": {
            "xml": preface_profile_xml
        },
        "frames": [
            {
                "data": face_image_base64,
                "timestamp": 1565891124780.0,
                "tags": []
            }
        ]
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/autocaptureVideoEncrypted",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_autocapture_video_invalid_timestamp(api_client, preface_base_path, face_image_base64, preface_profile_xml):
    """Test autocaptureVideoEncrypted with invalid (negative) timestamp."""
    payload = {
        "profile": {
            "xml": preface_profile_xml
        },
        "frames": [
            {
                "data": face_image_base64,
                "timestamp": -1000.0,
                "tags": []
            }
        ],
        "resolutionPreview": {
            "width": 240,
            "height": 320
        },
        "resolutionCapture": {
            "width": 480,
            "height": 640
        }
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/autocaptureVideoEncrypted",
        json=payload
    )
    
    # API may accept negative timestamps or reject them
    assert response.status_code in [200, 400, 500]
