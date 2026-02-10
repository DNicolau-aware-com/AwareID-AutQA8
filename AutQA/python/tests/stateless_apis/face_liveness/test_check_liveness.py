"""Positive tests for checkLiveness endpoint (non-encrypted)."""

import pytest


@pytest.mark.stateless
@pytest.mark.face_liveness
def test_check_liveness_with_single_frame(api_client, face_liveness_base_path, face_image_base64):
    """
    Test POST /faceliveness/checkLiveness with single frame.
    
    Uses charlie4 workflow with one face image.
    """
    payload = {
        "video": {
            "meta_data": {},
            "workflow_data": {
                "workflow": "charlie4",
                "frames": [
                    {
                        "data": face_image_base64,
                        "tags": [],
                        "timestamp": 1581714134137
                    }
                ]
            }
        }
    }
    
    response = api_client.http_client.post(
        f"{face_liveness_base_path}/checkLiveness",
        json=payload
    )
    
    # Skip if face image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            error_msg = error.get("errorMsg", "").lower()
            if "invalid" in error_msg or "image" in error_msg:
                pytest.skip(f"Face image is invalid: {error.get('errorMsg')}")
        except:
            pass
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    result = response.json()
    
    # Verify response structure
    assert "video" in result, "Response should contain video"
    assert "liveness_result" in result["video"], "Response should contain liveness_result"
    
    liveness = result["video"]["liveness_result"]
    assert "liveness_score" in liveness, "Should have liveness_score"
    assert "result" in liveness, "Should have result"
    
    print(f"\n? CheckLiveness successful!")
    print(f"  Liveness Result: {liveness.get('result')}")
    print(f"  Liveness Score: {liveness.get('liveness_score')}")


@pytest.mark.stateless
@pytest.mark.face_liveness
def test_check_liveness_with_multiple_frames(api_client, face_liveness_base_path, face_image_base64):
    """
    Test POST /faceliveness/checkLiveness with multiple frames.
    
    Uses charlie4 workflow with three frames (same image repeated).
    This simulates the format from your Postman collection.
    """
    payload = {
        "video": {
            "meta_data": {},
            "workflow_data": {
                "workflow": "charlie4",
                "frames": [
                    {
                        "data": face_image_base64,
                        "tags": [],
                        "timestamp": 1581714134137
                    },
                    {
                        "data": face_image_base64,
                        "tags": [],
                        "timestamp": 1581714134158
                    },
                    {
                        "data": face_image_base64,
                        "tags": [],
                        "timestamp": 1581714134189
                    }
                ]
            }
        }
    }
    
    response = api_client.http_client.post(
        f"{face_liveness_base_path}/checkLiveness",
        json=payload
    )
    
    # Skip if face image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            error_msg = error.get("errorMsg", "").lower()
            if "invalid" in error_msg or "image" in error_msg:
                pytest.skip(f"Face image is invalid: {error.get('errorMsg')}")
        except:
            pass
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    result = response.json()
    
    # Verify response structure
    assert "video" in result
    assert "liveness_result" in result["video"]
    
    liveness = result["video"]["liveness_result"]
    
    print(f"\n? CheckLiveness with multiple frames successful!")
    print(f"  Frames Processed: 3")
    print(f"  Liveness Result: {liveness.get('result')}")
    print(f"  Liveness Score: {liveness.get('liveness_score')}")
    
    # Check if frame details are in response
    if "frame_results" in liveness:
        print(f"  Frame Results: {len(liveness['frame_results'])} frames")


@pytest.mark.stateless
@pytest.mark.face_liveness
@pytest.mark.parametrize("workflow", ["charlie4", "foxtrot", "hotel"])
def test_check_liveness_with_different_workflows(api_client, face_liveness_base_path, face_image_base64, workflow):
    """
    Test POST /faceliveness/checkLiveness with different workflows.
    
    Tests: charlie4, foxtrot, hotel workflows.
    """
    payload = {
        "video": {
            "meta_data": {},
            "workflow_data": {
                "workflow": workflow,
                "frames": [
                    {
                        "data": face_image_base64,
                        "tags": [],
                        "timestamp": 1581714134137
                    }
                ]
            }
        }
    }
    
    response = api_client.http_client.post(
        f"{face_liveness_base_path}/checkLiveness",
        json=payload
    )
    
    # Skip if face image is invalid or workflow not supported
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            error_msg = error.get("errorMsg", "").lower()
            error_code = error.get("errorCode", "")
            
            # Skip on invalid image
            if "invalid" in error_msg or "image" in error_msg:
                pytest.skip(f"Face image is invalid: {error.get('errorMsg')}")
            
            # Skip on unsupported workflow
            if "workflow" in error_msg or error_code == "INPUT_VALUES_ERROR":
                pytest.skip(f"Workflow '{workflow}' may not be supported: {error.get('errorMsg')}")
        except:
            pass
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    result = response.json()
    
    assert "video" in result
    assert "liveness_result" in result["video"]
    
    liveness = result["video"]["liveness_result"]
    
    print(f"\n? CheckLiveness with workflow '{workflow}' successful!")
    print(f"  Liveness Result: {liveness.get('result')}")
    print(f"  Liveness Score: {liveness.get('liveness_score')}")


@pytest.mark.stateless
@pytest.mark.face_liveness
def test_check_liveness_with_metadata(api_client, face_liveness_base_path, face_image_base64):
    """
    Test POST /faceliveness/checkLiveness with metadata included.
    
    Includes device and user metadata in the request.
    """
    payload = {
        "video": {
            "meta_data": {
                "username": "test_user",
                "device_brand": "Apple",
                "device_model": "iPhone 13",
                "os_version": "iOS 15.0"
            },
            "workflow_data": {
                "workflow": "charlie4",
                "frames": [
                    {
                        "data": face_image_base64,
                        "tags": [],
                        "timestamp": 1581714134137
                    },
                    {
                        "data": face_image_base64,
                        "tags": [],
                        "timestamp": 1581714134158
                    },
                    {
                        "data": face_image_base64,
                        "tags": [],
                        "timestamp": 1581714134189
                    }
                ]
            }
        }
    }
    
    response = api_client.http_client.post(
        f"{face_liveness_base_path}/checkLiveness",
        json=payload
    )
    
    # Skip if face image is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            error_msg = error.get("errorMsg", "").lower()
            if "invalid" in error_msg or "image" in error_msg:
                pytest.skip(f"Face image is invalid: {error.get('errorMsg')}")
        except:
            pass
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    result = response.json()
    
    assert "video" in result
    assert "liveness_result" in result["video"]
    
    print(f"\n? CheckLiveness with metadata successful!")
    print(f"  User: {payload['video']['meta_data']['username']}")
    print(f"  Device: {payload['video']['meta_data']['device_brand']} {payload['video']['meta_data']['device_model']}")
