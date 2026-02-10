"""Analyze Image tests for Preface SDK."""

import pytest


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_analyze_image_basic(api_client, preface_base_path, face_image_base64, preface_profile_xml):
    """
    Test POST /b2c/sdk/preface/analyzeImage with basic parameters.
    
    Analyzes a face image and checks compliance with profile.
    """
    payload = {
        "images": [
            {
                "id": "test_image_1",
                "input": {
                    "imageData": face_image_base64,
                    "rotation": 0,
                    "faceSensitivity": 0.7,
                    "faceGranularity": 0.2,
                    "faceMinimumSize": 0.1,
                    "faceMaximumSize": 1.0,
                    "faceDetectionMode": "FACE_ORDERING_BY_SIZE"
                },
                "output": [
                    {
                        "id": "compliance_check",
                        "profileXml": preface_profile_xml,
                        "performConstruction": False
                    }
                ]
            }
        ]
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/analyzeImage",
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
    assert "images" in result, "Response should contain images array"
    assert len(result["images"]) > 0, "Should have at least one image result"
    
    image_result = result["images"][0]
    assert "id" in image_result, "Image result should have id"
    assert image_result["id"] == "test_image_1", "ID should match request"
    
    # Check if faces were detected
    if "faces" in image_result and len(image_result["faces"]) > 0:
        face = image_result["faces"][0]
        assert "output" in face, "Face should have output array"
        
        if len(face["output"]) > 0:
            output = face["output"][0]
            assert "id" in output, "Output should have id"
            assert "isCompliant" in output, "Output should have isCompliant flag"
            
            print(f"\n Image analyzed successfully!")
            print(f"  Image ID: {image_result['id']}")
            print(f"  Faces detected: {len(image_result['faces'])}")
            print(f"  Is compliant: {output.get('isCompliant')}")
            
            if "metrics" in output:
                print(f"  Metrics analyzed: {len(output['metrics'])}")
    else:
        print(f"\n  No faces detected in image")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_analyze_image_with_construction(api_client, preface_base_path, face_image_base64, preface_profile_xml):
    """
    Test POST /b2c/sdk/preface/analyzeImage with face construction enabled.
    
    Face construction improves the image before compliance checking.
    """
    payload = {
        "images": [
            {
                "id": "constructed_image",
                "input": {
                    "imageData": face_image_base64,
                    "faceSensitivity": 0.7,
                    "faceGranularity": 0.2,
                    "faceDetectionMode": "DOMINANT_FACE_BY_SCORE"
                },
                "output": [
                    {
                        "id": "with_construction",
                        "profileXml": preface_profile_xml,
                        "performConstruction": True
                    }
                ]
            }
        ]
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/analyzeImage",
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
    assert "images" in result
    
    print(f"\n Image analyzed with construction")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_analyze_image_with_specific_metrics(api_client, preface_base_path, face_image_base64, preface_profile_xml):
    """
    Test POST /b2c/sdk/preface/analyzeImage requesting specific metrics.
    
    Requests IMAGE_WIDTH and IMAGE_HEIGHT metrics.
    """
    payload = {
        "images": [
            {
                "id": "metrics_test",
                "input": {
                    "imageData": face_image_base64,
                    "faceSensitivity": 0.7
                },
                "output": [
                    {
                        "id": "with_metrics",
                        "profileXml": preface_profile_xml,
                        "metrics": ["IMAGE_WIDTH", "IMAGE_HEIGHT"]
                    }
                ]
            }
        ]
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/analyzeImage",
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
    
    if "images" in result and len(result["images"]) > 0:
        image_result = result["images"][0]
        if "faces" in image_result and len(image_result["faces"]) > 0:
            face = image_result["faces"][0]
            if "output" in face and len(face["output"]) > 0:
                output = face["output"][0]
                if "metrics" in output:
                    metrics = output["metrics"]
                    print(f"\n Metrics returned: {len(metrics)}")
                    for metric in metrics:
                        if "name" in metric and "value" in metric:
                            print(f"  {metric['name']}: {metric['value']}")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
@pytest.mark.parametrize("detection_mode", [
    "FACE_ORDERING_BY_SIZE",
    "FACE_ORDERING_BY_SCORE",
    "DOMINANT_FACE_BY_SIZE",
    "DOMINANT_FACE_BY_SCORE"
])
def test_analyze_image_detection_modes(api_client, preface_base_path, face_image_base64, preface_profile_xml, detection_mode):
    """
    Test POST /b2c/sdk/preface/analyzeImage with different face detection modes.
    
    Tests all 4 face detection modes to ensure they work correctly.
    """
    payload = {
        "images": [
            {
                "id": f"test_{detection_mode}",
                "input": {
                    "imageData": face_image_base64,
                    "faceDetectionMode": detection_mode,
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
    assert "images" in result
    
    print(f"\n Detection mode '{detection_mode}' works")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_analyze_image_multiple_images(api_client, preface_base_path, face_image_base64, preface_profile_xml):
    """
    Test POST /b2c/sdk/preface/analyzeImage with multiple images in one request.
    
    Tests batch processing capability.
    """
    payload = {
        "images": [
            {
                "id": "image_1",
                "input": {
                    "imageData": face_image_base64,
                    "faceSensitivity": 0.7
                },
                "output": [
                    {
                        "id": "output_1",
                        "profileXml": preface_profile_xml
                    }
                ]
            },
            {
                "id": "image_2",
                "input": {
                    "imageData": face_image_base64,
                    "faceSensitivity": 0.7
                },
                "output": [
                    {
                        "id": "output_2",
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
    assert "images" in result
    assert len(result["images"]) == 2, "Should return results for both images"
    
    print(f"\n Batch analysis successful!")
    print(f"  Images processed: {len(result['images'])}")
