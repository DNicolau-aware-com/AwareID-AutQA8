"""Version endpoint tests."""

import pytest


@pytest.mark.stateless
@pytest.mark.face_liveness
def test_get_face_liveness_version(api_client, face_liveness_base_path):
    """Test GET /faceliveness/version endpoint."""
    response = api_client.http_client.get(f"{face_liveness_base_path}/version")
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    version = response.text
    assert version, "Version should not be empty"
    assert len(version) > 0, "Version should contain data"
    
    print(f"? Face Liveness version: {version}")
