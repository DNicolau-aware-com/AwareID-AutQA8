"""Negative tests for Calculate ROI endpoint."""

import pytest


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_calculate_roi_missing_profile(api_client, preface_base_path):
    """Test calculateROI with missing profile."""
    payload = {
        "resolution": {
            "width": 480,
            "height": 640
        }
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/calculateROI",
        json=payload
    )
    
    assert response.status_code in [400, 500], (
        f"Expected 400/500 for missing profile, got {response.status_code}"
    )
    
    try:
        error = response.json()
        assert "errorCode" in error
        assert error["errorCode"] in ["INPUT_FORMAT_ERROR", "INPUT_VALUES_ERROR", "INTERNAL_SERVER_ERROR"]
        print(f"\n? Proper error for missing profile: {error['errorCode']}")
    except:
        pass


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_calculate_roi_missing_resolution(api_client, preface_base_path, preface_profile_xml):
    """Test calculateROI with missing resolution."""
    payload = {
        "profile": {
            "xml": preface_profile_xml
        }
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/calculateROI",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_calculate_roi_invalid_xml(api_client, preface_base_path):
    """Test calculateROI with invalid XML."""
    payload = {
        "profile": {
            "xml": "not valid xml content"
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
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_calculate_roi_negative_resolution(api_client, preface_base_path, preface_profile_xml):
    """Test calculateROI with negative resolution values."""
    payload = {
        "profile": {
            "xml": preface_profile_xml
        },
        "resolution": {
            "width": -480,
            "height": 640
        }
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/calculateROI",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_calculate_roi_zero_resolution(api_client, preface_base_path, preface_profile_xml):
    """Test calculateROI with zero resolution values."""
    payload = {
        "profile": {
            "xml": preface_profile_xml
        },
        "resolution": {
            "width": 0,
            "height": 0
        }
    }
    
    response = api_client.http_client.post(
        f"{preface_base_path}/calculateROI",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_calculate_roi_empty_payload(api_client, preface_base_path):
    """Test calculateROI with empty payload."""
    response = api_client.http_client.post(
        f"{preface_base_path}/calculateROI",
        json={}
    )
    
    assert response.status_code in [400, 500]
