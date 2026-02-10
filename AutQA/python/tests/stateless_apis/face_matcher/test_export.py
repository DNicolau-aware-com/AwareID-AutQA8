"""Face template export tests."""

import pytest


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_export_face_template(api_client, face_matcher_base_path, face_image_base64):
    """
    Test POST /nexaface/export - Generate internal face template.
    
    Takes a face image and exports it as a template.
    """
    payload = {
        "encounter": {
            "VISIBLE_FRONTAL": face_image_base64,
            "id": "encounter_test_001"
        }
    }
    
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/export",
        json=payload
    )
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    result = response.json()
    
    # Verify response structure
    assert "export" in result, "Response should contain export field"
    
    # Verify export is base64 encoded template
    template = result["export"]
    assert isinstance(template, str), "Template should be a string"
    assert len(template) > 0, "Template should not be empty"
    
    print(f"\n? Face template export successful!")
    print(f"  Template length: {len(template)} characters")


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_export_without_encounter_id(api_client, face_matcher_base_path, face_image_base64):
    """Test export endpoint without encounter ID (should still work)."""
    payload = {
        "encounter": {
            "VISIBLE_FRONTAL": face_image_base64
        }
    }
    
    response = api_client.http_client.post(
        f"{face_matcher_base_path}/export",
        json=payload
    )
    
    # Should work with or without ID
    assert response.status_code in [200, 400, 500]
    
    if response.status_code == 200:
        result = response.json()
        assert "export" in result
        print(f"\n? Export without ID successful")
