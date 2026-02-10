"""Version endpoint tests for Face Matcher."""

import pytest


@pytest.mark.stateless
@pytest.mark.face_matcher
def test_get_nexaface_version(api_client, face_matcher_base_path):
    """
    Test GET /nexaface/version endpoint.
    
    Version of Knomi FaceMatcher. Check if the server is alive.
    Returns the version of Knomi FaceMatcher.
    """
    response = api_client.http_client.get(f"{face_matcher_base_path}/version")
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    # Version should be returned as plain text
    version = response.text
    assert version, "Version should not be empty"
    assert len(version) > 0, "Version should contain data"
    
    print(f"? Nexaface (Face Matcher) version: {version}")
