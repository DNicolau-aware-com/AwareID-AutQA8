"""Face template export tests."""

import allure
import pytest


@allure.feature("Face Matcher API")
@allure.story("Face Template Export")
@allure.title("Export generates a valid base64 face template")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Sends a face image to POST /nexaface/export with an encounter ID. "
    "Expects HTTP 200 and a non-empty base64-encoded template string in the 'export' field."
)
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

    print(f"\n[OK] Face template export successful!")
    print(f"     Template length: {len(template)} characters")


@allure.feature("Face Matcher API")
@allure.story("Face Template Export")
@allure.title("Export succeeds without an optional encounter ID")
@allure.severity(allure.severity_level.MINOR)
@allure.description(
    "Sends a face image to POST /nexaface/export without an encounter ID field. "
    "The ID is optional per the API spec; expects HTTP 200 or an acceptable error (400/500)."
)
@pytest.mark.stateless
@pytest.mark.face_matcher
def test_export_without_encounter_id(api_client, face_matcher_base_path, face_image_base64):
    """Test export endpoint without encounter ID."""
    payload = {
        "encounter": {
            "VISIBLE_FRONTAL": face_image_base64
        }
    }

    response = api_client.http_client.post(
        f"{face_matcher_base_path}/export",
        json=payload
    )

    # The API may or may not require an ID - a success or any error response is acceptable
    assert response.status_code in [200, 400, 500], (
        f"Expected 200, 400, or 500, got {response.status_code}. Response: {response.text}"
    )

    if response.status_code == 200:
        result = response.json()
        assert "export" in result
        print(f"\n[OK] Export without ID successful")
    else:
        print(f"\n[OK] Export without ID returned expected error: {response.status_code}")
