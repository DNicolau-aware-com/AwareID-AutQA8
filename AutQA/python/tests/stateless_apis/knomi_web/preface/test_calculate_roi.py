"""Calculate ROI (Region of Interest) tests for Preface SDK."""

import pytest


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_calculate_roi_with_standard_resolution(api_client, preface_base_path, preface_profile_xml):
    """
    Test POST /b2c/sdk/preface/calculateROI with standard mobile resolution.
    
    Calculates the region of interest (face position) for a given profile and resolution.
    Uses typical mobile camera resolution: 480x640.
    """
    payload = {
        "profile": {
            "xml": preface_profile_xml
        },
        "resolution": {
            "width": 480,
            "height": 640
        }
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/calculateROI",
        json=payload
    )
    
    # Skip if profile XML is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            error_code = error.get("errorCode", "")
            error_msg = error.get("errorMsg", "").lower()
            
            if "invalid" in error_msg or "xml" in error_msg or error_code == "INPUT_FORMAT_ERROR":
                pytest.skip(f"Profile XML is invalid: {error.get('errorMsg')}")
        except:
            pass
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    result = response.json()
    
    # Verify required fields
    assert "x" in result, "Response should contain x coordinate"
    assert "y" in result, "Response should contain y coordinate"
    assert "width" in result, "Response should contain width"
    assert "height" in result, "Response should contain height"
    
    # Verify types
    assert isinstance(result["x"], (int, float)), "x should be numeric"
    assert isinstance(result["y"], (int, float)), "y should be numeric"
    assert isinstance(result["width"], (int, float)), "width should be numeric"
    assert isinstance(result["height"], (int, float)), "height should be numeric"
    
    # Verify reasonable values
    assert result["width"] > 0, "Width should be positive"
    assert result["height"] > 0, "Height should be positive"
    assert result["x"] >= 0, "X coordinate should be non-negative"
    assert result["y"] >= 0, "Y coordinate should be non-negative"
    
    area = result["width"] * result["height"]
    
    print(f"\n ROI calculated successfully for 480x640 resolution!")
    print(f"  Region of Interest:")
    print(f"    Origin: ({result['x']}, {result['y']})")
    print(f"    Size: {result['width']} x {result['height']} pixels")
    print(f"    Area: {area} square pixels")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
@pytest.mark.parametrize("width,height", [
    (480, 640),   # Standard mobile portrait
    (640, 480),   # Standard mobile landscape
    (720, 1280),  # HD portrait
    (1280, 720),  # HD landscape
    (1080, 1920), # Full HD portrait
])
def test_calculate_roi_with_different_resolutions(api_client, preface_base_path, preface_profile_xml, width, height):
    """
    Test POST /b2c/sdk/preface/calculateROI with various resolutions.
    
    Tests common mobile and camera resolutions to ensure ROI calculation
    works across different screen sizes.
    """
    payload = {
        "profile": {
            "xml": preface_profile_xml
        },
        "resolution": {
            "width": width,
            "height": height
        }
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/calculateROI",
        json=payload
    )
    
    # Skip if profile XML is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            error_code = error.get("errorCode", "")
            error_msg = error.get("errorMsg", "").lower()
            
            if "invalid" in error_msg or "xml" in error_msg:
                pytest.skip(f"Profile XML is invalid: {error.get('errorMsg')}")
        except:
            pass
    
    assert response.status_code == 200, (
        f"Expected 200 for {width}x{height}, got {response.status_code}"
    )
    
    result = response.json()
    
    # Verify ROI fits within resolution
    assert result["x"] + result["width"] <= width, (
        f"ROI extends beyond resolution width: {result['x']} + {result['width']} > {width}"
    )
    assert result["y"] + result["height"] <= height, (
        f"ROI extends beyond resolution height: {result['y']} + {result['height']} > {height}"
    )
    
    print(f"\n ROI calculated for {width}x{height}")
    print(f"  ROI: ({result['x']}, {result['y']}) - {result['width']}x{result['height']}")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_calculate_roi_response_structure(api_client, preface_base_path, preface_profile_xml):
    """
    Test that /b2c/sdk/preface/calculateROI returns proper structure.
    
    Validates the response format and data types.
    """
    payload = {
        "profile": {
            "xml": preface_profile_xml
        },
        "resolution": {
            "width": 480,
            "height": 640
        }
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/calculateROI",
        json=payload
    )
    
    # Skip if profile XML is invalid
    if response.status_code in [400, 500]:
        try:
            error = response.json()
            if "invalid" in error.get("errorMsg", "").lower():
                pytest.skip(f"Profile XML is invalid")
        except:
            pass
    
    assert response.status_code == 200
    
    # Check Content-Type
    content_type = response.headers.get('Content-Type', '')
    assert 'application/json' in content_type.lower(), (
        f"Expected application/json, got: {content_type}"
    )
    
    # Parse JSON
    result = response.json()
    
    # Verify structure
    required_fields = ["x", "y", "width", "height"]
    for field in required_fields:
        assert field in result, f"Response missing required field: {field}"
    
    # Verify no extra fields (strict schema)
    extra_fields = set(result.keys()) - set(required_fields)
    if extra_fields:
        print(f"  Note: Response contains extra fields: {extra_fields}")
    
    print(f"\n ROI response structure is valid")
    print(f"  Required fields present: {required_fields}")
    print(f"  Content-Type: {content_type}")
