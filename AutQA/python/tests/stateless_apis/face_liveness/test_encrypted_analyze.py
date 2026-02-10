"""Encrypted analyze endpoint tests."""

import pytest


@pytest.mark.stateless
@pytest.mark.face_liveness
@pytest.mark.encrypted
def test_analyze_encrypted_with_knomi_data(api_client, face_liveness_base_path, face_liveness_data):
    """Test POST /faceliveness/analyzeEncrypted with Knomi-generated data."""
    payload = {
        "key": face_liveness_data["key"],
        "iv": face_liveness_data["iv"],
        "p": face_liveness_data["p"]
    }
    
    response = api_client.http_client.post(
        f"{face_liveness_base_path}/analyzeEncrypted", 
        json=payload
    )
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    result = response.json()
    
    assert "video" in result, "Response should contain video field"
    video = result["video"]
    
    assert "autocapture_result" in video, "Response should contain autocapture_result"
    assert "liveness_result" in video, "Response should contain liveness_result"
    
    if "version" in result:
        print(f"\n? Aware Face Liveness library version: {result['version']}")
        assert isinstance(result["version"], str), "Version should be a string"
    
    print(f"\n? Encrypted analyze successful!")
    print(f"  Autocapture result: {video.get('autocapture_result')}")
    print(f"  Liveness result: {video.get('liveness_result')}")
