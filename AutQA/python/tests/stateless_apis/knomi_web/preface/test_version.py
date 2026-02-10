"""Version endpoint tests for Preface SDK."""

import pytest


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_get_preface_version(api_client, preface_base_path):
    """
    Test GET /b2c/sdk/preface/version.
    
    Retrieves the version number of the Preface SDK server.
    Expected response: Plain text or JSON string with version info.
    """
    response = api_client.http_client.get(
        f"{preface_base_path}/version"
    )
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    # Response might be plain text or JSON
    version = response.text.strip()
    
    # Try to parse as JSON if it looks like JSON
    if version.startswith('"') and version.endswith('"'):
        try:
            import json
            version = json.loads(version)
        except:
            pass
    
    assert len(version) > 0, "Version string should not be empty"
    assert "Aware" in version or "KnomiFaceAnalyzer" in version or "version" in version.lower(), (
        f"Version string should contain 'Aware', 'KnomiFaceAnalyzer', or 'version'. Got: {version}"
    )
    
    print(f"\n? Preface SDK version retrieved successfully!")
    print(f"  Version: {version}")
    
    # Parse version info if possible
    if "version" in version.lower():
        parts = version.split("version")
        if len(parts) > 1:
            version_num = parts[1].strip()
            print(f"  Version Number: {version_num}")


@pytest.mark.stateless
@pytest.mark.knomi_web
@pytest.mark.preface
def test_preface_version_response_format(api_client, preface_base_path):
    """
    Test that /b2c/sdk/preface/version returns proper format.
    
    Validates the response structure and content.
    """
    response = api_client.http_client.get(
        f"{preface_base_path}/version"
    )
    
    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )
    
    # Get response as text
    version = response.text.strip()
    
    # Validate response
    assert len(version) > 0, "Version string should not be empty"
    assert len(version) < 500, f"Version string seems too long: {len(version)} chars"
    
    # Check if it contains expected keywords
    keywords = ["Aware", "Knomi", "FaceAnalyzer", "version", "Library"]
    has_keyword = any(keyword in version for keyword in keywords)
    
    assert has_keyword, (
        f"Version should contain at least one keyword: {keywords}. Got: {version}"
    )
    
    print(f"\n? Preface version response format is valid")
    print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"  Version length: {len(version)} characters")
    print(f"  Version: {version}")
