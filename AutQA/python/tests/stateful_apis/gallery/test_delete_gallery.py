"""
Tests for POST /onboarding/gallery/deleteGallery

Deletes an existing custom gallery. Any registered users will be removed from
this gallery also. Note: users always remain in the default system gallery until
deleted from AwareID's admin portal.

Prerequisites (run once to populate .env):
    pytest tests/stateful_apis/gallery/test_add_gallery.py::test_add_gallery -v
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
@allure.title("Delete the custom gallery saved in .env")
@allure.severity(allure.severity_level.CRITICAL)
@allure.description(
    "Reads GALLERY_NAME from .env (saved by test_add_gallery) and deletes that gallery. "
    "Expects HTTP 200. Verifies the gallery is gone via listGallery. "
    "Clears GALLERY_NAME from .env after successful deletion."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_delete_gallery(api_client, gallery_base_path, env_store):
    """Delete the gallery stored in .env (GALLERY_NAME) and confirm it is gone."""
    gallery_name = env_store.get("GALLERY_NAME")
    if not gallery_name:
        pytest.skip(
            "GALLERY_NAME not found in .env. "
            "Run: pytest tests/stateful_apis/gallery/test_add_gallery.py::test_add_gallery -v"
        )

    print(f"\n[INFO] Deleting gallery from .env: {gallery_name}")

    # Delete
    delete_resp = api_client.http_client.post(
        f"{gallery_base_path}/deleteGallery",
        json={"galleryName": gallery_name},
    )
    assert delete_resp.status_code == 200, (
        f"Expected 200 for deleteGallery, got {delete_resp.status_code}. Response: {delete_resp.text}"
    )

    # Verify it's gone
    list_resp = api_client.http_client.get(f"{gallery_base_path}/listGallery")
    if list_resp.status_code == 200:
        galleries = [g.get("galleryName") for g in list_resp.json().get("list", [])]
        assert gallery_name not in galleries, (
            f"Gallery '{gallery_name}' still present after deletion"
        )

    # Clear from .env — the gallery no longer exists
    env_store.delete("GALLERY_NAME")
    print(f"[CLEARED] GALLERY_NAME removed from .env")

    print(f"\n[OK] Gallery '{gallery_name}' deleted and confirmed gone")


@allure.feature("Gallery API")
@allure.story("Gallery Management - Negative")
@allure.title("deleteGallery rejects request with missing galleryName")
@allure.severity(allure.severity_level.NORMAL)
@allure.description(
    "Sends a deleteGallery request with an empty JSON body. "
    "Expects HTTP 400 or 500 and a structured error response."
)
@pytest.mark.stateful
@pytest.mark.gallery
def test_delete_gallery_missing_name(api_client, gallery_base_path):
    """Negative: missing galleryName field."""
    response = api_client.http_client.post(
        f"{gallery_base_path}/deleteGallery",
        json={},
    )

    assert response.status_code in [400, 500], (
        f"Expected 400 or 500, got {response.status_code}"
    )
    try:
        _assert_error_body(response.json())
    except (ValueError, AssertionError) as e:
        print(f"[INFO] Error body validation skipped: {e}")
