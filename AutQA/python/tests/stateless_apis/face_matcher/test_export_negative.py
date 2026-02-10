"""Negative tests for export endpoint."""

import pytest


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_export_missing_encounter(api_client, face_matcher_base_path):
    """Test export endpoint with missing encounter field."""
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/export",
        json={}
    )
    
    assert response.status_code in [400, 500]
    
    try:
        result = response.json()
        # Face Matcher uses nested error format
        assert "error" in result
        assert "code" in result["error"]
        assert "description" in result["error"]
        print(f"\n? Proper error: {result['error']['description']}")
    except (ValueError, KeyError):
        pass


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_export_missing_visible_frontal(api_client, face_matcher_base_path):
    """Test export endpoint with missing VISIBLE_FRONTAL field."""
    payload = {
        "encounter": {
            "id": "test_001"
        }
    }
    
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/export",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_export_invalid_base64(api_client, face_matcher_base_path):
    """Test export endpoint with invalid base64 data."""
    payload = {
        "encounter": {
            "VISIBLE_FRONTAL": "this_is_not_valid_base64_image_data",
            "id": "test_001"
        }
    }
    
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/export",
        json=payload
    )
    
    assert response.status_code in [400, 500]
