"""Face comparison tests (1-to-1 matching)."""

import pytest


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_compare_same_person_high_score(api_client, face_matcher_base_path, face_image_base64):
    """
    Test comparing the same person - should get high score.
    
    Uses TX_DL_FACE_B64 for both probe and gallery.
    Expected: High match score (>80%)
    """
    payload = {
        "probe": {"VISIBLE_FRONTAL": face_image_base64},
        "gallery": {"VISIBLE_FRONTAL": face_image_base64},
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
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    result = response.json()
    
    assert "score" in result, "Response should contain score"
    assert "scorePercent" in result, "Response should contain scorePercent"
    
    assert result["scorePercent"] > 80, (
        f"Expected high score for same person, got {result['scorePercent']}%"
    )
    
    print(f"\n? Same person comparison: {result['scorePercent']}% match")
    print(f"  Raw score: {result['score']}")


@pytest.mark.stateless
@pytest.mark.face_matcher
@pytest.mark.parametrize("algorithm", ["F200", "F500"])
def test_compare_with_different_algorithms(api_client, face_matcher_base_path, face_image_base64, algorithm):
    """
    Test compare endpoint with different algorithms.
    
    Supported algorithms: F200, F500
    Note: F200 may not be enabled on all servers.
    """
    payload = {
        "probe": {"VISIBLE_FRONTAL": face_image_base64},
        "gallery": {"VISIBLE_FRONTAL": face_image_base64},
        "workflow": {
            "comparator": {
                "algorithm": algorithm,
                "faceTypes": ["VISIBLE_FRONTAL"]
            }
        }
    }
    
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/compare",
        json=payload
    )
    
    # Check if F200 is not enabled before asserting success
    if response.status_code == 500 and algorithm == "F200":
        try:
            error_data = response.json()
            if "error" in error_data and error_data["error"].get("code") == 113:
                pytest.skip(f"Algorithm {algorithm} is not enabled on this server (error code 113)")
        except (ValueError, KeyError):
            pass
    
    # Now assert - if we get here and it's F200, it means it's a different error
    assert response.status_code == 200, (
        f"Algorithm {algorithm} failed with {response.status_code}: {response.text}"
    )
    
    result = response.json()
    assert "score" in result
    assert "scorePercent" in result
    
    assert result["scorePercent"] > 80, (
        f"Expected high score, got {result['scorePercent']}%"
    )
    
    print(f"\n? Algorithm {algorithm}: {result['scorePercent']}% match")


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_compare_with_metadata(api_client, face_matcher_base_path, face_image_base64):
    """Test compare endpoint with metadata included."""
    payload = {
        "metadata": {
            "username": "test_user",
            "client_device_brand": "Apple",
            "client_device_model": "iPhone 14",
            "client_os_version": "iOS 17.0",
            "client_version": "1.0.0",
            "localization": "en-US",
            "programming_language_version": "Python 3.12"
        },
        "probe": {"VISIBLE_FRONTAL": face_image_base64},
        "gallery": {"VISIBLE_FRONTAL": face_image_base64},
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
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    result = response.json()
    assert "score" in result
    assert "scorePercent" in result
    
    print(f"\n? Comparison with metadata: {result['scorePercent']}%")
