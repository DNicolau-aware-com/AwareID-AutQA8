"""Version endpoint tests for Face Matcher."""

import allure
import pytest


@allure.feature("Face Matcher API")
@allure.story("Server Health")
@allure.title("GET /nexaface/version returns 200 and a version string")
@allure.severity(allure.severity_level.BLOCKER)
@allure.description(
    "Calls GET /nexaface/version to confirm the Face Matcher service is running. "
    "Expects HTTP 200 and a non-empty version string in the response body."
)
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

    version = response.text
    assert version, "Version should not be empty"

    print(f"[OK] Nexaface (Face Matcher) version: {version}")
    print(version)
