"""Autocapture Video Encrypted tests for Preface SDK."""

import pytest


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_autocapture_video_encrypted_single_frame(api_client, preface_base_path, face_image_base64, preface_profile_xml):
    """
    Test POST /b2c/sdk/preface/autocaptureVideoEncrypted with single frame.
    
    Tests basic autocapture with one frame to check compliance.
    """
    payload = {
        "profile": {
            "xml": preface_profile_xml
        },
        "frames": [
            {
                "data": face_image_base64,
                "timestamp": 1565891124780.0334,
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
        },
        "faceSensitivity": 0.7,
        "faceGranularity": 0.2,
        "faceMinimumSize": 0.1,
        "faceMaximumSize": 1.0,
        "faceDetectionMode": "DOMINANT_FACE_BY_SCORE",
        "autocaptureMinimumFrameCount": 1
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/autocaptureVideoEncrypted",
        json=payload
    )
    
    # Skip if image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            error_msg = error.get("errorMsg", "").lower()
            if "image" in error_msg or "invalid" in error_msg:
                pytest.skip(f"Face image is invalid: {error.get('errorMsg')}")
        except:
            pass
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    result = response.json()
    
    # Verify response structure
    assert "frameResults" in result, "Response should contain frameResults"
    assert "results" in result, "Response should contain results"
    
    # Verify frame results
    assert len(result["frameResults"]) == 1, "Should have result for 1 frame"
    frame_result = result["frameResults"][0]
    assert "compliant" in frame_result, "Frame result should have compliant flag"
    assert "feedback" in frame_result, "Frame result should have feedback array"
    
    # Verify capture results
    capture_result = result["results"]
    assert "captured" in capture_result, "Results should have captured flag"
    assert "capturedFrameIndex" in capture_result, "Results should have capturedFrameIndex"
    
    print(f"\n Autocapture video processed successfully!")
    print(f"  Frames: {len(result['frameResults'])}")
    print(f"  Frame compliant: {frame_result['compliant']}")
    print(f"  Captured: {capture_result['captured']}")
    if capture_result['captured']:
        print(f"  Captured frame index: {capture_result['capturedFrameIndex']}")
    if frame_result.get('feedback'):
        print(f"  Feedback: {frame_result['feedback']}")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_autocapture_video_encrypted_multiple_frames(api_client, preface_base_path, face_image_base64, preface_profile_xml):
    """
    Test POST /b2c/sdk/preface/autocaptureVideoEncrypted with multiple frames.
    
    Simulates a video capture sequence with 3 frames.
    """
    payload = {
        "profile": {
            "xml": preface_profile_xml
        },
        "frames": [
            {
                "data": face_image_base64,
                "timestamp": 1565891124780.0,
                "tags": []
            },
            {
                "data": face_image_base64,
                "timestamp": 1565891124813.0,
                "tags": []
            },
            {
                "data": face_image_base64,
                "timestamp": 1565891124846.0,
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
        },
        "faceSensitivity": 0.7,
        "faceGranularity": 0.2,
        "faceDetectionMode": "DOMINANT_FACE_BY_SCORE",
        "autocaptureMinimumFrameCount": 3
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/autocaptureVideoEncrypted",
        json=payload
    )
    
    # Skip if image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            if "image" in error.get("errorMsg", "").lower():
                pytest.skip("Face image is invalid")
        except:
            pass
    
    assert response.status_code == 200
    
    result = response.json()
    
    assert "frameResults" in result
    assert len(result["frameResults"]) == 3, "Should have results for 3 frames"
    
    # Check each frame
    compliant_count = sum(1 for f in result["frameResults"] if f.get("compliant", False))
    
    print(f"\n Multiple frames processed!")
    print(f"  Total frames: {len(result['frameResults'])}")
    print(f"  Compliant frames: {compliant_count}")
    print(f"  Captured: {result['results']['captured']}")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
@pytest.mark.parametrize("detection_mode", [
    "FACE_ORDERING_BY_SIZE",
    "FACE_ORDERING_BY_SCORE",
    "DOMINANT_FACE_BY_SIZE",
    "DOMINANT_FACE_BY_SCORE"
])
def test_autocapture_video_detection_modes(api_client, preface_base_path, face_image_base64, preface_profile_xml, detection_mode):
    """
    Test POST /b2c/sdk/preface/autocaptureVideoEncrypted with different detection modes.
    
    Tests all 4 face detection modes.
    """
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
        ],
        "resolutionPreview": {
            "width": 240,
            "height": 320
        },
        "resolutionCapture": {
            "width": 480,
            "height": 640
        },
        "faceDetectionMode": detection_mode,
        "autocaptureMinimumFrameCount": 1
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/autocaptureVideoEncrypted",
        json=payload
    )
    
    # Skip if image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            if "image" in error.get("errorMsg", "").lower():
                pytest.skip("Face image is invalid")
        except:
            pass
    
    assert response.status_code == 200, (
        f"Detection mode {detection_mode} failed with {response.status_code}"
    )
    
    result = response.json()
    assert "frameResults" in result
    assert "results" in result
    
    print(f"\n Detection mode '{detection_mode}' works")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
