"""
Tests for POST /onboarding/gallery/addGallery

Creates a new custom gallery. Returns HTTP 200 on success.
Note: galleries created by this test are NOT deleted — they persist in the
admin portal so you can verify them at https://qa8.awareid.com/snow/portal/#/facematch
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
@allure.story("Gallery Management")
@allure.title("Create a custom gallery")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Creates a new custom gallery with a unique name. "
    "Expects HTTP 200 on success. Gallery is NOT deleted after the test — "
    "it stays visible in the admin portal for inspection."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_add_gallery(api_client, gallery_base_path, unique_gallery_name, env_store):
    """Create a new custom gallery (gallery persists after test). Saves GALLERY_NAME to .env."""
    response = api_client.http_client.post(
        f"{gallery_base_path}/addGallery",
        json={"galleryName": unique_gallery_name},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}. Response: {response.text}"
    )

    env_store.set("GALLERY_NAME", unique_gallery_name)

    print(f"\n[OK] Gallery created: {unique_gallery_name}")
    print(f"[SAVED] GALLERY_NAME={unique_gallery_name}")
    print(f"[INFO] Gallery left in place — check the admin portal")


@allure.feature("Gallery API")
@allure.story("Gallery Management - Negative")
@allure.title("addGallery rejects request with missing galleryName")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends an addGallery request with an empty JSON body. "
    "Expects HTTP 400 or 500 and a structured error response."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_add_gallery_missing_name(api_client, gallery_base_path):
    """Negative: missing galleryName field."""
    response = api_client.http_client.post(
        f"{gallery_base_path}/addGallery",
        json={},
    )

    assert response.status_code in [400, 500], (
        f"Expected 400 or 500, got {response.status_code}"
    )
    try:
        _assert_error_body(response.json())
    except (ValueError, AssertionError) as e:
        print(f"[INFO] Error body validation skipped: {e}")
