"""Negative tests for compare endpoint."""

import pytest


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_compare_missing_probe(api_client, face_matcher_base_path, gallery_face_image):
    """Test compare endpoint with missing probe image."""
    payload = {
        "gallery": {"VISIBLE_FRONTAL": gallery_face_image},
        "workflow": {
            "comparator": {
                "algorithm": "F500",
                "faceTypes": ["VISIBLE_FRONTAL"]
            }
        }
    }
    
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json=payload
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
def test_compare_missing_gallery(api_client, face_matcher_base_path, probe_face_image):
    """Test compare endpoint with missing gallery image."""
    payload = {
        "probe": {"VISIBLE_FRONTAL": probe_face_image},
        "workflow": {
            "comparator": {
                "algorithm": "F500",
                "faceTypes": ["VISIBLE_FRONTAL"]
            }
        }
    }
    
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_compare_missing_workflow(api_client, face_matcher_base_path, probe_face_image, gallery_face_image):
    """Test compare endpoint with missing workflow."""
    payload = {
        "probe": {"VISIBLE_FRONTAL": probe_face_image},
        "gallery": {"VISIBLE_FRONTAL": gallery_face_image}
    }
    
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_compare_invalid_algorithm(api_client, face_matcher_base_path, probe_face_image, gallery_face_image):
    """Test compare endpoint with invalid algorithm."""
    payload = {
        "probe": {"VISIBLE_FRONTAL": probe_face_image},
        "gallery": {"VISIBLE_FRONTAL": gallery_face_image},
        "workflow": {
            "comparator": {
                "algorithm": "INVALID_ALGO",
                "faceTypes": ["VISIBLE_FRONTAL"]
            }
        }
    }
    
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json=payload
    )
    
    assert response.status_code in [400, 500]


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_compare_empty_payload(api_client, face_matcher_base_path):
    """Test compare endpoint with empty payload."""
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json={}
    )
    
    assert response.status_code in [400, 500]
    
    try:
        result = response.json()
        # Face Matcher uses nested error format
        assert "error" in result
        assert "code" in result["error"]
        assert "description" in result["error"]
        print(f"\n? Error for empty payload: {result['error']['description']}")
    except (ValueError, KeyError):
        pass