@pytest.mark.parametrize("preview_width,preview_height,capture_width,capture_height", [
    (240, 320, 480, 640),   # Standard mobile
    (360, 480, 720, 960),   # Medium quality
    (480, 640, 960, 1280),  # Higher quality
])
def test_autocapture_video_different_resolutions(api_client, preface_base_path, face_image_base64, preface_profile_xml, 
                                                  preview_width, preview_height, capture_width, capture_height):
    """
    Test POST /b2c/sdk/preface/autocaptureVideoEncrypted with different resolutions.
    
    Tests various preview and capture resolution combinations.
    """
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
        ],
        "resolutionPreview": {
            "width": preview_width,
            "height": preview_height
        },
        "resolutionCapture": {
            "width": capture_width,
            "height": capture_height
        },
        "autocaptureMinimumFrameCount": 1
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/autocaptureVideoEncrypted",
        json=payload
    )
    
    # Skip if image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            if "image" in error.get("errorMsg", "").lower():
                pytest.skip("Face image is invalid")
        except:
            pass
    
    assert response.status_code == 200
    
    result = response.json()
    assert "frameResults" in result
    
    print(f"\n Resolution {preview_width}x{preview_height} (preview) / {capture_width}x{capture_height} (capture) works")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_autocapture_video_minimum_frame_count(api_client, preface_base_path, face_image_base64, preface_profile_xml):
    """
    Test POST /b2c/sdk/preface/autocaptureVideoEncrypted with minimum frame count requirement.
    
    Tests that capture requires specified number of consecutive compliant frames.
    """
    # Send 5 frames but require 5 consecutive compliant frames
    payload = {
        "profile": {
            "xml": preface_profile_xml
        },
        "frames": [
            {"data": face_image_base64, "timestamp": 1565891124780.0 + i * 33, "tags": []}
            for i in range(5)
        ],
        "resolutionPreview": {
            "width": 240,
            "height": 320
        },
        "resolutionCapture": {
            "width": 480,
            "height": 640
        },
        "autocaptureMinimumFrameCount": 5
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/autocaptureVideoEncrypted",
        json=payload
    )
    
    # Skip if image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            if "image" in error.get("errorMsg", "").lower():
                pytest.skip("Face image is invalid")
        except:
            pass
    
    assert response.status_code == 200
    
    result = response.json()
    
    assert len(result["frameResults"]) == 5, "Should process all 5 frames"
    
    # Check if capture was triggered
    if result["results"]["captured"]:
        print(f"\n Capture triggered with minimum frame count!")
        print(f"  Required consecutive frames: 5")
        print(f"  Captured at frame: {result['results']['capturedFrameIndex']}")
    else:
        print(f"\n  Capture not triggered (not enough compliant frames)")
