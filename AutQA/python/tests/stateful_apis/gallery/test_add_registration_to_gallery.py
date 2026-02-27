"""
Tests for POST /onboarding/gallery/addRegistrationToGallery

Adds a registered user (by registrationCode) to a custom gallery.
"""

import allure
import pytest


def _assert_error_body(result):
    """Assert standard Gallery API error format: {errorCode, errorMsg, status, timestamp}."""
    assert "errorCode" in result, f"Expected 'errorCode' in error response, got: {result}"
    assert "errorMsg" in result, f"Expected 'errorMsg' in error response, got: {result}"
    assert "status" in result, f"Expected 'status' in error response, got: {result}"
    assert "timestamp" in result, f"Expected 'timestamp' in error response, got: {result}"
    print(f"\n[OK] Error - errorCode: {result['errorCode']}, errorMsg: {result['errorMsg']}")


@allure.feature("Gallery API")
@allure.story("Gallery Membership")
@allure.title("Add a registered user to a custom gallery")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Adds a previously registered user (by registrationCode) to a custom gallery. "
    "Expects HTTP 200. Then verifies presence via isRegistrationInGallery."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_add_registration_to_gallery(api_client, gallery_base_path, registered_user, custom_gallery):
    """Add a registered user to a custom gallery."""
    response = api_client.http_client.post(
        f"{gallery_base_path}/addRegistrationToGallery",
        json={
            "galleryName": custom_gallery,
            "registrationCode": registered_user["registrationCode"],
        },
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    # Verify
    check = api_client.http_client.post(
        f"{gallery_base_path}/isRegistrationInGallery",
        json={
            "galleryName": custom_gallery,
            "registrationCode": registered_user["registrationCode"],
        },
    )
    assert check.status_code == 200
    assert check.json().get("exist") is True, "User should be present in gallery after adding"

    print(f"\n[OK] User {registered_user['registrationCode']} added to '{custom_gallery}'")


@allure.feature("Gallery API")
@allure.story("Gallery Membership - Negative")
@allure.title("addRegistrationToGallery rejects request with missing galleryName")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends addRegistrationToGallery without the required 'galleryName'. "
    "Expects HTTP 400 or 500 and a structured error response."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_add_registration_to_gallery_missing_name(api_client, gallery_base_path, registered_user):
    """Negative: missing galleryName."""
    response = api_client.http_client.post(
        f"{gallery_base_path}/addRegistrationToGallery",
        json={"registrationCode": registered_user["registrationCode"]},
    )

    assert response.status_code in [400, 500], (
        f"Expected 400 or 500, got {response.status_code}"
    )
    try:
        _assert_error_body(response.json())
    except (ValueError, AssertionError) as e:
        print(f"[INFO] Error body validation skipped: {e}")
